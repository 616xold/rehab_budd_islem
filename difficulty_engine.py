"""
difficulty_engine.py - Adaptive difficulty adjustment for Rehab Buddy Alexa Skill

This module provides functionality to adjust exercise difficulty based on user performance
and preferences. It implements an adaptive algorithm that can raise or lower the
difficulty level of exercises to match the user's capabilities and progress.

The module persists difficulty settings in DynamoDB and provides functions to retrieve
and update a user's current difficulty level.
"""

import boto3
import datetime
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

# Import configuration
import config

# Difficulty levels
DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]

# Feedback levels for DifficultyFeedbackIntent
FEEDBACK_COMFORTABLE = "comfortable"
FEEDBACK_CHALLENGING = "challenging"
FEEDBACK_TOO_HARD = "too-hard"

def get_dynamodb_resource():
    """
    Get the DynamoDB resource based on configuration settings.
    
    Returns:
        boto3.resource: The DynamoDB resource
    """
    dynamo_config = config.get_dynamo_config()
    return boto3.resource('dynamodb', **dynamo_config)

def get_user_difficulty(user_id: str) -> str:
    """
    Get the current difficulty level for a user.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        str: The current difficulty level ("beginner", "intermediate", or "advanced")
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get user data
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item', {})
        
        # Get difficulty level, default to beginner if not found
        difficulty = item.get('difficulty_level', 'beginner')
        
        # Validate difficulty level
        if difficulty not in DIFFICULTY_LEVELS:
            difficulty = 'beginner'
        
        return difficulty
    
    except Exception as e:
        print(f"Error getting user difficulty: {str(e)}")
        return 'beginner'  # Default to beginner on error

def set_user_difficulty(user_id: str, difficulty: str) -> bool:
    """
    Set the difficulty level for a user.
    
    Args:
        user_id (str): The unique identifier for the user
        difficulty (str): The difficulty level to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Validate difficulty level
    if difficulty not in DIFFICULTY_LEVELS:
        print(f"Invalid difficulty level: {difficulty}")
        return False
    
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Update user data
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET difficulty_level = :d, last_updated = :u",
            ExpressionAttributeValues={
                ':d': difficulty,
                ':u': datetime.datetime.now().isoformat()
            }
        )
        
        print(f"Set difficulty level for user {user_id} to {difficulty}")
        return True
    
    except Exception as e:
        print(f"Error setting user difficulty: {str(e)}")
        return False

def adjust_difficulty(user_id: str, make_easier: bool = False) -> str:
    """
    Adjust the difficulty level for a user based on performance or preference.
    
    Args:
        user_id (str): The unique identifier for the user
        make_easier (bool): True to make exercises easier, False to make them harder
        
    Returns:
        str: The new difficulty level
    """
    # Get current difficulty level
    current_difficulty = get_user_difficulty(user_id)
    print(f"Current difficulty for user {user_id}: {current_difficulty}")
    
    # Get index of current difficulty
    current_index = DIFFICULTY_LEVELS.index(current_difficulty)
    
    # Calculate new index
    if make_easier:
        # Make easier (move down in the list)
        new_index = max(0, current_index - 1)
        print(f"Making difficulty easier: {current_index} -> {new_index}")
    else:
        # Make harder (move up in the list)
        new_index = min(len(DIFFICULTY_LEVELS) - 1, current_index + 1)
        print(f"Making difficulty harder: {current_index} -> {new_index}")
    
    # Get new difficulty level
    new_difficulty = DIFFICULTY_LEVELS[new_index]
    print(f"New difficulty level: {new_difficulty}")
    
    # Only update if difficulty changed
    if new_difficulty != current_difficulty:
        success = set_user_difficulty(user_id, new_difficulty)
        print(f"Difficulty update success: {success}")
        
        # Log difficulty change
        log_success = log_difficulty_change(user_id, current_difficulty, new_difficulty, True)
        print(f"Difficulty change logging success: {log_success}")
    else:
        print(f"No difficulty change needed (already at {current_difficulty})")
    
    return new_difficulty


