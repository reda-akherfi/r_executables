import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
# Add import for streamlit-calendar
from streamlit_calendar import calendar
import math
import plotly.graph_objects as go
import numpy as np
from collections import defaultdict
from data_loader import load_super_productivity_data
from color_sync import create_color_sync

# --- Load JSON data ---
try:
    data = load_super_productivity_data()['data']
    # Initialize color and icon synchronization
    color_sync = create_color_sync(data)
except Exception as e:
    st.error(f"Error loading SuperProductivity data: {e}")
    st.stop()

# --- Normalize Tasks ---
tasks = []
for task_id, task in data['task']['entities'].items():
    is_leaf = not task.get('subTaskIds')  # True if no subtasks
    tasks.append({
        'id': task['id'],
        'title': task['title'],
        'isDone': task['isDone'],
        'timeSpent': task['timeSpent'] / 1000 / 60,  # ms to minutes
        'timeEstimate': task['timeEstimate'] / 1000 / 60 if task['timeEstimate'] else None,
        'created': datetime.fromtimestamp(task['created'] / 1000),
        'dueDay': task.get('dueDay'),
        'doneOn': datetime.fromtimestamp(task['doneOn'] / 1000) if task.get('doneOn') else None,
        'projectId': task['projectId'],
        'notes': task.get('notes', ''),
        'tagIds': task.get('tagIds', []),
        'is_leaf': is_leaf,
    })
df_tasks = pd.DataFrame(tasks)

# --- Normalize Projects ---
projects = []
for proj_id, proj in data['project']['entities'].items():
    projects.append({
        'id': proj['id'],
        'title': proj['title'],
    })
df_projects = pd.DataFrame(projects)

# --- Merge for richer info ---
df_tasks = df_tasks.merge(df_projects, left_on='projectId', right_on='id', suffixes=('', '_project'))

# --- Build a DataFrame of all time spent per day (leaf tasks only) ---
all_time_by_day = defaultdict(lambda: defaultdict(float))  # {date: {project: minutes}}
for _, task in df_tasks[df_tasks['is_leaf']].iterrows():
    project = task['title_project']
    if 'timeSpentOnDay' in data['task']['entities'][task['id']]:
        for day, ms in data['task']['entities'][task['id']]['timeSpentOnDay'].items():
            minutes = ms / 1000 / 60
            all_time_by_day[day][project] += minutes

# Build a DataFrame: columns = ['date', 'project', 'minutes']
rows = []
for day, proj_dict in all_time_by_day.items():
    for project, minutes in proj_dict.items():
        rows.append({'date': pd.to_datetime(day), 'project': project, 'minutes': minutes})
df_all_time = pd.DataFrame(rows)

# --- Calendar: show a green dot and minutes for every day with time spent ---
calendar_events = []
for day, group in df_all_time.groupby('date'):
    total_minutes = group['minutes'].sum()
    calendar_events.append({
        "title": f"🟢 {int(total_minutes)} min",
        "start": day.strftime('%Y-%m-%d'),
        "end": day.strftime('%Y-%m-%d'),
        "allDay": True,
        "display": "block",
    })

# --- Helper: Format minutes as 'Xh Ym' ---
def minutes_to_hm_str(minutes):
    minutes = int(round(minutes))
    h = minutes // 60
    m = minutes % 60
    if h > 0:
        return f"{h}h {m}m"
    else:
        return f"{m}m"

# --- Tasks Completed Over Time (now: All Time Spent Per Day) ---
df_time_per_day = df_all_time.groupby('date')['minutes'].sum().reset_index()
df_time_per_day['hm_str'] = df_time_per_day['minutes'].apply(minutes_to_hm_str)

fig1 = go.Figure(data=[go.Bar(
    x=df_time_per_day['date'],
    y=df_time_per_day['minutes'],
    marker_color='#636efa',
    customdata=df_time_per_day['hm_str'],
    hovertemplate='%{x}<br>%{customdata}<extra></extra>'
)])
fig1.update_layout(
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'All Time Spent Per Day (min)', 'x': 0.5, 'xanchor': 'center'}
)

# --- Time Spent Per Project ---
time_per_project = df_all_time.groupby('project')['minutes'].sum().reset_index()
time_per_project = df_projects[['title']].merge(
    time_per_project, left_on='title', right_on='project', how='left'
)
time_per_project['minutes'] = time_per_project['minutes'].fillna(0)
time_per_project['hm_str'] = time_per_project['minutes'].apply(minutes_to_hm_str)

