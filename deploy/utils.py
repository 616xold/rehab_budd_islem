"""
utils.py - Utility functions for Rehab Buddy Alexa Skill

This module provides common helper functions used across the Rehab Buddy application.
It includes utilities for building consistent Alexa responses, formatting dates and times,
and other shared functionality to reduce code duplication and ensure consistency.
"""

import datetime
import json
from typing import Dict, Any, Optional, List, Tuple

def build_response(
    speech_text: str,
    reprompt_text: Optional[str] = None,
    card_title: Optional[str] = None,
    card_text: Optional[str] = None,
    should_end_session: bool = False
) -> Dict[str, Any]:
    """
    Build a standardized Alexa response object.
    
    Args:
        speech_text (str): The text for Alexa to speak
        reprompt_text (Optional[str]): The text for reprompting if no response
        card_title (Optional[str]): The title for the card in the Alexa app
        card_text (Optional[str]): The text for the card in the Alexa app
        should_end_session (bool): Whether to end the session
        
    Returns:
        Dict[str, Any]: The formatted response object
    """
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_text
            },
            "shouldEndSession": should_end_session
        }
    }
    
    # Add reprompt if provided
    if reprompt_text:
        response["response"]["reprompt"] = {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        }
    
    # Add card if title and text provided
    if card_title and card_text:
        response["response"]["card"] = {
            "type": "Simple",
            "title": card_title,
            "content": card_text
        }
    
    return response

def format_date(date_str: str, format_str: str = "%Y-%m-%d") -> str:
    """
    Format a date string into a more readable format.
    
    Args:
        date_str (str): ISO format date string (YYYY-MM-DD)
        format_str (str): Output format string
        
    Returns:
        str: Formatted date string
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime(format_str)
    except ValueError:
        return date_str

def format_time(time_str: str, format_str: str = "%I:%M %p") -> str:
    """
    Format a time string into a more readable format.
    
    Args:
        time_str (str): Time string in 24-hour format (HH:MM)
        format_str (str): Output format string
        
    Returns:
        str: Formatted time string
    """
    try:
        time_obj = datetime.datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime(format_str)
    except ValueError:
        return time_str

def get_slot_value(handler_input, slot_name: str, default_value: Any = None) -> Any:
    """
    Safely extract a slot value from an Alexa intent request.
    
    Args:
        handler_input: The Alexa handler input object
        slot_name (str): The name of the slot to extract
        default_value (Any): Default value if slot not found
        
    Returns:
        Any: The slot value or default value
    """
    try:
        slots = handler_input.request_envelope.request.intent.slots
        return slots.get(slot_name, {}).get('value', default_value)
    except (AttributeError, KeyError):
        return default_value

def get_slot_str(handler_input, slot_name: str) -> Optional[str]:
    """Safely extract a slot string from the handler input.

    This helper abstracts the differences between the ask-sdk ``Slot`` object
    and a simple ``dict`` representation. ``None`` is returned if the slot or
    value cannot be found.

    Args:
        handler_input: The Alexa handler input object.
        slot_name: Name of the slot to retrieve.

    Returns:
        Optional[str]: The slot value as a string or ``None``.
    """
    try:
        slots = handler_input.request_envelope.request.intent.slots or {}
    except AttributeError:
        return None

    slot = slots.get(slot_name)
    if slot is None:
        return None

    if isinstance(slot, dict):
        return slot.get("value")

    return getattr(slot, "value", None)

def get_user_id(handler_input) -> Optional[str]:
    """
    Safely extract the user ID from an Alexa request.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Optional[str]: The user ID or None if not found
    """
    try:
        return handler_input.request_envelope.session.user.user_id
    except AttributeError:
        return None

def log_error(error: Exception, context: str = "") -> None:
    """
    Log an error with context information.
    
    Args:
        error (Exception): The exception to log
        context (str): Additional context information
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    if context:
        print(f"ERROR in {context}: {error_type} - {error_message}")
    else:
        print(f"ERROR: {error_type} - {error_message}")

def is_same_day(date1_str: str, date2_str: str) -> bool:
    """
    Check if two ISO format date strings represent the same day.
    
    Args:
        date1_str (str): First ISO format date string
        date2_str (str): Second ISO format date string
        
    Returns:
        bool: True if same day, False otherwise
    """
    try:
        date1 = datetime.datetime.fromisoformat(date1_str).date()
        date2 = datetime.datetime.fromisoformat(date2_str).date()
        return date1 == date2
    except (ValueError, TypeError):
        return False

def days_between(date1_str: str, date2_str: str) -> int:
    """
    Calculate the number of days between two ISO format date strings.
    
    Args:
        date1_str (str): First ISO format date string
        date2_str (str): Second ISO format date string
        
    Returns:
        int: Number of days between dates (absolute value)
    """
    try:
        date1 = datetime.datetime.fromisoformat(date1_str).date()
        date2 = datetime.datetime.fromisoformat(date2_str).date()
        return abs((date2 - date1).days)
    except (ValueError, TypeError):
        return -1  # Error indicator

def sanitize_for_speech(text: str) -> str:
    """
    Sanitize text for better speech output.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Sanitized text
    """
    # Replace symbols that might not be spoken well
    replacements = {
        "&": " and ",
        "%": " percent ",
        "/": " or ",
        "-": " ",
        "_": " ",
        "+": " plus ",
        "=": " equals ",
        "#": " number ",
        "@": " at "
    }
    
    for symbol, replacement in replacements.items():
        text = text.replace(symbol, replacement)
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    return text
