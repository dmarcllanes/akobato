import os
import random
import httpx
from collections import deque
from groq import Groq

# Rolling window of recently used prompts — never repeat within last 60 matches
_used_prompts: deque = deque(maxlen=60)

# ── Fallback pools (used when News API or Groq is unavailable) ────────────────

FALLBACK = {
    "world": [
        "Should wealthy nations be legally required to accept climate refugees?",
        "Is the United Nations still relevant in today's geopolitical landscape?",
        "Should foreign aid be conditional on human rights records?",
        "Should nuclear-armed countries be banned from the UN Security Council?",
        "Is economic sanctions a form of modern warfare?",
        "Should the world adopt a single global currency?",
        "Is globalisation doing more harm than good to developing nations?",
        "Should wealthy countries pay reparations for colonialism?",
        "Should the internet be treated as a basic human right?",
        "Is NATO still necessary in today's world order?",
        "Should countries with high emissions face trade penalties?",
        "Is the current world order too dominated by a few superpowers?",
        "Should the International Criminal Court have binding power over all nations?",
        "Do open borders do more good than harm to society?",
        "Should the world have a single governing body for AI?",
    ],
    "technology": [
        "Should AI be banned from writing music and art?",
        "Is remote work killing collaboration or saving workers' sanity?",
        "Should social media platforms be held legally responsible for misinformation?",
        "Should there be a global pause on developing superintelligent AI?",
        "Is screen time addiction as dangerous as drug addiction?",
        "Should algorithm-driven feeds be made illegal?",
        "Is cryptocurrency doing more harm than good to the global economy?",
        "Should children under 16 be banned from all social media?",
        "Does big tech have too much power over democracy?",
        "Should AI-generated content always be labelled?",
        "Is the metaverse a revolutionary leap or a waste of resources?",
        "Should deepfakes be criminalised in all contexts?",
        "Is surveillance capitalism an acceptable trade-off for free services?",
        "Should self-driving cars be allowed on roads before they're perfect?",
        "Is open-source software a threat to national security?",
    ],
    "politics": [
        "Should voting be mandatory in democracies?",
        "Is cancel culture doing more harm than good to society?",
        "Should billionaires be legally required to give away most of their wealth?",
        "Should the voting age be lowered to 16?",
        "Is democracy the best system of government we have?",
        "Should politicians be banned from receiving corporate donations?",
        "Is civil disobedience ever justified in a functioning democracy?",
        "Should there be term limits for all elected officials?",
        "Is political correctness stifling honest debate?",
        "Should taxes on the ultra-wealthy be raised to 90%?",
        "Should lobbying be made illegal?",
        "Is universal basic income a realistic solution to poverty?",
        "Should electoral college systems be abolished?",
        "Is nationalism inherently dangerous?",
        "Should whistleblowers always be protected by law?",
    ],
    "sports": [
        "Should performance-enhancing drugs be legalised in professional sports?",
        "Is esports a real sport deserving Olympic inclusion?",
        "Should college athletes be paid like professionals?",
        "Has money ruined the spirit of football?",
        "Should fighting sports like boxing and MMA be banned?",
        "Is VAR technology ruining football?",
        "Should trans athletes compete in their identified gender category?",
        "Has commercialisation killed fan loyalty in sports?",
        "Should athletes be banned from political expression during competition?",
        "Is the Olympics still a relevant event in today's world?",
        "Should extreme sports be excluded from public health insurance?",
        "Is sports betting destroying the integrity of the game?",
        "Are sports stars overpaid compared to their social value?",
        "Should women's sports receive equal broadcast time and pay?",
        "Is hosting the World Cup worth the cost for developing nations?",
    ],
    "entertainment": [
        "Are reboots and sequels killing Hollywood creativity?",
        "Should streaming platforms be forced to fund local content?",
        "Is celebrity culture more harmful than inspiring to young people?",
        "Has social media made musicians more or less authentic?",
        "Should film ratings be determined by AI, not humans?",
        "Is reality TV making society dumber?",
        "Should influencers be held to the same advertising standards as traditional media?",
        "Has streaming killed the communal experience of cinema?",
        "Is award season in Hollywood just a popularity contest?",
        "Should violent video games carry the same warnings as cigarettes?",
        "Is nostalgic content a sign of cultural stagnation?",
        "Should actors be allowed to use AI to extend their careers after death?",
        "Has the attention economy ruined long-form storytelling?",
        "Are podcasts making us less informed or more?",
        "Should ticket prices for live music be government-regulated?",
    ],
    "science": [
        "Should human genetic engineering be legal for non-medical use?",
        "Is space colonisation a moral obligation or a dangerous distraction?",
        "Should we revive extinct species through cloning?",
        "Is nuclear energy the only realistic answer to climate change?",
        "Should animal testing be banned entirely in favour of lab alternatives?",
        "Is geoengineering too risky to ever deploy?",
        "Should there be limits on human lifespan extension through technology?",
        "Is the pursuit of immortality ethical?",
        "Should scientists be held legally responsible for misuse of their research?",
        "Is GMO food the solution to global hunger?",
        "Should government fund basic science research over applied research?",
        "Is the brain-computer interface the next civil rights frontier?",
        "Should CRISPR gene editing in embryos be globally banned?",
        "Is dark matter research worth the billions it costs?",
        "Should lab-grown meat replace conventional farming?",
    ],
    "business": [
        "Should a four-day work week be legally mandated?",
        "Is fast fashion ethically worse than owning a gas-powered car?",
        "Should gig economy companies be forced to treat workers as employees?",
        "Do loyalty programmes exploit customers more than they reward them?",
        "Should corporations be legally required to have worker representation on boards?",
        "Is hustle culture destroying mental health?",
        "Should advertising to children under 12 be completely banned?",
        "Do non-compete clauses unfairly restrict workers' freedom?",
        "Should companies be legally required to be carbon neutral by 2030?",
        "Is the concept of infinite economic growth fundamentally flawed?",
        "Should profit margins in the pharmaceutical industry be capped?",
        "Is entrepreneurship overglorified as a path to success?",
        "Should supermarkets be banned from wasting unsold food?",
        "Is private equity doing more harm than good to the economy?",
        "Should CEOs earn no more than 20x their lowest-paid employee?",
    ],
    "gaming": [
        "Should loot boxes be classified and regulated as gambling?",
        "Has online multiplayer made gaming more toxic than enjoyable?",
        "Should esports players be treated as professional athletes?",
        "Are video games genuinely art or just sophisticated entertainment?",
        "Should governments fund esports the way they fund traditional sports?",
        "Has game streaming culture made gaming more accessible or more elitist?",
        "Should violent video games be banned for players under 18?",
        "Is pay-to-win a form of cheating?",
        "Are gaming addiction and social media addiction the same problem?",
        "Should game developers be legally responsible for in-game toxic behaviour?",
        "Has the rise of mobile gaming lowered the quality of the medium?",
        "Should AI-generated game content replace human developers?",
        "Is game preservation a legal right?",
        "Should subscription gaming models replace one-time purchases?",
        "Has games journalism become too close to the industry it covers?",
    ],
}

