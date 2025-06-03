"""
lambda_function.py - Main AWS Lambda handler for Rehab Buddy Alexa Skill

This module serves as the entry point for the Rehab Buddy Alexa skill. It uses the
Alexa Skills Kit SDK to handle incoming requests and route them to the appropriate
handlers. The module integrates all other components of the application (session flow,
progress tracking, reminders) to provide a complete rehabilitation experience.
"""

import logging
import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any

# Import Alexa Skills Kit SDK
from ask_sdk_core.skill_builder import CustomSkillBuilder as SkillBuilder 
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

# Import DynamoDB persistence adapter
from ask_sdk_dynamodb.adapter import DynamoDbAdapter 

# Import API client
from ask_sdk_core.api_client import DefaultApiClient

# Import other modules
import config
from session_flow import (
    start_session,
    next_exercise,
    repeat_exercise,
    skip_exercise,
    end_session,
    get_session_summary,
    process_difficulty_feedback_response,
    resume_session
)
from reminder_manager import (
    has_reminders_permission,
    schedule_daily_reminder,
    cancel_all_reminders,
    build_permissions_response
)
from progress_tracker import (
    get_user_progress,
    get_weekly_summary
)
from difficulty_engine import (
    adjust_difficulty,
    get_current_difficulty,
    get_session_progress
)
from encouragements import get_random_encouragement

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Set up DynamoDB persistence adapter
ddb_table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'RehabBuddyUserData')
ddb_persistence_adapter = DynamoDbAdapter(
    table_name=ddb_table_name,
    create_table=True,
    partition_key_name="user_id",
)

# Skill Builder with persistence adapter and API client
sb = SkillBuilder(persistence_adapter=ddb_persistence_adapter, api_client=DefaultApiClient())

