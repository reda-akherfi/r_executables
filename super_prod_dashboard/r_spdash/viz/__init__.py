"""
Visualization modules for the Super Productivity Dashboard.
"""
from .plots import (
    create_figures, 
    create_calendar_events, 
    create_placeholder_figure,
    create_tags_pie_chart,
    create_simple_counter_plots
)
from .color_sync import create_color_sync

__all__ = [
    'create_figures', 
    'create_calendar_events', 
    'create_placeholder_figure',
    'create_tags_pie_chart',
    'create_simple_counter_plots',
    'create_color_sync'
] 