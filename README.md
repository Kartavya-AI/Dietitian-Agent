# AI Dietitian 🍎

A production-ready AI-powered nutrition and diet planning application that provides personalized meal recommendations using Google's Gemini AI. Built with FastAPI, Streamlit, and LangChain.

## 🌟 Features

- **Personalized Diet Plans**: AI-generated meal plans based on individual health goals, preferences, and restrictions
- **Interactive Chat Interface**: Natural conversation flow for collecting user information
- **Multiple Deployment Options**: Both API and web interface available
- **Session Management**: Persistent conversations with memory across interactions
- **Production Ready**: Dockerized with proper error handling, logging, and security middleware
- **Health Monitoring**: Built-in health check endpoints for monitoring

## 🏗️ Architecture

### Components

1. **FastAPI API (`api.py`)**: Production-ready REST API with session management
2. **Streamlit App (`app.py`)**: User-friendly web interface
3. **AI Agent (`tool.py`)**: LangChain-based conversational AI with structured prompting
4. **Docker Support**: Containerized deployment with optimized Python runtime

### Tech Stack

- **Backend**: FastAPI, Uvicorn, Gunicorn
- **AI/ML**: LangChain, Google Gemini AI, ConversationBufferMemory
- **Frontend**: Streamlit
- **Containerization**: Docker
- **Data Validation**: Pydantic
- **Environment**: Python 3.11

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Kartavya-AI/Dietitian-Agent/
cd Dietitian-Agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
# OR
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
```

### Running the Application

#### Option 1: Streamlit Web App (Recommended for users)
```bash
streamlit run app.py
```
- Access at: `http://localhost:8501`
- Enter your Gemini API key in the sidebar
- Start chatting with the AI Dietitian

#### Option 2: FastAPI Server (Recommended for production)
```bash
# Development
uvicorn api:app --reload --port 8080

# Production
gunicorn --bind 0.0.0.0:8080 --workers 2 --worker-class uvicorn.workers.UvicornWorker api:app
```
- API Documentation: `http://localhost:8080/docs`
- Health Check: `http://localhost:8080/health`

#### Option 3: Docker Deployment
```bash
# Build the image
docker build -t ai-dietitian .

# Run the container
docker run -p 8080:8080 -e GEMINI_API_KEY=your_api_key_here ai-dietitian
```

## 📖 API Documentation

### Base URL
```
http://localhost:8080
```

### Endpoints

#### 1. Health Check
```http
GET /health
```
Returns server health status and uptime information.

#### 2. Initialize Session
```http
POST /init-session
Content-Type: application/json

{
  "session_id": "user123"
}
```

#### 3. Chat with AI Dietitian
```http
POST /chat
Content-Type: application/json

{
  "message": "I want to lose weight",
  "session_id": "user123"
}
```

#### 4. Clear Session
```http
DELETE /clear-session/{session_id}
```

#### 5. List Active Sessions
```http
GET /sessions
```

### Example Usage

```python
import requests

# Initialize session
response = requests.post("http://localhost:8080/init-session", 
                        json={"session_id": "user123"})

# Chat with AI
response = requests.post("http://localhost:8080/chat", 
                        json={
                            "message": "I want to gain muscle mass",
                            "session_id": "user123"
                        })
print(response.json()["response"])
```

## 🤖 How It Works

### AI Dietitian Process

The AI follows a structured approach to create personalized diet plans:

1. **Initial Greeting**: Welcomes user and acknowledges their goal
2. **Information Gathering**: Asks specific questions one by one:
   - Age, gender, height, weight
   - Activity level
   - Health goals
   - Food allergies/dislikes
   - Dietary preferences
   - Meal frequency
   - Medical conditions

3. **Plan Generation**: Creates a comprehensive diet plan including:
   - Executive Summary
   - Caloric & Macronutrient Goals
   - 7-Day Sample Meal Plan
   - Hydration Guidelines
   - General Advice
   - Medical Disclaimer

### Memory Management

- Each session maintains conversation history
- Context is preserved across multiple interactions
- Session-based isolation for multiple users

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GOOGLE_API_KEY` | Alternative to GEMINI_API_KEY | Yes (if GEMINI_API_KEY not set) |
| `PORT` | Server port (default: 8080) | No |

### API Key Setup

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key (starts with 'AI')
4. Set it in your environment variables

## 🐳 Docker Deployment

### Dockerfile Features

- Python 3.11 slim base image
- SQLite3 support for potential database needs
- Non-root user execution for security
- Optimized for production with Gunicorn + Uvicorn
- Multi-worker setup for better performance

### Docker Commands

```bash
# Build
docker build -t ai-dietitian .

# Run with environment file
docker run -p 8080:8080 --env-file .env ai-dietitian

# Run with inline environment
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key ai-dietitian
```

## 📁 Project Structure

```
ai-dietitian/
├── api.py              # FastAPI application
├── app.py              # Streamlit web interface
├── tool.py             # AI agent and prompt configuration
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
├── .env               # Environment variables (create this)
└── README.md          # This file
```

## 🔒 Security Features

- Input validation with Pydantic models
- Session ID sanitization
- CORS middleware configuration
- Trusted host middleware
- Non-root Docker user
- API key validation
- Error handling without information leakage

## 🚨 Important Notes

### Medical Disclaimer
This application is for informational purposes only and should not replace professional medical advice. Users with medical conditions should consult healthcare providers before following any diet recommendations.

### API Key Security
- Never commit API keys to version control
- Use environment variables for production
- Rotate keys regularly
- Monitor API usage and costs

## 🧪 Testing

### Manual Testing

1. **Streamlit App**:
   - Start the app and enter API key
   - Go through the complete conversation flow
   - Verify diet plan generation

2. **API Endpoints**:
   - Test health endpoint: `curl http://localhost:8080/health`
   - Test chat flow with session management
   - Verify error handling with invalid inputs

### Load Testing

```bash
# Using curl for basic testing
curl -X POST "http://localhost:8080/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello", "session_id": "test123"}'
```

## 🚀 Production Deployment

### Recommended Setup

1. **Environment**: Use production WSGI server (Gunicorn)
2. **Reverse Proxy**: Nginx for static files and SSL termination
3. **Monitoring**: Health checks and logging
4. **Scaling**: Multiple worker processes
5. **Security**: Proper CORS and host configuration

### Environment Configuration

```bash
# Production environment variables
GEMINI_API_KEY=your_production_key
PORT=8080
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the health endpoint at `/health`
3. Check logs for detailed error information
4. Ensure API key is valid and has sufficient quota
