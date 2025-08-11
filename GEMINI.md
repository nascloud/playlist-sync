# Plex Playlist Sync - Project Context for AI Assistant

## Project Overview

Plex Playlist Sync is a tool for automatically synchronizing music playlists from external music platforms (like NetEase Cloud Music, QQ Music) to your Plex media server. The project consists of a FastAPI backend and a React frontend.

### Main Technologies

- **Backend**: Python 3.9+, FastAPI, SQLite, SQLAlchemy, Alembic
- **Frontend**: React 18+, TypeScript, Tailwind CSS, Vite
- **Deployment**: Docker and Docker Compose
- **Dependencies**: Managed with `uv` (Python) and `npm` (JavaScript)

## Project Structure

```
plex-playlist-sync/
├── backend/              # FastAPI backend application
│   ├── api/              # API routes and endpoints
│   ├── core/             # Core configuration and security
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas for data validation
│   ├── services/         # Business logic services
│   ├── utils/            # Utility functions
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test files
│   ├── main.py           # Application entry point
│   ├── pyproject.toml    # Python dependencies
│   └── .env.example      # Environment variable template
├── web/                  # React frontend application
│   ├── src/              # Source code
│   ├── package.json      # Frontend dependencies
│   └── vite.config.ts    # Vite configuration
├── docs/                 # Project documentation
├── scripts/              # Utility scripts
├── docker-compose.yml    # Docker Compose configuration
└── Dockerfile            # Docker build configuration
```

## Environment Configuration

Before running the application, you must configure environment variables by copying `backend/.env.example` to `backend/.env` and filling in your values:

- `SECRET_KEY`: A long random string for JWT security
- `APP_PASSWORD`: Password for web interface login
- `PLEX_URL`: Your Plex server URL
- `PLEX_TOKEN`: Your Plex access token
- `DOWNLOADER_API_KEY`: API key for the music downloader service
- `DOWNLOAD_PATH`: Path where downloaded files are stored

## Building and Running

### Development Setup

1. **Backend Setup**:
   ```bash
   cd backend
   # Install Python dependencies
   uv sync
   # Run database migrations
   uv run alembic upgrade head
   ```

2. **Frontend Setup**:
   ```bash
   cd web
   # Install Node.js dependencies
   npm install
   ```

### Running in Development

- **Backend** (from `backend` directory):
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 3001
  ```
  API will be available at `http://localhost:3001`

- **Frontend** (from `web` directory):
  ```bash
  npm run dev
  ```
  Web interface will be available at `http://localhost:5173`

### Production Deployment

Using Docker Compose:
```bash
docker-compose up --build
```

## Database Schema

The application uses SQLite with the following main tables:

1. **settings**: Plex server configurations
2. **tasks**: Sync tasks for playlists
3. **download_settings**: Download configuration
4. **download_queue**: Download queue items
5. **download_sessions**: Download sessions
6. **logs**: Application logs

## Core Services

1. **SettingsService**: Manages server configurations
2. **SyncService**: Handles playlist synchronization
3. **DownloadService**: Manages music downloads
4. **TaskScheduler**: Handles scheduled sync tasks

## API Endpoints

Main API prefix: `/api/v1`

### Settings
- `GET /settings`: Get all server configurations
- `POST /settings`: Add a new server
- `GET /settings/{id}`: Get a specific server
- `PUT /settings/{id}`: Update a server
- `DELETE /settings/{id}`: Delete a server
- `POST /settings/{id}/test`: Test server connection

### Tasks
- `GET /tasks`: Get all sync tasks
- `POST /tasks`: Create a new sync task
- `GET /tasks/{id}`: Get a specific task
- `PUT /tasks/{id}`: Update a task
- `DELETE /tasks/{id}`: Delete a task
- `POST /tasks/{id}/sync`: Trigger immediate sync
- `GET /tasks/{id}/unmatched`: Get unmatched songs

### Logs
- `GET /logs`: Get application logs

### Download
- `GET /download/download-settings`: Get download settings
- `POST /download/download-settings`: Save download settings
- `POST /download/download-settings/test`: Test download API connection
- `GET /download/status`: Get download status
- `POST /download/all-missing`: Download all missing songs
- `POST /download/single`: Download a single song
- `POST /download/cancel-session/{session_id}`: Cancel a download session

## Development Conventions

### Backend
- Follows REST API conventions
- Uses Pydantic for data validation
- SQLAlchemy for database operations
- Alembic for database migrations
- Comprehensive logging with different levels
- Secure handling of sensitive data (encryption for tokens)

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- React Router for navigation
- Component-based architecture

### Testing
- Backend tests using pytest
- API testing script in `scripts/test_backend_api.py`

## Key Features

1. **Playlist Sync**: Automatic synchronization of playlists from NetEase/QQ Music to Plex
2. **Web Interface**: User-friendly management dashboard
3. **Scheduled Tasks**: CRON-based scheduling for automatic sync
4. **Download Management**: Download missing songs from external platforms
5. **Security**: Encrypted storage of credentials
6. **Containerization**: Docker support for easy deployment

## Common Development Tasks

### Adding a New API Endpoint
1. Create a new endpoint file in `backend/api/v1/endpoints/`
2. Add the route in `backend/api/v1/api.py`
3. Implement the business logic in a service class

### Database Migration
1. Modify models in `backend/models/`
2. Generate migration: `uv run alembic revision --autogenerate -m "Description"`
3. Apply migration: `uv run alembic upgrade head`

### Adding a New Setting
1. Update the database schema with a new migration
2. Modify the relevant service class
3. Add API endpoints if needed
4. Update the frontend to display/manage the setting

## Troubleshooting

### Common Issues
1. **Environment Variables**: Ensure all required variables are set in `.env`
2. **Database Issues**: Run migrations with `uv run alembic upgrade head`
3. **Frontend Not Found**: Build the frontend with `npm run build` in the `web` directory

### Logs
Check logs in the `backend/logs` directory for debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit a pull request