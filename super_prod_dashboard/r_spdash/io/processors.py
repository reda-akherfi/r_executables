"""
Data processing functions for the Super Productivity Dashboard.
"""
import pandas as pd
from datetime import datetime
from collections import defaultdict


def normalize_tasks(data):
    """
    Normalize task data from SuperProductivity JSON format.
    
    Args:
        data (dict): Raw SuperProductivity data
        
    Returns:
        pd.DataFrame: Normalized task data
    """
    tasks = []
    for task_id, task in data['task']['entities'].items():
        is_leaf = not task.get('subTaskIds')
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
    return pd.DataFrame(tasks)


def normalize_projects(data):
    """
    Normalize project data from SuperProductivity JSON format.
    
    Args:
        data (dict): Raw SuperProductivity data
        
    Returns:
        pd.DataFrame: Normalized project data
    """
    projects = []
    for proj_id, proj in data['project']['entities'].items():
        projects.append({
            'id': proj['id'],
            'title': proj['title'],
        })
    return pd.DataFrame(projects)


def build_time_by_day(df_tasks, data):
    """
    Build a DataFrame of all time spent per day (leaf tasks only).
    
    Args:
        df_tasks (pd.DataFrame): Normalized task data
        data (dict): Raw SuperProductivity data
        
    Returns:
        pd.DataFrame: DataFrame with columns ['date', 'project', 'minutes']
    """
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
    
    return pd.DataFrame(rows) 