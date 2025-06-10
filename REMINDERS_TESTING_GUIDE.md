# Rehab Buddy Reminders Feature Testing Guide

## Overview
This guide covers testing the enhanced Reminders feature for the Rehab Buddy Alexa skill, including local testing, simulator testing, and device testing.

## Test Event Files

### 1. Set Reminder Test Event
Create `events/set_reminder_test.json`:
```json
{
    "version": "1.0",
    "session": {
        "new": false,
        "sessionId": "amzn1.echo-api.session.test-reminder",
        "user": {
            "userId": "amzn1.ask.account.test-user",
            "permissions": {
                "consentToken": "test-consent-token"
            }
        },
        "application": {
            "applicationId": "amzn1.ask.skill.test"
        }
    },
    "context": {
        "System": {
            "application": {
                "applicationId": "amzn1.ask.skill.test"
            },
            "user": {
                "userId": "amzn1.ask.account.test-user",
                "permissions": {
                    "consentToken": "test-consent-token"
                }
            },
            "device": {
                "deviceId": "amzn1.ask.device.test",
                "supportedInterfaces": {}
            },
            "apiEndpoint": "https://api.amazonalexa.com",
            "apiAccessToken": "test-access-token"
        }
    },
    "request": {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.test",
        "timestamp": "2024-01-01T12:00:00Z",
        "locale": "en-US",
        "intent": {
            "name": "SetRehabReminderIntent",
            "confirmationStatus": "NONE",
            "slots": {
                "ReminderTime": {
                    "name": "ReminderTime",
                    "value": "09:00",
                    "confirmationStatus": "NONE"
                }
            }
        }
    }
}
```

### 2. Cancel Reminders Test Event
Create `events/cancel_reminders_test.json`:
```json
{
    "version": "1.0",
    "session": {
        "new": false,
        "sessionId": "amzn1.echo-api.session.test-cancel",
        "user": {
            "userId": "amzn1.ask.account.test-user",
            "permissions": {
                "consentToken": "test-consent-token"
            }
        }
    },
    "context": {
        "System": {
            "user": {
                "permissions": {
                    "consentToken": "test-consent-token"
                }
            },
            "device": {
                "deviceId": "amzn1.ask.device.test"
            },
            "apiEndpoint": "https://api.amazonalexa.com",
            "apiAccessToken": "test-access-token"
        }
    },
    "request": {
        "type": "IntentRequest",
        "intent": {
            "name": "CancelRehabReminderIntent"
        }
    }
}
```

### 3. List Reminders Test Event
Create `events/list_reminders_test.json`:
```json
{
    "version": "1.0",
    "session": {
        "new": false,
        "sessionId": "amzn1.echo-api.session.test-list",
        "user": {
            "userId": "amzn1.ask.account.test-user"
        }
    },
    "context": {
        "System": {
            "device": {
                "deviceId": "amzn1.ask.device.test"
            }
        }
    },
    "request": {
        "type": "IntentRequest",
        "intent": {
            "name": "ListRemindersIntent"
        }
    }
}
```

### 4. No Permission Test Event
Create `events/no_permission_test.json`:
```json
{
    "version": "1.0",
    "session": {
        "new": false,
        "sessionId": "amzn1.echo-api.session.test-no-perm",
        "user": {
            "userId": "amzn1.ask.account.test-user"
        }
    },
    "context": {
        "System": {
            "user": {},
            "device": {
                "deviceId": "amzn1.ask.device.test"
            }
        }
    },
    "request": {
        "type": "IntentRequest",
        "intent": {
            "name": "SetRehabReminderIntent",
            "slots": {
                "ReminderTime": {
                    "value": "14:00"
                }
            }
        }
    }
}
```

## Local Testing Steps

### 1. Unit Testing
```bash
# Install test dependencies
pip install pytest pytest-mock boto3-stubs

# Run unit tests
python -m pytest tests/test_reminder_manager.py -v
```

### 2. Lambda Local Testing
```bash
# Test with SAM CLI
sam local invoke RehabBuddyFunction -e events/set_reminder_test.json

# Test different scenarios
sam local invoke RehabBuddyFunction -e events/cancel_reminders_test.json
sam local invoke RehabBuddyFunction -e events/list_reminders_test.json
sam local invoke RehabBuddyFunction -e events/no_permission_test.json
```

### 3. DynamoDB Local Testing
```bash
# Start DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Set environment variable
export DYNAMODB_ENDPOINT_URL=http://localhost:8000

# Test reminder preference storage
python -c "from reminder_manager import store_reminder_preference; print(store_reminder_preference('test-user', {'time': '09:00', 'frequency': 'DAILY'}))"
```

