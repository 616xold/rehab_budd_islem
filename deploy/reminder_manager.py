"""
reminder_manager.py - Alexa Reminders API integration for Rehab Buddy Alexa Skill

This module handles the integration with the Alexa Reminders API, allowing users to
schedule and manage reminders for their rehabilitation sessions. It provides functions
to create daily reminders, cancel reminders, and check for the necessary permissions.

The module abstracts the complexity of the Alexa Reminders API, providing a clean
interface for other modules to schedule and manage reminders.
"""

import requests
import json
import datetime
import time
from typing import Dict, Any, Optional, List, Tuple, Literal
from functools import wraps
import pytz
import logging

# Import configuration
import config
from progress_tracker import get_dynamodb_resource

# Reminder frequency types
ReminderFrequency = Literal["DAILY", "WEEKLY", "WEEKDAYS"]

logger = logging.getLogger(__name__)

def parse_time_slot(time_str: str) -> Tuple[int, int, int]:
    """
    Parse time slot value from Alexa into hours, minutes, seconds.
    
    Args:
        time_str (str): Time string from Alexa slot (e.g., "09:00", "9:00", "09:00:00")
        
    Returns:
        Tuple[int, int, int]: (hour, minute, second)
        
    Raises:
        ValueError: If time format is invalid
    """
    if not time_str:
        raise ValueError("Time string is empty")
    
    # Remove any whitespace
    time_str = time_str.strip()
    
    # Split by colon
    parts = time_str.split(':')
    
    if len(parts) == 2:
        # HH:MM format
        hour, minute = int(parts[0]), int(parts[1])
        second = 0
    elif len(parts) == 3:
        # HH:MM:SS format
        hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
    else:
        raise ValueError(f"Invalid time format: {time_str}")
    
    # Validate ranges
    if not (0 <= hour <= 23):
        raise ValueError(f"Invalid hour: {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"Invalid minute: {minute}")
    if not (0 <= second <= 59):
        raise ValueError(f"Invalid second: {second}")
    
    return hour, minute, second

def retry_with_backoff(max_retries=3, base_delay=1):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        base_delay (int): Base delay in seconds between retries
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retry attempt {attempt + 1} after {delay}s delay. Error: {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def store_reminder_preference(user_id: str, reminder_data: Dict[str, Any]) -> bool:
    """
    Store user's reminder preferences in DynamoDB.
    
    Args:
        user_id (str): The unique identifier for the user
        reminder_data (Dict[str, Any]): Reminder preference data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET reminder_preferences = :r, last_updated = :u",
            ExpressionAttributeValues={
                ':r': reminder_data,
                ':u': datetime.datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error storing reminder preference: {str(e)}")
        return False

def get_reminder_preferences(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's reminder preferences from DynamoDB.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        Optional[Dict[str, Any]]: Reminder preferences or None
    """
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item', {})
        return item.get('reminder_preferences')
    except Exception as e:
        logger.error(f"Error getting reminder preferences: {str(e)}")
        return None

def has_reminders_permission(handler_input) -> bool:
    """
    Check if the user has granted permission to use reminders.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        bool: True if permission is granted, False otherwise
    """
    try:
        # Get permissions from request envelope
        permissions = handler_input.request_envelope.context.system.user.permissions
        
        # Check if permissions exist and include reminders permission
        if permissions and hasattr(permissions, 'consent_token'):
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking reminders permission: {str(e)}")
        return False

def get_reminders_api_endpoint(handler_input) -> Optional[str]:
    """
    Get the Alexa Reminders API endpoint URL.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Optional[str]: The API endpoint URL or None if not available
    """
    try:
        # Get API endpoint from request envelope
        api_endpoint = handler_input.request_envelope.context.system.api_endpoint
        
        # Map of region-specific endpoints
        region_endpoints = {
            'api.amazonalexa.com': 'api.amazonalexa.com',  # US
            'api.eu.amazonalexa.com': 'api.eu.amazonalexa.com',  # EU
            'api.fe.amazonalexa.com': 'api.fe.amazonalexa.com',  # Far East
            'api.jp.amazonalexa.com': 'api.jp.amazonalexa.com'   # Japan
        }
        
        # Extract the base domain from the API endpoint
        base_domain = api_endpoint.split('//')[-1].split('/')[0]
        
        # Get the correct regional endpoint
        regional_endpoint = region_endpoints.get(base_domain, base_domain)
        
        # Ensure endpoint ends with '/'
        if not regional_endpoint.endswith('/'):
            regional_endpoint += '/'
        
        # Append reminders path
        return f"https://{regional_endpoint}v1/alerts/reminders"
    except Exception as e:
        logger.error(f"Error getting reminders API endpoint: {str(e)}")
        return None

def get_api_access_token(handler_input) -> Optional[str]:
    """
    Get the API access token for Alexa Reminders API.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Optional[str]: The API access token or None if not available
    """
    try:
        # Get API access token from request envelope
        return handler_input.request_envelope.context.system.api_access_token
    except Exception as e:
        logger.error(f"Error getting API access token: {str(e)}")
        return None

def get_user_timezone(handler_input) -> str:
    """
    Get the user's timezone from device settings or default.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        str: Timezone string (e.g., 'Europe/London')
    """
    try:
        system = handler_input.request_envelope.context.system
        if not hasattr(system, 'device'):
            logger.warning("No device information available, defaulting to Europe/London")
            return "Europe/London"
            
        device_id = system.device.device_id
        api_endpoint = system.api_endpoint
        api_token = system.api_access_token
        
        if not all([device_id, api_endpoint, api_token]):
            logger.warning("Missing required API information, defaulting to Europe/London")
            return "Europe/London"
            
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.get(
            f"{api_endpoint}/v2/devices/{device_id}/settings/System.timeZone",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.text.strip('"')
        else:
            logger.warning(f"Failed to get timezone: {response.status_code}, defaulting to Europe/London")
            return "Europe/London"
            
    except Exception as e:
        logger.error(f"Error getting user timezone: {str(e)}, defaulting to Europe/London")
        return "Europe/London"

@retry_with_backoff(max_retries=3)
def schedule_daily_reminder(handler_input, reminder_time, reminder_text, timezone=None):
    """Schedule a daily reminder using the Alexa Reminders API."""
    try:
        # Check for reminders permission
        if not has_reminders_permission(handler_input):
            logger.warning("Reminders permission not granted")
            return False, "permission_required"
            
        # Get user's timezone if not provided
        if not timezone:
            timezone = get_user_timezone(handler_input)
            if not timezone:
                logger.warning("Could not determine user timezone, using default")
                timezone = "America/New_York"
        
        # Parse the reminder time
        try:
            hour, minute = map(int, reminder_time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                logger.error(f"Invalid time format: {reminder_time}")
                return False, "invalid_time"
        except ValueError:
            logger.error(f"Invalid time format: {reminder_time}")
            return False, "invalid_time"
            
        # Get the API access token
        api_access_token = handler_input.request_envelope.context.system.api_access_token
        if not api_access_token:
            logger.error("No API access token available")
            return False, "api_error"
            
        # Get the API endpoint
        api_endpoint = handler_input.request_envelope.context.system.api_endpoint
        if not api_endpoint:
            logger.error("No API endpoint available")
            return False, "api_error"
            
        # Calculate the next occurrence of the reminder time
        now = datetime.datetime.now(pytz.timezone(timezone))
        reminder_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the time has already passed today, schedule for tomorrow
        if reminder_datetime <= now:
            reminder_datetime = reminder_datetime + datetime.timedelta(days=1)
            
        # Format the time in YYYY-MM-DDThh:mm:ss format without timezone offset
        scheduled_time = reminder_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Prepare the reminder request
        reminder_request = {
            "requestTime": datetime.datetime.utcnow().isoformat() + "Z",
            "trigger": {
                "type": "SCHEDULED_ABSOLUTE",
                "scheduledTime": scheduled_time,
                "timeZoneId": timezone,
                "recurrence": {
                    "freq": "DAILY"
                }
            },
            "alertInfo": {
                "spokenInfo": {
                    "content": [{
                        "locale": "en-US",
                        "text": reminder_text
                    }]
                }
            },
            "pushNotification": {
                "status": "ENABLED"
            }
        }
        
        # Make the API request with retry mechanism
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{api_endpoint}/v1/alerts/reminders",
                    headers={
                        "Authorization": f"Bearer {api_access_token}",
                        "Content-Type": "application/json"
                    },
                    json=reminder_request
                )
                
                if response.status_code == 201:
                    logger.info("Reminder scheduled successfully")
                    # Store reminder preference
                    store_reminder_preference(handler_input.request_envelope.session.user.user_id, {
                        "time": reminder_time,
                        "timezone": timezone,
                        "frequency": "DAILY",
                        "message": reminder_text,
                        "last_scheduled": scheduled_time
                    })
                    return True, None
                elif response.status_code == 403:
                    logger.error("Permission denied for reminders API")
                    return False, "permission_denied"
                elif response.status_code == 400:
                    logger.error(f"Invalid request: {response.text}")
                    return False, "invalid_request"
                else:
                    logger.error(f"Failed to schedule reminder: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    return False, "api_error"
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                return False, "network_error"
                
        return False, "max_retries_exceeded"
        
    except Exception as e:
        logger.error(f"Unexpected error in schedule_daily_reminder: {str(e)}")
        return False, "unexpected_error"

@retry_with_backoff(max_retries=3)
def cancel_reminder(handler_input, reminder_id: str) -> Tuple[bool, str]:
    """
    Cancel a specific reminder.
    
    Args:
        handler_input: The Alexa handler input object
        reminder_id (str): The ID of the reminder to cancel
        
    Returns:
        Tuple[bool, str]: (success, message) tuple
    """
    # Check for permission
    if not has_reminders_permission(handler_input):
        return False, "no_permission"
    
    # Get API endpoint and token
    api_endpoint = get_reminders_api_endpoint(handler_input)
    api_token = get_api_access_token(handler_input)
    
    if not api_endpoint or not api_token:
        return False, "Failed to get API endpoint or token"
    
    try:
        # Set up headers
        headers = {
            "Authorization": f"Bearer {api_token}"
        }
        
        # Make the API request to delete the reminder
        response = requests.delete(
            f"{api_endpoint}/{reminder_id}",
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            return True, "Reminder cancelled successfully"
        else:
            logger.error(f"Error cancelling reminder: {response.status_code} - {response.text}")
            return False, f"Error {response.status_code}: {response.text}"
    
    except Exception as e:
        logger.error(f"Error cancelling reminder: {str(e)}")
        return False, str(e)

@retry_with_backoff(max_retries=3)
def get_all_reminders(handler_input) -> Tuple[bool, Any]:
    """
    Get all reminders for the user.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Tuple[bool, Any]: (success, reminders_data) tuple
    """
    # Check for permission
    if not has_reminders_permission(handler_input):
        return False, "no_permission"
    
    # Get API endpoint and token
    api_endpoint = get_reminders_api_endpoint(handler_input)
    api_token = get_api_access_token(handler_input)
    
    if not api_endpoint or not api_token:
        return False, "Failed to get API endpoint or token"
    
    try:
        # Set up headers
        headers = {
            "Authorization": f"Bearer {api_token}"
        }
        
        # Make the API request to get all reminders
        response = requests.get(
            api_endpoint,
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            return True, response.json()
        else:
            logger.error(f"Error getting reminders: {response.status_code} - {response.text}")
            return False, f"Error {response.status_code}: {response.text}"
    
    except Exception as e:
        logger.error(f"Error getting reminders: {str(e)}")
        return False, str(e)

@retry_with_backoff(max_retries=3)
def cancel_all_reminders(handler_input, user_id: str | None = None) -> Tuple[bool, str]:
    """
    Cancel all reminders for the user.

    Args:
        handler_input: Alexa handler input
        user_id      : (optional) explicit user-id; if omitted we read it
                       from the handler_input
    """
    # If caller didn't supply user_id, pull it from the request
    if user_id is None:
        user_id = handler_input.request_envelope.session.user.user_id

    # Check for permission
    if not has_reminders_permission(handler_input):
        return False, "no_permission"
    
    try:
        # Get all reminders
        success, reminders_data = get_all_reminders(handler_input)
        
        if not success:
            return False, reminders_data
        
        # Cancel each reminder
        for reminder in reminders_data.get('alerts', []):
            reminder_id = reminder.get('alertToken')
            if reminder_id:
                cancel_reminder(handler_input, reminder_id)
        
        # Clear reminder preferences
        store_reminder_preference(user_id, {})
        
        return True, "All reminders cancelled successfully"
    
    except Exception as e:
        logger.error(f"Error cancelling all reminders: {str(e)}")
        return False, str(e)

def build_permissions_response(handler_input) -> Dict[str, Any]:
    """
    Build a response requesting reminders permission.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Dict[str, Any]: Response dictionary
    """
    speech_text = (
        "To set reminders for your rehabilitation exercises, I'll need permission "
        "to access the Alexa Reminders API. You can grant this permission in the "
        "Alexa app under Settings > Your Skills > Rehab Buddy."
    )
    
    return handler_input.response_builder.speak(speech_text).ask(speech_text).response
