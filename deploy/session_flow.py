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
import time

# Import from other modules
from exercise_library import (
    get_exercise_by_id,
    get_exercise_routine,
    get_formatted_instructions
)
import config
from progress_tracker import log_session_completion, log_partial_session
from difficulty_engine import (
    get_user_difficulty, 
    should_check_difficulty_feedback,
    get_difficulty_feedback_prompt,
    process_difficulty_feedback,
    evaluate_session,
    save_session_progress,
    get_session_progress,
    clear_session_progress,
    get_congratulatory_message
)

class SessionState:
    """Class to represent and manage the state of a rehabilitation session."""

    def __init__(self, user_id: str, exercise_type: str = "physical"):
        """
        Initialize a new session state.

        Args:
            user_id (str): The unique identifier for the user
            exercise_type (str): The type of exercise ("physical", "speech", or "cognitive")
        """
        self.user_id = user_id
        self.exercise_type = exercise_type
        self.current_index = 0

        # Get user's difficulty level
        self.difficulty = get_user_difficulty(user_id)

        # Get appropriate exercise routine based on type and difficulty
        self.exercises = get_exercise_routine(exercise_type, self.difficulty)

        self.start_time = datetime.datetime.now().isoformat()
        self.completed = False
        self.last_action_time = datetime.datetime.now().isoformat()
        
        # New fields for passive tracking
        self.skips = []  # List of skipped exercise IDs
        self.repeats = []  # List of integers counting repeats for each exercise
        self.completion_times = []  # List of completion times in seconds for each exercise
        self.feedback = []  # List of feedback levels for exercises
        self.last_exercise_start_time = time.time()  # Track when the current exercise started
        self.should_ask_feedback = False  # Flag to indicate if we should ask for feedback
        self.pending_congratulation = False  # Flag to indicate if we should congratulate the user

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the session state to a dictionary for storage in Alexa session attributes.

        Returns:
            Dict[str, Any]: Dictionary representation of the session state
        """
        return {
            "user_id": self.user_id,
            "exercise_type": self.exercise_type,
            "difficulty": self.difficulty,
            "current_index": self.current_index,
            "exercise_ids": [ex["id"] for ex in self.exercises],
            "start_time": self.start_time,
            "completed": self.completed,
            "last_action_time": datetime.datetime.now().isoformat(),
            "skips": self.skips,
            "repeats": self.repeats,
            "completion_times": self.completion_times,
            "feedback": self.feedback,
            "last_exercise_start_time": self.last_exercise_start_time,
            "should_ask_feedback": self.should_ask_feedback,
            "pending_congratulation": self.pending_congratulation,
            "inProgress": not self.completed,
            "sessionStartDate": self.start_time
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
        session = cls(state_dict["user_id"], state_dict.get("exercise_type", "physical"))
        session.current_index = int(state_dict.get("current_index", 0))
        session.difficulty = state_dict.get("difficulty", "beginner")

        # Reconstruct exercises from IDs
        exercise_ids = state_dict.get("exercise_ids", [])
        session.exercises = [get_exercise_by_id(ex_id) for ex_id in exercise_ids if get_exercise_by_id(ex_id)]

        session.start_time = state_dict.get("start_time", session.start_time)
        session.completed = state_dict.get("completed", False)
        session.last_action_time = state_dict.get("last_action_time", session.last_action_time)
        
        # Restore passive tracking fields
        session.skips = state_dict.get("skips", [])
        session.repeats = state_dict.get("repeats", [])
        session.completion_times = state_dict.get("completion_times", [])
        session.feedback = state_dict.get("feedback", [])
        session.last_exercise_start_time = state_dict.get("last_exercise_start_time", time.time())
        session.should_ask_feedback = state_dict.get("should_ask_feedback", False)
        session.pending_congratulation = state_dict.get("pending_congratulation", False)

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
        # Record completion time for the current exercise
        completion_time = time.time() - self.last_exercise_start_time
        while len(self.completion_times) <= self.current_index:
            self.completion_times.append(0)
        self.completion_times[self.current_index] = completion_time

        if self.current_index < len(self.exercises) - 1:
            self.current_index += 1
            self.last_action_time = datetime.datetime.now().isoformat()
            self.last_exercise_start_time = time.time()
            
            # Check if we should ask for feedback after this exercise
            self.should_ask_feedback = should_check_difficulty_feedback(self.current_index)
            
            return True
        return False

    def skip(self) -> bool:
        """
        Skip the current exercise and move to the next one.

        Returns:
            bool: True if successfully skipped, False if at the end of the session
        """
        # Record that this exercise was skipped by storing its ID
        current_exercise = self.get_current_exercise()
        if current_exercise:
            self.skips.append(current_exercise["id"])
        
        # Advance to next exercise
        if self.current_index < len(self.exercises) - 1:
            self.current_index += 1
            self.last_action_time = datetime.datetime.now().isoformat()
            self.last_exercise_start_time = time.time()
            
            # Check if we should ask for feedback after this exercise
            self.should_ask_feedback = should_check_difficulty_feedback(self.current_index)
            
            return True
        return False

    def repeat(self) -> None:
        """Record that the current exercise was repeated."""
        # Increment repeat count for the current exercise
        while len(self.repeats) <= self.current_index:
            self.repeats.append(0)
        self.repeats[self.current_index] += 1
        
        # Reset the start time for this exercise
        self.last_exercise_start_time = time.time()

    def record_feedback(self, feedback_level: str) -> Dict[str, Any]:
        """
        Record user feedback for the current exercise.
        
        Args:
            feedback_level (str): The feedback level (comfortable, challenging, too-hard)
            
        Returns:
            Dict[str, Any]: Result of processing the feedback
        """
        # Record the feedback
        while len(self.feedback) <= self.current_index:
            self.feedback.append("")
        self.feedback[self.current_index] = feedback_level
        
        # Process the feedback
        current_exercise = self.get_current_exercise()
        if current_exercise:
            return process_difficulty_feedback(self.user_id, feedback_level, current_exercise["id"])
        return {"difficulty_changed": False}

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
        
        # Evaluate the session and adjust difficulty if needed
        session_stats = {
            "feedback": self.feedback,
            "skips": self.skips,
            "repeats": self.repeats,
            "completion_times": self.completion_times
        }
        
        evaluation = evaluate_session(self.user_id, session_stats)
        self.pending_congratulation = evaluation.get("congratulate", False)
        
        # Clear session progress since we're done
        clear_session_progress(self.user_id)

    def reload_exercises(self) -> None:
        """Reload exercises based on current difficulty level."""
        # Save current position
        current_position = self.current_index / max(1, len(self.exercises))
        
        # Get updated difficulty level
        self.difficulty = get_user_difficulty(self.user_id)
        
        # Reload exercises
        self.exercises = get_exercise_routine(self.exercise_type, self.difficulty)
        
        # Adjust current index to maintain approximate position
        self.current_index = min(len(self.exercises) - 1, int(current_position * len(self.exercises)))
        
        # Reset start time for current exercise
        self.last_exercise_start_time = time.time()

    def save_progress(self) -> bool:
        """
        Save session progress for resume functionality.
        
        Returns:
            bool: True if successful, False otherwise
        """
        session_data = {
            "inProgress": not self.completed,
            "exerciseType": self.exercise_type,
            "currentIndex": self.current_index,
            "difficultyLevel": self.difficulty,
            "sessionStartDate": self.start_time,
            "exercise_ids": [ex["id"] for ex in self.exercises],
            "skips": self.skips,
            "repeats": self.repeats,
            "feedback": self.feedback
        }
        
        return save_session_progress(self.user_id, session_data)


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
        
        # Also save progress for resume functionality if session is in progress
        if not session_state.completed:
            session_state.save_progress()
    except Exception as e:
        print(f"Error saving session state: {str(e)}")


def start_session(handler_input, user_id: str, exercise_type: str = "physical") -> Tuple[str, bool]:
    """
    Start a new rehabilitation session.

    Args:
        handler_input: The Alexa handler input object
        user_id (str): The unique identifier for the user
        exercise_type (str): The type of exercise ("physical", "speech", or "cognitive")

    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Validate exercise type
    if exercise_type not in ["physical", "speech", "cognitive"]:
        exercise_type = "physical"  # Default to physical if invalid

    # Create a new session state
    session_state = SessionState(user_id, exercise_type)

    # Save to session attributes
    save_session_state(handler_input, session_state)

    # Get the first exercise
    current_exercise = session_state.get_current_exercise()

    if not current_exercise:
        return f"I couldn't find any {exercise_type} exercises for your session. Please try again later.", True

    # Format the response based on exercise type
    exercise_instructions = get_formatted_instructions(current_exercise)

    # Customize intro based on exercise type
    if exercise_type == "physical":
        intro = "Starting your physical therapy session. Make sure you're in a comfortable position with enough space to move safely."
    elif exercise_type == "speech":
        intro = "Starting your speech therapy session. Find a quiet place where you can speak comfortably without distractions."
    elif exercise_type == "cognitive":
        intro = "Starting your cognitive exercise session. Find a quiet place where you can focus without distractions."
    else:
        intro = f"Starting your {exercise_type} rehabilitation session."

    response_text = (
        f"{intro} "
        f"Let's begin with the first exercise. {exercise_instructions} "
        f"When you're ready for the next exercise, say 'next exercise'."
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
        return "I couldn't find your active session. Let's start a new one. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", True

    # Check if we have a pending congratulation for difficulty increase
    congratulation_text = ""
    if session_state.pending_congratulation:
        congratulation_text = get_congratulatory_message() + " "
        session_state.pending_congratulation = False

    # Try to advance to the next exercise
    if session_state.advance():
        # Get the new current exercise
        current_exercise = session_state.get_current_exercise()

        # Save updated state
        save_session_state(handler_input, session_state)

        # Format the response
        exercise_instructions = get_formatted_instructions(current_exercise)

        # Customize encouragement based on exercise type
        if session_state.exercise_type == "physical":
            encouragement = "Great job with your physical exercise!"
        elif session_state.exercise_type == "speech":
            encouragement = "Excellent work with your speech practice!"
        elif session_state.exercise_type == "cognitive":
            encouragement = "Well done with that cognitive exercise!"
        else:
            encouragement = "Great job!"

        response_text = f"{congratulation_text}{encouragement} Let's move on to the next exercise. {exercise_instructions}"

        # Check if this is the last exercise
        if session_state.is_complete():
            response_text += " This is the last exercise in your session. Take your time."
            
        # Check if we should ask for difficulty feedback
        if session_state.should_ask_feedback:
            response_text += f" {get_difficulty_feedback_prompt()}"

        return response_text, False
    else:
        # We're at the end of the session
        session_state.mark_completed()
        save_session_state(handler_input, session_state)

        # Log session completion with exercise type
        log_session_completion(session_state.user_id, session_state.exercise_type)
        
        # Update session attributes for simulator testing
        update_session_completion_attributes(handler_input, session_state.exercise_type)
        
        # Rest of the function...


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
        return "I couldn't find your active session. Let's start a new one. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", True

    # Get the current exercise
    current_exercise = session_state.get_current_exercise()

    if not current_exercise:
        return "I couldn't find the current exercise. Let's start a new session. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", True

    # Record that this exercise was repeated
    session_state.repeat()
    save_session_state(handler_input, session_state)

    # Format the response
    exercise_instructions = get_formatted_instructions(current_exercise)
    response_text = f"I'll repeat the current exercise. {exercise_instructions}"

    return response_text, False


def skip_exercise(handler_input) -> Tuple[str, bool]:
    """
    Skip the current exercise and move to the next one.

    Args:
        handler_input: The Alexa handler input object

    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get current session state
    session_state = get_session_state(handler_input)

    if not session_state:
        return "I couldn't find your active session. Let's start a new one. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", True

    # Get the current exercise before skipping
    current_exercise = session_state.get_current_exercise()

    if not current_exercise:
        return "I couldn't find the current exercise. Let's start a new session. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", True

    # Try to skip to the next exercise
    if session_state.skip():
        # Get the new current exercise
        new_exercise = session_state.get_current_exercise()

        # Save updated state
        save_session_state(handler_input, session_state)

        # Format the response
        exercise_instructions = get_formatted_instructions(new_exercise)
        response_text = f"Skipping that exercise. Let's try this one instead. {exercise_instructions}"

        # Check if this is the last exercise
        if session_state.is_complete():
            response_text += " This is the last exercise in your session. Take your time."

        return response_text, False
    else:
        # We're at the end of the session
        session_state.mark_completed()
        save_session_state(handler_input, session_state)

        # Log session completion
        log_session_completion(session_state.user_id, session_state.exercise_type)
        
        # Update session attributes for simulator testing
        update_session_completion_attributes(handler_input, session_state.exercise_type)

        return "That was the last exercise. Your session is now complete. Great job today!", True


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
            log_partial_session(
                session_state.user_id,
                session_state.current_index + 1,
                len(session_state.exercises),
                session_state.exercise_type
            )
        except Exception as e:
            print(f"Error logging partial session: {str(e)}")

    return "Your rehabilitation session has been ended. Remember, consistent practice helps with recovery. Come back soon!", True


def get_session_summary(handler_input) -> Tuple[str, bool]:
    """
    Get a summary of the current session.

    Args:
        handler_input: The Alexa handler input object

    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get current session state
    session_state = get_session_state(handler_input)

    if not session_state:
        return "You don't have an active session. You can start one by saying 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", False

    # Get current exercise
    current_exercise = session_state.get_current_exercise()
    
    if not current_exercise:
        return "I couldn't find information about your current exercise. Let's start a new session. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", True

    # Calculate progress
    total_exercises = len(session_state.exercises)
    current_index = session_state.current_index + 1  # 1-based for user-friendly display
    progress_percent = int((session_state.current_index / total_exercises) * 100)

    # Format response
    response_text = (
        f"You're doing {session_state.exercise_type} therapy at {session_state.difficulty} level. "
        f"You're on exercise {current_index} of {total_exercises}, which is {progress_percent}% through your session. "
    )

    # Add information about skips and repeats
    skips_count = sum(1 for skip in session_state.skips if skip)
    repeats_count = sum(session_state.repeats)
    
    if skips_count > 0:
        response_text += f"You've skipped {skips_count} exercise{'s' if skips_count > 1 else ''}. "
    
    if repeats_count > 0:
        response_text += f"You've repeated exercises {repeats_count} time{'s' if repeats_count > 1 else ''}. "

    response_text += "Would you like to continue your session?"

    return response_text, False


def process_difficulty_feedback_response(handler_input, feedback_level: str) -> Tuple[str, bool]:
    """
    Process user's response to difficulty feedback prompt.
    
    Args:
        handler_input: The Alexa handler input object
        feedback_level (str): The feedback level (comfortable, challenging, too-hard)
        
    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get current session state
    session_state = get_session_state(handler_input)

    if not session_state:
        return "I couldn't find your active session. Let's start a new one. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", True

    # Record the feedback
    result = session_state.record_feedback(feedback_level)
    
    # Save updated state
    save_session_state(handler_input, session_state)
    
    # Check if difficulty was changed immediately
    if result.get("difficulty_changed", False) and result.get("immediate_action", False):
        # Reload exercises with new difficulty
        session_state.reload_exercises()
        save_session_state(handler_input, session_state)
        
        # Get the current exercise
        current_exercise = session_state.get_current_exercise()
        exercise_instructions = get_formatted_instructions(current_exercise)
        
        response_text = (
            f"I've adjusted the exercises to be easier. Your new difficulty level is {result.get('new_difficulty', 'beginner')}. "
            f"Let's continue with your session. {exercise_instructions}"
        )
    else:
        # Thank the user for their feedback
        response_text = "Thanks for your feedback. "
        
        if feedback_level == "comfortable":
            response_text += "I'm glad the exercises are at a good level for you. "
        elif feedback_level == "challenging":
            response_text += "That's good - exercises should be a bit challenging but still doable. "
        elif feedback_level == "too-hard":
            response_text += "I'll make note of that and adjust accordingly. "
        
        response_text += "Say 'next exercise' when you're ready to continue."
    
    return response_text, False


def resume_session(handler_input, user_id: str) -> Tuple[str, bool]:
    """
    Resume a previously saved session.
    
    Args:
        handler_input: The Alexa handler input object
        user_id (str): The unique identifier for the user
        
    Returns:
        Tuple[str, bool]: A tuple containing (response_text, should_end_session)
    """
    # Get saved session progress
    session_progress = get_session_progress(user_id)
    
    if not session_progress:
        return "I couldn't find a saved session to resume. Let's start a new one. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", False
    
    # Extract session data
    exercise_type = session_progress.get("exerciseType", "physical")
    current_index = int(session_progress.get("currentIndex", 0))
    difficulty_level = session_progress.get("difficultyLevel", "beginner")
    
    # Create a new session state
    session_state = SessionState(user_id, exercise_type)
    session_state.difficulty = difficulty_level
    session_state.current_index = current_index
    
    # Restore other tracking data if available
    if "skips" in session_progress:
        session_state.skips = session_progress["skips"]
    if "repeats" in session_progress:
        session_state.repeats = session_progress["repeats"]
    if "feedback" in session_progress:
        session_state.feedback = session_progress["feedback"]
    
    # Save to session attributes
    save_session_state(handler_input, session_state)
    
    # Get the current exercise
    current_exercise = session_state.get_current_exercise()
    
    if not current_exercise:
        return "I couldn't find your saved exercise. Let's start a new session. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'.", False
    
    # Format the response
    exercise_instructions = get_formatted_instructions(current_exercise)
    
    response_text = (
        f"Welcome back to your {exercise_type} therapy session. "
        f"We'll continue where you left off. {exercise_instructions} "
        f"Say 'next exercise' when you're ready to continue."
    )
    
    return response_text, False


def update_session_completion_attributes(handler_input, exercise_type):
    """Update session attributes after completing a session for simulator testing"""
    session_attr = handler_input.attributes_manager.session_attributes
    
    # Mark that a session was completed
    session_attr['completed_session'] = True
    
    # Increment total sessions
    total_sessions = session_attr.get('total_sessions_completed', 0) + 1
    session_attr['total_sessions_completed'] = total_sessions
    
    # Track exercise types
    exercise_counts = session_attr.get('exercise_counts', {})
    exercise_counts[exercise_type] = exercise_counts.get(exercise_type, 0) + 1
    session_attr['exercise_counts'] = exercise_counts
    
    # Save updated attributes
    handler_input.attributes_manager.session_attributes = session_attr
