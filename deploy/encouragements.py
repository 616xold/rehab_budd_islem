"""
encouragements.py - Motivational messages for Rehab Buddy Alexa Skill

This module provides a collection of motivational and encouraging messages that can be
used throughout the Rehab Buddy application. It offers functions to retrieve random
encouragements or select specific messages based on context (exercise type, progress, etc.).

The variety of messages helps keep the user experience fresh and engaging during
rehabilitation sessions.
"""

import random
from typing import List, Dict, Any, Optional

# General encouragement messages
GENERAL_ENCOURAGEMENTS = [
    "You're doing an awesome job! Every small step counts toward your recovery.",
    "Great work! Consistency is key to rehabilitation success.",
    "You should be proud of yourself. Your dedication to recovery is inspiring.",
    "Keep up the great work! Your efforts today will pay off tomorrow.",
    "Excellent job! Remember that progress in rehabilitation is often gradual but meaningful.",
    "You're making progress! Each session brings you closer to your recovery goals.",
    "Well done! Your commitment to rehabilitation is admirable.",
    "Fantastic effort! Recovery is a journey, and you're taking important steps.",
    "You're showing real determination. That's exactly what successful rehabilitation requires.",
    "Impressive work! Your persistence will help you regain strength and ability."
]

# Exercise type specific encouragements
PHYSICAL_ENCOURAGEMENTS = [
    "Your physical progress is impressive! Keep building that strength.",
    "Great job with your movements! Physical therapy is all about consistency.",
    "Your body is getting stronger with each exercise. Keep it up!",
    "Excellent physical work! These exercises are helping rebuild important connections.",
    "Your coordination is improving! These physical exercises make a real difference."
]

SPEECH_ENCOURAGEMENTS = [
    "Your speech practice is paying off! Communication is such an important skill.",
    "Great articulation! Speech therapy takes patience, and you're showing plenty of it.",
    "Your speech exercises are strengthening important muscles. Well done!",
    "Excellent pronunciation! These speech exercises are making a difference.",
    "Your communication skills are improving with each session. Keep practicing!"
]

COGNITIVE_ENCOURAGEMENTS = [
    "Your brain is building new connections with each cognitive exercise. Great work!",
    "Excellent mental workout! Cognitive exercises are key to recovery.",
    "Your problem-solving skills are improving! These cognitive challenges help rebuild pathways.",
    "Great job with that mental exercise! Your focus and attention are getting stronger.",
    "Your cognitive abilities are strengthening with practice. Keep up the good work!"
]

# Progress-based encouragements
STREAK_ENCOURAGEMENTS = [
    "You've been consistent with your exercises - that's the key to recovery!",
    "Your streak shows real dedication to your health. Impressive!",
    "Consistency is everything in rehabilitation, and you're proving your commitment!",
    "Your regular practice is the best way to improve. Keep that streak going!",
    "What an impressive streak! Your consistent effort will lead to better results."
]

MILESTONE_ENCOURAGEMENTS = [
    "Congratulations on reaching this milestone! Your hard work is paying off.",
    "This is a significant achievement in your recovery journey. Well done!",
    "You've reached an important milestone! Take a moment to appreciate your progress.",
    "This milestone represents all the effort you've put into your recovery. Great job!",
    "Reaching this milestone shows how far you've come. Keep going!"
]

# Difficulty adjustment encouragements
EASIER_ENCOURAGEMENTS = [
    "I've adjusted the difficulty to help you build confidence. You're doing great!",
    "These exercises should feel more manageable now. It's important to find the right level.",
    "I've made the exercises a bit easier so you can focus on proper technique.",
    "The difficulty is now adjusted to help you succeed. Remember, rehabilitation is a journey.",
    "Sometimes taking a step back helps us move forward more effectively. You're doing well!"
]

HARDER_ENCOURAGEMENTS = [
    "I've increased the challenge to help you progress. You're ready for this!",
    "These more challenging exercises will help you continue to improve. You can do it!",
    "You're ready for the next level! These exercises will help you build on your progress.",
    "The difficulty is now higher to match your improving abilities. Keep up the great work!",
    "Challenging yourself is how we grow stronger. You've shown you're ready for more!"
]

def get_random_encouragement() -> str:
    """
    Get a random general encouragement message.
    
    Returns:
        str: A random encouragement message
    """
    return random.choice(GENERAL_ENCOURAGEMENTS)

def get_typed_encouragement(exercise_type: str) -> str:
    """
    Get a random encouragement message specific to an exercise type.
    
    Args:
        exercise_type (str): The type of exercise ("physical", "speech", or "cognitive")
        
    Returns:
        str: A random encouragement message for the specified exercise type
    """
    if exercise_type == "physical":
        return random.choice(PHYSICAL_ENCOURAGEMENTS)
    elif exercise_type == "speech":
        return random.choice(SPEECH_ENCOURAGEMENTS)
    elif exercise_type == "cognitive":
        return random.choice(COGNITIVE_ENCOURAGEMENTS)
    else:
        return get_random_encouragement()

def get_streak_encouragement() -> str:
    """
    Get a random encouragement message related to maintaining a streak.
    
    Returns:
        str: A random streak-related encouragement message
    """
    return random.choice(STREAK_ENCOURAGEMENTS)

def get_milestone_encouragement() -> str:
    """
    Get a random encouragement message for reaching a milestone.
    
    Returns:
        str: A random milestone-related encouragement message
    """
    return random.choice(MILESTONE_ENCOURAGEMENTS)

def get_difficulty_encouragement(made_easier: bool) -> str:
    """
    Get a random encouragement message related to difficulty adjustment.
    
    Args:
        made_easier (bool): True if difficulty was made easier, False if made harder
        
    Returns:
        str: A random difficulty adjustment encouragement message
    """
    if made_easier:
        return random.choice(EASIER_ENCOURAGEMENTS)
    else:
        return random.choice(HARDER_ENCOURAGEMENTS)

def get_contextual_encouragement(
    exercise_type: Optional[str] = None,
    streak: Optional[int] = None,
    milestone: bool = False,
    difficulty_changed: Optional[bool] = None
) -> str:
    """
    Get an encouragement message based on context.
    
    Args:
        exercise_type (Optional[str]): The type of exercise
        streak (Optional[int]): The user's current streak
        milestone (bool): Whether the user has reached a milestone
        difficulty_changed (Optional[bool]): True if made easier, False if harder, None if unchanged
        
    Returns:
        str: A contextual encouragement message
    """
    # Prioritize which type of encouragement to give
    if milestone:
        return get_milestone_encouragement()
    elif difficulty_changed is not None:
        return get_difficulty_encouragement(difficulty_changed)
    elif streak is not None and streak >= 3:
        return get_streak_encouragement()
    elif exercise_type:
        return get_typed_encouragement(exercise_type)
    else:
        return get_random_encouragement()