def log_difficulty_change(user_id: str, old_difficulty: str, new_difficulty: str, user_requested: bool) -> bool:
    """
    Log a change in difficulty level.
    
    Args:
        user_id (str): The unique identifier for the user
        old_difficulty (str): The previous difficulty level
        new_difficulty (str): The new difficulty level
        user_requested (bool): Whether the change was requested by the user
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get user data
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item', {})
        
        # Get difficulty change history
        difficulty_changes = item.get('difficulty_changes', [])
        
        # Add new change
        difficulty_changes.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'old_difficulty': old_difficulty,
            'new_difficulty': new_difficulty,
            'user_requested': user_requested
        })
        
        # Keep only the last 10 changes
        if len(difficulty_changes) > 10:
            difficulty_changes = difficulty_changes[-10:]
        
        # Update user data
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET difficulty_changes = :c, last_updated = :u",
            ExpressionAttributeValues={
                ':c': difficulty_changes,
                ':u': datetime.datetime.now().isoformat()
            }
        )
        
        print(f"Logged difficulty change for user {user_id}: {old_difficulty} -> {new_difficulty}")
        return True
    
    except Exception as e:
        print(f"Error logging difficulty change: {str(e)}")
        return False

def get_current_difficulty(user_id: str) -> str:
    """
    Get the current difficulty level for a user.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        str: The current difficulty level
    """
    return get_user_difficulty(user_id)

def analyze_performance(user_id: str) -> Dict[str, Any]:
    """
    Analyze user performance to determine if difficulty should be adjusted.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get user data
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item', {})
        
        # Get partial sessions
        partial_sessions = item.get('partial_sessions', [])
        
        # If no partial sessions, return default analysis
        if not partial_sessions:
            return {
                'recommend_change': False,
                'make_easier': False,
                'confidence': 0.0,
                'reason': "Not enough data to analyze performance"
            }
        
        # Calculate completion rate for recent sessions
        recent_sessions = partial_sessions[-5:]  # Last 5 sessions
        completion_rates = [s.get('percentage', 0) for s in recent_sessions]
        avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # Determine if difficulty should be adjusted
        if avg_completion_rate < 60:
            # Completion rate below 60%, recommend making easier
            return {
                'recommend_change': True,
                'make_easier': True,
                'confidence': min(1.0, (60 - avg_completion_rate) / 30),
                'reason': f"Average completion rate ({avg_completion_rate:.1f}%) is below 60%"
            }
        elif avg_completion_rate > 90:
            # Completion rate above 90%, recommend making harder
            return {
                'recommend_change': True,
                'make_easier': False,
                'confidence': min(1.0, (avg_completion_rate - 90) / 10),
                'reason': f"Average completion rate ({avg_completion_rate:.1f}%) is above 90%"
            }
        else:
            # Completion rate between 60% and 90%, no change recommended
            return {
                'recommend_change': False,
                'make_easier': False,
                'confidence': 0.0,
                'reason': f"Average completion rate ({avg_completion_rate:.1f}%) is within optimal range"
            }
    
    except Exception as e:
        print(f"Error analyzing performance: {str(e)}")
        return {
            'recommend_change': False,
            'make_easier': False,
            'confidence': 0.0,
            'reason': f"Error analyzing performance: {str(e)}"
        }

# New functions for smart difficulty adaptation

def log_exercise_feedback(user_id: str, exercise_id: str, feedback_level: str) -> bool:
    """
    Log user feedback for a specific exercise.
    
    Args:
        user_id (str): The unique identifier for the user
        exercise_id (str): The ID of the exercise
        feedback_level (str): The feedback level (comfortable, challenging, too-hard)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get user data
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item', {})
        
        # Get exercise feedback history
        exercise_feedback = item.get('exercise_feedback', [])
        
        # Add new feedback
        exercise_feedback.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'exercise_id': exercise_id,
            'feedback_level': feedback_level
        })
        
        # Keep only the last 50 feedback entries
        if len(exercise_feedback) > 50:
            exercise_feedback = exercise_feedback[-50:]
        
        # Update user data
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET exercise_feedback = :f, last_updated = :u",
            ExpressionAttributeValues={
                ':f': exercise_feedback,
                ':u': datetime.datetime.now().isoformat()
            }
        )
        
        print(f"Logged exercise feedback for user {user_id}, exercise {exercise_id}: {feedback_level}")
        return True
    
    except Exception as e:
        print(f"Error logging exercise feedback: {str(e)}")
        return False

def log_exercise_stats(user_id: str, exercise_id: str, stats: Dict[str, Any]) -> bool:
    """
    Log passive statistics for a specific exercise.
    
    Args:
        user_id (str): The unique identifier for the user
        exercise_id (str): The ID of the exercise
        stats (Dict[str, Any]): Exercise statistics (completion time, skipped, repeated)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get user data
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item', {})
        
        # Get exercise stats history
        exercise_stats = item.get('exercise_stats', [])
        
        # Add timestamp to stats
        stats['timestamp'] = datetime.datetime.now().isoformat()
        stats['exercise_id'] = exercise_id
        
        # Add new stats
        exercise_stats.append(stats)
        
        # Keep only the last 100 stats entries
        if len(exercise_stats) > 100:
            exercise_stats = exercise_stats[-100:]
        
        # Update user data
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET exercise_stats = :s, last_updated = :u",
            ExpressionAttributeValues={
                ':s': exercise_stats,
                ':u': datetime.datetime.now().isoformat()
            }
        )
        
        print(f"Logged exercise stats for user {user_id}, exercise {exercise_id}")
        return True
    
    except Exception as e:
        print(f"Error logging exercise stats: {str(e)}")
        return False

