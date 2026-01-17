# Quick Start Deployment Guide
## Get GentleQuest Running in 10 Minutes

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (optional, can use filesystem sessions)
- Gemini API key

## Local Development Setup

### 1. Clone & Install (2 min)

```bash
git clone https://github.com/yourusername/ai-mvp-backend.git
cd ai-mvp-backend

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Database Setup (2 min)

```bash
# Create database
createdb mental_health

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_quests.py
python scripts/seed_resources.py
```

### 3. Environment Variables (1 min)

Create `.env` file:

```bash
DATABASE_URL=postgresql://ai_buddy:ai_buddy_password@localhost:5432/mental_health
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_min_32_chars
ENVIRONMENT=local
```

### 4. Run Backend (1 min)

```bash
python app.py
# Server running at http://localhost:5055
```

### 5. Run Frontend (2 min)

```bash
cd ai_buddy_web
flutter pub get
flutter run -d chrome
# App running at http://localhost:8080
```

### 6. Test (2 min)

Open browser: http://localhost:8080

- Sign up (enter email)
- Send chat message
- Log mood
- View quests
- Browse resources

## Production Deployment (Render)

### 1. Create Render Account

- Sign up at https://render.com
- Connect GitHub repository

### 2. Create PostgreSQL Database

- New → PostgreSQL
- Name: gentlequest-db
- Plan: Free or Starter
- Copy DATABASE_URL

### 3. Create Web Service

- New → Web Service
- Repository: ai-mvp-backend
- Name: gentlequest
- Environment: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

### 4. Environment Variables

Add in Render dashboard:

```
DATABASE_URL=<from step 2>
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=<your key>
SECRET_KEY=<generate random 32+ chars>
ENVIRONMENT=production
SENDGRID_API_KEY=<your key>
CORS_ORIGINS=https://gentlequest.onrender.com
```

### 5. Deploy

- Click "Manual Deploy" or push to main branch
- Wait 3-5 minutes
- Check logs for errors

### 6. Run Migrations

In Render Shell:

```bash
alembic upgrade head
python scripts/seed_quests.py
python scripts/seed_resources.py
```

### 7. Test

```bash
curl https://gentlequest.onrender.com/api/health
```

## Troubleshooting

### "Database connection failed"
- Check DATABASE_URL is correct
- Verify PostgreSQL is running
- Check firewall/network

### "Gemini API error"
- Verify GEMINI_API_KEY is set
- Check API key is valid
- Check quota not exceeded

### "Migrations failed"
- Check database exists
- Run `alembic current` to see state
- Try `alembic downgrade -1` then `alembic upgrade head`

### "Frontend won't load"
- Check backend is running (http://localhost:5055/api/health)
- Check CORS_ORIGINS includes frontend URL
- Check browser console for errors

## Common Commands

### Backend
```bash
# Run server
python app.py

# Run tests
pytest -v

# Run migrations
alembic upgrade head

# Check migration status
alembic current

# Rollback migration
alembic downgrade -1
```

### Frontend
```bash
# Run web
cd ai_buddy_web && flutter run -d chrome

# Run tests
cd ai_buddy_web && flutter test

# Build for production
cd ai_buddy_web && flutter build web
```

### Database
```bash
# Connect to database
psql mental_health

# Check tables
\dt

# Check data
SELECT COUNT(*) FROM sessions;
SELECT COUNT(*) FROM quests;
SELECT COUNT(*) FROM resources;
```

## Next Steps

1. Complete validation (Jan 17-24)
2. Make GO/NO-GO decision (Jan 24)
3. Implement features (Jan 25-31 if GO)
4. Launch (Feb 1 if GO)

**Total setup time: 10 minutes local, 15 minutes production**
