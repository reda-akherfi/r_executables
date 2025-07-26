"""
Main Streamlit dashboard application for Super Productivity Dashboard.
"""
import math
import time
import streamlit as st

# Import modularized functions from r_spdash
from r_spdash import (
    load_super_productivity_data,
    SuperProductivityDataLoader,
    normalize_tasks,
    normalize_projects,
    build_time_by_day,
    create_figures,
    create_calendar_events,
    create_tags_pie_chart,
    create_simple_counter_plots,
    create_color_sync,
    render_sidebar,
    render_calendar,
    render_navigation,
    render_plots
)
from r_spdash.viz.plots import (
    create_tag_time_trends_plot,
    create_project_efficiency_plot,
    create_task_estimation_accuracy_plot
)

# --- File Monitoring ---
def monitor_file_changes():
    """
    Monitor for changes in the most recent SuperProductivity file and rerun if changed.
    """
    if 'file_monitor_initialized' not in st.session_state:
        st.session_state['file_monitor_initialized'] = True
        st.session_state['last_file_path'] = None
        st.session_state['last_file_mtime'] = None
        st.session_state['last_check'] = 0
    now = time.time()
    if now - st.session_state['last_check'] > 10:
        loader = SuperProductivityDataLoader()
        info = loader.get_most_recent_file_info()
        st.session_state['last_check'] = now
        if info:
            current_file_path = info['path']
            current_file_mtime = info['mtime']
            if (st.session_state['last_file_path'] != current_file_path or
                st.session_state['last_file_mtime'] != current_file_mtime):
                st.session_state['last_file_path'] = current_file_path
                st.session_state['last_file_mtime'] = current_file_mtime
                st.rerun()

# --- Data Loading ---
def load_data():
    """
    Load SuperProductivity data and initialize color sync.

    Returns:
        tuple: (data, color_sync) - Raw data and color synchronization object
        
    Raises:
        (FileNotFoundError, KeyError, ValueError, OSError): 
            If data loading fails, displays error in Streamlit UI
    """
    try:
        data = load_super_productivity_data()['data']
        color_sync = create_color_sync(data)
        return data, color_sync
    except (FileNotFoundError, KeyError, ValueError, OSError) as e:
        st.error(f"Error loading SuperProductivity data: {e}")
        st.stop()

# --- Main App ---
def main():
    """
    Main entry point for the dashboard app.

    Sets up the Streamlit page configuration, loads data, creates visualizations,
    and renders the dashboard with navigation and plots.
    """
    st.set_page_config(page_title="Super Productivity Dashboard",
     layout="wide",
      initial_sidebar_state="collapsed")
    monitor_file_changes()
    data, color_sync = load_data()
    df_tasks = normalize_tasks(data)
    df_projects = normalize_projects(data)
    df_tasks = df_tasks.merge(df_projects,
     left_on='projectId',
      right_on='id',
       suffixes=('', '_project'))
    df_all_time = build_time_by_day(df_tasks, data)
    calendar_events = create_calendar_events(df_all_time)
    fig1, fig2, fig3, fig4, cumulative_fig = create_figures(df_all_time, df_projects, color_sync)

    # Create actual plots instead of placeholders
    fig_tags = create_tags_pie_chart(df_tasks, data, color_sync)
    simple_counter_plots = create_simple_counter_plots(data)
    
    # Create new advanced analytics plots
    fig_tag_trends = create_tag_time_trends_plot(df_tasks, data, color_sync)
    fig_project_efficiency = create_project_efficiency_plot(df_tasks, df_projects, color_sync)
    fig_estimation_accuracy = create_task_estimation_accuracy_plot(df_tasks)

    # Store plot information in session state for sidebar
    plots_per_page = 2
    plot_keys = ['accumulated', 'fig3', 'fig4', 'fig1', 'fig2', 'tags_pie']
    plot_keys += list(simple_counter_plots.keys())
    plot_keys += ['tag_trends', 'project_efficiency', 'estimation_accuracy']
    plot_objs = {
        'accumulated': cumulative_fig,
        'fig3': fig3,
        'fig4': fig4,
        'fig1': fig1,
        'fig2': fig2,
        'tags_pie': fig_tags,  # Use actual tags pie chart
        **simple_counter_plots,  # Use actual simple counter plots
        'tag_trends': fig_tag_trends,
        'project_efficiency': fig_project_efficiency,
        'estimation_accuracy': fig_estimation_accuracy
    }
    
    # Store plot information for sidebar
    st.session_state['plot_keys'] = plot_keys
    st.session_state['plots_per_page'] = plots_per_page
    st.session_state['num_plot_pages'] = math.ceil(len(plot_keys) / plots_per_page)
    
    render_sidebar()
    num_plot_pages = math.ceil(len(plot_keys) / plots_per_page)
    num_pages = 1 + num_plot_pages
    if 'plot_page' not in st.session_state:
        st.session_state['plot_page'] = 0
    page = st.session_state['plot_page']
    render_navigation(page, num_pages)
    if page == 0:
        render_calendar(calendar_events, calendar_options, CUSTOM_CSS)
    else:
        render_plots(plot_keys, plot_objs, page, plots_per_page)

# --- Calendar Options and CSS ---
calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,dayGridWeek"
    },
    "height": 416,  # Increased by 4% from 400 to 416 to remove scrollbar
    "locale": "en",
    "eventDisplay": "block",
    "dayMaxEventRows": 2,
    "fixedWeekCount": False,
    "showNonCurrentDates": True,
    "selectable": False,
    "editable": False,
}
CUSTOM_CSS = """
    .fc-daygrid-day-number {
        color: #fff;
    }
    .fc-event {
        background-color: #000 !important;
        border-color: #000 !important;
    }
    .fc-event-main {
        background-color: #000 !important;
    }
    .fc-button-primary {
        background-color: #1a1a2e !important;
        border-color: #1a1a2e !important;
        color: #fff !important;
    }
    .fc-button-primary:hover {
        background-color: #16213e !important;
        border-color: #16213e !important;
    }
    .fc-button-primary:active {
        background-color: #0f3460 !important;
        border-color: #0f3460 !important;
    }
    .fc-button-primary:focus {
        background-color: #1a1a2e !important;
        border-color: #1a1a2e !important;
        box-shadow: 0 0 0 0.2rem rgba(26, 26, 46, 0.5) !important;
    }
    .fc-button-primary:disabled {
        background-color: #2d2d44 !important;
        border-color: #2d2d44 !important;
        color: #888 !important;
    }
    .fc-button-primary.fc-button-active {
        background-color: #4a4a8a !important;
        border-color: #4a4a8a !important;
        color: #fff !important;
    }
    .fc-button-primary.fc-button-active:hover {
        background-color: #5a5a9a !important;
        border-color: #5a5a9a !important;
    }
"""

if __name__ == "__main__":
    main()