def evaluate_session(user_id: str, session_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate session statistics and determine if difficulty should be adjusted.
    
    Implements the adaptive algorithm:
    - If > 70% "comfortable" feedback → bump level next session
    - If ≥ 2 consecutive skips or any "too-hard" → step down immediately
    - Else keep level
    
    Args:
        user_id (str): The unique identifier for the user
        session_stats (Dict[str, Any]): Session statistics including feedback and passive metrics
        
    Returns:
        Dict[str, Any]: Evaluation results including recommended difficulty change
    """
    try:
        # Extract feedback from session stats
        feedback = session_stats.get('feedback', [])
        skips = session_stats.get('skips', [])
        
        # Count feedback types
        total_feedback = len(feedback)
        comfortable_count = sum(1 for f in feedback if f == FEEDBACK_COMFORTABLE)
        too_hard_count = sum(1 for f in feedback if f == FEEDBACK_TOO_HARD)
        
        # Calculate percentages
        comfortable_percentage = (comfortable_count / total_feedback * 100) if total_feedback > 0 else 0
        
        # Check for consecutive skips
        consecutive_skips = 0
        max_consecutive_skips = 0
        for is_skipped in skips:
            if is_skipped:
                consecutive_skips += 1
                max_consecutive_skips = max(max_consecutive_skips, consecutive_skips)
            else:
                consecutive_skips = 0
        
        # Apply adaptive algorithm
        if too_hard_count > 0 or max_consecutive_skips >= 2:
            # Step down immediately
            current_difficulty = get_user_difficulty(user_id)
            current_index = DIFFICULTY_LEVELS.index(current_difficulty)
            
            if current_index > 0:
                new_difficulty = DIFFICULTY_LEVELS[current_index - 1]
                set_user_difficulty(user_id, new_difficulty)
                log_difficulty_change(user_id, current_difficulty, new_difficulty, False)
                
                return {
                    'difficulty_changed': True,
                    'make_easier': True,
                    'old_difficulty': current_difficulty,
                    'new_difficulty': new_difficulty,
                    'reason': "Too hard feedback or consecutive skips detected",
                    'congratulate': False
                }
        elif comfortable_percentage > 70 and total_feedback >= 2:
            # Bump level next session
            current_difficulty = get_user_difficulty(user_id)
            current_index = DIFFICULTY_LEVELS.index(current_difficulty)
            
            if current_index < len(DIFFICULTY_LEVELS) - 1:
                new_difficulty = DIFFICULTY_LEVELS[current_index + 1]
                set_user_difficulty(user_id, new_difficulty)
                log_difficulty_change(user_id, current_difficulty, new_difficulty, False)
                
                return {
                    'difficulty_changed': True,
                    'make_easier': False,
                    'old_difficulty': current_difficulty,
                    'new_difficulty': new_difficulty,
                    'reason': f"High comfortable percentage ({comfortable_percentage:.1f}%)",
                    'congratulate': True
                }
        
        # No change needed
        return {
            'difficulty_changed': False,
            'current_difficulty': get_user_difficulty(user_id),
            'reason': "Current difficulty level is appropriate",
            'congratulate': False
        }
    
    except Exception as e:
        print(f"Error evaluating session: {str(e)}")
        return {
            'difficulty_changed': False,
            'error': str(e),
            'congratulate': False
        }

def get_congratulatory_message() -> str:
    """
    Get a congratulatory message for when difficulty is automatically increased.
    
    Returns:
        str: A congratulatory message
    """
    messages = [
        "Great progress! I've increased the difficulty level for your next session.",
        "You're doing so well that I've made your exercises a bit more challenging.",
        "Excellent work! I've adjusted your difficulty level upward for more challenge.",
        "You've mastered this level! I've increased the difficulty for your next session.",
        "Impressive progress! Your exercises will be more challenging next time."
    ]
    
    import random
    return random.choice(messages)

def should_check_difficulty_feedback(exercise_index: int) -> bool:
    """
    Determine if it's time to ask for difficulty feedback.
    
    Args:
        exercise_index (int): The current exercise index (0-based)
        
    Returns:
        bool: True if it's time to ask for feedback, False otherwise
    """
    # Ask after every N exercises (default = 2)
    check_frequency = 2
    
    # Check if it's time to ask (index is 0-based, so add 1)
    return (exercise_index + 1) % check_frequency == 0

def get_difficulty_feedback_prompt() -> str:
    """
    Get a prompt to ask for difficulty feedback.
    
    Returns:
        str: A prompt asking for difficulty feedback
    """
    return "Was that comfortable, a little challenging, or too hard?"

def process_difficulty_feedback(user_id: str, feedback_level: str, exercise_id: str) -> Dict[str, Any]:
    """
    Process user feedback about difficulty level.
    
    Args:
        user_id (str): The unique identifier for the user
        feedback_level (str): The feedback level (comfortable, challenging, too-hard)
        exercise_id (str): The ID of the current exercise
        
    Returns:
        Dict[str, Any]: Processing results
    """
    # Log the feedback
    log_success = log_exercise_feedback(user_id, exercise_id, feedback_level)
    
    # Check if immediate action is needed
    if feedback_level == FEEDBACK_TOO_HARD:
        # Make it easier immediately
        current_difficulty = get_user_difficulty(user_id)
        current_index = DIFFICULTY_LEVELS.index(current_difficulty)
        
        if current_index > 0:
            new_difficulty = DIFFICULTY_LEVELS[current_index - 1]
            set_user_difficulty(user_id, new_difficulty)
            log_difficulty_change(user_id, current_difficulty, new_difficulty, False)
            
            return {
                'difficulty_changed': True,
                'make_easier': True,
                'old_difficulty': current_difficulty,
                'new_difficulty': new_difficulty,
                'immediate_action': True
            }
    
    # No immediate action needed
    return {
        'difficulty_changed': False,
        'feedback_logged': log_success,
        'immediate_action': False
    }

def save_session_progress(user_id: str, session_data: Dict[str, Any]) -> bool:
    """
    Save session progress for resume functionality.
    
    Args:
        user_id (str): The unique identifier for the user
        session_data (Dict[str, Any]): Session data to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Add timestamp
        session_data['last_updated'] = datetime.datetime.now().isoformat()
        
        # Update user data
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET session_progress = :s",
            ExpressionAttributeValues={
                ':s': session_data
            }
        )
        
        print(f"Saved session progress for user {user_id}")
        return True
    
    except Exception as e:
        print(f"Error saving session progress: {str(e)}")
        return False

