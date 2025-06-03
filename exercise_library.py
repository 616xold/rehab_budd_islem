"""
exercise_library.py - Exercise library for Rehab Buddy Alexa Skill

This module contains the stroke rehabilitation exercise content and functions to access them.
It separates the exercise content from the application logic, making it easier to modify
or expand the exercise library without changing the core functionality.

Exercises are organized by type (physical, speech, cognitive) and difficulty level
to allow for personalized rehabilitation programs.
"""

from typing import List, Dict, Any, Optional, Union
import random

# Exercise Types
TYPE_PHYSICAL = "physical"
TYPE_SPEECH = "speech"
TYPE_COGNITIVE = "cognitive"

# Difficulty Levels
DIFFICULTY_BEGINNER = "beginner"
DIFFICULTY_INTERMEDIATE = "intermediate"
DIFFICULTY_ADVANCED = "advanced"

# Exercise Structure:
# Each exercise is a dictionary with the following keys:
# - id: Unique identifier for the exercise
# - name: Short name of the exercise
# - instructions: Detailed instructions for performing the exercise
# - type: Type of the exercise (physical, speech, cognitive)
# - difficulty: Difficulty level (beginner, intermediate, advanced)
# - repetitions: Recommended number of repetitions
# - duration: Recommended duration in seconds (if applicable)
# - rest: Recommended rest time in seconds between repetitions
# - precautions: Any safety precautions or warnings

