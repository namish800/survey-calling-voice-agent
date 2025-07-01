"""
Time management tools for LiveKit Voice Agents.

This module provides tools for agents to get current time information
in various formats and timezones.
"""

import datetime
import pytz
from typing import Optional
from universalagent.tools.tool_holder import ToolHolder


async def get_current_time(
    timezone: Optional[str] = None,
    format_type: str = "full"
) -> str:
    """Get the current date and time in a specific timezone or UTC by default
    
    Args:
        timezone: Timezone name (e.g., 'US/Eastern', 'Europe/London', 'UTC'). 
                 If None, uses UTC.
        format_type: Format type - 'full' (default), 'date', 'time', 'short'
    
    Returns:
        Formatted current date and time string
    """
    try:
        # Get current time
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                now = datetime.datetime.now(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                # Fallback to UTC if timezone is invalid
                now = datetime.datetime.now(pytz.UTC)
                timezone = "UTC (invalid timezone specified)"
        else:
            now = datetime.datetime.now(pytz.UTC)
            timezone = "UTC"
        
        # Format based on type
        if format_type == "full":
            formatted_time = now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        elif format_type == "date":
            formatted_time = now.strftime("%A, %B %d, %Y")
        elif format_type == "time":
            formatted_time = now.strftime("%I:%M %p %Z")
        elif format_type == "short":
            formatted_time = now.strftime("%m/%d/%Y %I:%M %p")
        else:
            # Default to full format
            formatted_time = now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        
        return f"Current time ({timezone}): {formatted_time}"
        
    except Exception as e:
        return f"Error getting current time: {str(e)}"


async def get_timezones_for_region(region: str = "") -> str:
    """Get available timezones for a region.
    
    Args:
        region: Region name (e.g., 'US', 'Europe', 'Asia', 'America'). 
                If empty, returns common timezones.
    
    Returns:
        List of available timezones for the region
    """
    try:
        if not region:
            # Return common timezones
            common_zones = [
                "UTC",
                "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
                "Europe/London", "Europe/Paris", "Europe/Berlin",
                "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata",
                "Australia/Sydney", "Australia/Melbourne"
            ]
            result = "Common timezones:\n"
            for zone in common_zones:
                result += f"• {zone}\n"
            return result.strip()
        
        # Filter timezones by region
        all_timezones = pytz.all_timezones
        region_timezones = [tz for tz in all_timezones if region.lower() in tz.lower()]
        
        if not region_timezones:
            return f"No timezones found for region '{region}'. Try 'US', 'Europe', 'Asia', 'America', or 'Australia'."
        
        # Limit to first 20 results to avoid overwhelming output
        limited_zones = sorted(region_timezones)[:20]
        result = f"Timezones for '{region}' (showing first 20):\n"
        for zone in limited_zones:
            result += f"• {zone}\n"
        
        if len(region_timezones) > 20:
            result += f"... and {len(region_timezones) - 20} more"
        
        return result.strip()
        
    except Exception as e:
        return f"Error getting timezones for region: {str(e)}"


async def get_time_difference(
    timezone1: str,
    timezone2: str
) -> str:
    """Calculate the time difference between two timezones.
    
    Args:
        timezone1: First timezone (e.g., 'US/Eastern')
        timezone2: Second timezone (e.g., 'Europe/London')
    
    Returns:
        Time difference information between the two timezones
    """
    try:
        # Get current time in both timezones
        tz1 = pytz.timezone(timezone1)
        tz2 = pytz.timezone(timezone2)
        
        now = datetime.datetime.now(pytz.UTC)
        time1 = now.astimezone(tz1)
        time2 = now.astimezone(tz2)
        
        # Calculate difference in hours
        diff = (time1.utcoffset() - time2.utcoffset()).total_seconds() / 3600
        
        # Format the result
        time1_str = time1.strftime("%I:%M %p")
        time2_str = time2.strftime("%I:%M %p")
        
        if diff > 0:
            diff_str = f"{timezone1} is {abs(diff):.0f} hours ahead of {timezone2}"
        elif diff < 0:
            diff_str = f"{timezone1} is {abs(diff):.0f} hours behind {timezone2}"
        else:
            diff_str = f"{timezone1} and {timezone2} are in the same time zone"
        
        return f"Time comparison:\n• {timezone1}: {time1_str}\n• {timezone2}: {time2_str}\n• {diff_str}"
        
    except pytz.exceptions.UnknownTimeZoneError as e:
        return f"Invalid timezone specified: {str(e)}"
    except Exception as e:
        return f"Error calculating time difference: {str(e)}"


time_management_tools = [
    ToolHolder(get_current_time, usage_instructions_llm="Use this tool when the user asks for the current time or when you need to know what time it is. You can specify a timezone (e.g., 'US/Eastern', 'Europe/London', 'Asia/Tokyo') or leave it blank for UTC."),
    ToolHolder(get_timezones_for_region, usage_instructions_llm="Use this tool when the user asks about available timezones for a specific region or wants to know the correct timezone name to use."),
    ToolHolder(get_time_difference, usage_instructions_llm="Use this tool when the you want to know the time difference between two locations or timezones. Helpful for scheduling meetings or calls."),
]

