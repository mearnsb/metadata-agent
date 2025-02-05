# Metadata Agent (Chat API)

A FastAPI-based chat application that provides persistent chat sessions with AI agents.

## Features

- Persistent chat sessions across requests
- Multiple AI model support (Gemini, Cerebras, etc.)
- Session management
- Error handling and logging
- Health check endpoint
- CORS support

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd metadata-agent
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Start or Continue a Chat Session
```python
import requests

# Start a new chat session
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "prompt": "Hello, how can you help me?",
        # session_id will be auto-generated if not provided
    }
)

# Get the session ID from the response
session_id = response.json()["session_id"]

# Continue the chat using the same session
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "prompt": "What's next?",
        "session_id": session_id  # Use the same session_id for continuity
    }
)
```

### Clear a Chat Session
```python
response = requests.post(
    "http://localhost:8000/api/v1/clear",
    json={
        "session_id": session_id
    }
)
```

## Response Examples

### Chat Response
```json
{
    "message": "AI response message",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "context": {
        "recent_context": "Previous conversation context..."
    }
}
```

### Clear Session Response
```json
{
    "success": true,
    "message": "Successfully cleared session 550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Response
```json
{
    "message": "An error occurred processing your request",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "error": "Error details"
}
```

## Development

### Project Structure
```
app/
├── __init__.py
├── main.py
├── api/
│   ├── __init__.py
│   └── routes.py
├── core/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── config.py
│   ├── session.py
│   └── logging.py
├── services/
│   ├── __init__.py
│   └── chat_service.py
├── agents/
│   ├── __init__.py
│   ├── agent_config.py
│   └── agent_factory.py
├── chat/
│   ├── __init__.py
│   └── chat_manager.py
├── preprocessing/
│   ├── __init__.py
│   ├── assistants.py
│   └── routine.py
├── tools/
│   ├── __init__.py
│   ├── dq_tools.py
│   ├── sql_tools.py
│   └── job_tools.py
└── models/
    ├── __init__.py
    └── models.py
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]