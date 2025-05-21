"""
config.py - Configuration settings for Rehab Buddy Alexa Skill

This module centralizes all configuration settings, environment variables, and constants
used throughout the Rehab Buddy application. It provides a single source of truth for
configuration values, making it easier to modify settings without changing code elsewhere.

Environment variables can be set in the AWS Lambda console for production or in a .env file
for local development.
"""

import os
from typing import Dict, Any

# DynamoDB Configuration
DYNAMO_TABLE_NAME = os.getenv("DYNAMO_TABLE_NAME", "RehabBuddyUserData")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# For local development/testing, set USE_LOCAL_DYNAMO=True in environment
USE_LOCAL_DYNAMO = os.getenv("USE_LOCAL_DYNAMO", "False").lower() == "true"
LOCAL_DYNAMO_ENDPOINT = os.getenv("LOCAL_DYNAMO_ENDPOINT", "http://localhost:8000")

# Alexa Skill Configuration
SKILL_ID = os.getenv("SKILL_ID", "amzn1.ask.skill.d87d6b75-7711-4373-b5e0-21f4a7244762")

# Feature Flags
REMINDERS_ENABLED = os.getenv("REMINDERS_ENABLED", "True").lower() == "true"
PROGRESS_TRACKING_ENABLED = os.getenv("PROGRESS_TRACKING_ENABLED", "True").lower() == "true"

# Alexa Permissions
REMINDERS_PERMISSION = "alexa::alerts:reminders:skill:readwrite"

# Session Configuration
DEFAULT_SESSION_LENGTH = 5  # Number of exercises per session
MIN_STREAK_DAYS = 3  # Minimum days to consider as a streak

# Response Text Templates
WELCOME_MESSAGE = "Welcome to Rehab Buddy. I can guide you through your stroke rehabilitation exercises. Would you like to start a session now?"
HELP_MESSAGE = "I can guide you through your rehabilitation exercises. You can say 'start rehab' to begin, 'next step' to move forward, or 'repeat' to hear instructions again."
EXIT_MESSAGE = "Thank you for using Rehab Buddy. Remember, consistent practice is key to recovery. See you next time!"
SESSION_COMPLETE_MESSAGE = "Great job! You've completed today's rehabilitation session. Keep up the good work!"
PERMISSION_CARD_TITLE = "Rehab Buddy Permissions"
PERMISSION_CARD_TEXT = "To set reminders, Rehab Buddy needs permission to access the Alexa Reminders feature."

# Error Messages
ERROR_GENERIC = "I'm sorry, something went wrong. Please try again later."
ERROR_NO_PERMISSION = "I need permission to set reminders. Please check the Alexa app to grant permission."
ERROR_DATABASE = "I'm having trouble accessing your progress data. Please try again later."

def get_dynamo_config() -> Dict[str, Any]:
    """
    Returns DynamoDB configuration based on environment settings.
    
    Returns:
        Dict[str, Any]: Configuration dictionary for boto3 DynamoDB client
    """
    config = {
        'region_name': AWS_REGION
    }
    
    if USE_LOCAL_DYNAMO:
        config['endpoint_url'] = LOCAL_DYNAMO_ENDPOINT
    
    return config

def get_streak_message(streak_days: int) -> str:
    """
    Returns an encouraging message based on the user's current streak.
    
    Args:
        streak_days (int): Number of consecutive days with completed sessions
        
    Returns:
        str: Encouraging message about the streak
    """
    if streak_days == 0:
        return "Let's start building a streak by completing sessions regularly."
    elif streak_days == 1:
        return "You've completed 1 day. Come back tomorrow to start a streak!"
    elif streak_days < MIN_STREAK_DAYS:
        return f"You've completed {streak_days} days in a row. Keep going!"
    elif streak_days < 7:
        return f"Great job! You have a {streak_days}-day streak going. Keep it up!"
    elif streak_days < 14:
        return f"Impressive! Your {streak_days}-day streak shows real dedication!"
    elif streak_days < 30:
        return f"Amazing! Your {streak_days}-day streak is helping your recovery!"
    else:
        return f"Outstanding! Your {streak_days}-day streak is exceptional! Your dedication to recovery is inspiring!"
