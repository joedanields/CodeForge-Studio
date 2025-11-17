# CodeForge Studio

An AI-powered platform for comprehensive problem analysis and innovative solution generation.

## Features

- **Problem Submission**: Users can submit problems with title and description
- **AI Analysis**: Comprehensive analysis using structured prompt templates
- **Solution Comparison**: Side-by-side comparison of existing solutions
- **Innovation Engine**: Novel solution proposals with feasibility assessment
- **Implementation Roadmap**: Step-by-step implementation guidance

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery
- **Package Manager**: UV

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run database migrations**:
   ```bash
   uv run alembic upgrade head
   ```

4. **Start the development server**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

5. **Start the frontend** (in a separate terminal):
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Project Structure

```
├── app/                    # Backend application
│   ├── api/               # API routes
│   ├── core/              # Core functionality
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── main.py            # FastAPI app
├── frontend/              # React frontend
├── tests/                 # Test files
├── migrations/            # Database migrations
└── docker-compose.yml     # Docker configuration
```

## API Endpoints

- `POST /api/problems/` - Submit a new problem
- `GET /api/problems/{id}` - Get problem details
- `POST /api/problems/{id}/analyze` - Trigger AI analysis
- `GET /api/problems/{id}/analysis` - Get analysis results

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.