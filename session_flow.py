"""
session_flow.py - Session flow management for Rehab Buddy Alexa Skill

This module manages the exercise session dialogue and flow logic for the Rehab Buddy
Alexa skill. It handles the core interaction of the rehabilitation exercises,
including starting sessions, advancing through exercises, and completing sessions.

The module maintains session state (which exercise the user is on) and provides
functions that the Alexa intent handlers can call to progress through a session.
"""

from typing import Dict, Any, List, Optional, Tuple
import datetime
import json

# Import from other modules
from exercises import (
    get_exercise_by_id, 
    get_exercise_routine, 
    create_custom_routine,
    get_formatted_instructions
)
import config

class SessionState:
    """Class to represent and manage the state of a rehabilitation session."""
    
    def __init__(self, user_id: str, routine_type: str = "beginner"):
        """
        Initialize a new session state.
        
        Args:
            user_id (str): The unique identifier for the user
            routine_type (str): The type of exercise routine ("beginner" or "intermediate")
        """
        self.user_id = user_id
        self.routine_type = routine_type
        self.current_index = 0
        self.exercises = get_exercise_routine(routine_type)
        self.start_time = datetime.datetime.now().isoformat()
        self.completed = False
        self.last_action_time = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the session state to a dictionary for storage in Alexa session attributes.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the session state
        """
        return {
            "user_id": self.user_id,
            "routine_type": self.routine_type,
            "current_index": self.current_index,
            "exercise_ids": [ex["id"] for ex in self.exercises],
            "start_time": self.start_time,
            "completed": self.completed,
            "last_action_time": datetime.datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, state_dict: Dict[str, Any]) -> 'SessionState':
        """
        Create a SessionState object from a dictionary (from Alexa session attributes).
        
        Args:
            state_dict (Dict[str, Any]): Dictionary representation of session state
            
        Returns:
            SessionState: Reconstructed session state object
        """
        session = cls(state_dict["user_id"], state_dict["routine_type"])
        session.current_index = state_dict["current_index"]
        
        # Reconstruct exercises from IDs
        exercise_ids = state_dict.get("exercise_ids", [])
        session.exercises = [get_exercise_by_id(ex_id) for ex_id in exercise_ids if get_exercise_by_id(ex_id)]
        
        session.start_time = state_dict.get("start_time", session.start_time)
        session.completed = state_dict.get("completed", False)
        session.last_action_time = state_dict.get("last_action_time", session.last_action_time)
        
        return session
    
    def get_current_exercise(self) -> Optional[Dict[str, Any]]:
        """
        Get the current exercise in the session.
        
        Returns:
            Optional[Dict[str, Any]]: The current exercise or None if no exercises or out of bounds
        """
        if not self.exercises or self.current_index >= len(self.exercises):
            return None
        return self.exercises[self.current_index]
    
    def advance(self) -> bool:
        """
        Advance to the next exercise in the session.
        
        Returns:
            bool: True if successfully advanced, False if at the end of the session
        """
        if self.current_index < len(self.exercises) - 1:
            self.current_index += 1
            self.last_action_time = datetime.datetime.now().isoformat()
            return True
        return False
    
    def is_complete(self) -> bool:
        """
        Check if the session is complete (all exercises done).
        
        Returns:
            bool: True if all exercises have been completed
        """
        return self.current_index >= len(self.exercises) - 1
    
    def mark_completed(self) -> None:
        """Mark the session as completed."""
        self.completed = True
        self.last_action_time = datetime.datetime.now().isoformat()


def get_session_state(handler_input) -> Optional[SessionState]:
    """
    Extract session state from Alexa handler input.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Optional[SessionState]: The session state or None if not found
    """
    try:
        attributes_manager = handler_input.attributes_manager
        session_attr = attributes_manager.session_attributes
        
        if "session_state" in session_attr:
            return SessionState.from_dict(session_attr["session_state"])
        return None
    except Exception as e:
        print(f"Error getting session state: {str(e)}")
        return None


def save_session_state(handler_input, session_state: SessionState) -> None:
    """
    Save session state to Alexa session attributes.
    
    Args:
        handler_input: The Alexa handler input object
        session_state (SessionState): The session state to save
    """
    try:
        attributes_manager = handler_input.attributes_manager
        session_attr = attributes_manager.session_attributes
        
        session_attr["session_state"] = session_state.to_dict()
        attributes_manager.session_attributes = session_attr
    except Exception as e:
        print(f"Error saving session state: {str(e)}")


def start_session(handler_input, user_id: str, routine_type: str = "beginner") -> Tuple[str, bool]:
    """
    Start a new rehabilitation session.
    
    Args:
        handler_input: The Alexa handler input object
        user_id (str): The unique identifier for the user
        routine_type (str): The type of exercise routine
        
    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Create a new session state
    session_state = SessionState(user_id, routine_type)
    
    # Save to session attributes
    save_session_state(handler_input, session_state)
    
    # Get the first exercise
    current_exercise = session_state.get_current_exercise()
    
    if not current_exercise:
        return "I couldn't find any exercises for your session. Please try again later.", True
    
    # Format the response
    exercise_instructions = get_formatted_instructions(current_exercise)
    response_text = (
        f"Starting your {routine_type} rehabilitation session. "
        f"Let's begin with the first exercise. {exercise_instructions} "
        f"When you're ready for the next exercise, say 'next step'."
    )
    
    return response_text, False