# Physical Exercises
PHYSICAL_EXERCISES = [
    # Physical Exercises - Beginner
    {
        "id": "phys_b_1",
        "name": "Shoulder Rolls",
        "instructions": "Sit comfortably with your back straight. Slowly roll your shoulders forward in a circular motion. Do this 5 times, then roll your shoulders backward 5 times. Take your time with each movement.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Stop if you feel pain or discomfort."
    },
    {
        "id": "phys_b_2",
        "name": "Wrist Rotations",
        "instructions": "Hold your affected arm out in front of you with your elbow bent. Slowly rotate your wrist in a circular motion, 5 times clockwise and 5 times counterclockwise. Keep your movements smooth and controlled.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Keep your movements within a comfortable range."
    },
    {
        "id": "phys_b_3",
        "name": "Finger Taps",
        "instructions": "Place your hand flat on a table or your lap. Slowly lift each finger one at a time, then lower it back down. Start with your thumb and work through to your little finger. Repeat this sequence 5 times.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Don't force any movement that causes pain."
    },
    {
        "id": "phys_b_4",
        "name": "Ankle Rotations",
        "instructions": "Sit comfortably with your feet flat on the floor. Lift your affected foot slightly off the ground and rotate your ankle in a circular motion. Do 5 circles clockwise, then 5 circles counterclockwise.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Keep the movement slow and controlled."
    },
    {
        "id": "phys_b_5",
        "name": "Seated Trunk Rotations",
        "instructions": "Sit upright in a chair with your feet flat on the floor. Place your hands on your thighs. Slowly turn your upper body to the right as far as is comfortable. Hold for 2 seconds, then return to center. Now turn to the left. Repeat 5 times on each side.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Keep your movements slow and controlled. Don't twist beyond what's comfortable."
    },
    
    # Physical Exercises - Intermediate
    {
        "id": "phys_i_1",
        "name": "Arm Raises",
        "instructions": "Sit with your back straight. Slowly raise your affected arm out to the side, up to shoulder height if possible. Hold for 3 seconds, then slowly lower it back down. Repeat this 8 times, taking a short rest between repetitions.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 8,
        "duration": None,
        "rest": 10,
        "precautions": "Only raise your arm as high as is comfortable. Stop if you feel pain."
    },
    {
        "id": "phys_i_2",
        "name": "Elbow Bends",
        "instructions": "Hold your affected arm out in front of you, palm facing up. Slowly bend your elbow to bring your hand toward your shoulder. Hold for 2 seconds, then slowly straighten your arm again. Repeat this 8 times.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 8,
        "duration": None,
        "rest": 10,
        "precautions": "Keep your movements smooth and controlled."
    },
    {
        "id": "phys_i_3",
        "name": "Knee Straightening",
        "instructions": "Sit in a chair with your feet flat on the floor. Slowly straighten your affected leg until it's as straight as possible, without locking your knee. Hold for 3 seconds, then slowly lower it back down. Repeat 8 times.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 8,
        "duration": None,
        "rest": 10,
        "precautions": "Don't lock your knee at full extension."
    },
    {
        "id": "phys_i_4",
        "name": "Seated Marching",
        "instructions": "Sit upright in a chair with your feet flat on the floor. Slowly lift your right knee up, then lower it back down. Now lift your left knee. Continue alternating for a total of 10 lifts, 5 on each side.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 10,
        "duration": None,
        "rest": 10,
        "precautions": "Hold onto the chair if needed for balance."
    },
    {
        "id": "phys_i_5",
        "name": "Finger-to-Nose",
        "instructions": "Sit with your back straight. Extend your affected arm out to the side at shoulder height. Slowly bring your index finger to touch your nose, then extend your arm back out. Repeat this 8 times.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 8,
        "duration": None,
        "rest": 10,
        "precautions": "Move slowly and focus on accuracy."
    },
    
    # Physical Exercises - Advanced
    {
        "id": "phys_a_1",
        "name": "Standing Balance",
        "instructions": "Stand behind a sturdy chair, holding the back for support. Slowly lift one foot off the ground and try to balance on the other foot. Hold for 10 seconds if possible, then switch feet. Repeat 5 times on each side.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 5,
        "duration": 10,
        "rest": 15,
        "precautions": "Always have something sturdy nearby to hold onto. Stop if you feel unsteady."
    },
    {
        "id": "phys_a_2",
        "name": "Sit-to-Stand",
        "instructions": "Sit in a chair with your feet flat on the floor. Slowly stand up without using your hands if possible. Once standing, pause for a moment, then slowly sit back down. Repeat 10 times.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 10,
        "duration": None,
        "rest": 15,
        "precautions": "Use your hands for support if needed. Stop if you feel unsteady."
    },
    {
        "id": "phys_a_3",
        "name": "Wall Push-Ups",
        "instructions": "Stand facing a wall, about arm's length away. Place your palms flat against the wall at shoulder height. Slowly bend your elbows to bring your body toward the wall, then push back to the starting position. Repeat 10 times.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 10,
        "duration": None,
        "rest": 15,
        "precautions": "Keep your body straight from head to heels. Stop if you feel pain in your shoulders or wrists."
    },
    {
        "id": "phys_a_4",
        "name": "Heel-Toe Walking",
        "instructions": "Stand near a wall or countertop for support if needed. Walk forward by placing the heel of one foot directly in front of the toes of your other foot. Take 10 steps forward, then 10 steps backward.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 10,
        "duration": None,
        "rest": 15,
        "precautions": "Stay near something you can hold onto for balance. Look ahead, not down at your feet."
    },
    {
        "id": "phys_a_5",
        "name": "Diagonal Arm Movements",
        "instructions": "Stand or sit with your back straight. Start with your affected arm down by your side. Slowly raise it diagonally across your body, as if reaching for the opposite shoulder. Then return to the starting position. Repeat 10 times.",
        "type": TYPE_PHYSICAL,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 10,
        "duration": None,
        "rest": 15,
        "precautions": "Move slowly and with control. Stop if you feel pain."
    }
]