def get_session_progress(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get saved session progress for resume functionality.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        Optional[Dict[str, Any]]: Saved session progress or None if not found
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Get user data
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item', {})
        
        # Get session progress
        session_progress = item.get('session_progress')
        
        if not session_progress:
            return None
        
        # Check if session is still valid (less than 7 days old)
        last_updated = session_progress.get('last_updated')
        if last_updated:
            last_updated_date = datetime.datetime.fromisoformat(last_updated)
            now = datetime.datetime.now()
            
            if (now - last_updated_date).days >= 7:
                # Session is too old, clear it
                clear_session_progress(user_id)
                return None
        
        return session_progress
    
    except Exception as e:
        print(f"Error getting session progress: {str(e)}")
        return None

def clear_session_progress(user_id: str) -> bool:
    """
    Clear saved session progress.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get DynamoDB resource
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(config.DYNAMO_TABLE_NAME)
        
        # Update user data to remove session progress
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="REMOVE session_progress",
            ConditionExpression="attribute_exists(session_progress)"
        )
        
        print(f"Cleared session progress for user {user_id}")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # No session progress to clear
            print(f"No session progress to clear for user {user_id}")
            return True
        else:
            print(f"Error clearing session progress: {str(e)}")
            return False
    
    except Exception as e:
        print(f"Error clearing session progress: {str(e)}")
        return False
