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
from typing import Dict, Any, Optional, List, Tuple

# Import configuration
import config

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
        print(f"Error checking reminders permission: {str(e)}")
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
        
        # Ensure endpoint ends with '/'
        if not api_endpoint.endswith('/'):
            api_endpoint += '/'
        
        # Append reminders path
        return f"{api_endpoint}v1/reminders"
    except Exception as e:
        print(f"Error getting reminders API endpoint: {str(e)}")
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
        print(f"Error getting API access token: {str(e)}")
        return None

def schedule_daily_reminder(
    handler_input, 
    time_str: str = "09:00", 
    message: str = "Time for your rehabilitation exercises"
) -> Tuple[bool, str]:
    """
    Schedule a daily reminder for rehabilitation exercises.
    
    Args:
        handler_input: The Alexa handler input object
        time_str (str): Time for the reminder in 24-hour format (HH:MM)
        message (str): The reminder message
        
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
        # Parse time string
        hour, minute = map(int, time_str.split(':'))
        
        # Create reminder request payload
        now = datetime.datetime.now()
        reminder_time = now.replace(hour=hour, minute=minute)
        
        # If the time is in the past for today, set it for tomorrow
        if reminder_time < now:
            reminder_time = reminder_time + datetime.timedelta(days=1)
        
        # Format the scheduled time
        scheduled_time = reminder_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Create the reminder request payload
        reminder_payload = {
            "requestTime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "trigger": {
                "type": "SCHEDULED_ABSOLUTE",
                "scheduledTime": scheduled_time,
                "recurrence": {
                    "freq": "DAILY"
                }
            },
            "alertInfo": {
                "spokenInfo": {
                    "content": [{
                        "locale": "en-US",
                        "text": message
                    }]
                }
            },
            "pushNotification": {
                "status": "ENABLED"
            }
        }
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Make the API request
        response = requests.post(
            api_endpoint,
            headers=headers,
            data=json.dumps(reminder_payload)
        )
        
        # Check response
        if response.status_code == 200:
            reminder_id = response.json().get('alertToken')
            return True, reminder_id
        else:
            print(f"Error scheduling reminder: {response.status_code} - {response.text}")
            return False, f"Error {response.status_code}: {response.text}"
    
    except Exception as e:
        print(f"Error scheduling reminder: {str(e)}")
        return False, str(e)

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
            print(f"Error cancelling reminder: {response.status_code} - {response.text}")
            return False, f"Error {response.status_code}: {response.text}"
    
    except Exception as e:
        print(f"Error cancelling reminder: {str(e)}")
        return False, str(e)

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
            reminders = response.json().get('alerts', [])
            return True, reminders
        else:
            print(f"Error getting reminders: {response.status_code} - {response.text}")
            return False, f"Error {response.status_code}: {response.text}"
    
    except Exception as e:
        print(f"Error getting reminders: {str(e)}")
        return False, str(e)

def cancel_all_reminders(handler_input) -> Tuple[bool, str]:
    """
    Cancel all reminders for the user.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Tuple[bool, str]: (success, message) tuple
    """
    # Get all reminders
    success, reminders = get_all_reminders(handler_input)
    
    if not success:
        if reminders == "no_permission":
            return False, "no_permission"
        return False, f"Failed to get reminders: {reminders}"
    
    # No reminders to cancel
    if not reminders:
        return True, "No reminders to cancel"
    
    # Cancel each reminder
    cancelled_count = 0
    for reminder in reminders:
        reminder_id = reminder.get('alertToken')
        if reminder_id:
            success, _ = cancel_reminder(handler_input, reminder_id)
            if success:
                cancelled_count += 1
    
    return True, f"Cancelled {cancelled_count} reminders"

def build_permissions_response(handler_input) -> Dict[str, Any]:
    """
    Build a response that prompts the user to grant reminders permission.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Dict[str, Any]: Response object with permissions card
    """
    try:
        # Import response builder from ASK SDK
        from ask_sdk_model.ui import AskForPermissionsConsentCard
        
        # Create speech output
        speech = "To set reminders for your rehabilitation sessions, I need permission to use the Alexa Reminders feature. I've sent a card to your Alexa app where you can grant this permission."
        
        # Create permissions card
        permissions_card = AskForPermissionsConsentCard(
            permissions=["alexa::alerts:reminders:skill:readwrite"]
        )
        
        # Build response
        return handler_input.response_builder.speak(speech)\
            .set_card(permissions_card)\
            .response
    
    except ImportError:
        # If ASK SDK is not available, return a dictionary for the response
        return {
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "To set reminders for your rehabilitation sessions, I need permission to use the Alexa Reminders feature. I've sent a card to your Alexa app where you can grant this permission."
                },
                "card": {
                    "type": "AskForPermissionsConsent",
                    "permissions": ["alexa::alerts:reminders:skill:readwrite"]
                },
                "shouldEndSession": True
            }
        }
