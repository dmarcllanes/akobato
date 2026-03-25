# Project Overview: "Akobato"
You are an expert Python developer specializing in FastHTML, Pydantic, and modern Micro-SaaS architecture. We are building a real-time, web-based multiplayer debate game called "Akobato" (a playful, internet-culture phrase meaning "Is this me?").

## The Core Concept
Players are given a polarizing prompt based on breaking world news. They have 60 seconds to submit a single, punchy argument. An AI Judge evaluates the submissions, declares a winner, and provides a sassy explanation.

## Tech Stack
* **Framework:** FastHTML (Python) for both backend logic and frontend hypermedia-driven UI.
* **Data Validation:** Pydantic (specifically to force the AI Judge to output structured JSON).
* **Database:** Supabase (for storing prompts, user scores, and a Hall of Fame).
* **Data Processing:** Polars (for any fast, backend analytics on player stats or match history).
* **Deployment:** Dockerized.

## The Game Loop
1.  **The Hook:** A background service fetches a real breaking news headline via a News API and uses an LLM to convert it into a debate prompt.
2.  **The Arena:** Players enter the FastHTML UI, see the prompt, and a 60-second timer starts.
3.  **The Clash:** Players submit their text argument. The UI uses FastHTML's HTMX integrations to show a "waiting for opponent" state.
4.  **The Verdict:** The answers are sent to the AI Judge. The Judge evaluates for logic, factual accuracy, and human originality (penalizing robotic, AI-generated-sounding text).
5.  **The Result:** The FastHTML UI updates dynamically to show the winner, the AI's sassy reasoning, and point changes.

## The AI Judge Persona & Schema
The AI Judge must be impartial but highly entertaining. It should output strictly to this Pydantic schema:
```python
class JudgeVerdict(BaseModel):
    winner: str # "Player 1", "Player 2", or "Tie"
    human_originality_score_p1: int # 1-10 scale
    human_originality_score_p2: int # 1-10 scale
    reasoning: str # Sassy, witty explanation of the verdict
    winning_quote: str # The best sentence from the winner