# Speech Exercises
SPEECH_EXERCISES = [
    # Speech Exercises - Beginner
    {
        "id": "speech_b_1",
        "name": "Deep Breathing",
        "instructions": "Sit comfortably with your back straight. Take a deep breath in through your nose for a count of 4, hold for a count of 2, then exhale slowly through your mouth for a count of 6. Repeat this 5 times.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Don't rush. Focus on smooth, controlled breathing."
    },
    {
        "id": "speech_b_2",
        "name": "Lip Exercises",
        "instructions": "Purse your lips tightly, hold for 5 seconds, then relax. Next, smile widely, hold for 5 seconds, then relax. Repeat this sequence 5 times.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Don't strain your facial muscles."
    },
    {
        "id": "speech_b_3",
        "name": "Tongue Exercises",
        "instructions": "Stick your tongue out straight, hold for 5 seconds, then relax. Next, try to touch your chin with your tongue, hold, then relax. Finally, try to touch your nose with your tongue, hold, then relax. Repeat this sequence 5 times.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Don't strain. It's okay if you can't reach your nose or chin."
    },
    {
        "id": "speech_b_4",
        "name": "Vowel Sounds",
        "instructions": "Take a deep breath and say 'Ahhh' for as long as you can on one breath. Rest, then repeat with 'Eeee', 'Oooo', 'Uhhh', and 'Iiii'. Try to make each sound last at least 5 seconds.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": 5,
        "rest": 5,
        "precautions": "Don't strain your voice. Stop if you feel discomfort."
    },
    {
        "id": "speech_b_5",
        "name": "Simple Word Repetition",
        "instructions": "Repeat each word after me, speaking clearly: 'Cat', 'Dog', 'House', 'Tree', 'Book'. Say each word twice before moving to the next one.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 2,
        "duration": None,
        "rest": 5,
        "precautions": "Focus on clarity rather than speed."
    },
    
    # Speech Exercises - Intermediate
    {
        "id": "speech_i_1",
        "name": "Tongue Twisters",
        "instructions": "Try to say this tongue twister slowly and clearly: 'She sells seashells by the seashore.' Repeat it 3 times, gradually increasing your speed while maintaining clarity.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 3,
        "duration": None,
        "rest": 10,
        "precautions": "Focus on clarity first, then speed. Don't rush."
    },
    {
        "id": "speech_i_2",
        "name": "Sentence Repetition",
        "instructions": "Repeat each sentence after me, focusing on clear pronunciation: 'The quick brown fox jumps over the lazy dog.' 'How much wood would a woodchuck chuck if a woodchuck could chuck wood?' 'Peter Piper picked a peck of pickled peppers.'",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 2,
        "duration": None,
        "rest": 10,
        "precautions": "Take your time. It's okay to break longer sentences into parts."
    },
    {
        "id": "speech_i_3",
        "name": "Volume Control",
        "instructions": "Say the days of the week, starting with a whisper and gradually increasing your volume with each day. Then do the reverse, starting loud and getting softer: 'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday.'",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 2,
        "duration": None,
        "rest": 10,
        "precautions": "Don't strain your voice at the loudest level."
    },
    {
        "id": "speech_i_4",
        "name": "Reading Aloud",
        "instructions": "If you have a book or newspaper nearby, read a short paragraph aloud, focusing on clear pronunciation. If not, try reciting a familiar poem or song lyrics. Speak slowly and deliberately.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 1,
        "duration": 60,
        "rest": 10,
        "precautions": "Take breaks if you get tired or frustrated."
    },
    {
        "id": "speech_i_5",
        "name": "Word Categories",
        "instructions": "Name as many items as you can in each category. Take about 15 seconds per category: 'Fruits', 'Animals', 'Colors', 'Things in a kitchen', 'Types of transportation'.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 1,
        "duration": 75,
        "rest": 10,
        "precautions": "Don't worry about how many items you can name. Focus on clear pronunciation."
    },
    
    # Speech Exercises - Advanced
    {
        "id": "speech_a_1",
        "name": "Storytelling",
        "instructions": "Create a short story about your day or a recent event. Speak for about 1 minute, focusing on clear speech and logical flow. Try to include details about who, what, when, where, and why.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 1,
        "duration": 60,
        "rest": 15,
        "precautions": "Take your time. It's okay to pause and think."
    },
    {
        "id": "speech_a_2",
        "name": "Debate Practice",
        "instructions": "Choose a simple topic like 'Dogs vs. Cats' or 'Summer vs. Winter'. Present arguments for both sides, speaking for about 30 seconds on each side. Focus on clear articulation and persuasive speaking.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 1,
        "duration": 60,
        "rest": 15,
        "precautions": "This is challenging. Take breaks if needed."
    },
    {
        "id": "speech_a_3",
        "name": "Complex Tongue Twisters",
        "instructions": "Try this challenging tongue twister: 'The sixth sick sheikh's sixth sheep's sick.' Start slowly, then gradually increase your speed while maintaining clarity. Repeat 5 times.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 5,
        "duration": None,
        "rest": 15,
        "precautions": "Don't worry if it's difficult. The challenge helps strengthen speech muscles."
    },
    {
        "id": "speech_a_4",
        "name": "Phone Conversation",
        "instructions": "Pretend you're making a phone call to schedule an appointment. Practice what you would say, including greeting, stating your purpose, responding to questions, and concluding the call. Speak clearly and at a natural pace.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 1,
        "duration": 60,
        "rest": 15,
        "precautions": "This simulates real-world communication. Take your time."
    },
    {
        "id": "speech_a_5",
        "name": "Speech Intonation",
        "instructions": "Say the sentence 'I didn't say she stole the money' seven times, each time emphasizing a different word. This changes the meaning each time. For example: 'I didn't say she stole the money', 'I didn't SAY she stole the money', and so on.",
        "type": TYPE_SPEECH,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 7,
        "duration": None,
        "rest": 15,
        "precautions": "Focus on how changing emphasis changes meaning."
    }
]