# Add synchronized colors and display names with icons
time_per_project['display_name'] = time_per_project['title'].apply(color_sync.get_project_display_name)
time_per_project['color'] = time_per_project['title'].apply(color_sync.get_project_color)

fig2 = go.Figure(data=[go.Pie(
    labels=time_per_project['display_name'],
    values=time_per_project['minutes'],
    hole=0,
    customdata=time_per_project['hm_str'],
    hovertemplate='%{label}: %{customdata}<extra></extra>',
    textfont=dict(color='white'),
    textposition='outside',
    textinfo='label+percent',
    marker=dict(colors=time_per_project['color'])
)])
fig2.update_layout(
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    height=400,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Time Spent Per Project (minutes)', 'x': 0.5, 'xanchor': 'center'}
)

# --- Stacked Bar: Time Spent Per Day Per Project ---
fig3 = go.Figure()
for project in df_all_time['project'].unique():
    proj_data = df_all_time[df_all_time['project'] == project].copy()
    proj_data['hm_str'] = proj_data['minutes'].apply(minutes_to_hm_str)
    project_display_name = color_sync.get_project_display_name(project)
    project_color = color_sync.get_project_color(project)
    fig3.add_bar(x=proj_data['date'], y=proj_data['minutes'], name=project_display_name,
                 customdata=proj_data['hm_str'],
                 hovertemplate='%{x}<br>%{customdata}<extra></extra>',
                 marker_color=project_color)
fig3.update_layout(
    barmode='stack',
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Time Spent/day/project', 'x': 0.5, 'xanchor': 'center'}
)

# --- Average Time Per Workday (Stacked by Project, All Weekdays) ---
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# Step 1: Sum minutes per day per project
df_daily_proj = df_all_time.groupby(['date', 'project'])['minutes'].sum().reset_index()
# Step 2: Add weekday
df_daily_proj['weekday'] = df_daily_proj['date'].dt.day_name()
# Step 3: Average per weekday per project
df_avg_workday_proj = df_daily_proj.groupby(['weekday', 'project'])['minutes'].mean().reset_index()

# Ensure all combinations of weekday and project exist
all_projects = df_avg_workday_proj['project'].unique()
full_index = pd.MultiIndex.from_product([weekday_order, all_projects], names=['weekday', 'project'])
df_avg_workday_proj = df_avg_workday_proj.set_index(['weekday', 'project']).reindex(full_index, fill_value=0).reset_index()
df_avg_workday_proj['weekday'] = pd.Categorical(df_avg_workday_proj['weekday'], categories=weekday_order, ordered=True)
df_avg_workday_proj = df_avg_workday_proj.sort_values(['weekday', 'project'])

fig4 = go.Figure()
for project in all_projects:
    proj_data = df_avg_workday_proj[df_avg_workday_proj['project'] == project].copy()
    proj_data['hm_str'] = proj_data['minutes'].apply(minutes_to_hm_str)
    project_display_name = color_sync.get_project_display_name(project)
    project_color = color_sync.get_project_color(project)
    fig4.add_bar(x=proj_data['weekday'], y=proj_data['minutes'], name=project_display_name,
                 customdata=proj_data['hm_str'],
                 hovertemplate='%{x}<br>%{customdata}<extra></extra>',
                 marker_color=project_color)
fig4.update_layout(
    barmode='stack',
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Average Time Spent Per Workday (Stacked by Project)', 'x': 0.5, 'xanchor': 'center'}
)

# --- Cumulative Work Time Plot ---
df_time_per_day = df_time_per_day.sort_values('date')
df_time_per_day['cumulative_minutes'] = df_time_per_day['minutes'].cumsum()
df_time_per_day['cumulative_hm_str'] = df_time_per_day['cumulative_minutes'].apply(minutes_to_hm_str)
cumulative_fig = go.Figure(data=[go.Bar(
    x=df_time_per_day['date'],
    y=df_time_per_day['cumulative_minutes'],
    marker_color='#636efa',
    customdata=df_time_per_day['cumulative_hm_str'],
    hovertemplate='%{x}<br>%{customdata}<extra></extra>'
)])
cumulative_fig.update_layout(
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Accumulated Work Time Across Days (Minutes)', 'x': 0.5, 'xanchor': 'center'}
)

# --- Create Pie Plot for Tag Distribution ---
# Calculate total time spent per tag, and for untagged work

df_tags = df_tasks[df_tasks['timeSpent'] > 0].copy()  # Only tasks with time spent
if 'tagIds' not in df_tags.columns:
    df_tags['tagIds'] = [[] for _ in range(len(df_tags))]
