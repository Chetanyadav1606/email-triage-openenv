# 📚 API Quick Reference

## Getting Started

### Initialize Environment
```bash
curl -X POST http://localhost:8000/reset
```

**Response:**
```json
{
  "queue": [...],
  "current_email": {
    "id": "1",
    "subject": "Payment failed",
    "body": "Card declined",
    "customer_id": "C1",
    "customer_tier": "premium",
    "true_label": "billing",
    "true_priority": "high",
    "true_response": "Retry payment or contact bank"
  },
  "history": {},
  "step_count": 0
}
```

## Actions

### 1. Classify Email
Categorize the email into a label.

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "classify",
    "email_id": "1",
    "label": "billing"
  }'
```

**Valid Labels:** `billing`, `technical`, `feature`, `general`

**Response:**
```json
{
  "observation": {...},
  "reward": {
    "score": 0.2,
    "feedback": "✓ Correct classification"
  },
  "done": false,
  "info": {...}
}
```

### 2. Prioritize Email
Set the priority level (urgency) of the email.

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "prioritize",
    "email_id": "1",
    "priority": "high"
  }'
```

**Valid Priorities:** `low`, `medium`, `high`

**Response:**
```json
{
  "observation": {...},
  "reward": {
    "score": 0.2,
    "feedback": "✓ Correct priority"
  },
  "done": false,
  "info": {...}
}
```

### 3. Send Response
Write and send a response to the customer.

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "respond",
    "email_id": "1",
    "response": "We will help you resolve this payment issue. Please try again or contact your bank."
  }'
```

**Response:**
```json
{
  "observation": {...},
  "reward": {
    "score": 0.4,
    "feedback": "✓ Response sent to customer"
  },
  "done": false,
  "info": {...}
}
```

### 4. Close Ticket
Mark the email as resolved and move to the next one.

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "close",
    "email_id": "1"
  }'
```

**Response:**
```json
{
  "observation": {...},
  "reward": {
    "score": 0.2,
    "feedback": "✓ Email closed → Next email loaded"
  },
  "done": false,
  "info": {...}
}
```

## Evaluation

### Get Final Score
```bash
curl -X GET http://localhost:8000/score
```

**Response:**
```json
{
  "final_score": 85.5,
  "evaluation_metrics": {
    "total_emails": 10,
    "correct_classifications": 9,
    "correct_priorities": 8,
    "responses_sent": 10,
    "total_steps": 25,
    "total_reward": 2.5,
    "accuracy": 0.9,
    "priority_accuracy": 0.8,
    "response_rate": 1.0,
    "efficiency": 0.8,
    "overall_score": 85.5
  },
  "rank": "A Tier ⭐",
  "feedback": "Excellent performance!",
  "steps_taken": 25,
  "total_reward": 2.5
}
```

## Status & Health

### Get Current Status
```bash
curl -X GET http://localhost:8000/status
```

**Response:**
```json
{
  "status": "active",
  "current_email": "1",
  "queue_size": 9,
  "step_count": 1,
  "total_reward": 0.2,
  "done": false,
  "max_steps": 100,
  "customer_count": 1
}
```

### Health Check
```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "environment_ready": true,
  "message": "Service is running"
}
```

## Complete Example Workflow

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Reset
print("1️⃣  Resetting environment...")
response = requests.post(f"{BASE_URL}/reset")
state = response.json()
print(f"   Current email: {state['current_email']['subject']}")

# 2. Classify
print("\n2️⃣  Classifying email...")
action = {
    "action_type": "classify",
    "email_id": state['current_email']['id'],
    "label": "billing"
}
response = requests.post(f"{BASE_URL}/step", json=action)
result = response.json()
print(f"   Reward: {result['reward']['score']}")
print(f"   Feedback: {result['reward']['feedback']}")

# 3. Prioritize
print("\n3️⃣  Prioritizing email...")
action = {
    "action_type": "prioritize",
    "email_id": result['observation']['current_email']['id'],
    "priority": "high"
}
response = requests.post(f"{BASE_URL}/step", json=action)
result = response.json()
print(f"   Reward: {result['reward']['score']}")

# 4. Respond
print("\n4️⃣  Sending response...")
action = {
    "action_type": "respond",
    "email_id": result['observation']['current_email']['id'],
    "response": "Thank you for contacting us. We'll help you with this issue."
}
response = requests.post(f"{BASE_URL}/step", json=action)
result = response.json()
print(f"   Reward: {result['reward']['score']}")

# 5. Close
print("\n5️⃣  Closing ticket...")
action = {
    "action_type": "close",
    "email_id": result['observation']['current_email']['id']
}
response = requests.post(f"{BASE_URL}/step", json=action)
result = response.json()
print(f"   Reward: {result['reward']['score']}")

# 6. Get Score
print("\n📊 Getting final score...")
response = requests.get(f"{BASE_URL}/score")
score = response.json()
print(f"   Final Score: {score['final_score']}")
print(f"   Rank: {score['rank']}")
print(f"   Accuracy: {score['evaluation_metrics']['accuracy']*100:.1f}%")
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Environment not initialized. Call /reset first."
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Invalid action: label required for classify action"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Step execution failed: <error message>"
}
```

## Tips & Tricks

### Optimal Workflow per Email
1. **Classify** (0.2 reward) - Identify category
2. **Prioritize** (0.2 reward) - Set urgency
3. **Respond** (0.4 reward) - Send response
4. **Close** (0.2 reward) - Mark resolved
**Total: 1.0 reward per email**

### Scoring Strategy
- **Accuracy matters**: 35% of score
- **Efficiency matters**: 20% of score
- **Consistency matters**: Respond to all emails
- **No shortcuts**: All steps add value

### Performance Tips
- Use web UI for interactive learning
- Batch-analyze patterns before actions
- Reference customer history for decisions
- Test API with ReDoc documentation

---

**Need Help?** Check `/docs` for interactive API explorer