# Cognitive Exercises
COGNITIVE_EXERCISES = [
    # Cognitive Exercises - Beginner
    {
        "id": "cog_b_1",
        "name": "Number Sequence",
        "instructions": "I'll say a sequence of numbers, and I'd like you to repeat them back to me. Let's start with: 3, 8, 2. Now repeat those numbers in the same order.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 3,
        "duration": None,
        "rest": 5,
        "precautions": "Take your time. This exercise helps with short-term memory."
    },
    {
        "id": "cog_b_2",
        "name": "Word Association",
        "instructions": "I'll say a word, and I'd like you to respond with a related word. For example, if I say 'dog', you might say 'cat' or 'pet'. Let's try: 'Sun', 'Book', 'Car', 'Water', 'House'.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "There are no wrong answers. Say whatever comes to mind."
    },
    {
        "id": "cog_b_3",
        "name": "Simple Math",
        "instructions": "Let's practice some simple addition. What is 5 plus 3? What is 7 plus 2? What is 4 plus 6? What is 8 plus 1? What is 9 plus 5?",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 5,
        "duration": None,
        "rest": 5,
        "precautions": "Take your time. This exercise helps with processing and calculation skills."
    },
    {
        "id": "cog_b_4",
        "name": "Object Naming",
        "instructions": "Look around the room you're in and name 5 objects you can see. Try to be specific, for example, say 'wooden chair' instead of just 'chair'.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 1,
        "duration": 30,
        "rest": 5,
        "precautions": "This exercise helps with word finding and observation skills."
    },
    {
        "id": "cog_b_5",
        "name": "Day Orientation",
        "instructions": "Let's practice orientation. What day of the week is it today? What month is it? What year is it? What season is it? Is it morning, afternoon, or evening right now?",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_BEGINNER,
        "repetitions": 1,
        "duration": None,
        "rest": 5,
        "precautions": "This exercise helps with temporal orientation."
    },
    
    # Cognitive Exercises - Intermediate
    {
        "id": "cog_i_1",
        "name": "Reverse Numbers",
        "instructions": "I'll say a sequence of numbers, and I'd like you to repeat them back to me in reverse order. For example, if I say '1, 2, 3', you would say '3, 2, 1'. Let's try: '4, 7, 1', '9, 2, 8, 5', '3, 6, 1, 9, 2'.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 3,
        "duration": None,
        "rest": 10,
        "precautions": "This is challenging for working memory. Take your time."
    },
    {
        "id": "cog_i_2",
        "name": "Word Categories",
        "instructions": "I'll give you a category, and I'd like you to name as many items in that category as you can in 15 seconds. Let's try: 'Fruits', 'Animals', 'Countries', 'Occupations', 'Vehicles'.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 5,
        "duration": 15,
        "rest": 10,
        "precautions": "This exercise helps with word retrieval and semantic memory."
    },
    {
        "id": "cog_i_3",
        "name": "Mental Math",
        "instructions": "Let's practice some mental math. What is 12 plus 15? What is 23 minus 7? What is 6 times 4? What is 20 divided by 5? What is 18 plus 27?",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 5,
        "duration": None,
        "rest": 10,
        "precautions": "Take your time. This exercise helps with calculation and concentration."
    },
    {
        "id": "cog_i_4",
        "name": "Spelling Backward",
        "instructions": "I'll say a word, and I'd like you to spell it backward. For example, if I say 'dog', you would say 'd-o-g' spelled backward is 'g-o-d'. Let's try: 'cat', 'book', 'house', 'water', 'friend'.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 5,
        "duration": None,
        "rest": 10,
        "precautions": "This exercise challenges working memory and concentration."
    },
    {
        "id": "cog_i_5",
        "name": "Sequential Instructions",
        "instructions": "I'll give you a series of instructions to follow in order. Listen carefully: Touch your nose, then clap your hands, then touch your ear. Now, touch your knee, then your shoulder, then your forehead, then clap twice.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_INTERMEDIATE,
        "repetitions": 2,
        "duration": None,
        "rest": 10,
        "precautions": "This exercise helps with sequential processing and following directions."
    },
    
    # Cognitive Exercises - Advanced
    {
        "id": "cog_a_1",
        "name": "Complex Number Sequences",
        "instructions": "I'll say a sequence of numbers, and I'd like you to continue the pattern. For example, if I say '2, 4, 6', the pattern is adding 2, so you would say '8'. Let's try: '3, 6, 9, 12...', '1, 3, 6, 10...', '2, 4, 8, 16...'.",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 3,
        "duration": None,
        "rest": 15,
        "precautions": "This exercise challenges pattern recognition and logical thinking."
    },
    {
        "id": "cog_a_2",
        "name": "Word Puzzles",
        "instructions": "I'll give you a word puzzle. Rearrange the letters to form a common word. For example, 'ATC' rearranges to 'CAT'. Let's try: 'TIEM' (TIME), 'USHOE' (HOUSE), 'ARPK' (PARK), 'YROTS' (STORY).",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 4,
        "duration": None,
        "rest": 15,
        "precautions": "This exercise challenges problem-solving and language skills."
    },
    {
        "id": "cog_a_3",
        "name": "Abstract Reasoning",
        "instructions": "I'll give you a scenario with a problem to solve. A man needs to cross a river with a fox, a chicken, and a bag of grain. His boat can only carry himself and one other item. If left alone, the fox will eat the chicken, and the chicken will eat the grain. How can he get everything across safely?",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 1,
        "duration": 120,
        "rest": 15,
        "precautions": "This is a challenging puzzle. Take your time and think step by step."
    },
    {
        "id": "cog_a_4",
        "name": "Memory Story",
        "instructions": "I'll tell you a short story, and then ask you questions about it. Listen carefully: 'John went to the store on Tuesday. He bought milk, bread, and apples. The milk cost $2.50, the bread was $3.00, and the apples were $4.25. He paid with a $20 bill.' Now, what day did John go to the store? What items did he buy? How much did he spend in total? How much change did he receive?",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 1,
        "duration": 60,
        "rest": 15,
        "precautions": "This exercise challenges auditory memory and calculation skills."
    },
    {
        "id": "cog_a_5",
        "name": "Verbal Fluency",
        "instructions": "I'll give you a letter, and I'd like you to name as many words as you can that start with that letter in 30 seconds. Let's try with the letter 'S'. Ready? Go!",
        "type": TYPE_COGNITIVE,
        "difficulty": DIFFICULTY_ADVANCED,
        "repetitions": 1,
        "duration": 30,
        "rest": 15,
        "precautions": "This exercise challenges word retrieval and verbal fluency."
    }
]