# If tagIds is not a list, convert to list
if not isinstance(df_tags['tagIds'].iloc[0], list):
    df_tags['tagIds'] = df_tags['tagIds'].apply(lambda x: [x] if pd.notnull(x) else [])

# Mark untagged rows
df_tags['has_tag'] = df_tags['tagIds'].apply(lambda x: bool(x) and any(x))

# Time spent for tagged tasks
df_tagged = df_tags[df_tags['has_tag']].explode('tagIds')
tag_time = df_tagged.groupby('tagIds')['timeSpent'].sum().reset_index()
tag_time = tag_time[tag_time['tagIds'].notnull() & (tag_time['tagIds'] != '')]
# Map tagIds to tag names if available
if 'tag' in data and 'entities' in data['tag']:
    tag_map = {k: v['title'] for k, v in data['tag']['entities'].items()}
    tag_time['tag'] = tag_time['tagIds'].map(tag_map)
else:
    tag_time['tag'] = tag_time['tagIds']

# Time spent for untagged tasks
untagged_time = df_tags[~df_tags['has_tag']]['timeSpent'].sum()

# Combine
pie_labels = list(tag_time['tag']) if not tag_time.empty else []
pie_values = list(tag_time['timeSpent']) if not tag_time.empty else []
pie_hm_strs = [minutes_to_hm_str(m) for m in pie_values]

# Add synchronized colors and display names with icons
pie_display_labels = []
pie_colors = []
for label in pie_labels:
    if label == 'Untagged':
        pie_display_labels.append('Untagged')
        pie_colors.append('grey')
    else:
        pie_display_labels.append(color_sync.get_tag_display_name(label))
        pie_colors.append(color_sync.get_tag_color(label))

if untagged_time > 0 or not pie_labels:
    pie_display_labels.append('Untagged')
    pie_values.append(untagged_time)
    pie_hm_strs.append(minutes_to_hm_str(untagged_time))
    pie_colors.append('grey')

fig_tags = go.Figure(data=[go.Pie(labels=pie_display_labels, values=pie_values, marker=dict(colors=pie_colors), hole=0,
                                  customdata=pie_hm_strs,
                                  hovertemplate='%{label}: %{customdata}<extra></extra>',
                                  textfont=dict(color='white'),
                                  textposition='outside',
                                  textinfo='label+percent',
                                  )])
fig_tags.update_layout(
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    height=400,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Time Spent Distribution by Tag', 'x': 0.5, 'xanchor': 'center'}
)

# --- Simple Counter Visualizations ---
simple_counters = data['simpleCounter']['entities']

# Water Intake Tracker
water_counter = simple_counters['wQuxogx-iByRYzzw9_LdZ']
water_data = water_counter.get('countOnDay', {})
water_dates = list(water_data.keys())
water_liters = [v * 1.0 for v in water_data.values()]  # 1 unit = 1L
bar_colors = ['#2ca02c' if v >= 2 else '#d62728' for v in water_liters]  # green if >=2L, else red

df_water = pd.DataFrame({'date': pd.to_datetime(water_dates), 'liters': water_liters, 'color': bar_colors})
fig_water = go.Figure(data=[go.Bar(x=df_water['date'], y=df_water['liters'], marker_color=df_water['color'])])
fig_water.add_hline(y=2, line_dash='dash', line_color='#888', annotation_text='2L Recommended', annotation_position='top left')
fig_water.update_layout(
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    height=400,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Daily Water Intake (L)', 'x': 0.5, 'xanchor': 'center'}
)

# Media Watching Tracker
media_counter = simple_counters['a53564Qzc3w2LHXE6c-1_']
media_data = media_counter.get('countOnDay', {})
media_dates = list(media_data.keys())
media_hours = [v / 1000 / 60 / 60 for v in media_data.values()]
bar_colors_media = ['#2ca02c' if v < 4 else '#d62728' for v in media_hours]  # green if <4h, else red

df_media = pd.DataFrame({'date': pd.to_datetime(media_dates), 'hours': media_hours, 'color': bar_colors_media})
fig_media = go.Figure(data=[go.Bar(x=df_media['date'], y=df_media['hours'], marker_color=df_media['color'])])
fig_media.add_hline(y=4, line_dash='dash', line_color='#888', annotation_text='4h Limit', annotation_position='top left')
fig_media.update_layout(
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    height=400,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Daily Media Watching (Hours)', 'x': 0.5, 'xanchor': 'center'}
)

