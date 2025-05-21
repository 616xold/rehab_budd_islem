"""
exercises.py - Exercise library for Rehab Buddy Alexa Skill

This module contains the stroke rehabilitation exercise content and functions to access them.
It separates the exercise content from the application logic, making it easier to modify
or expand the exercise library without changing the core functionality.

Exercises are organized by category (upper limb, lower limb, mobility) and difficulty level
to allow for personalized rehabilitation programs.
"""

from typing import List, Dict, Any, Optional, Union
import random

# Exercise Categories
CATEGORY_UPPER_LIMB = "upper_limb"
CATEGORY_LOWER_LIMB = "lower_limb"
CATEGORY_MOBILITY = "mobility"
CATEGORY_COGNITIVE = "cognitive"

# Difficulty Levels
DIFFICULTY_BEGINNER = "beginner"
DIFFICULTY_INTERMEDIATE = "intermediate"
DIFFICULTY_ADVANCED = "advanced"

# Exercise Structure:
# Each exercise is a dictionary with the following keys:
# - id: Unique identifier for the exercise
# - name: Short name of the exercise
# - instructions: Detailed instructions for performing the exercise
# - category: Category of the exercise (upper_limb, lower_limb, mobility, cognitive)
# - difficulty: Difficulty level (beginner, intermediate, advanced)
# - repetitions: Recommended number of repetitions
# - duration: Recommended duration in seconds (if applicable)
# - rest: Recommended rest time in seconds between repetitions
# - precautions: Any safety precautions or warnings

# Exercise Library
EXERCISES = [
    # Upper Limb Exercises - Beginner
    {
        "id": "ul_b_1",
        "name": "Shoulder Rolls",
        "instructions": "Sit comfortably with your back straight. Slowly roll your shoulders forward in a circular motion. Do this 5 times, then roll your shoulders backward 5 times. Take your time with each movement.",
        "category": CATEGORY_UPPER_LIMB,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Stop if you feel pain or discomfort."
    },
    {
        "id": "ul_b_2",
        "name": "Wrist Rotations",
        "instructions": "Hold your affected arm out in front of you with your elbow bent. Slowly rotate your wrist in a circular motion, 5 times clockwise and 5 times counterclockwise. Keep your movements smooth and controlled.",
        "category": CATEGORY_UPPER_LIMB,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Keep your movements within a comfortable range."
    },
    {
        "id": "ul_b_3",
        "name": "Finger Taps",
        "instructions": "Place your hand flat on a table or your lap. Slowly lift each finger one at a time, then lower it back down. Start with your thumb and work through to your little finger. Repeat this sequence 5 times.",
        "category": CATEGORY_UPPER_LIMB,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Don't force any movement that causes pain."
    },
    
    # Upper Limb Exercises - Intermediate
    {
        "id": "ul_i_1",
        "name": "Arm Raises",
        "instructions": "Sit with your back straight. Slowly raise your affected arm out to the side, up to shoulder height if possible. Hold for 3 seconds, then slowly lower it back down. Repeat this 8 times, taking a short rest between repetitions.",
        "category": CATEGORY_UPPER_LIMB,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 8,
        "duration": None,
        "rest": 10,
        "precautions": "Only raise your arm as high as is comfortable. Stop if you feel pain."
    },
    {
        "id": "ul_i_2",
        "name": "Elbow Bends",
        "instructions": "Hold your affected arm out in front of you, palm facing up. Slowly bend your elbow to bring your hand toward your shoulder. Hold for 2 seconds, then slowly straighten your arm again. Repeat this 8 times.",
        "category": CATEGORY_UPPER_LIMB,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 8,
        "duration": None,
        "rest": 10,
        "precautions": "Keep your movements smooth and controlled."
    },
    
    # Lower Limb Exercises - Beginner
    {
        "id": "ll_b_1",
        "name": "Ankle Rotations",
        "instructions": "Sit comfortably with your feet flat on the floor. Lift your affected foot slightly off the ground and rotate your ankle in a circular motion. Do 5 circles clockwise, then 5 circles counterclockwise.",
        "category": CATEGORY_LOWER_LIMB,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Keep the movement slow and controlled."
    },
    {
        "id": "ll_b_2",
        "name": "Knee Straightening",
        "instructions": "Sit in a chair with your feet flat on the floor. Slowly straighten your affected leg until it's as straight as possible, without locking your knee. Hold for 3 seconds, then slowly lower it back down. Repeat 5 times.",
        "category": CATEGORY_LOWER_LIMB,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 10,
        "precautions": "Don't lock your knee at full extension."
    },
    
    # Mobility Exercises - Beginner
    {
        "id": "m_b_1",
        "name": "Seated Trunk Rotations",
        "instructions": "Sit upright in a chair with your feet flat on the floor. Place your hands on your thighs. Slowly turn your upper body to the right as far as is comfortable. Hold for 2 seconds, then return to center. Now turn to the left. Repeat 5 times on each side.",
        "category": CATEGORY_MOBILITY,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Keep your movements slow and controlled. Don't twist beyond what's comfortable."
    },
    {
        "id": "m_b_2",
        "name": "Seated Marching",
        "instructions": "Sit upright in a chair with your feet flat on the floor. Slowly lift your right knee up, then lower it back down. Now lift your left knee. Continue alternating for a total of 10 lifts, 5 on each side.",
        "category": CATEGORY_MOBILITY,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Hold onto the chair if needed for balance."
    },
    
    # Cognitive Exercises
    {
        "id": "c_b_1",
        "name": "Hand-Eye Coordination",
        "instructions": "Place 5 small objects like coins or buttons on a table. Using your affected hand, pick up each object one at a time and place it in a container. Focus on your precision and control.",
        "category": CATEGORY_COGNITIVE,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 1,
        "duration": None,
        "rest": 0,
        "precautions": "Take your time and focus on accuracy rather than speed."
    }
]

