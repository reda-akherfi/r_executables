import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
# Add import for streamlit-calendar
from streamlit_calendar import calendar
import math

# --- Load JSON data ---
with open('super-productivity-backup.json', 'r', encoding='utf-8') as f:
    data = json.load(f)['data']

# --- Normalize Tasks ---
tasks = []
for task_id, task in data['task']['entities'].items():
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

# --- Tasks Completed Over Time ---
df_done = df_tasks[df_tasks['isDone'] & df_tasks['doneOn'].notnull()].copy()
df_done['done_date'] = df_done['doneOn'].dt.date
tasks_per_day = df_done.groupby('done_date').size().reset_index(name='tasks_completed')

# --- Time Spent Per Project ---
time_per_project = df_tasks.groupby('title_project')['timeSpent'].sum().reset_index()

# --- Stacked Bar: Time Spent Per Day Per Project ---
df_stacked = df_tasks[df_tasks['isDone'] & df_tasks['doneOn'].notnull()].copy()
df_stacked['done_date'] = df_stacked['doneOn'].dt.date
grouped = df_stacked.groupby(['done_date', 'title_project'])['timeSpent'].sum().reset_index()
date_order = list(grouped['done_date'].astype(str).unique())

# --- Average Time Per Workday ---
df_avg = df_tasks[df_tasks['isDone'] & df_tasks['doneOn'].notnull()].copy()
df_avg['done_date'] = df_avg['doneOn'].dt.date
df_avg['weekday'] = df_avg['doneOn'].dt.day_name()
daily = df_avg.groupby(['done_date', 'weekday'])['timeSpent'].sum().reset_index()
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
avg_by_weekday = daily.groupby('weekday')['timeSpent'].mean().reindex(weekday_order).reset_index()

# --- Cumulative Work Time Plot ---
cumulative_df = tasks_per_day.sort_values('done_date').copy()
cumulative_df['cumulative_minutes'] = cumulative_df['tasks_completed'].copy()
if 'timeSpent' in df_done.columns:
    # If you want cumulative time spent, not just tasks completed
    time_per_day = df_done.groupby('done_date')['timeSpent'].sum().reset_index()
    cumulative_df = time_per_day.sort_values('done_date').copy()
    cumulative_df['cumulative_minutes'] = cumulative_df['timeSpent'].cumsum()
else:
    cumulative_df['cumulative_minutes'] = cumulative_df['tasks_completed'].cumsum()

# Create all figures before layout
fig1 = px.bar(
    tasks_per_day.sort_values('done_date'),
    x='done_date',
    y='tasks_completed',
    template='plotly_dark',
    labels={'done_date': 'Date', 'tasks_completed': 'Tasks Completed'},
    category_orders={'done_date': list(tasks_per_day['done_date'].astype(str))},
    title='Tasks Completed Over Time'
)
fig1.update_layout(
    plot_bgcolor='#222',
    paper_bgcolor='#222',
    margin=dict(l=20, r=20, t=40, b=20),
    font_color='#fff',
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=False, zeroline=False),
    shapes=[
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color="#444", width=3),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
    ]
)

fig2 = px.pie(
    time_per_project.sort_values('title_project'),
    names='title_project',
    values='timeSpent',
    template='plotly_dark',
    labels={'title_project': 'Project', 'timeSpent': 'Time Spent (min)'},
    title='Time Spent Per Project (minutes)'
)
fig2.update_layout(
    plot_bgcolor='#222',
    paper_bgcolor='#222',
    margin=dict(l=20, r=20, t=40, b=20),
    font_color='#fff',
    shapes=[
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color="#444", width=3),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
    ]
)

fig3 = px.bar(
    grouped,
    x='done_date',
    y='timeSpent',
    color='title_project',
    template='plotly_dark',
    labels={'timeSpent': 'Time Spent (min)', 'done_date': 'Date', 'title_project': 'Project'},
    title='Time Spent/day/project',
    category_orders={'done_date': date_order}
)
fig3.update_layout(
    plot_bgcolor='#222',
    paper_bgcolor='#222',
    margin=dict(l=20, r=20, t=40, b=20),
    font_color='#fff',
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=False, zeroline=False),
    shapes=[
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color="#444", width=3),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
    ]
)

fig4 = px.bar(
    avg_by_weekday,
    x='weekday',
    y='timeSpent',
    template='plotly_dark',
    labels={'timeSpent': 'Average Time Spent (min)', 'weekday': 'Day of Week'},
    title='Average Time Spent Per Workday',
    category_orders={'weekday': weekday_order}
)
fig4.update_layout(
    plot_bgcolor='#222',
    paper_bgcolor='#222',
    margin=dict(l=20, r=20, t=40, b=20),
    font_color='#fff',
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=False, zeroline=False),
    shapes=[
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color="#444", width=3),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
    ]
)

cumulative_fig = px.bar(
    cumulative_df,
    x='done_date',
    y='cumulative_minutes',
    template='plotly_dark',
    labels={'done_date': 'Date', 'cumulative_minutes': 'Cumulative Minutes Worked'},
    title='Accumulated Work Time Across Days (Minutes)'
)
cumulative_fig.update_layout(
    plot_bgcolor='#222',
    paper_bgcolor='#222',
    margin=dict(l=20, r=20, t=40, b=20),
    font_color='#fff',
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=False, zeroline=False),
    shapes=[
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color="#444", width=3),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
    ]
)

# --- Streamlit App ---
st.set_page_config(page_title="Super Productivity Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Interactive Calendar (streamlit-calendar) ---
# Prepare events: one per day worked, with minutes worked as title
calendar_events = []
for idx, row in tasks_per_day.iterrows():
    date_str = row['done_date'].strftime('%Y-%m-%d')
    minutes = df_done[df_done['done_date'] == row['done_date']]['timeSpent'].sum()
    # Use green dot emoji and minutes as title
    event_title = f"🟢 {int(minutes)} min"
    calendar_events.append({
        "title": event_title,
        "start": date_str,
        "end": date_str,
        "allDay": True,
        "display": "block",
    })

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

# --- Remove Plot Height Slider ---
# (No slider in sidebar, set fixed height for plots)
fixed_plot_height = 400

# Set height for all plotly figures for a tighter grid, add more top margin, and truly center titles
fig1.update_layout(
    height=fixed_plot_height,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Tasks Completed Over Time', 'x': 0.5, 'xanchor': 'center'}
)
fig2.update_layout(
    height=fixed_plot_height,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Time Spent Per Project (minutes)', 'x': 0.5, 'xanchor': 'center'}
)
fig3.update_layout(
    height=fixed_plot_height,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Time Spent/day/project', 'x': 0.5, 'xanchor': 'center'}
)
fig4.update_layout(
    height=fixed_plot_height,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Average Time Spent Per Workday', 'x': 0.5, 'xanchor': 'center'}
)
cumulative_fig.update_layout(
    height=fixed_plot_height,
    margin=dict(l=20, r=20, t=120, b=20),
    title={'text': 'Accumulated Work Time Across Days (Minutes)', 'x': 0.5, 'xanchor': 'center'}
)

# --- Paginated Dashboard: Page 1 = calendar, Pages 2+ = 1x2 grid of plots ---
# List all plots in the desired order: accumulated, fig3, fig4, fig1, fig2
plot_keys = ['accumulated', 'fig3', 'fig4', 'fig1', 'fig2']
plot_objs = {
    'accumulated': cumulative_fig,
    'fig3': fig3,
    'fig4': fig4,
    'fig1': fig1,
    'fig2': fig2,
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