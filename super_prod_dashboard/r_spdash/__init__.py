"""
Super Productivity Dashboard package.

A modular dashboard for visualizing SuperProductivity data.
"""
from .io import (
    load_super_productivity_data, 
    SuperProductivityDataLoader,
    normalize_tasks, 
    normalize_projects, 
    build_time_by_day
)
from .viz import (
    create_figures, 
    create_calendar_events, 
    create_placeholder_figure,
    create_tags_pie_chart,
    create_simple_counter_plots,
    create_color_sync
)
from .utils import minutes_to_hm_str, format_datetime
from .ui import render_sidebar, render_calendar, render_navigation, render_plots

__all__ = [
    # IO functions
    'load_super_productivity_data',
    'SuperProductivityDataLoader', 
    'normalize_tasks',
    'normalize_projects',
    'build_time_by_day',
    # Visualization functions
    'create_figures',
    'create_calendar_events',
    'create_placeholder_figure',
    'create_tags_pie_chart',
    'create_simple_counter_plots',
    'create_color_sync',
    # Utility functions
    'minutes_to_hm_str',
    'format_datetime',
    # UI functions
    'render_sidebar',
    'render_calendar', 
    'render_navigation',
    'render_plots'
] 