# Pre-defined exercise routines
DEFAULT_BEGINNER_ROUTINE = ["ul_b_1", "ul_b_2", "ll_b_1", "m_b_1", "c_b_1"]
DEFAULT_INTERMEDIATE_ROUTINE = ["ul_b_3", "ul_i_1", "ul_i_2", "ll_b_2", "m_b_2"]

def get_exercise_by_id(exercise_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an exercise by its ID.
    
    Args:
        exercise_id (str): The unique identifier of the exercise
        
    Returns:
        Optional[Dict[str, Any]]: The exercise dictionary or None if not found
    """
    for exercise in EXERCISES:
        if exercise["id"] == exercise_id:
            return exercise
    return None

def get_exercises_by_category(category: str, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve exercises filtered by category and optionally by difficulty.
    
    Args:
        category (str): The exercise category to filter by
        difficulty (Optional[str]): The difficulty level to filter by
        
    Returns:
        List[Dict[str, Any]]: List of exercises matching the criteria
    """
    if difficulty:
        return [ex for ex in EXERCISES if ex["category"] == category and ex["difficulty"] == difficulty]
    return [ex for ex in EXERCISES if ex["category"] == category]

def get_exercises_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """
    Retrieve exercises filtered by difficulty level.
    
    Args:
        difficulty (str): The difficulty level to filter by
        
    Returns:
        List[Dict[str, Any]]: List of exercises matching the difficulty
    """
    return [ex for ex in EXERCISES if ex["difficulty"] == difficulty]

def get_exercise_routine(routine_type: str = "beginner") -> List[Dict[str, Any]]:
    """
    Get a pre-defined exercise routine based on type.
    
    Args:
        routine_type (str): Type of routine ("beginner" or "intermediate")
        
    Returns:
        List[Dict[str, Any]]: List of exercises in the routine
    """
    if routine_type.lower() == "intermediate":
        routine_ids = DEFAULT_INTERMEDIATE_ROUTINE
    else:  # Default to beginner
        routine_ids = DEFAULT_BEGINNER_ROUTINE
    
    return [get_exercise_by_id(ex_id) for ex_id in routine_ids if get_exercise_by_id(ex_id) is not None]

def create_custom_routine(
    num_exercises: int = 5, 
    categories: Optional[List[str]] = None,
    difficulty: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Create a custom exercise routine based on specified parameters.
    
    Args:
        num_exercises (int): Number of exercises to include in the routine
        categories (Optional[List[str]]): List of categories to include
        difficulty (Optional[str]): Difficulty level to filter by
        
    Returns:
        List[Dict[str, Any]]: List of exercises in the custom routine
    """
    filtered_exercises = EXERCISES.copy()
    
    # Apply category filter if specified
    if categories:
        filtered_exercises = [ex for ex in filtered_exercises if ex["category"] in categories]
    
    # Apply difficulty filter if specified
    if difficulty:
        filtered_exercises = [ex for ex in filtered_exercises if ex["difficulty"] == difficulty]
    
    # If we don't have enough exercises after filtering, use all available
    if len(filtered_exercises) < num_exercises:
        return filtered_exercises
    
    # Randomly select exercises
    return random.sample(filtered_exercises, num_exercises)

def get_formatted_instructions(exercise: Dict[str, Any]) -> str:
    """
    Format exercise instructions for Alexa to speak.
    
    Args:
        exercise (Dict[str, Any]): The exercise dictionary
        
    Returns:
        str: Formatted instructions including name, instructions, and repetitions
    """
    name = exercise["name"]
    instructions = exercise["instructions"]
    reps = exercise["repetitions"]
    
    formatted = f"{name}. {instructions}"
    
    # Add repetition information if applicable
    if reps and reps > 1:
        formatted += f" Do this {reps} times."
    
    # Add precautions if available
    if exercise.get("precautions"):
        formatted += f" Remember: {exercise['precautions']}"
    
    return formatted
