# utils/formatters.py
"""Utility functions for formatting data"""

from datetime import datetime


def format_datetime(dt_string: str, format_str: str = '%B %d, %Y at %I:%M %p') -> str:
    """
    Convert ISO datetime string to readable format
    
    Args:
        dt_string: ISO format datetime string
        format_str: strftime format string
        
    Returns:
        Formatted datetime string or original if parsing fails
    """
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime(format_str)
    except (ValueError, AttributeError):
        return dt_string
