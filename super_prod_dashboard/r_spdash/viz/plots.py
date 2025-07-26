"""
Plot creation functions for the Super Productivity Dashboard.
"""
import pandas as pd
import plotly.graph_objects as go
from ..utils.helpers import minutes_to_hm_str


def create_calendar_events(df_all_time):
    """
    Create calendar events from time data.
    
    Args:
        df_all_time (pd.DataFrame): DataFrame with date, project, minutes columns
        
    Returns:
        list: List of calendar event dictionaries
    """
    events = []
    for day, group in df_all_time.groupby('date'):
        total_minutes = group['minutes'].sum()
        events.append({
            "title": f"🟢 {int(total_minutes)} min",
            "start": day.strftime('%Y-%m-%d'),
            "end": day.strftime('%Y-%m-%d'),
            "allDay": True,
            "display": "block",
        })
    return events


def create_figures(df_all_time, df_projects, color_sync):
    """
    Create all main dashboard figures.
    
    Args:
        df_all_time (pd.DataFrame): Time data by day and project
        df_projects (pd.DataFrame): Project data
        color_sync: Color synchronization object
        
    Returns:
        tuple: (fig1, fig2, fig3, fig4, cumulative_fig) - All plotly figures
    """
    # All Time Spent Per Day
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

    # Time Spent Per Project
    time_per_project = df_all_time.groupby('project')['minutes'].sum().reset_index()
    time_per_project = df_projects[['title']].merge(
        time_per_project, left_on='title', right_on='project', how='left'
    )
    time_per_project['minutes'] = time_per_project['minutes'].fillna(0)
    time_per_project['hm_str'] = time_per_project['minutes'].apply(minutes_to_hm_str)
    time_per_project['display_name'] = (
        time_per_project['title'].apply(color_sync.get_project_display_name)
    )
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

    # Stacked Bar: Time Spent Per Day Per Project
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

    # Average Time Per Workday (Stacked by Project, All Weekdays)
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_daily_proj = df_all_time.groupby(['date', 'project'])['minutes'].sum().reset_index()
    df_daily_proj['weekday'] = df_daily_proj['date'].dt.day_name()
    df_avg_workday_proj = (
        df_daily_proj.groupby(['weekday', 'project'])['minutes'].mean().reset_index()
    )

    all_projects = df_avg_workday_proj['project'].unique()
    full_index = (
        pd.MultiIndex.from_product([weekday_order, all_projects], names=['weekday', 'project'])
    )
    df_avg_workday_proj = (
        df_avg_workday_proj.set_index(['weekday', 'project'])
                            .reindex(full_index, fill_value=0).reset_index()
    )
    df_avg_workday_proj['weekday'] = (
        pd.Categorical(df_avg_workday_proj['weekday'], categories=weekday_order, ordered=True)
    )
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
        title={'text': 'Average Time Spent Per Workday (Stacked by Project)',
                 'x': 0.5,
                  'xanchor': 'center'
            }
    )

    # Cumulative Work Time Plot
    df_time_per_day = df_time_per_day.sort_values('date')
    df_time_per_day['cumulative_minutes'] = df_time_per_day['minutes'].cumsum()
    df_time_per_day['cumulative_hm_str'] = (
        df_time_per_day['cumulative_minutes'].apply(minutes_to_hm_str)
    )

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

    return fig1, fig2, fig3, fig4, cumulative_fig


