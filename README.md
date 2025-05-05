# AI Customer Support Bot - MCP Server

A Model Context Protocol (MCP) server that provides AI-powered customer support using Cursor AI and Glama.ai integration.

## Features

- Real-time context fetching from Glama.ai
- AI-powered response generation with Cursor AI
- Batch processing support
- Priority queuing
- Rate limiting
- User interaction tracking
- Health monitoring
- MCP protocol compliance

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Glama.ai API key
- Cursor AI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

5. Configure your `.env` file with your credentials:
```env
# API Keys
GLAMA_API_KEY=your_glama_api_key_here
CURSOR_API_KEY=your_cursor_api_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost/customer_support_bot

# API URLs
GLAMA_API_URL=https://api.glama.ai/v1

# Security
SECRET_KEY=your_secret_key_here

# MCP Server Configuration
SERVER_NAME="AI Customer Support Bot"
SERVER_VERSION="1.0.0"
API_PREFIX="/mcp"
MAX_CONTEXT_RESULTS=5

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Logging
LOG_LEVEL=INFO
```

6. Set up the database:
```bash
# Create the database
createdb customer_support_bot

# Run migrations (if using Alembic)
alembic upgrade head
```

## Running the Server

Start the server:
```bash
python app.py
```

The server will be available at `http://localhost:8000`

## API Endpoints

### 1. Root Endpoint
```bash
GET /
```
Returns basic server information.

### 2. MCP Version
```bash
GET /mcp/version
```
Returns supported MCP protocol versions.

### 3. Capabilities
```bash
GET /mcp/capabilities
```
Returns server capabilities and supported features.

### 4. Process Request
```bash
POST /mcp/process
```
Process a single query with context.

Example request:
```bash
curl -X POST http://localhost:8000/mcp/process \
  -H "Content-Type: application/json" \
  -H "X-MCP-Auth: your-auth-token" \
  -H "X-MCP-Version: 1.0" \
  -d '{
    "query": "How do I reset my password?",
    "priority": "high",
    "mcp_version": "1.0"
  }'
```

### 5. Batch Processing
```bash
POST /mcp/batch
```
Process multiple queries in a single request.

Example request:
```bash
curl -X POST http://localhost:8000/mcp/batch \
  -H "Content-Type: application/json" \
  -H "X-MCP-Auth: your-auth-token" \
  -H "X-MCP-Version: 1.0" \
  -d '{
    "queries": [
      "How do I reset my password?",
      "What are your business hours?",
      "How do I contact support?"
    ],
    "mcp_version": "1.0"
  }'
```

### 6. Health Check
```bash
GET /mcp/health
```
Check server health and service status.

## Rate Limiting

The server implements rate limiting with the following defaults:
- 100 requests per 60 seconds
- Rate limit information is included in the health check endpoint
- Rate limit exceeded responses include reset time

## Error Handling

The server returns structured error responses in the following format:
```json
{
  "code": "ERROR_CODE",
  "message": "Error description",
  "details": {
    "timestamp": "2024-02-14T12:00:00Z",
    "additional_info": "value"
  }
}
```

Common error codes:
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `UNSUPPORTED_MCP_VERSION`: Unsupported MCP version
- `PROCESSING_ERROR`: Error processing request
- `CONTEXT_FETCH_ERROR`: Error fetching context from Glama.ai
- `BATCH_PROCESSING_ERROR`: Error processing batch request

## Development

### Project Structure
```
.
├── app.py              # Main application file
├── database.py         # Database configuration
├── middleware.py       # Middleware (rate limiting, validation)
├── models.py          # Database models
├── mcp_config.py      # MCP-specific configuration
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

### Adding New Features

1. Update `mcp_config.py` with new configuration options
2. Add new models in `models.py` if needed
3. Create new endpoints in `app.py`
4. Update capabilities endpoint to reflect new features

## Security

- All MCP endpoints require authentication via `X-MCP-Auth` header
- Rate limiting is implemented to prevent abuse
- Database credentials should be kept secure
- API keys should never be committed to version control

## Monitoring

The server provides health check endpoints for monitoring:
- Service status
- Rate limit usage
- Connected services
- Processing times

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Verification Badge

[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/1dfb7c9a-f35f-420d-9569-3dbcea100dba)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please create an issue in the repository or contact the development team. 


<a href="https://glama.ai/mcp/servers/@ChiragPatankar/AI-Customer-Support-Bot---MCP-Server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@ChiragPatankar/AI-Customer-Support-Bot---MCP-Server/badge" />
</a>
