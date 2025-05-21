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
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

# Import other modules
import config
from session_flow import (
    start_session,
    next_exercise,
    repeat_exercise,
    end_session,
    get_session_summary
)
from reminders import (
    has_reminders_permission,
    schedule_daily_reminder,
    cancel_all_reminders,
    build_permissions_response
)
from progress import (
    get_user_progress,
    get_weekly_summary
)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Skill Builder
sb = SkillBuilder()

# ===== REQUEST HANDLERS ===== #

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        try:
            progress = get_user_progress(user_id)
            sessions_completed = progress.get('sessions_completed', 0) if progress else 0
            if sessions_completed > 0:
                speech_text = (
                    f"Welcome back to Rehab Buddy. You've completed {sessions_completed} "
                    f"rehabilitation sessions so far. Would you like to start a new session now?"
                )
            else:
                speech_text = config.WELCOME_MESSAGE
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            speech_text = config.WELCOME_MESSAGE

        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class StartSessionIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("StartSessionIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        try:
            slots = handler_input.request_envelope.request.intent.slots
            routine_type = slots.get('RoutineType', {}).get('value', 'beginner')
        except (AttributeError, KeyError):
            routine_type = 'beginner'

        speech_text, should_end_session = start_session(handler_input, user_id, routine_type)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next step' when you're ready to continue.").response

class NextStepIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("NextStepIntent")(handler_input)

    def handle(self, handler_input):
        speech_text, should_end_session = next_exercise(handler_input)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask(
                "Say 'next step' when you're ready to continue, or 'repeat' to hear that again."
            ).response

class RepeatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.RepeatIntent")(handler_input) or
                is_intent_name("RepeatIntent")(handler_input))

    def handle(self, handler_input):
        speech_text, should_end_session = repeat_exercise(handler_input)

        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next step' when you're ready to continue.").response

class SetReminderIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SetReminderIntent")(handler_input)

    def handle(self, handler_input):
        if not has_reminders_permission(handler_input):
            return build_permissions_response(handler_input)

        try:
            slots = handler_input.request_envelope.request.intent.slots
            time_str = slots.get('ReminderTime', {}).get('value', '09:00')
        except (AttributeError, KeyError):
            time_str = '09:00'

        success, result = schedule_daily_reminder(
            handler_input,
            time_str,
            "Time for your rehabilitation exercises with Rehab Buddy"
        )

        if success:
            speech_text = f"I've scheduled a daily reminder for your rehabilitation exercises at {time_str}."
        else:
            if result == "no_permission":
                return build_permissions_response(handler_input)
            else:
                speech_text = f"I'm sorry, I couldn't schedule the reminder. {result}"

        return handler_input.response_builder.speak(speech_text).response

class CancelReminderIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CancelReminderIntent")(handler_input)

    def handle(self, handler_input):
        if not has_reminders_permission(handler_input):
            return build_permissions_response(handler_input)

        success, result = cancel_all_reminders(handler_input)

        if success:
            speech_text = "I've cancelled all your rehabilitation reminders."
        else:
            if result == "no_permission":
                return build_permissions_response(handler_input)
            else:
                speech_text = f"I'm sorry, I couldn't cancel the reminders. {result}"

        return handler_input.response_builder.speak(speech_text).response

# --- MISSING FROM FILE 2: EncouragementIntentHandler ---
class EncouragementIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("EncouragementIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "You're doing an awesome job! Every small step counts toward your recovery, so keep at it."
        )
        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask("Anything else I can help you with?")
            .response
        )

class CheckProgressIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CheckProgressIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        try:
            summary = get_weekly_summary(user_id)
            sessions_this_week = summary.get('sessions_this_week', 0)
            total_sessions = summary.get('total_sessions', 0)
            current_streak = summary.get('current_streak', 0)

            if total_sessions == 0:
                speech_text = "You haven't completed any rehabilitation sessions yet. Would you like to start one now?"
            else:
                speech_text = f"You've completed {total_sessions} rehabilitation sessions in total"
                if sessions_this_week > 0:
                    speech_text += f", with {sessions_this_week} in the past week"
                if current_streak > 0:
                    speech_text += f". You're on a {current_streak}-day streak"
                speech_text += ". Keep up the good work! Would you like to start a new session now?"
        except Exception as e:
            logger.error(f"Error getting progress: {str(e)}")
            speech_text = "I'm having trouble retrieving your progress information. Would you like to start a rehabilitation session instead?"

        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class SessionSummaryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SessionSummaryIntent")(handler_input)

    def handle(self, handler_input):
        speech_text, should_end_session = get_session_summary(handler_input)
        if should_end_session:
            return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response
        else:
            return handler_input.response_builder.speak(speech_text).ask("Say 'next step' to continue with your exercises.").response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = config.HELP_MESSAGE
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class CancelAndStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speech_text, _ = end_session(handler_input)
        return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = "I'm not sure what you want to do. You can say 'start rehab' to begin a session, 'next step' to move forward, or 'help' for more options."
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

# ===== Exception Handler ===== #
class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speech_text = "Sorry, I had trouble doing what you asked. Please try again."
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

# ===== Register Handlers ===== #
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StartSessionIntentHandler())
sb.add_request_handler(NextStepIntentHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(SetReminderIntentHandler())
sb.add_request_handler(CancelReminderIntentHandler())
sb.add_request_handler(EncouragementIntentHandler())  # Added missing intent
sb.add_request_handler(CheckProgressIntentHandler())
sb.add_request_handler(SessionSummaryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

def lambda_handler(event, context):
    """AWS Lambda handler."""
    return sb.lambda_handler()(event, context)
