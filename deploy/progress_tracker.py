"""
progress_tracker.py - User progress tracking for Rehab Buddy Alexa Skill

This module manages user progress tracking and DynamoDB interactions for the Rehab Buddy
Alexa skill. It provides functions to log session completions, retrieve user progress data,
and calculate streaks to support the progress tracking feature of the application.

The module abstracts all database operations, providing a clean interface for other
modules to interact with the persistence layer.
"""

import boto3
import datetime
import json
import time
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

# Import configuration
import config

# Initialize DynamoDB client/resource based on configuration
def get_dynamodb_resource():
    """
    Get the DynamoDB resource based on configuration settings.
    
    Returns:
        boto3.resource: The DynamoDB resource
    """
    dynamo_config = config.get_dynamo_config()
    return boto3.resource('dynamodb', **dynamo_config)

def get_dynamodb_client():
    """
    Get the DynamoDB client based on configuration settings.
    
    Returns:
        boto3.client: The DynamoDB client
    """
    dynamo_config = config.get_dynamo_config()
    return boto3.client('dynamodb', **dynamo_config)

def ensure_table_exists():
    """
    Ensure the DynamoDB table exists, creating it if necessary.
    
    Returns:
        bool: True if table exists or was created, False on error
    """
    try:
        dynamodb = get_dynamodb_client()
        
        # Check if table exists
        try:
            dynamodb.describe_table(TableName=config.DYNAMO_TABLE_NAME)
            print(f"Table {config.DYNAMO_TABLE_NAME} exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                print(f"Creating table {config.DYNAMO_TABLE_NAME}")
                
                # Create the table
                table = dynamodb.create_table(
                    TableName=config.DYNAMO_TABLE_NAME,
                    KeySchema=[
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'  # Partition key
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'user_id',
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                
                # Wait for table creation
                print(f"Waiting for table {config.DYNAMO_TABLE_NAME} to be created...")
                waiter = dynamodb.get_waiter('table_exists')
                waiter.wait(TableName=config.DYNAMO_TABLE_NAME)
                print(f"Table {config.DYNAMO_TABLE_NAME} created")
                return True
            else:
                # Other error
                print(f"Error checking table existence: {str(e)}")
                return False
    except Exception as e:
        print(f"Error ensuring table exists: {str(e)}")
        return False

def log_session_completion(user_id: str, exercise_type: str = "physical") -> bool:
    """
    Log a completed rehabilitation session for a user.
    
    Args:
        user_id (str): The unique identifier for the user
        exercise_type (str): The type of exercise completed (physical, speech, cognitive)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config.PROGRESS_TRACKING_ENABLED:
        print("Progress tracking is disabled")
        return True
    
    try:
        # Ensure table exists
        if not ensure_table_exists():
            print("Failed to ensure table exists")
            return False
        
        # Get current date in ISO format
        today = datetime.datetime.now().date().isoformat()
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get current user data
        try:
            response = table.get_item(Key={'user_id': user_id})
            item = response.get('Item', {})
        except ClientError as e:
            print(f"Error getting user data: {str(e)}")
            item = {}
        
        # Update session count and dates
        sessions_completed = item.get('sessions_completed', 0) + 1
        last_session_date = item.get('last_session_date', '')
        session_dates = item.get('session_dates', [])
        
        # Add today's date if not already in the list
        if today not in session_dates:
            session_dates.append(today)
        
        # Update exercise type specific counts
        physical_sessions = item.get('physical_sessions', 0)
        speech_sessions = item.get('speech_sessions', 0)
        cognitive_sessions = item.get('cognitive_sessions', 0)
        
        if exercise_type == "physical":
            physical_sessions += 1
        elif exercise_type == "speech":
            speech_sessions += 1
        elif exercise_type == "cognitive":
            cognitive_sessions += 1
        
        # Calculate streak
        current_streak = calculate_streak(session_dates)
        
        # Update max streak if needed
        max_streak = max(current_streak, item.get('max_streak', 0))
        
        # Prepare update data
        update_data = {
            'user_id': user_id,
            'sessions_completed': sessions_completed,
            'physical_sessions': physical_sessions,
            'speech_sessions': speech_sessions,
            'cognitive_sessions': cognitive_sessions,
            'last_session_date': today,
            'session_dates': session_dates,
            'current_streak': current_streak,
            'max_streak': max_streak,
            'last_updated': datetime.datetime.now().isoformat()
        }
        
        # Update DynamoDB
        table.put_item(Item=update_data)
        print(f"Session completion logged for user {user_id}, type: {exercise_type}")
        return True
    
    except Exception as e:
        print(f"Error logging session completion: {str(e)}")
        return False


def finish_session(user_id: str, exercise_type: str, completed: bool = True) -> bool:
    """Finish a rehabilitation session and update counters.

    This is a thin wrapper around :func:`log_session_completion` that allows
    callers to conditionally update the user's session counters. If
    ``completed`` is ``False`` the function simply returns ``True`` without
    touching the counters.  This enables callers such as the Stop intent
    handler to avoid double counting when a session is ended early.

    Args:
        user_id: The Alexa user identifier.
        exercise_type: The type of exercise session.
        completed: Whether the session was fully completed.

    Returns:
        bool: ``True`` on success, ``False`` otherwise.
    """

    if not completed:
        # Nothing to update if the session wasn't completed.
        return True

    return log_session_completion(user_id, exercise_type)

def log_partial_session(user_id: str, completed: int, total: int, exercise_type: str = "physical") -> bool:
    """
    Log a partially completed rehabilitation session.
    
    Args:
        user_id (str): The unique identifier for the user
        completed (int): Number of exercises completed
        total (int): Total number of exercises in the session
        exercise_type (str): The type of exercise (physical, speech, cognitive)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config.PROGRESS_TRACKING_ENABLED:
        print("Progress tracking is disabled")
        return True
    
    try:
        # Ensure table exists
        if not ensure_table_exists():
            print("Failed to ensure table exists")
            return False
        
        # Get current date in ISO format
        today = datetime.datetime.now().date().isoformat()
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get current user data
        try:
            response = table.get_item(Key={'user_id': user_id})
            item = response.get('Item', {})
        except ClientError as e:
            print(f"Error getting user data: {str(e)}")
            item = {}
        
        # Update partial sessions data
        partial_sessions = item.get('partial_sessions', [])
        
        # Add this partial session
        partial_sessions.append({
            'date': today,
            'completed': completed,
            'total': total,
            'percentage': round((completed / total) * 100),
            'exercise_type': exercise_type
        })
        
        # Keep only the last 10 partial sessions
        if len(partial_sessions) > 10:
            partial_sessions = partial_sessions[-10:]
        
        # Prepare update data
        update_data = {
            'user_id': user_id,
            'partial_sessions': partial_sessions,
            'last_updated': datetime.datetime.now().isoformat()
        }
        
        # Update DynamoDB
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET partial_sessions = :p, last_updated = :u",
            ExpressionAttributeValues={
                ':p': partial_sessions,
                ':u': update_data['last_updated']
            }
        )
        
        print(f"Partial session logged for user {user_id}: {completed}/{total}, type: {exercise_type}")
        return True
    
    except Exception as e:
        print(f"Error logging partial session: {str(e)}")
        return False

def get_user_progress(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve progress data for a user.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        Optional[Dict[str, Any]]: User progress data or None if not found or error
    """
    if not config.PROGRESS_TRACKING_ENABLED:
        print("Progress tracking is disabled")
        return {
            'sessions_completed': 0,
            'physical_sessions': 0,
            'speech_sessions': 0,
            'cognitive_sessions': 0,
            'current_streak': 0,
            'max_streak': 0
        }
    
    try:
        # Ensure table exists
        if not ensure_table_exists():
            print("Failed to ensure table exists")
            return None
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get user data
        try:
            response = table.get_item(Key={'user_id': user_id})
            item = response.get('Item')
            
            if not item:
                # No data found, return default values
                return {
                    'sessions_completed': 0,
                    'physical_sessions': 0,
                    'speech_sessions': 0,
                    'cognitive_sessions': 0,
                    'current_streak': 0,
                    'max_streak': 0
                }
            
            return item
        
        except ClientError as e:
            print(f"Error getting user progress: {str(e)}")
            return None
    
    except Exception as e:
        print(f"Error retrieving user progress: {str(e)}")
        return None

def calculate_streak(session_dates: List[str]) -> int:
    """
    Calculate the current streak based on session dates.
    
    A streak is defined as consecutive days with completed sessions.
    
    Args:
        session_dates (List[str]): List of ISO format dates when sessions were completed
        
    Returns:
        int: The current streak length in days
    """
    if not session_dates:
        return 0
    
    # Sort dates in descending order (newest first)
    sorted_dates = sorted(session_dates, reverse=True)
    
    # Get today and yesterday as ISO strings
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    today_iso = today.isoformat()
    yesterday_iso = yesterday.isoformat()
    
    # Check if the most recent session is from today or yesterday
    if sorted_dates[0] != today_iso and sorted_dates[0] != yesterday_iso:
        # Most recent session is older than yesterday, streak is broken
        return 0
    
    # Count consecutive days
    streak = 1
    for i in range(1, len(sorted_dates)):
        # Convert current and previous dates to datetime objects
        current_date = datetime.date.fromisoformat(sorted_dates[i])
        prev_date = datetime.date.fromisoformat(sorted_dates[i-1])
        
        # Check if dates are consecutive
        if (prev_date - current_date).days == 1:
            streak += 1
        elif (prev_date - current_date).days == 0:
            # Same day, don't increment streak
            continue
        else:
            # Gap in dates, streak is broken
            break
    
    return streak

def get_weekly_summary(user_id: str) -> Dict[str, Any]:
    """
    Get a summary of the user's activity for the current week.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        Dict[str, Any]: Weekly summary data
    """
    progress = get_user_progress(user_id)
    
    if not progress:
        return {
            'sessions_this_week': 0,
            'total_sessions': 0,
            'physical_sessions': 0,
            'speech_sessions': 0,
            'cognitive_sessions': 0,
            'current_streak': 0,
            'max_streak': 0
        }
    
    # Get dates for the current week (last 7 days)
    today = datetime.datetime.now().date()
    week_start = today - datetime.timedelta(days=6)  # 7 days including today
    
    # Filter session dates for the current week
    session_dates = progress.get('session_dates', [])
    sessions_this_week = sum(1 for date in session_dates if date >= week_start.isoformat())
    
    return {
        'sessions_this_week': sessions_this_week,
        'total_sessions': progress.get('sessions_completed', 0),
        'physical_sessions': progress.get('physical_sessions', 0),
        'speech_sessions': progress.get('speech_sessions', 0),
        'cognitive_sessions': progress.get('cognitive_sessions', 0),
        'current_streak': progress.get('current_streak', 0),
        'max_streak': progress.get('max_streak', 0)
    }

def get_exercise_type_stats(user_id: str) -> Dict[str, int]:
    """
    Get statistics for each exercise type.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        Dict[str, int]: Dictionary with counts for each exercise type
    """
    progress = get_user_progress(user_id)
    
    if not progress:
        return {
            'physical': 0,
            'speech': 0,
            'cognitive': 0
        }
    
    return {
        'physical': progress.get('physical_sessions', 0),
        'speech': progress.get('speech_sessions', 0),
        'cognitive': progress.get('cognitive_sessions', 0)
    }

def delete_user_data(user_id: str) -> bool:
    """
    Delete all progress data for a user.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config.PROGRESS_TRACKING_ENABLED:
        print("Progress tracking is disabled")
        return True
    
    try:
        # Ensure table exists
        if not ensure_table_exists():
            print("Failed to ensure table exists")
            return False
        
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Delete user data
        table.delete_item(Key={'user_id': user_id})
        print(f"User data deleted for user {user_id}")
        return True
    
    except Exception as e:
        print(f"Error deleting user data: {str(e)}")
        return False