def create_tags_pie_chart(df_tasks, data, color_sync):
    """
    Create pie chart for tag distribution, including all tags (even those with zero minutes),
    but excluding tags in the exclusion list.
    
    Args:
        df_tasks (pd.DataFrame): Normalized task data
        data (dict): Raw SuperProductivity data
        color_sync: Color synchronization object
        
    Returns:
        go.Figure: Tags pie chart
    """
    # Exclusion list for tags
    excluded_tags = {"Today"}

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
        tag_map = {}
        tag_time['tag'] = tag_time['tagIds']

    # --- Ensure all tags are present, even if zero ---
    all_tags = [t for t in tag_map.values() if t not in excluded_tags] if tag_map else []
    tag_time_dict = dict(zip(tag_time['tag'], tag_time['timeSpent']))
    pie_labels = list(all_tags)
    pie_values = [tag_time_dict.get(label, 0) for label in pie_labels]
    pie_hm_strs = [minutes_to_hm_str(m) for m in pie_values]

    # Add synchronized colors and display names with icons
    pie_display_labels = []
    pie_colors = []
    for label in pie_labels:
        pie_display_labels.append(color_sync.get_tag_display_name(label))
        pie_colors.append(color_sync.get_tag_color(label))

    # Time spent for untagged tasks
    untagged_time = df_tags[~df_tags['has_tag']]['timeSpent'].sum()
    if untagged_time > 0 or not pie_labels:
        pie_display_labels.append('Untagged')
        pie_values.append(untagged_time)
        pie_hm_strs.append(minutes_to_hm_str(untagged_time))
        pie_colors.append('grey')

    fig_tags = go.Figure(data=[go.Pie(
        labels=pie_display_labels,
        values=pie_values,
        marker=dict(colors=pie_colors),
        hole=0,
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

    return fig_tags


def create_simple_counter_plots(data):
    """
    Create plots for simple counters (water, media, workout).
    
    Args:
        data (dict): Raw SuperProductivity data
        
    Returns:
        dict: Dictionary with water, media, and workout figures
    """
    simple_counters = data['simpleCounter']['entities']

    # Water Intake Tracker
    water_counter = simple_counters['wQuxogx-iByRYzzw9_LdZ']
    water_data = water_counter.get('countOnDay', {})
    water_dates = list(water_data.keys())
    # 1 unit = 1L
    water_liters = [v * 1.0 for v in water_data.values()]
    # green if >=2L, else red
    bar_colors = ['#2ca02c' if v >= 2 else '#d62728' for v in water_liters]

    df_water = (
        pd.DataFrame({'date': pd.to_datetime(water_dates),
         'liters': water_liters,
          'color': bar_colors})
    )
    fig_water = go.Figure(data=[go.Bar(x=df_water['date'],
        y=df_water['liters'],
        marker_color=df_water['color'])])
    fig_water.add_hline(y=2,
                 line_dash='dash',
                  line_color='#888',
                   annotation_text='2L Recommended',
                    annotation_position='top left')
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
    # green if <4h, else red
    bar_colors_media = ['#2ca02c' if v < 4 else '#d62728' for v in media_hours]

    # Human-readable time for media
    media_hm_strs = [minutes_to_hm_str(h * 60) for h in media_hours]
    df_media = pd.DataFrame({'date': pd.to_datetime(media_dates),
         'hours': media_hours,
         'color': bar_colors_media,
         'hm_str': media_hm_strs})
    fig_media = go.Figure(data=[go.Bar(
        x=df_media['date'],
        y=df_media['hours'],
        marker_color=df_media['color'],
        customdata=df_media['hm_str'],
        hovertemplate='%{x}<br>%{customdata}<extra></extra>'
    )])
    fig_media.add_hline(y=4,
     line_dash='dash',
      line_color='#888',
       annotation_text='4h Limit',
        annotation_position='top left'
        )
    fig_media.update_layout(
        plot_bgcolor='#000',
        paper_bgcolor='#000',
        height=400,
        margin=dict(l=20, r=20, t=120, b=20),
        title={'text': 'Daily Media Watching (Hours)', 'x': 0.5, 'xanchor': 'center'},
        yaxis=dict(
            title='Time Watched',
            tickmode='array',
            tickvals=df_media['hours'],
            ticktext=df_media['hm_str'],
        )
    )

    # Workout Tracker
    workout_counter = simple_counters['dD4T3Ulg16FpTqlkwTtpq']
    workout_data = workout_counter.get('countOnDay', {})
    workout_dates = list(workout_data.keys())
    workout_hours = [v / 1000 / 60 / 60 for v in workout_data.values()]
    # Human-readable time for workout
    workout_hm_strs = [minutes_to_hm_str(h * 60) for h in workout_hours]
    df_workout = pd.DataFrame({'date': pd.to_datetime(workout_dates),
         'hours': workout_hours,
         'hm_str': workout_hm_strs}
      )
    fig_workout = go.Figure(data=[go.Bar(
        x=df_workout['date'],
        y=df_workout['hours'],
        marker_color='#2ca02c',
        customdata=df_workout['hm_str'],
        hovertemplate='%{x}<br>%{customdata}<extra></extra>'
    )])
    fig_workout.update_layout(
        plot_bgcolor='#000',
        paper_bgcolor='#000',
        height=400,
        margin=dict(l=20, r=20, t=120, b=20),
        title={'text': 'Daily Workout Time (Hours)', 'x': 0.5, 'xanchor': 'center'},
        yaxis=dict(
            title='Workout Time',
            tickmode='array',
            tickvals=df_workout['hours'],
            ticktext=df_workout['hm_str'],
        )
    )

    return {
        'water': fig_water,
        'media': fig_media,
        'workout': fig_workout
    }


def create_placeholder_figure():
    """
    Create a placeholder figure for missing plots.
    
    Returns:
        go.Figure: Empty placeholder figure with dark theme
    """
    placeholder_fig = go.Figure()
    placeholder_fig.update_layout(
        plot_bgcolor='#000',
        paper_bgcolor='#000',
        title={'text': 'Placeholder', 'x': 0.5, 'xanchor': 'center'}
    )
    return placeholder_fig


def create_tag_time_trends_plot(df_tasks, data, color_sync):
    """
    Create a plot showing how tag usage changes over time.
    
    Args:
        df_tasks (pd.DataFrame): Normalized task data
        data (dict): Raw SuperProductivity data
        color_sync: Color synchronization object
        
    Returns:
        go.Figure: Tag time trends plot
    """
    # Get tag mapping
    tag_map = {}
    if 'tag' in data and 'entities' in data['tag']:
        tag_map = {k: v['title'] for k, v in data['tag']['entities'].items()}
    
    # Process tag data over time
    tag_time_data = {}
    for _, task in df_tasks.iterrows():
        if 'timeSpentOnDay' in data['task']['entities'][task['id']]:
            task_tags = task.get('tagIds', [])
            if not isinstance(task_tags, list):
                task_tags = [task_tags] if task_tags else []
            
            for day, ms in data['task']['entities'][task['id']]['timeSpentOnDay'].items():
                minutes = ms / 1000 / 60
                for tag_id in task_tags:
                    if tag_id in tag_map:
                        tag_name = tag_map[tag_id]
                        if tag_name not in tag_time_data:
                            tag_time_data[tag_name] = {}
                        if day not in tag_time_data[tag_name]:
                            tag_time_data[tag_name][day] = 0
                        tag_time_data[tag_name][day] += minutes
    
    # Create line plot
    fig = go.Figure()
    
    # Sort tags by total time spent
    tag_totals = {tag: sum(days.values()) for tag, days in tag_time_data.items()}
    sorted_tags = sorted(tag_totals.items(), key=lambda x: x[1], reverse=True)
    
    # Plot top 8 tags
    for tag_name, _ in sorted_tags[:8]:
        if tag_name in tag_time_data:
            dates = sorted(tag_time_data[tag_name].keys())
            values = [tag_time_data[tag_name][date] for date in dates]
            
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(dates),
                y=values,
                mode='lines+markers',
                name=color_sync.get_tag_display_name(tag_name),
                line=dict(color=color_sync.get_tag_color(tag_name), width=2),
                marker=dict(size=4),
                hovertemplate='%{x}<br>%{y:.1f} min<extra></extra>'
            ))
    
    fig.update_layout(
        plot_bgcolor='#000',
        paper_bgcolor='#000',
        height=400,
        margin=dict(l=20, r=20, t=120, b=20),
        title={'text': 'Tag Usage Trends Over Time', 'x': 0.5, 'xanchor': 'center'},
        xaxis=dict(title='Date', gridcolor='#333'),
        yaxis=dict(title='Time Spent (minutes)', gridcolor='#333'),
        legend=dict(bgcolor='rgba(0,0,0,0.8)', bordercolor='#333')
    )
    
    return fig


def create_project_efficiency_plot(df_tasks, df_projects, color_sync):
    """
    Create a plot showing time spent vs. tasks completed per project.
    
    Args:
        df_tasks (pd.DataFrame): Normalized task data
        df_projects (pd.DataFrame): Project data
        color_sync: Color synchronization object
        
    Returns:
        go.Figure: Project efficiency scatter plot
    """
    # Calculate efficiency metrics per project
    project_stats = {}
    
    for _, project in df_projects.iterrows():
        project_tasks = df_tasks[df_tasks['projectId'] == project['id']]
        
        if len(project_tasks) > 0:
            total_time = project_tasks['timeSpent'].sum()
            completed_tasks = len(project_tasks[project_tasks['isDone'] == True])
            total_tasks = len(project_tasks)
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            project_stats[project['title']] = {
                'total_time': total_time,
                'completed_tasks': completed_tasks,
                'total_tasks': total_tasks,
                'completion_rate': completion_rate,
                'avg_time_per_task': total_time / total_tasks if total_tasks > 0 else 0
            }
    
    # Create scatter plot
    fig = go.Figure()
    
    for project_name, stats in project_stats.items():
        if stats['total_time'] > 0:  # Only show projects with time spent
            fig.add_trace(go.Scatter(
                x=[stats['total_time']],
                y=[stats['completion_rate'] * 100],
                mode='markers',
                name=color_sync.get_project_display_name(project_name),
                marker=dict(
                    size=stats['total_tasks'] * 2 + 10,  # Size based on number of tasks
                    color=color_sync.get_project_color(project_name),
                    line=dict(color='white', width=1)
                ),
                text=f"{project_name}<br>Tasks: {stats['total_tasks']}<br>Time: {stats['total_time']:.1f} min",
                hovertemplate='%{text}<br>Completion: %{y:.1f}%<extra></extra>'
            ))
    
    fig.update_layout(
        plot_bgcolor='#000',
        paper_bgcolor='#000',
        height=400,
        margin=dict(l=20, r=20, t=120, b=20),
        title={'text': 'Project Efficiency: Time vs. Completion Rate', 'x': 0.5, 'xanchor': 'center'},
        xaxis=dict(title='Total Time Spent (minutes)', gridcolor='#333'),
        yaxis=dict(title='Completion Rate (%)', gridcolor='#333'),
        legend=dict(bgcolor='rgba(0,0,0,0.8)', bordercolor='#333')
    )
    
    return fig


def create_task_estimation_accuracy_plot(df_tasks):
    """
    Create a plot comparing estimated vs. actual time spent on tasks.
    
    Args:
        df_tasks (pd.DataFrame): Normalized task data
        
    Returns:
        go.Figure: Task estimation accuracy plot
    """
    # Filter tasks with both estimates and actual time
    tasks_with_estimates = df_tasks[
        (df_tasks['timeEstimate'].notna()) & 
        (df_tasks['timeSpent'] > 0) &
        (df_tasks['timeEstimate'] > 0)
    ].copy()
    
    if len(tasks_with_estimates) == 0:
        return create_placeholder_figure()
    
    # Calculate accuracy metrics
    tasks_with_estimates['accuracy_ratio'] = tasks_with_estimates['timeSpent'] / tasks_with_estimates['timeEstimate']
    tasks_with_estimates['accuracy_percent'] = (tasks_with_estimates['accuracy_ratio'] - 1) * 100
    
    # Create histogram of estimation accuracy
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=tasks_with_estimates['accuracy_percent'],
        nbinsx=20,
        marker_color='#636efa',
        opacity=0.8,
        hovertemplate='Accuracy: %{x:.1f}%<br>Count: %{y}<extra></extra>'
    ))
    
    # Add vertical line at 0% (perfect estimation)
    fig.add_vline(x=0, line_dash="dash", line_color="#888", 
                  annotation_text="Perfect Estimation", annotation_position="top right")
    
    # Add vertical lines at ±50% and ±100%
    fig.add_vline(x=50, line_dash="dot", line_color="#666", line_width=1)
    fig.add_vline(x=-50, line_dash="dot", line_color="#666", line_width=1)
    fig.add_vline(x=100, line_dash="dot", line_color="#666", line_width=1)
    fig.add_vline(x=-100, line_dash="dot", line_color="#666", line_width=1)
    
    fig.update_layout(
        plot_bgcolor='#000',
        paper_bgcolor='#000',
        height=400,
        margin=dict(l=20, r=20, t=120, b=20),
        title={'text': 'Task Estimation Accuracy Distribution', 'x': 0.5, 'xanchor': 'center'},
        xaxis=dict(
            title='Estimation Accuracy (% over/under)',
            gridcolor='#333',
            range=[-150, 150]
        ),
        yaxis=dict(title='Number of Tasks', gridcolor='#333'),
        showlegend=False
    )
    
    return fig
