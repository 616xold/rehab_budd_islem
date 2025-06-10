# invoke.py
import json
from lambda_function import lambda_handler

# Adjust this path if your file is named differently or in another folder:
with open("events/launch_event.json", "r") as f:
    event = json.load(f)

# Call your handler; context can be None for local tests
response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