def next_exercise(handler_input) -> Tuple[str, bool]:
    """
    Advance to the next exercise in the session.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get current session state
    session_state = get_session_state(handler_input)
    
    if not session_state:
        return "I couldn't find your active session. Let's start a new one. Say 'start rehab' to begin.", True
    
    # Try to advance to the next exercise
    if session_state.advance():
        # Get the new current exercise
        current_exercise = session_state.get_current_exercise()
        
        # Save updated state
        save_session_state(handler_input, session_state)
        
        # Format the response
        exercise_instructions = get_formatted_instructions(current_exercise)
        response_text = f"Great job! Let's move on to the next exercise. {exercise_instructions}"
        
        # Check if this is the last exercise
        if session_state.is_complete():
            response_text += " This is the last exercise in your session. Take your time."
        
        return response_text, False
    else:
        # We're at the end of the session
        session_state.mark_completed()
        save_session_state(handler_input, session_state)
        
        # Import here to avoid circular imports
        try:
            from progress import log_session_completion
            log_session_completion(session_state.user_id)
            
            # Try to get user progress for a personalized message
            from progress import get_user_progress
            progress = get_user_progress(session_state.user_id)
            
            if progress and "sessions_completed" in progress:
                sessions = progress["sessions_completed"]
                streak = progress.get("current_streak", 0)
                
                response_text = (
                    f"{config.SESSION_COMPLETE_MESSAGE} "
                    f"You've completed {sessions} rehabilitation sessions so far. "
                )
                
                # Add streak message if applicable
                if streak > 0:
                    response_text += config.get_streak_message(streak)
                
                return response_text, True
            
        except ImportError:
            # If progress module not available, use generic message
            pass
        
        return config.SESSION_COMPLETE_MESSAGE, True


def repeat_exercise(handler_input) -> Tuple[str, bool]:
    """
    Repeat the current exercise instructions.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get current session state
    session_state = get_session_state(handler_input)
    
    if not session_state:
        return "I couldn't find your active session. Let's start a new one. Say 'start rehab' to begin.", True
    
    # Get the current exercise
    current_exercise = session_state.get_current_exercise()
    
    if not current_exercise:
        return "I couldn't find the current exercise. Let's start a new session. Say 'start rehab' to begin.", True
    
    # Format the response
    exercise_instructions = get_formatted_instructions(current_exercise)
    response_text = f"I'll repeat the current exercise. {exercise_instructions}"
    
    return response_text, False


def end_session(handler_input) -> Tuple[str, bool]:
    """
    End the current rehabilitation session.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get current session state
    session_state = get_session_state(handler_input)
    
    if not session_state:
        return "You don't have an active session to end. Goodbye!", True
    
    # Mark session as completed if it was in progress
    if not session_state.completed:
        session_state.mark_completed()
        save_session_state(handler_input, session_state)
        
        # Log partial completion
        try:
            from progress import log_partial_session
            log_partial_session(session_state.user_id, session_state.current_index + 1, len(session_state.exercises))
        except (ImportError, Exception):
            # If progress module not available or error occurs, continue without logging
            pass
    
    return "Your rehabilitation session has been ended. Remember, consistent practice helps with recovery. Come back soon!", True


def get_session_summary(handler_input) -> Tuple[str, bool]:
    """
    Get a summary of the current session progress.
    
    Args:
        handler_input: The Alexa handler input object
        
    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get current session state
    session_state = get_session_state(handler_input)
    
    if not session_state:
        return "You don't have an active session. Say 'start rehab' to begin a new session.", True
    
    # Calculate progress
    current = session_state.current_index + 1
    total = len(session_state.exercises)
    remaining = total - current
    
    # Get current exercise
    current_exercise = session_state.get_current_exercise()
    current_name = current_exercise["name"] if current_exercise else "Unknown"
    
    response_text = (
        f"You're on exercise {current} of {total} in your {session_state.routine_type} routine. "
        f"The current exercise is {current_name}. "
    )
    
    if remaining == 0:
        response_text += "This is your last exercise. Great job making it to the end!"
    elif remaining == 1:
        response_text += "You have 1 more exercise after this one."
    else:
        response_text += f"You have {remaining} more exercises to go."
    
    return response_text, False
