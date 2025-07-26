"""
Utility helper functions for the Super Productivity Dashboard.
"""
from datetime import datetime
import pandas as pd


def minutes_to_hm_str(minutes):
    """
    Convert minutes to human-readable format (Xh Ym).
    
    Args:
        minutes (float): Minutes to convert
        
    Returns:
        str: Formatted time string (e.g., "2h 30m" or "45m")
    """
    minutes = int(round(minutes))
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if h > 0 else f"{m}m"


def format_datetime(timestamp):
    """
    Format timestamp to readable datetime string.
    
    Args:
        timestamp (float): Unix timestamp
        
    Returns:
        str: Formatted datetime string
    """
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') 