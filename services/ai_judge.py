import os
import json
import asyncio
from groq import Groq
from models.schemas import JudgeVerdict

BOT_SYSTEM = """You are AkobatoBot — a spicy, opinionated AI debater.
You take the OPPOSING side of whatever the human just argued.
Be bold, punchy, and human-sounding. Max 3 sentences. No bullet points."""


async def generate_bot_argument(prompt: str, player_arg: str) -> str:
    """Generate a counter-argument for the AI bot in solo mode."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return "I, AkobatoBot, refuse to dignify that argument with a response. You win by default — but don't get comfortable."

    def _call():
        client = Groq(api_key=groq_key)
        return client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": BOT_SYSTEM},
                {"role": "user", "content": f"Debate topic: {prompt}\n\nHuman argued: {player_arg}\n\nNow argue the opposite side."},
            ],
            max_tokens=120,
            temperature=0.95,
        ).choices[0].message.content.strip()

    try:
        return await asyncio.to_thread(_call)
    except Exception:
        return "Error loading bot response — the human wins this round. Enjoy it."


SYSTEM_PROMPT = """You are the AI Judge of Akobato — an unhinged, hilariously entertaining debate arena.
You are 100% impartial but EXTREMELY sassy, opinionated, and witty in your explanations.

Evaluate two sides based on:
1. Logic and coherence (does the argument actually make a point?)
2. Factual accuracy (are claims plausible?)
3. Human originality — HEAVILY penalize robotic, AI-sounding, overly structured text
4. Persuasiveness, wit, and gut-punch impact

Output ONLY valid JSON with EXACTLY these fields:
{
  "winner": "Team A" or "Team B" or "Tie",
  "human_originality_score_p1": integer between 1 and 10,
  "human_originality_score_p2": integer between 1 and 10,
  "reasoning": "2-3 sentence sassy verdict that roasts the loser and praises the winner",
  "winning_quote": "the single best sentence from the winner's argument, or empty string if Tie"
}"""


async def judge_debate(
    prompt: str,
    player1: str,
    arg1: str,
    player2: str,
    arg2: str,
) -> JudgeVerdict:
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        # Graceful fallback when no API key
        return JudgeVerdict(
            winner="Tie",
            human_originality_score_p1=5,
            human_originality_score_p2=5,
            reasoning="The AI Judge is offline today. Both sides argued into the void. Respect.",
            winning_quote="",
        )

    client = Groq(api_key=groq_key)
    user_msg = (
        f"Debate Prompt: {prompt}\n\n"
        f"{player1}: {arg1 or '(submitted nothing — coward)'}\n\n"
        f"{player2}: {arg2 or '(submitted nothing — coward)'}\n\n"
        "Judge these arguments now."
    )

    def _call_groq():
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
            temperature=0.85,
        )
        return completion.choices[0].message.content

    try:
        # Run the blocking Groq call in a thread so the server stays responsive
        raw = await asyncio.to_thread(_call_groq)
        data = json.loads(raw)
        return JudgeVerdict(**data)
    except Exception:
        return JudgeVerdict(
            winner="Tie",
            human_originality_score_p1=5,
            human_originality_score_p2=5,
            reasoning="The AI Judge crashed mid-deliberation. Both of you broke the system. Impressive.",
            winning_quote="",
        )
