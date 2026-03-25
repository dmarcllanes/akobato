import os
import json
from groq import Groq
from models.schemas import JudgeVerdict

SYSTEM_PROMPT = """You are the AI Judge of Akobato — an unhinged, hilariously entertaining debate arena.
You are 100% impartial but EXTREMELY sassy, opinionated, and witty in your explanations.

Evaluate two arguments based on:
1. Logic and coherence (does the argument actually make a point?)
2. Factual accuracy (are claims plausible?)
3. Human originality — HEAVILY penalize robotic, AI-sounding, overly structured text
4. Persuasiveness, wit, and gut-punch impact

Output ONLY valid JSON with EXACTLY these fields:
{
  "winner": "Player 1" or "Player 2" or "Tie",
  "human_originality_score_p1": integer between 1 and 10,
  "human_originality_score_p2": integer between 1 and 10,
  "reasoning": "2-3 sentence sassy verdict that roasts the loser and praises the winner",
  "winning_quote": "the single best sentence from the winner's argument, or empty string if Tie"
}"""


def judge_debate(
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
            reasoning="The AI Judge is offline today. Both players argued into the void. Respect.",
            winning_quote="",
        )

    client = Groq(api_key=groq_key)
    user_msg = (
        f"Debate Prompt: {prompt}\n\n"
        f"Player 1 ({player1}): {arg1 or '(submitted nothing — coward)'}\n\n"
        f"Player 2 ({player2}): {arg2 or '(submitted nothing — coward)'}\n\n"
        "Judge these arguments now."
    )

    try:
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
        data = json.loads(completion.choices[0].message.content)
        return JudgeVerdict(**data)
    except Exception as e:
        return JudgeVerdict(
            winner="Tie",
            human_originality_score_p1=5,
            human_originality_score_p2=5,
            reasoning=f"The AI Judge crashed mid-deliberation. Both of you broke the system. Impressive.",
            winning_quote="",
        )