# Workout Tracker
workout_counter = simple_counters['dD4T3Ulg16FpTqlkwTtpq']
workout_data = workout_counter.get('countOnDay', {})
workout_dates = list(workout_data.keys())
workout_hours = [v / 1000 / 60 / 60 for v in workout_data.values()]
df_workout = pd.DataFrame({'date': pd.to_datetime(workout_dates), 'hours': workout_hours})
fig_workout = go.Figure(data=[go.Bar(x=df_workout['date'], y=df_workout['hours'], marker_color='#2ca02c')])
fig_workout.update_layout(
    plot_bgcolor='#000',
    paper_bgcolor='#000',
    height=400,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Daily Workout Time (Hours)', 'x': 0.5, 'xanchor': 'center'}
)

extra_plot_keys = ['water', 'media', 'workout']
extra_plot_objs = {
    'water': fig_water,
    'media': fig_media,
    'workout': fig_workout,
}

# --- Streamlit App ---
st.set_page_config(page_title="Super Productivity Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Interactive Calendar (streamlit-calendar) ---
calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,dayGridWeek,dayGridDay"
    },
    "height": 500,
    "locale": "en",
    "eventDisplay": "block",
    "dayMaxEventRows": 2,
    "fixedWeekCount": False,
    "showNonCurrentDates": True,
    "selectable": False,
    "editable": False,
}
# Remove custom CSS for dot/minutes, keep only the rest if needed
custom_css = """
    .fc-daygrid-day-number {
        color: #fff;
    }
"""

st.markdown("""
    <style>
    .plot-box {
        border: 2px solid #444;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background: #222;
    }
    </style>
""", unsafe_allow_html=True)

# Add custom CSS to force alignment in columns
st.markdown("""
    <style>
    .element-container, .stColumn {
        padding: 0 !important;
        margin: 0 !important;
        display: flex;
        flex-direction: column;
        align-items: stretch;
        justify-content: stretch;
    }
    .stPlotlyChart, .stPlotlyChart > div {
        height: 100% !important;
        min-height: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Paginated Dashboard: Page 1 = calendar, Pages 2+ = 1x2 grid of plots ---
# List all plots in the desired order: accumulated, fig3, fig4, fig1, fig2, tags_pie
plot_keys = ['accumulated', 'fig3', 'fig4', 'fig1', 'fig2', 'tags_pie'] + extra_plot_keys
plot_objs = {
    'accumulated': cumulative_fig,
    'fig3': fig3,
    'fig4': fig4,
    'fig1': fig1,
    'fig2': fig2,
    'tags_pie': fig_tags,
    **extra_plot_objs
}

plots_per_page = 2  # 1x2 grid for pages 2+
num_plot_pages = math.ceil(len(plot_keys) / plots_per_page)
num_pages = 1 + num_plot_pages  # 1 for calendar, rest for plots

if 'plot_page' not in st.session_state:
    st.session_state['plot_page'] = 0
page = st.session_state['plot_page']

# Navigation arrows always visible, but disabled as appropriate
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
with col_nav1:
    st.button('⬅️', key='prev_page', disabled=(page == 0), on_click=lambda: st.session_state.update({'plot_page': max(0, page - 1)}))
with col_nav2:
    st.markdown(f"<h4 style='text-align:center; margin-bottom:0;'>Plots Page {page+1} of {num_pages}</h4>", unsafe_allow_html=True)
with col_nav3:
    st.button('➡️', key='next_page', disabled=(page == num_pages - 1), on_click=lambda: st.session_state.update({'plot_page': min(num_pages - 1, page + 1)}))

if page == 0:
    # Page 1: Calendar only, centered, natural height
    st.markdown(f"<div style='display:flex;justify-content:center;align-items:center;'>", unsafe_allow_html=True)
    calendar(
        events=calendar_events,
        options=calendar_options,
        custom_css=custom_css,
        key="work-calendar"
    )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    # Pages 2+: 1x2 grid of plots
    plot_page_idx = page - 1
    start_idx = plot_page_idx * plots_per_page
    end_idx = start_idx + plots_per_page
    plots_to_show = plot_keys[start_idx:end_idx]
    while len(plots_to_show) < plots_per_page:
        plots_to_show.append(None)
    cols_list = st.columns(2, gap="small")
    for col in range(2):
        plot_key = plots_to_show[col]
        with cols_list[col]:
            if plot_key is not None:
                st.plotly_chart(plot_objs[plot_key], use_container_width=True)
            else:
                st.empty()