# Themes used to seed Groq when no news headline is available
_AI_THEMES = {
    "world":         ["climate change", "migration", "international law", "geopolitics", "global inequality"],
    "technology":    ["artificial intelligence", "social media", "privacy", "automation", "big tech"],
    "politics":      ["democracy", "free speech", "taxation", "government power", "elections"],
    "sports":        ["doping", "money in sports", "inclusivity in sports", "esports", "athlete activism"],
    "entertainment": ["streaming", "celebrity influence", "AI in creative arts", "social media fame", "cancel culture"],
    "science":       ["gene editing", "space exploration", "climate technology", "medical ethics", "AI research"],
    "business":      ["remote work", "wealth inequality", "corporate responsibility", "gig economy", "startup culture"],
    "gaming":        ["loot boxes", "gaming addiction", "esports legitimacy", "toxic communities", "AI in games"],
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
    prompt   = _headline_to_prompt(headline, category)

    # Deduplicate: if this exact prompt was used recently, try once more
    if prompt in _used_prompts:
        headline = _get_headline(category)
        prompt   = _headline_to_prompt(headline, category)

    _used_prompts.append(prompt)
    return prompt


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
                        "pageSize": 20,
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
                        "pageSize":   20,
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
            # Pick randomly from top 10 so each call can yield a different headline
            return random.choice(valid[:10])["title"] if valid else ""

    except Exception:
        return ""


def _headline_to_prompt(headline: str, category: str) -> str:
    groq_key = os.getenv("GROQ_API_KEY", "")

    if not groq_key:
        return _pick_unused(category)

    try:
        client = Groq(api_key=groq_key)

        if headline:
            # Convert a real news headline into a debate question
            content = (
                f"News headline: '{headline}'\n\n"
                "Write ONE punchy debate question based on this news. "
                "Make it provocative, fun, and something two people would strongly disagree on. "
                "Output ONLY the question. Max 25 words. No quotes around it."
            )
        else:
            # No news available — ask Groq to invent one from a random theme
            themes = _AI_THEMES.get(category, ["current events"])
            theme  = random.choice(themes)
            content = (
                f"Topic area: {category} — specifically about: {theme}\n\n"
                "Invent ONE original, spicy debate question that two people would strongly disagree on. "
                "Be provocative and specific, not generic. "
                "Output ONLY the question. Max 25 words. No quotes around it."
            )

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": content}],
            max_tokens=60,
            temperature=1.0,
        )
        result = completion.choices[0].message.content.strip().strip('"').strip("'")
        return result if result else _pick_unused(category)

    except Exception:
        return _pick_unused(category)


def _pick_unused(category: str) -> str:
    """Pick a prompt from the fallback pool that hasn't been used recently."""
    pool   = FALLBACK.get(category) or [p for v in FALLBACK.values() for p in v]
    unused = [p for p in pool if p not in _used_prompts]
    return random.choice(unused if unused else pool)