# Combine all exercises
ALL_EXERCISES = PHYSICAL_EXERCISES + SPEECH_EXERCISES + COGNITIVE_EXERCISES

# Pre-defined exercise routines by type and difficulty
ROUTINES = {
    TYPE_PHYSICAL: {
        DIFFICULTY_BEGINNER: ["phys_b_1", "phys_b_2", "phys_b_3", "phys_b_4", "phys_b_5"],
        DIFFICULTY_INTERMEDIATE: ["phys_i_1", "phys_i_2", "phys_i_3", "phys_i_4", "phys_i_5"],
        DIFFICULTY_ADVANCED: ["phys_a_1", "phys_a_2", "phys_a_3", "phys_a_4", "phys_a_5"]
    },
    TYPE_SPEECH: {
        DIFFICULTY_BEGINNER: ["speech_b_1", "speech_b_2", "speech_b_3", "speech_b_4", "speech_b_5"],
        DIFFICULTY_INTERMEDIATE: ["speech_i_1", "speech_i_2", "speech_i_3", "speech_i_4", "speech_i_5"],
        DIFFICULTY_ADVANCED: ["speech_a_1", "speech_a_2", "speech_a_3", "speech_a_4", "speech_a_5"]
    },
    TYPE_COGNITIVE: {
        DIFFICULTY_BEGINNER: ["cog_b_1", "cog_b_2", "cog_b_3", "cog_b_4", "cog_b_5"],
        DIFFICULTY_INTERMEDIATE: ["cog_i_1", "cog_i_2", "cog_i_3", "cog_i_4", "cog_i_5"],
        DIFFICULTY_ADVANCED: ["cog_a_1", "cog_a_2", "cog_a_3", "cog_a_4", "cog_a_5"]
    }
}

