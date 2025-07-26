"""
UI rendering functions for the Super Productivity Dashboard.
"""
import os
import streamlit as st
from streamlit_calendar import calendar
from .utils.helpers import format_datetime


def render_sidebar():
    """Render the sidebar with controls and file info."""
    with st.sidebar:
        st.header("Dashboard Controls")
        if st.button("🔄 Refresh Data", help="Manually refresh data from the latest JSON file"):
            st.rerun()

        if st.session_state.get('last_file_path'):
            st.info(f"📁 Current file: {os.path.basename(st.session_state['last_file_path'])}")
            if st.session_state.get('last_file_mtime'):
                st.caption(f"Last modified: {format_datetime(st.session_state['last_file_mtime'])}")
        
        # Plot search functionality
        st.markdown("---")
        st.subheader("🔍 Plot Search")
        
        # Get all available plots and their descriptions
        plot_descriptions = {
            'Calendar': 'Calendar view with work events',
            'Accumulated Work Time': 'Cumulative work time across days',
            'Time Spent Per Day Per Project': 'Stacked bar chart of daily project time',
            'Average Time Per Workday': 'Average time by weekday and project',
            'All Time Spent Per Day': 'Daily total work time',
            'Time Spent Per Project': 'Pie chart of project time distribution',
            'Time Spent Distribution by Tag': 'Pie chart of tag time distribution',
            'Daily Water Intake': 'Water consumption tracking',
            'Daily Media Watching': 'Media consumption tracking',
            'Daily Workout Time': 'Workout time tracking',
            'Tag Usage Trends Over Time': 'How tag usage changes over time',
            'Project Efficiency': 'Time vs. completion rate per project',
            'Task Estimation Accuracy': 'Estimated vs. actual time distribution'
        }
        
        # Create search input
        search_term = st.text_input("Search plots...", placeholder="Type to search...", key="plot_search")
        
        # Filter plots based on search
        if search_term:
            filtered_plots = {
                name: desc for name, desc in plot_descriptions.items() 
                if search_term.lower() in name.lower() or search_term.lower() in desc.lower()
            }
        else:
            filtered_plots = plot_descriptions
        
        # Display filtered plots as clickable buttons
        if filtered_plots:
            st.markdown("**Available Plots:**")
            for plot_name, description in filtered_plots.items():
                if st.button(f"📊 {plot_name}", key=f"search_{plot_name}", help=description):
                    # Navigate to the appropriate page
                    navigate_to_plot(plot_name)
        else:
            st.info("No plots match your search.")
        
        # Show current page info
        if 'plot_page' in st.session_state:
            current_page = st.session_state['plot_page']
            st.markdown("---")
            st.markdown(f"**Current Page:** {current_page + 1}")
            if current_page == 0:
                st.markdown("📍 **Calendar View**")
            else:
                # Show which plots are on current page
                if 'plot_keys' in st.session_state and 'plots_per_page' in st.session_state:
                    plot_keys = st.session_state['plot_keys']
                    plots_per_page = st.session_state['plots_per_page']
                    plot_page_idx = current_page - 1
                    start_idx = plot_page_idx * plots_per_page
                    end_idx = start_idx + plots_per_page
                    plots_on_page = plot_keys[start_idx:end_idx]
                    
                    st.markdown("📍 **Plots on this page:**")
                    for plot_key in plots_on_page:
                        plot_name = get_plot_display_name(plot_key)
                        st.markdown(f"• {plot_name}")


def get_plot_display_name(plot_key):
    """
    Convert plot key to display name.
    
    Args:
        plot_key (str): Plot key from plot_keys list
        
    Returns:
        str: Human-readable plot name
    """
    plot_name_mapping = {
        'accumulated': 'Accumulated Work Time',
        'fig1': 'All Time Spent Per Day',
        'fig2': 'Time Spent Per Project',
        'fig3': 'Time Spent Per Day Per Project',
        'fig4': 'Average Time Per Workday',
        'tags_pie': 'Time Spent Distribution by Tag',
        'water': 'Daily Water Intake',
        'media': 'Daily Media Watching',
        'workout': 'Daily Workout Time',
        'tag_trends': 'Tag Usage Trends Over Time',
        'project_efficiency': 'Project Efficiency',
        'estimation_accuracy': 'Task Estimation Accuracy'
    }
    return plot_name_mapping.get(plot_key, plot_key)


def navigate_to_plot(plot_name):
    """
    Navigate to the page containing the specified plot.
    
    Args:
        plot_name (str): Name of the plot to navigate to
    """
    # Map plot names to their page numbers
    plot_page_mapping = {
        'Calendar': 0,
        'Accumulated Work Time': 1,
        'Time Spent Per Day Per Project': 1,
        'Average Time Per Workday': 2,
        'All Time Spent Per Day': 2,
        'Time Spent Per Project': 3,
        'Time Spent Distribution by Tag': 3,
        'Daily Water Intake': 4,
        'Daily Media Watching': 4,
        'Daily Workout Time': 5,
        'Tag Usage Trends Over Time': 5,
        'Project Efficiency': 6,
        'Task Estimation Accuracy': 6
    }
    
    if plot_name in plot_page_mapping:
        target_page = plot_page_mapping[plot_name]
        st.session_state['plot_page'] = target_page
        st.rerun()
    else:
        st.error(f"Plot '{plot_name}' not found.")


def render_calendar(calendar_events, calendar_options, custom_css):
    """
    Render the calendar component.
    
    Args:
        calendar_events (list): List of calendar events
        calendar_options (dict): Calendar configuration options
        custom_css (str): Custom CSS for calendar styling
    """
    st.markdown("<div style='display:flex;justify-content:center;align-items:center;'>",
         unsafe_allow_html=True)
    calendar(
        events=calendar_events,
        options=calendar_options,
        custom_css=custom_css,
        key="work-calendar"
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_navigation(page, num_pages):
    """
    Render the navigation controls.
    
    Args:
        page (int): Current page number
        num_pages (int): Total number of pages
    """
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    with col_nav1:
        st.button('⬅️', key='prev_page', disabled=(page == 0),
                 on_click=lambda: st.session_state.update({'plot_page': max(0, page - 1)}))
    with col_nav2:
        st.markdown(f"<h4 style='text-align:center; margin-bottom:0;'>{page+1} of {num_pages}</h4>",
                   unsafe_allow_html=True)
    with col_nav3:
        st.button('➡️', key='next_page', disabled=(page == num_pages - 1),
            on_click=lambda: st.session_state.update({'plot_page': min(num_pages - 1, page + 1)}))


def render_plots(plot_keys, plot_objs, page, plots_per_page):
    """
    Render the plots in a grid layout.
    
    Args:
        plot_keys (list): List of plot keys to display
        plot_objs (dict): Dictionary mapping plot keys to plotly figures
        page (int): Current page number
        plots_per_page (int): Number of plots per page
    """
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
            if plot_key is not None and plot_key in plot_objs and plot_objs[plot_key] is not None:
                # Add unique key to prevent duplicate element ID errors
                unique_key = f"plot_{page}_{col}_{plot_key}"
                st.plotly_chart(plot_objs[plot_key], use_container_width=True, key=unique_key)
            else:
                st.empty()
