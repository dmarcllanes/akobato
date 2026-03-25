import os
import random
import httpx
from groq import Groq

# Fallback prompts per category
FALLBACK = {
    "world": [
        "Should wealthy nations be legally required to accept climate refugees?",
        "Is the United Nations still relevant in today's geopolitical landscape?",
        "Should foreign aid be conditional on human rights records?",
    ],
    "technology": [
        "Should AI be banned from writing music and art?",
        "Is remote work killing collaboration or saving workers' sanity?",
        "Should social media platforms be held legally responsible for misinformation?",
        "Should there be a global pause on developing superintelligent AI?",
    ],
    "politics": [
        "Should voting be mandatory in democracies?",
        "Is cancel culture doing more harm than good to society?",
        "Should billionaires be legally required to give away most of their wealth?",
        "Should the voting age be lowered to 16?",
    ],
    "sports": [
        "Should performance-enhancing drugs be legalised in professional sports?",
        "Is esports a real sport deserving Olympic inclusion?",
        "Should college athletes be paid like professionals?",
        "Has money ruined the spirit of football?",
    ],
    "entertainment": [
        "Are reboots and sequels killing Hollywood creativity?",
        "Should streaming platforms be forced to fund local content?",
        "Is celebrity culture more harmful than inspiring to young people?",
        "Has social media made musicians more or less authentic?",
    ],
    "science": [
        "Should human genetic engineering be legal for non-medical use?",
        "Is space colonisation a moral obligation or a dangerous distraction?",
        "Should we revive extinct species through cloning?",
        "Is nuclear energy the only realistic answer to climate change?",
    ],
    "business": [
        "Should a four-day work week be legally mandated?",
        "Is fast fashion ethically worse than owning a gas-powered car?",
        "Should gig economy companies be forced to treat workers as employees?",
        "Do loyalty programmes exploit customers more than they reward them?",
    ],
    "gaming": [
        "Should loot boxes be classified and regulated as gambling?",
        "Has online multiplayer made gaming more toxic than enjoyable?",
        "Should esports players be treated as professional athletes?",
        "Are video games genuinely art or just sophisticated entertainment?",
    ],
}

# Categories with a direct NewsAPI top-headlines category
_HEADLINES_CATEGORY = {
    "technology":    "technology",
    "sports":        "sports",
    "entertainment": "entertainment",
    "science":       "science",
    "business":      "business",
}

# Categories that need keyword search via /v2/everything
_KEYWORD_SEARCH = {
    "world":    "international world global",
    "politics": "politics government election policy",
    "gaming":   "gaming video games esports",
}


async def fetch_debate_prompt(category: str = "random") -> str:
    if category == "random":
        category = random.choice([k for k in FALLBACK if k != "random"])
    headline = _get_headline(category)
    return _headline_to_prompt(headline, category)


def _get_headline(category: str) -> str:
    news_key = os.getenv("NEWS_API_KEY", "")
    if not news_key or "your_" in news_key:
        return ""

    try:
        with httpx.Client(timeout=6) as client:

            # ── Top-headlines endpoint (official category) ─────────────────
            if category in _HEADLINES_CATEGORY:
                resp = client.get(
                    "https://newsapi.org/v2/top-headlines",
                    params={
                        "country":  "us",
                        "category": _HEADLINES_CATEGORY[category],
                        "pageSize": 10,
                        "apiKey":   news_key,
                    },
                )

            # ── Everything endpoint (keyword search) ───────────────────────
            elif category in _KEYWORD_SEARCH:
                resp = client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q":          _KEYWORD_SEARCH[category],
                        "language":   "en",
                        "sortBy":     "publishedAt",
                        "pageSize":   10,
                        "apiKey":     news_key,
                    },
                )
            else:
                return ""

            articles = resp.json().get("articles", [])
            valid = [
                a for a in articles
                if a.get("title") and a["title"] != "[Removed]"
            ]
            return random.choice(valid[:5])["title"] if valid else ""

    except Exception:
        return ""


def _headline_to_prompt(headline: str, category: str) -> str:
    groq_key = os.getenv("GROQ_API_KEY", "")

    if not headline or not groq_key:
        pool = FALLBACK.get(category) or [p for v in FALLBACK.values() for p in v]
        return random.choice(pool)

    try:
        client = Groq(api_key=groq_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    f"News headline: '{headline}'\n\n"
                    "Write ONE punchy debate question based on this news. "
                    "Make it provocative, fun, and something two people would strongly disagree on. "
                    "Output ONLY the question. Max 25 words. No quotes around it."
                ),
            }],
            max_tokens=60,
            temperature=0.9,
        )
        result = completion.choices[0].message.content.strip().strip('"').strip("'")
        pool = FALLBACK.get(category, [])
        return result if result else (random.choice(pool) if pool else "Is AI taking over too fast?")
    except Exception:
        pool = FALLBACK.get(category) or [p for v in FALLBACK.values() for p in v]
        return random.choice(pool)