def get_exercise_by_id(exercise_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an exercise by its ID.
    
    Args:
        exercise_id (str): The unique identifier of the exercise
        
    Returns:
        Optional[Dict[str, Any]]: The exercise dictionary or None if not found
    """
    for exercise in ALL_EXERCISES:
        if exercise["id"] == exercise_id:
            return exercise
    return None

def get_exercises_by_type(exercise_type: str, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve exercises filtered by type and optionally by difficulty.
    
    Args:
        exercise_type (str): The exercise type to filter by
        difficulty (Optional[str]): The difficulty level to filter by
        
    Returns:
        List[Dict[str, Any]]: List of exercises matching the criteria
    """
    if difficulty:
        return [ex for ex in ALL_EXERCISES if ex["type"] == exercise_type and ex["difficulty"] == difficulty]
    return [ex for ex in ALL_EXERCISES if ex["type"] == exercise_type]

def get_exercises_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """
    Retrieve exercises filtered by difficulty level.
    
    Args:
        difficulty (str): The difficulty level to filter by
        
    Returns:
        List[Dict[str, Any]]: List of exercises matching the difficulty
    """
    return [ex for ex in ALL_EXERCISES if ex["difficulty"] == difficulty]

def get_exercise_routine(exercise_type: str = "physical", difficulty: str = "beginner") -> List[Dict[str, Any]]:
    """
    Get a pre-defined exercise routine based on type and difficulty.
    
    Args:
        exercise_type (str): Type of exercise ("physical", "speech", or "cognitive")
        difficulty (str): Difficulty level ("beginner", "intermediate", or "advanced")
        
    Returns:
        List[Dict[str, Any]]: List of exercises in the routine
    """
    # Validate exercise type
    if exercise_type not in [TYPE_PHYSICAL, TYPE_SPEECH, TYPE_COGNITIVE]:
        exercise_type = TYPE_PHYSICAL
    
    # Validate difficulty
    if difficulty not in [DIFFICULTY_BEGINNER, DIFFICULTY_INTERMEDIATE, DIFFICULTY_ADVANCED]:
        difficulty = DIFFICULTY_BEGINNER
    
    # Get routine IDs
    routine_ids = ROUTINES.get(exercise_type, {}).get(difficulty, [])
    
    # If no routine found, return default
    if not routine_ids:
        return get_exercises_by_type(exercise_type, difficulty)[:5]
    
    # Get exercises by IDs
    return [get_exercise_by_id(ex_id) for ex_id in routine_ids if get_exercise_by_id(ex_id) is not None]

def create_custom_routine(
    exercise_type: str = "physical",
    difficulty: str = "beginner",
    num_exercises: int = 5
) -> List[Dict[str, Any]]:
    """
    Create a custom exercise routine based on specified parameters.
    
    Args:
        exercise_type (str): Type of exercise ("physical", "speech", or "cognitive")
        difficulty (str): Difficulty level ("beginner", "intermediate", or "advanced")
        num_exercises (int): Number of exercises to include in the routine
        
    Returns:
        List[Dict[str, Any]]: List of exercises in the custom routine
    """
    # Get exercises matching criteria
    filtered_exercises = get_exercises_by_type(exercise_type, difficulty)
    
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
    reps = exercise.get("repetitions")
    duration = exercise.get("duration")
    
    formatted = f"{name}. {instructions}"
    
    # Add repetition or duration information if applicable
    if reps and reps > 1 and not "repetitions" in instructions.lower():
        formatted += f" Do this {reps} times."
    elif duration and not "seconds" in instructions.lower():
        formatted += f" Do this for {duration} seconds."
    
    # Add precautions if available
    if exercise.get("precautions") and not "precautions" in instructions.lower():
        formatted += f" Remember: {exercise['precautions']}"
    
    return formatted
