# util/invoke.py
import sys, json
import lambda_function as lf

with open(sys.argv[1]) as f:
    event = json.load(f)

response = lf.lambda_handler(event, None)
print(json.dumps(response, indent=2))
