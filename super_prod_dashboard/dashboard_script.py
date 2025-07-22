import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px

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

cumulative_fig = px.bar(
    cumulative_df,
    x='done_date',
    y='cumulative_minutes',
    template='plotly_dark',
    labels={'done_date': 'Date', 'cumulative_minutes': 'Cumulative Minutes Worked'},
    title='Accumulated Work Time Across Days (Minutes)'
)

# --- Streamlit App ---
st.set_page_config(page_title="Super Productivity Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("Super Productivity Dashboard")

col1, col2 = st.columns(2)
with col1:
    st.header("Tasks Completed Over Time")
    fig1 = px.bar(
        tasks_per_day.sort_values('done_date'),
        x='done_date',
        y='tasks_completed',
        template='plotly_dark',
        labels={'done_date': 'Date', 'tasks_completed': 'Tasks Completed'},
        category_orders={'done_date': list(tasks_per_day['done_date'].astype(str))}
    )
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.header("Time Spent Per Project (minutes)")
    fig2 = px.pie(
        time_per_project.sort_values('title_project'),
        names='title_project',
        values='timeSpent',
        template='plotly_dark',
        labels={'title_project': 'Project', 'timeSpent': 'Time Spent (min)'}
    )
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.header("Time Spent Per Day Per Project (Stacked)")
    fig3 = px.bar(
        grouped,
        x='done_date',
        y='timeSpent',
        color='title_project',
        template='plotly_dark',
        labels={'timeSpent': 'Time Spent (min)', 'done_date': 'Date', 'title_project': 'Project'},
        title='Time Spent Per Day Per Project (Stacked)',
        category_orders={'done_date': date_order}
    )
    st.plotly_chart(fig3, use_container_width=True)
with col4:
    st.header("Average Time Spent Per Workday")
    fig4 = px.bar(
        avg_by_weekday,
        x='weekday',
        y='timeSpent',
        template='plotly_dark',
        labels={'timeSpent': 'Average Time Spent (min)', 'weekday': 'Day of Week'},
        title='Average Time Spent Per Workday',
        category_orders={'weekday': weekday_order}
    )
    st.plotly_chart(fig4, use_container_width=True)

# New row for cumulative plot
st.header("Accumulated Work Time Across Days (Minutes)")
st.plotly_chart(cumulative_fig, use_container_width=True)