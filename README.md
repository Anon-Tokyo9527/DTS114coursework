# AI Tourism Planner

AI-powered tourism recommendation system — enter any city and get curated attractions with AI-generated images and personalized travel plans.

## Setup

```bash
# 1. Install dependencies
pip install flask flask-cors

# 2. Create .env file in project root with your API key:
#    APIFREE_API_KEY=sk-xxx

# 3. Run
cd artifacts/app/flask
python main.py
```

Open **http://127.0.0.1:5005** in your browser.

## Features

- Search any city worldwide for attraction recommendations
- AI-generated landmark images
- Day-by-day travel plan generation
- Disk cache for instant repeat queries

## Pre-cached Cities (instant response)

Beijing, Shanghai, Chengdu, Xi'an, Hangzhou, Guilin, Tokyo, Seoul, Paris, Nanjing

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/cities` | List cached cities |
| GET | `/api/attractions?city=X` | Get attractions and images |
| POST | `/api/plan` | Generate travel plan `{city, days}` |

## Project Structure

```
├── Task1/tourism_cw.ipynb    # Jupyter Notebook (AI-driven SDLC)
├── Task2/                    # Screenshots (commits, deploy, CI/CD)
├── artifacts/app/flask/      # Generated Flask application
├── utils.py                  # LLM integration library
└── .github/workflows/        # CI/CD pipeline
```