## Simulator Testing Steps

### 1. Deploy to Development Stage
```bash
# Deploy using SAM
sam deploy --guided --stage dev

# Or using ASK CLI
ask deploy --target lambda
ask deploy --target model
```

### 2. Test in Alexa Developer Console
1. Go to https://developer.amazon.com/alexa/console/ask
2. Select your skill
3. Click "Test" tab
4. Enable testing for "Development"

### 3. Test Conversations

#### Test 1: Set Daily Reminder
```
User: "Alexa, open Rehab Buddy"
Alexa: "Welcome to Rehab Buddy..."
User: "Set a reminder for 9 AM"
Alexa: "I've set a daily reminder for your rehabilitation exercises at 9 AM..."
```

#### Test 2: Set Weekday Reminder
```
User: "Schedule my rehab reminder for weekdays at 7:30 PM"
Alexa: "I've set a reminder for your rehabilitation exercises on weekdays at 7:30 PM..."
```

#### Test 3: List Reminders
```
User: "What reminders do I have?"
Alexa: "You have a reminder set for 9:00 AM every day in America/New_York..."
```

#### Test 4: Cancel Reminders
```
User: "Cancel my exercise reminders"
Alexa: "I've cancelled all your rehabilitation exercise reminders..."
```

#### Test 5: Permission Flow
```
User: "Set a reminder" (without permission)
Alexa: "To set reminders for your rehabilitation sessions, I need permission..."
[Permission card appears in Alexa app]
```

### 4. Check CloudWatch Logs
```bash
# View Lambda logs
aws logs tail /aws/lambda/RehabBuddyFunction --follow

# Filter for reminder-related logs
aws logs filter-log-events --log-group-name /aws/lambda/RehabBuddyFunction --filter-pattern "reminder"
```

## Device Testing Steps

### 1. Enable Beta Testing
1. In Alexa Developer Console, go to "Distribution"
2. Add beta testers by email
3. Have testers enable the skill

### 2. Test on Physical Device

#### Pre-test Setup
1. Ensure device timezone is set correctly
2. Grant reminder permissions in Alexa app
3. Enable skill notifications

#### Test Cases

**Test A: Basic Reminder Flow**
1. "Alexa, open Rehab Buddy"
2. "Set a reminder for 10 AM"
3. Wait for confirmation
4. Check Alexa app for reminder
5. Wait for reminder to trigger

**Test B: Timezone Handling**
1. Change device timezone in Alexa app
2. Set a reminder
3. Verify reminder shows in correct timezone

**Test C: Multiple Reminders**
1. Set daily reminder
2. Try to set another reminder
3. List reminders
4. Cancel specific reminder

**Test D: Edge Cases**
1. Set reminder for past time (should schedule for next day)
2. Set reminder without specifying time
3. Cancel when no reminders exist

### 3. Verify DynamoDB Storage
```bash
# Check reminder preferences
aws dynamodb get-item \
  --table-name RehabBuddyUserData \
  --key '{"user_id": {"S": "amzn1.ask.account.YOUR_USER_ID"}}' \
  --query 'Item.reminder_preferences'
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check skill manifest includes reminder permission
   - Verify user granted permission in Alexa app
   - Check consent token is present

2. **Timezone Issues**
   - Verify device timezone API is accessible
   - Check pytz is installed in Lambda
   - Default timezone fallback working

3. **API Errors**
   - Check API endpoint URL format
   - Verify access token is valid
   - Check reminder payload format

### Debug Commands
```bash
# Check Lambda environment
aws lambda get-function-configuration --function-name RehabBuddyFunction

# Test API directly
curl -X POST https://api.amazonalexa.com/v1/reminders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @reminder_payload.json
```

## Verification Checklist

- [ ] Intent names match between model and handlers
- [ ] Reminder permissions in skill manifest
- [ ] DynamoDB table has reminder_preferences field
- [ ] Timezone handling works correctly
- [ ] Retry logic handles transient failures
- [ ] Error messages are user-friendly
- [ ] Simulator detection works properly
- [ ] All test events execute successfully
- [ ] CloudWatch logs show expected behavior
- [ ] Physical device testing passes all scenarios

## Next Steps

1. Add unit tests for new reminder functions
2. Implement reminder modification capability
3. Add support for custom recurrence patterns
4. Create reminder analytics dashboard
5. Add multi-language support for reminders 