# Akobato — Gamification Upgrade Plan

---

## Sprint 1 — Quick Wins (1-2 days, mostly CSS/front-end)

| # | Feature | What it does |
|---|---|---|
| G1 | **Animated rank badge** | Pulsing glow on the rank title on dashboard — zero DB work, pure CSS on existing elements |
| G2 | **Streak flame on nav** | `🔥3` pill in the nav when win streak ≥ 3 — always visible, maximum reach |
| D2 | **Win confetti / loss red flash** | CSS particle burst on win, red overlay flash on loss — transforms match feel instantly |
| G3 | **Hot topic badge on categories** | `🔥 HOT` tag on trending categories — one DB column add + cached query |

---

## Sprint 2 — Core Retention Loop (3-4 days)

| # | Feature | What it does |
|---|---|---|
| B1 | **Win streak counter** | Track consecutive wins — strongest single retention mechanic (loss aversion) |
| D3 | **Streak callout after match** | "🔥 You're on a 5-win streak!" in verdict — free once B1 exists |
| A1 | **XP / Level system** | Separate XP from score so players always progress even on a loss — dashboard scaffolding already built |
| E1 | **Token regeneration** | +1 token every 2 hours — eliminates the hard-stop that causes players to leave and never return |

---

## Sprint 3 — Social Layer (3-5 days)

| # | Feature | What it does |
|---|---|---|
| C1 | **Badge system (5 starter badges)** | First Blood, 10 Wins, 3-win streak, Roast King, Legend rank |
| C3 | **Badge toast notification** | Slide-in toast when a badge is earned right after the match — anchors the reward to the action |
| F3 | **Share result card** | Copy-paste text card for Discord/X — organic growth driver |

---

## Sprint 4 — Deep Engagement (5-7 days)

| # | Feature | What it does |
|---|---|---|
| B2 | **Daily challenge prompt** | One shared prompt/day, bonus tokens for winning it — daily return habit |
| A3 | **Avatar frames** | Unlockable rings around the pixel avatar based on rank/badges |
| F1 | **Weekly seasons** | Leaderboard resets weekly with season badges for top 3 — keeps leaderboard competitive |
| F2 | **Rival system** | Track head-to-head record vs. a specific opponent — "I'm 3-4 vs NeonFox, need revenge" |

---

## Priority Matrix (Impact vs Effort)

| # | Feature | Impact (1-5) | Effort (1-5) | Notes |
|---|---|---|---|---|
| 1 | Streak flame icon on nav + dashboard | 4 | 1 | One DB column; always-visible nav hook |
| 2 | Animated rank badge on dashboard | 4 | 1 | Zero DB; pure CSS on existing elements |
| 3 | Win confetti / loss red flash | 4 | 1 | Pure front-end; no backend changes |
| 4 | Win streak counter | 5 | 2 | Strongest single retention mechanic |
| 5 | Streak callout after match | 4 | 1 | Free once streak column exists |
| 6 | XP / Level system | 5 | 2 | Dashboard scaffolding already built |
| 7 | Token regeneration | 5 | 2 | Eliminates hard-stop churn trigger |
| 8 | Hot topic indicator on categories | 3 | 1 | One column + cached query |
| 9 | Badge toast notification | 4 | 2 | Needs badge system first |
| 10 | Achievement / Badge system (5 badges) | 5 | 3 | Start small; unlocks entire reward layer |

---

## New DB Columns Needed

```sql
-- players table
xp                INTEGER DEFAULT 0
level             INTEGER DEFAULT 1
win_streak        INTEGER DEFAULT 0
best_streak       INTEGER DEFAULT 0
last_token_regen  TIMESTAMPTZ DEFAULT NOW()
login_streak      INTEGER DEFAULT 0
last_active_date  DATE

-- verdicts table
category          TEXT   -- for hot topic queries

-- new tables
player_badges     (username, badge_slug, earned_at)
rivalries         (player_a, player_b, wins_a, wins_b, ties)
season_archive    (season_num, username, final_score, rank)
```

---

## Key Files to Touch per Sprint

| File | Sprints |
|---|---|
| `pages/dashboard.py` | S1, S2 — rank glow, streak stat card, XP progress bar |
| `components/verdicts.py` | S1, S2, S3 — animations, streak callout, badge toast, share button |
| `components/layout.py` | S2 — streak flame pill in nav |
| `pages/category.py` | S1 — hot topic badge on carousel cards |
| `routes/game.py` | S2, S3 — post-match stat update: XP, streak, token grants, badge checks |
| `static/css/custom.css` | S1, S2, S3 — keyframes: rankPulse, confetti, flash, toast slide-in |
| `supabase_setup.sql` | S2+ — all new columns and tables |

---

## Badge Catalogue (Sprint 3 starter set — expand later)

| Slug | Icon | Name | Unlock Condition |
|---|---|---|---|
| `first_blood` | ⚔ | First Blood | Win your first match |
| `ten_wins` | 🏆 | Decade of Dominance | 10 total wins |
| `streak_3` | 🔥 | Hat Trick | 3-win streak |
| `streak_7` | 🔥🔥 | Inferno | 7-win streak |
| `roast_king` | 🎤 | Roast King | Receive a 10/10 human originality score |
| `fifty_wins` | 👑 | Half-Century | 50 total wins |
| `legend_rank` | 💎 | LEGEND | Reach LEGEND rank |
| `daily_7` | ☀ | Daily Devotee | Complete 7 daily challenges |
| `comeback_kid` | 💪 | Comeback Kid | Win after submitting with < 5 seconds left |
| `zero_to_hero` | 🚀 | Zero to Hero | Win after losing 5 in a row |
