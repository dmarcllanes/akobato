# Project:Akobato
# Tech Stack: Python, FastHTML, Pydantic, Supabase, Docker

akobato/
├── .env                    # API keys (News API, AI API, Supabase)
├── .gitignore
├── Dockerfile              # For easy deployment later
├── requirements.txt        # python-fasthtml, pydantic, supabase, httpx, etc.
├── main.py                 # FastHTML app entry point and main router
├── components/             # Reusable FastHTML UI chunks
│   ├── __init__.py
│   ├── layout.py           # Base HTML shell, headers, dark mode styling
│   ├── arena.py            # The active debate game UI (timers, input fields)
│   └── verdicts.py         # UI for displaying the AI Judge's sassy ruling
├── routes/                 # Game loop endpoints
│   ├── __init__.py
│   ├── game.py             # Handles starting a match, submitting answers
│   └── leaderboard.py      # Displays the "Hall of Fame" best debates
├── services/               # External API integrations
│   ├── __init__.py
│   ├── news_fetcher.py     # Pulls breaking news and generates the prompt
│   └── ai_judge.py         # The LLM call that evaluates answers using Pydantic
├── models/                 # Data structures
│   ├── __init__.py
│   └── schemas.py          # Pydantic models for the AI output (JudgeVerdict)
└── static/                 # Static assets
    ├── css/
    │   └── custom.css      # Any custom styling on top of PicoCSS (FastHTML default)
    └── img/
        └── logo.svg        # The Ako Akobato branding