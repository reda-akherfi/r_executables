"""
UI rendering functions for the Super Productivity Dashboard.
"""
import streamlit as st
import os
from datetime import datetime
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


def render_calendar(calendar_events, calendar_options, custom_css):
    """
    Render the calendar component.
    
    Args:
        calendar_events (list): List of calendar events
        calendar_options (dict): Calendar configuration options
        custom_css (str): Custom CSS for calendar styling
    """
    st.markdown(f"<div style='display:flex;justify-content:center;align-items:center;'>", unsafe_allow_html=True)
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
        st.markdown(f"<h4 style='text-align:center; margin-bottom:0;'>Plots Page {page+1} of {num_pages}</h4>", 
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