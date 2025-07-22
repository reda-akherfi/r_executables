import json
import pandas as pd
from datetime import datetime
import plotly.express as px
from dash import Dash, dcc, html

# Load JSON data
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

# --- Example: Tasks Completed Over Time ---
df_done = df_tasks.loc[df_tasks['isDone'] & df_tasks['doneOn'].notnull()].copy()
df_done['done_date'] = df_done['doneOn'].dt.date
tasks_per_day = df_done.groupby('done_date').size().reset_index(name='tasks_completed')

# --- Example: Time Spent Per Project ---
time_per_project = df_tasks.groupby('title_project')['timeSpent'].sum().reset_index()

# --- Dash App ---
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Super Productivity Dashboard"),
    html.H2("Tasks Completed Over Time"),
    dcc.Graph(figure=px.bar(tasks_per_day, x='done_date', y='tasks_completed')),
    html.H2("Time Spent Per Project (minutes)"),
    dcc.Graph(figure=px.pie(time_per_project, names='title_project', values='timeSpent')),
    # Add more graphs here!
])

if __name__ == '__main__':
    app.run(debug=True)