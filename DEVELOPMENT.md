# 🚀 Development Guide

This guide helps you understand the OpenEnv Email Triage project structure and how to extend it.

## 📁 Project Structure Explained

```
openenv-email-triage/
├── main.py              # FastAPI app with all endpoints
├── environment.py       # Core EmailEnv class - the simulation engine
├── models.py           # Pydantic data models with validation
├── tasks.py            # Email datasets
├── grader.py           # Performance evaluation system
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
├── run.sh | run.bat    # Quick start scripts
├── test_environment.py # Test suite
├── static/
│   └── index.html      # Web UI frontend
└── README.md           # Project documentation
```

## 🔧 Key Components Explained

### `main.py` - FastAPI Application
Handles all HTTP endpoints for the environment:
- `/reset` - Initialize environment
- `/step` - Execute action
- `/score` - Get evaluation
- `/status` - Environment status
- `/health` - Health check

**Improvements made:**
- ✅ Comprehensive error handling
- ✅ CORS support for frontend
- ✅ Logging integration
- ✅ OpenAPI documentation
- ✅ Health checks

### `environment.py` - Core Engine
The main simulation environment:
- Manages email queue
- Executes actions
- Tracks rewards and history
- Calculates evaluation scores

**Features:**
- Multi-email queue processing
- Customer memory tracking
- SLA-aware prioritization
- Flexible reward system

### `models.py` - Data Models
Pydantic models for data validation:
- `Email` - Customer support emails
- `Action` - Agent actions
- `Observation` - Environment state
- `Reward` - Action feedback

**Improvements:**
- ✅ Field validation
- ✅ Type hints
- ✅ Documentation
- ✅ Enum types for valid values

### `grader.py` - Performance Evaluation
Comprehensive grading system:
- Accuracy metrics
- Priority assessment
- Efficiency measurement
- Detailed feedback generation

**Capabilities:**
- 📊 Multi-metric evaluation
- 💬 Human-readable feedback
- 🏆 Performance ranking
- 📈 Metric comparison

### `static/index.html` - Web UI
Beautiful, responsive frontend:
- Modern gradient design
- Real-time updates
- Interactive email processing
- Performance visualization

**Features:**
- ✅ Mobile responsive
- ✅ Smooth animations
- ✅ Intuitive controls
- ✅ Live statistics

## 🛠️ How to Extend the Project

### Adding New Email Categories

1. **Update `models.py`:**
```python
# Add new category to Email validation
true_label: str  # Add "support", "partnership", etc.
```

2. **Update `tasks.py`:**
```python
Email(
    id="11",
    subject="Partnership inquiry",
    body="...",
    customer_id="C9",
    customer_tier="enterprise",
    true_label="partnership",  # New category
    true_priority="medium",
    true_response="..."
)
```

### Adding LLM Integration

1. **Update `environment.py`:**
```python
from openai import OpenAI

class EmailEnv:
    def __init__(self, emails):
        self.client = OpenAI()
        ...
    
    def auto_classify(self, email):
        """Use Hugging Face OpenAI-compatible LLM to classify email"""
        response = self.client.chat.completions.create(...)
        return response.choices[0].message.content
```

2. **Add to API in `main.py`:**
```python
@app.post("/auto-classify")
async def auto_classify(email_id: str):
    """Get AI-suggested classification"""
    ...
```

### Adding Database Support

1. **Create `database.py`:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/openenv"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

2. **Update `main.py`:**
```python
from database import SessionLocal

@app.on_event("startup")
async def startup():
    # Initialize database
    pass
```

### Adding Authentication

1. **Create `auth.py`:**
```python
from fastapi.security import HTTPBearer
from jwt import encode, decode

security = HTTPBearer()

async def verify_token(credentials):
    # Verify JWT token
    pass
```

2. **Protect endpoints:**
```python
@app.post("/step", dependencies=[Depends(verify_token)])
async def step(action: Action):
    ...
```

## 📚 API Convention

### Response Format
All endpoints follow this pattern:
```json
{
  "success": true,
  "data": {...},
  "message": "Success message",
  "timestamp": "2026-04-07T10:00:00Z"
}
```

### Error Handling
```json
{
  "success": false,
  "error": "Error code",
  "message": "Human-readable error",
  "details": {...},
  "timestamp": "2026-04-07T10:00:00Z"
}
```

## 🧪 Testing

Run the test suite:
```bash
python test_environment.py
```

Expected output:
```
🧪 OpenEnv Email Triage Test Suite
============================================================
📋 Testing Models...
  ✅ Email model works
  ✅ Action model works
📧 Testing Tasks...
  ✅ Loaded 10 tasks
  ✅ All tasks are valid
🏢 Testing Environment...
  ✅ Reset works
  ✅ Step execution works
  ✅ Evaluation works
🎓 Testing Grader...
  ✅ Grader initialized
  ✅ Grading works - Score: 75.00/100
🎮 Testing Full Workflow...
  ✅ Processed 10 actions
  📊 Final Score: 80.50/100
```

## 🔍 Debugging Tips

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn main:app --reload
```

### Check API Documentation
- Interactive: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Common Issues

**Frontend not loading:**
- Check that `static/index.html` exists
- Verify CORS is enabled in `/main.py`
- Check browser console for errors

**API errors:**
- Check request format matches schema
- Verify all required fields are provided
- Look at API docs for examples

**Performance issues:**
- Review logs for bottlenecks
- Check system resources
- Consider async optimizations

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| Pydantic | Data validation |
| OpenAI-compatible | LLM integration (optional) |

## 🚀 Deployment Checklist

- [ ] Update `README.md` with deployment info
- [ ] Set `DEBUG=false` in production
- [ ] Configure environment variables
- [ ] Set up logging
- [ ] Configure CORS properly
- [ ] Set up health checks
- [ ] Configure resource limits
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Document deployment process

## 💡 Best Practices

1. **Always validate input** - Use Pydantic models
2. **Handle errors gracefully** - Provide useful messages
3. **Log important events** - Track user actions
4. **Test thoroughly** - Use test suite
5. **Document code** - Use docstrings
6. **Keep it DRY** - Reuse components
7. **Optimize performance** - Profile before optimization
8. **Secure endpoints** - Use authentication where needed

## 📖 Further Reading

- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/concepts/)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

---

Happy developing! 🎉