# ===== REQUEST HANDLERS ===== #

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        # Check if running in simulator
        device_id = handler_input.request_envelope.context.system.device.device_id
        is_simulator = device_id.startswith("simulator")
        
        # Get session attributes
        session_attr = handler_input.attributes_manager.session_attributes
        
        try:
            # Check for in-progress session to resume
            session_progress = get_session_progress(user_id)
            
            if session_progress and session_progress.get("inProgress", False):
                # Found an in-progress session less than 7 days old
                exercise_type = session_progress.get("exerciseType", "physical")
                current_index = session_progress.get("currentIndex", 0) + 1  # Convert to 1-based for user display
                total_exercises = len(session_progress.get("exercise_ids", []))
                
                speech_text = (
                    f"Welcome back to Rehab Buddy. "
                    f"You left off on exercise {current_index} of your {exercise_type} therapy session. "
                    f"Would you like to continue where you left off?"
                )
                
                # Set a flag to indicate we're offering to resume
                session_attr["offering_resume"] = True
                handler_input.attributes_manager.session_attributes = session_attr
                
                return handler_input.response_builder.speak(speech_text).ask(speech_text).response
            
            # No in-progress session, check for completed sessions
            progress = get_user_progress(user_id)
            sessions_completed = progress.get('sessions_completed', 0) if progress else 0
            
            # For simulator testing: If no sessions in DynamoDB but we have session attributes,
            # use those instead to simulate returning user
            if is_simulator and sessions_completed == 0 and 'completed_session' in session_attr:
                sessions_completed = session_attr.get('total_sessions_completed', 1)
                
            if sessions_completed > 0:
                speech_text = (
                    f"Welcome back to Rehab Buddy. You've completed {sessions_completed} "
                    f"rehabilitation sessions so far. Would you like to start a new session? "
                    f"You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'."
                )
            else:
                speech_text = (
                    f"{config.WELCOME_MESSAGE} You can say 'start physical therapy', "
                    f"'start speech therapy', or 'start cognitive exercises'."
                )
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            speech_text = (
                f"{config.WELCOME_MESSAGE} You can say 'start physical therapy', "
                f"'start speech therapy', or 'start cognitive exercises'."
            )

        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class StartSessionIntentHandler(AbstractRequestHandler):
    """Handler for StartSessionIntent

    This handler replaces the previous StartRehabSessionIntentHandler and handles
    all session starts with the exerciseType slot.
    """
    def can_handle(self, handler_input):
        return is_intent_name("StartSessionIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        try:
            slots = handler_input.request_envelope.request.intent.slots
            exercise_type = slots.get('exerciseType', {}).get('value', 'physical')
        except (AttributeError, KeyError):
            exercise_type = 'physical'

        speech_text, should_end_session = start_session(handler_input, user_id, exercise_type)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class StartPhysicalTherapyIntentHandler(AbstractRequestHandler):
    """Handler for StartPhysicalTherapyIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("StartPhysicalTherapyIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        exercise_type = 'physical'

        speech_text, should_end_session = start_session(handler_input, user_id, exercise_type)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class StartSpeechTherapyIntentHandler(AbstractRequestHandler):
    """Handler for StartSpeechTherapyIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("StartSpeechTherapyIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        exercise_type = 'speech'

        speech_text, should_end_session = start_session(handler_input, user_id, exercise_type)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class StartCognitiveExerciseIntentHandler(AbstractRequestHandler):
    """Handler for StartCognitiveExerciseIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("StartCognitiveExerciseIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        exercise_type = 'cognitive'

        speech_text, should_end_session = start_session(handler_input, user_id, exercise_type)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class NextExerciseIntentHandler(AbstractRequestHandler):
    """Handler for NextExerciseIntent (renamed from NextStepIntent)"""
    def can_handle(self, handler_input):
        return (is_intent_name("NextExerciseIntent")(handler_input) or
                is_intent_name("NextStepIntent")(handler_input))  # Support both for backward compatibility

    def handle(self, handler_input):
        speech_text, should_end_session = next_exercise(handler_input)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask(
                "Say 'next exercise' when you're ready to continue, or 'repeat' to hear that again."
            ).response

class RepeatExerciseIntentHandler(AbstractRequestHandler):
    """Handler for RepeatExerciseIntent (renamed from RepeatStepIntent)"""
    def can_handle(self, handler_input):
        return (is_intent_name("RepeatExerciseIntent")(handler_input) or
                is_intent_name("RepeatStepIntent")(handler_input))  # Support both for backward compatibility

    def handle(self, handler_input):
        speech_text, should_end_session = repeat_exercise(handler_input)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class SkipExerciseIntentHandler(AbstractRequestHandler):
    """Handler for SkipExerciseIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("SkipExerciseIntent")(handler_input)

    def handle(self, handler_input):
        speech_text, should_end_session = skip_exercise(handler_input)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class AdjustDifficultyIntentHandler(AbstractRequestHandler):
    """Handler for AdjustDifficultyIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("AdjustDifficultyIntent")(handler_input)

    def handle(self, handler_input):
        try:
            user_id = handler_input.request_envelope.session.user.user_id
            
            # Check if running in simulator
            device_id = handler_input.request_envelope.context.system.device.device_id
            is_simulator = device_id.startswith("simulator")
            
            # Get the direction (easier or harder)
            slots = handler_input.request_envelope.request.intent.slots or {}
            
            # Log the slots for debugging
            logger.info(f"AdjustDifficultyIntent slots: {slots}")
            
            # Check if direction slot exists
            if 'direction' in slots:
                direction = slots.get('direction', {}).get('value', '')
                logger.info(f"Direction from slot: {direction}")
            else:
                # No direction slot found, default to "easier" and log
                direction = ''
                logger.info("No direction slot found in request, defaulting to 'easier'")
            
            # Default to making it easier if direction is unclear
            make_easier = True
            if direction and ('hard' in direction.lower() or 'difficult' in direction.lower() or 'challenge' in direction.lower()):
                make_easier = False
            
            logger.info(f"Adjusting difficulty, make_easier={make_easier}")
            
            # Adjust difficulty
            new_level = adjust_difficulty(user_id, make_easier)
            
            # Update session attributes with new difficulty level
            session_attr = handler_input.attributes_manager.session_attributes
            if 'current_difficulty' not in session_attr:
                session_attr['current_difficulty'] = {}
            session_attr['current_difficulty'] = new_level
            
            # Update session state if it exists
            if 'session_state' in session_attr:
                session_state = session_attr['session_state']
                session_state['difficulty'] = new_level
                session_attr['session_state'] = session_state
                
            handler_input.attributes_manager.session_attributes = session_attr
            
            # Get session state and reload exercises if in a session
            from session_flow import get_session_state, save_session_state
            session_state = get_session_state(handler_input)
            if session_state:
                # Reload exercises with new difficulty
                session_state.reload_exercises()
                save_session_state(handler_input, session_state)
            
            # Log additional information for simulator testing
            if is_simulator:
                logger.info(f"Simulator detected: Difficulty adjusted to {new_level} (make_easier={make_easier})")
                logger.info(f"Session attributes updated: {session_attr}")
            
            if make_easier:
                speech_text = f"I've adjusted the exercises to be easier. Your new difficulty level is {new_level}. Let's continue with your session."
            else:
                speech_text = f"I've adjusted the exercises to be more challenging. Your new difficulty level is {new_level}. Let's continue with your session."
            
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response
            
        except Exception as e:
            # Log the full exception details
            logger.error(f"Error in AdjustDifficultyIntentHandler: {str(e)}", exc_info=True)
            
            # Provide a more helpful error message
            speech_text = "I'm having trouble adjusting the difficulty level. Let's continue with your current exercises for now. You can try again later by saying 'make it easier' or 'make it harder'."
            
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class DifficultyFeedbackIntentHandler(AbstractRequestHandler):
    """Handler for DifficultyFeedbackIntent"""
    def can_handle(self, handler_input):
        # Check for both intent name and direct utterance patterns
        if is_intent_name("DifficultyFeedbackIntent")(handler_input):
            return True
            
        # Also check AMAZON.FallbackIntent for common feedback phrases
        if is_intent_name("AMAZON.FallbackIntent")(handler_input):
            try:
                # Get the raw utterance
                utterance = handler_input.request_envelope.request.intent.slots.get('text', {}).value
                if utterance and any(phrase in utterance.lower() for phrase in ["comfortable", "challenging", "too hard", "difficult", "easy"]):
                    return True
            except:
                pass
        return False

    def handle(self, handler_input):
        try:
            # Log the entire request for debugging
            request = handler_input.request_envelope.request
            logger.info(f"DifficultyFeedbackIntent processing: {request}")
            
            # Try multiple approaches to get the feedback level
            feedback_level = "challenging"  # Default
            
            # Approach 1: Check for level slot in DifficultyFeedbackIntent
            if hasattr(request, 'intent') and hasattr(request.intent, 'slots') and request.intent.slots:
                slots = request.intent.slots
                if 'level' in slots and hasattr(slots['level'], 'value') and slots['level'].value:
                    feedback_level = slots['level'].value
                    logger.info(f"Got feedback from level slot: {feedback_level}")
            
            # Approach 2: Check for raw utterance in FallbackIntent
            if is_intent_name("AMAZON.FallbackIntent")(handler_input):
                try:
                    utterance = request.intent.slots.get('text', {}).value.lower()
                    logger.info(f"FallbackIntent utterance: {utterance}")
                    
                    if "comfortable" in utterance or "easy" in utterance:
                        feedback_level = "comfortable"
                    elif "challenging" in utterance:
                        feedback_level = "challenging"
                    elif "hard" in utterance or "difficult" in utterance:
                        feedback_level = "too-hard"
                        
                    logger.info(f"Extracted feedback from fallback: {feedback_level}")
                except:
                    logger.warning("Failed to extract from fallback utterance")
            
            # Normalize the feedback level
            if 'comfort' in feedback_level.lower():
                feedback_level = 'comfortable'
            elif 'challenge' in feedback_level.lower():
                feedback_level = 'challenging'
            elif 'hard' in feedback_level.lower() or 'difficult' in feedback_level.lower():
                feedback_level = 'too-hard'
                
            logger.info(f"Final normalized feedback level: {feedback_level}")
            
            # Get session state to ensure it exists
            from session_flow import get_session_state, save_session_state
            session_state = get_session_state(handler_input)
            
            if not session_state:
                logger.error("No session state found when processing feedback")
                speech_text = "I couldn't find your active session. Let's start a new one. You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'."
                return handler_input.response_builder.speak(speech_text).ask(speech_text).response
            
            # Process the feedback directly with session_state to avoid any state loss
            result = session_state.record_feedback(feedback_level)
            save_session_state(handler_input, session_state)
            
            # Generate personalized response based on feedback level
            response_text = "Thanks for your feedback. "
            
            if feedback_level == "comfortable":
                response_text += "I'm glad the exercises are at a good level for you. "
            elif feedback_level == "challenging":
                response_text += "That's good - exercises should be a bit challenging but still doable. "
            elif feedback_level == "too-hard":
                response_text += "I'll make note of that and adjust accordingly. "
            
            response_text += "Say 'next exercise' when you're ready to continue."
            
            logger.info(f"Sending response: {response_text}")
            return handler_input.response_builder.speak(response_text).ask("Say 'next exercise' when you're ready to continue.").response
                
        except Exception as e:
            # Log the full exception details
            logger.error(f"Error in DifficultyFeedbackIntentHandler: {str(e)}", exc_info=True)
            
            # Provide a helpful error message
            speech_text = "Thanks for your feedback. Let's continue with your session. Say 'next exercise' when you're ready to continue."
            
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class YesIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.YesIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        session_attr = handler_input.attributes_manager.session_attributes
        
        # Check if we're offering to resume a session
        if session_attr.get("offering_resume", False):
            # Clear the flag
            session_attr["offering_resume"] = False
            handler_input.attributes_manager.session_attributes = session_attr
            
            # Resume the session
            speech_text, should_end_session = resume_session(handler_input, user_id)
            
            if should_end_session:
                return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
            else:
                return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response
        
        # Default to starting a physical therapy session
        speech_text, should_end_session = start_session(handler_input, user_id, 'physical')

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next exercise' when you're ready to continue.").response

class NoIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.NoIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        session_attr = handler_input.attributes_manager.session_attributes
        
        # Check if we're offering to resume a session
        if session_attr.get("offering_resume", False):
            # Clear the flag and any saved session progress
            session_attr["offering_resume"] = False
            handler_input.attributes_manager.session_attributes = session_attr
            
            # Clear the saved session
            from difficulty_engine import clear_session_progress
            clear_session_progress(user_id)
            
            # Prompt to start a new session
            speech_text = (
                "I've cleared your previous session. Would you like to start a new session? "
                "You can say 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'."
            )
            
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response
        
        # When user says "no" in other contexts, we provide a farewell message and end the session
        speech_text = "Okay, no problem. Remember that regular rehabilitation exercises are important for your recovery. You can start a session anytime by saying 'Alexa, open Rehab Buddy'. Goodbye!"
        return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response

class SetRehabReminderIntentHandler(AbstractRequestHandler):
    """Handler for SetRehabReminderIntent (renamed from SetReminderIntent)"""
    def can_handle(self, handler_input):
        return (is_intent_name("SetRehabReminderIntent")(handler_input) or
                is_intent_name("SetReminderIntent")(handler_input))  # Support both for backward compatibility

    def handle(self, handler_input):
        # Check if running in simulator (device ID starts with "simulator")
        device_id = handler_input.request_envelope.context.system.device.device_id
        is_simulator = device_id.startswith("simulator")
        
        if is_simulator:
            # Simulator-friendly response
            speech_text = (
                "In the simulator, I can't actually set reminders, but I can show you what would happen. "
                "I would normally schedule a daily reminder for your rehabilitation exercises. "
                "On a real device, this reminder would appear at your requested time."
            )
            return handler_input.response_builder.speak(speech_text).ask("Would you like to continue with your session?").response
        
        # Check if we have permission to set reminders
        if not has_reminders_permission(handler_input):
            return build_permissions_response(handler_input)
        
        # Get the requested time from slots
        try:
            slots = handler_input.request_envelope.request.intent.slots
            reminder_time = slots.get('ReminderTime', {}).get('value')
            
            if not reminder_time:
                # No time specified, ask for one
                speech_text = "What time would you like me to remind you about your rehabilitation exercises?"
                return handler_input.response_builder.speak(speech_text).ask(speech_text).response
            
            # Schedule the reminder
            user_id = handler_input.request_envelope.session.user.user_id
            success = schedule_daily_reminder(handler_input, user_id, reminder_time)
            
            if success:
                speech_text = f"I've set a daily reminder for your rehabilitation exercises at {reminder_time}. Is there anything else you'd like to do?"
            else:
                speech_text = "I had trouble setting your reminder. Please try again later or with a different time."
            
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response
            
        except Exception as e:
            logger.error(f"Error setting reminder: {str(e)}")
            speech_text = "I had trouble setting your reminder. Please try again later."
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class CancelRemindersIntentHandler(AbstractRequestHandler):
    """Handler for CancelRemindersIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("CancelRemindersIntent")(handler_input)

    def handle(self, handler_input):
        # Check if running in simulator (device ID starts with "simulator")
        device_id = handler_input.request_envelope.context.system.device.device_id
        is_simulator = device_id.startswith("simulator")
        
        if is_simulator:
            # Simulator-friendly response
            speech_text = (
                "In the simulator, I can't actually cancel reminders, but I can show you what would happen. "
                "I would normally cancel all your rehabilitation exercise reminders. "
                "On a real device, your reminders would be removed."
            )
            return handler_input.response_builder.speak(speech_text).ask("Would you like to continue with your session?").response
        
        # Check if we have permission to manage reminders
        if not has_reminders_permission(handler_input):
            return build_permissions_response(handler_input)
        
        # Cancel all reminders
        try:
            user_id = handler_input.request_envelope.session.user.user_id
            success = cancel_all_reminders(handler_input, user_id)
            
            if success:
                speech_text = "I've cancelled all your rehabilitation exercise reminders. Is there anything else you'd like to do?"
            else:
                speech_text = "I had trouble cancelling your reminders. Please try again later."
            
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response
            
        except Exception as e:
            logger.error(f"Error cancelling reminders: {str(e)}")
            speech_text = "I had trouble cancelling your reminders. Please try again later."
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class GetProgressIntentHandler(AbstractRequestHandler):
    """Handler for GetProgressIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("GetProgressIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        try:
            # Get user progress
            progress = get_user_progress(user_id)
            
            if not progress or progress.get('sessions_completed', 0) == 0:
                speech_text = "You haven't completed any rehabilitation sessions yet. Would you like to start one now?"
                return handler_input.response_builder.speak(speech_text).ask(speech_text).response
            
            # Get weekly summary
            weekly = get_weekly_summary(user_id)
            
            # Format response
            sessions_completed = progress.get('sessions_completed', 0)
            sessions_this_week = weekly.get('sessions_this_week', 0)
            current_streak = progress.get('current_streak', 0)
            
            speech_text = f"You've completed {sessions_completed} rehabilitation sessions in total"
            
            if sessions_this_week > 0:
                speech_text += f", including {sessions_this_week} this week"
            
            if current_streak > 0:
                speech_text += f". Your current streak is {current_streak} day"
                if current_streak > 1:
                    speech_text += "s"
            
            # Add exercise type breakdown
            physical = progress.get('physical_sessions', 0)
            speech = progress.get('speech_sessions', 0)
            cognitive = progress.get('cognitive_sessions', 0)
            
            speech_text += f". You've done {physical} physical therapy, {speech} speech therapy, and {cognitive} cognitive exercise sessions."
            
            # Add encouragement
            speech_text += f" {get_random_encouragement()}"
            
            return handler_input.response_builder.speak(speech_text).ask("Would you like to start a new session?").response
            
        except Exception as e:
            logger.error(f"Error getting progress: {str(e)}")
            speech_text = "I had trouble retrieving your progress information. Would you like to start a new session?"
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class GetSessionSummaryIntentHandler(AbstractRequestHandler):
    """Handler for GetSessionSummaryIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("GetSessionSummaryIntent")(handler_input)

    def handle(self, handler_input):
        speech_text, should_end_session = get_session_summary(handler_input)
        
        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class EndSessionIntentHandler(AbstractRequestHandler):
    """Handler for EndSessionIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("EndSessionIntent")(handler_input)

    def handle(self, handler_input):
        speech_text, should_end_session = end_session(handler_input)
        return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.HelpIntent"""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # Check if we're in a session
        from session_flow import get_session_state
        session_state = get_session_state(handler_input)
        
        if session_state:
            # In-session help
            speech_text = (
                "You're currently in a rehabilitation session. "
                "You can say 'next exercise' to move to the next exercise, 'repeat' to hear the current exercise again, "
                "or 'skip' to skip the current exercise. "
                "You can also say 'make it easier' or 'make it harder' to adjust the difficulty, "
                "or 'end session' to end your session. "
                "What would you like to do?"
            )
        else:
            # General help
            speech_text = (
                "Rehab Buddy helps you with your stroke rehabilitation exercises. "
                "You can start a session by saying 'start physical therapy', 'start speech therapy', or 'start cognitive exercises'. "
                "During a session, you can say 'next exercise', 'repeat', or 'skip'. "
                "You can also say 'set a reminder' to schedule daily reminders, "
                "or 'get my progress' to hear about your rehabilitation progress. "
                "What would you like to do?"
            )
        
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.CancelIntent and AMAZON.StopIntent"""
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # Check if we're in a session
        from session_flow import get_session_state
        session_state = get_session_state(handler_input)
        
        if session_state and not session_state.completed:
            # End the current session
            speech_text, _ = end_session(handler_input)
        else:
            # Just say goodbye
            speech_text = "Goodbye! Remember that regular rehabilitation exercises are important for your recovery."
        
        return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent"""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        try:
            # Check if this might be difficulty feedback
            utterance = handler_input.request_envelope.request.intent.slots.get('text', {}).value
            if utterance and any(word in utterance.lower() for word in ["comfortable", "challenging", "hard", "difficult", "easy"]):
                logger.info(f"Fallback caught potential difficulty feedback: {utterance}")
                # Forward to DifficultyFeedbackIntentHandler
                return DifficultyFeedbackIntentHandler().handle(handler_input)
        except:
            pass
            
        # Regular fallback handling
        speech_text = "I'm not sure what you want to do. You can say 'start physical therapy', 'next exercise', or 'help' for more options."
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for SessionEndedRequest"""
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Check if we're in a session and save progress if needed
        from session_flow import get_session_state
        session_state = get_session_state(handler_input)
        
        if session_state and not session_state.completed:
            # Save progress for resume functionality
            session_state.save_progress()
            
            # Log partial completion
            from progress_tracker import log_partial_session
            try:
                log_partial_session(
                    session_state.user_id,
                    session_state.current_index + 1,
                    len(session_state.exercises),
                    session_state.exercise_type
                )
            except Exception as e:
                logger.error(f"Error logging partial session: {str(e)}")
        
        # We can't send a response here, so just return an empty one
        return handler_input.response_builder.response

# ===== EXCEPTION HANDLERS ===== #

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and respond with custom message."""
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)

        speech = "Sorry, I had trouble doing what you asked. Please try again."
        return handler_input.response_builder.speak(speech).ask(speech).response

# ===== REGISTER HANDLERS ===== #

# Register request handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StartSessionIntentHandler())
sb.add_request_handler(StartPhysicalTherapyIntentHandler())
sb.add_request_handler(StartSpeechTherapyIntentHandler())
sb.add_request_handler(StartCognitiveExerciseIntentHandler())
sb.add_request_handler(NextExerciseIntentHandler())
sb.add_request_handler(RepeatExerciseIntentHandler())
sb.add_request_handler(SkipExerciseIntentHandler())
sb.add_request_handler(AdjustDifficultyIntentHandler())
sb.add_request_handler(DifficultyFeedbackIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(SetRehabReminderIntentHandler())
sb.add_request_handler(CancelRemindersIntentHandler())
sb.add_request_handler(GetProgressIntentHandler())
sb.add_request_handler(GetSessionSummaryIntentHandler())
sb.add_request_handler(EndSessionIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Lambda handler
lambda_handler = sb.lambda_handler()
