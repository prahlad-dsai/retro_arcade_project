# 🕹️ Retro-Arcade Smart Token & Cabinet Management Network

A full-stack mini project for managing a modern retro arcade. The **FastAPI** backend handles gamers, cabinets, token-based queues, high scores and statistics. A single-page **HTML + Tailwind CSS** dashboard lets gamers and floor managers use the system from the browser.

Gamers hold a token balance and spend tokens to join virtual queues for arcade cabinets. Beating a cabinet's high score earns reward tickets. Floor managers manage gamers, cabinets and queues, and can view lounge-wide statistics.

Data is stored in simple JSON files, so no database setup is needed.

---

## ✨ Features

**Backend (API)**
- Gamer profile management (token balance, ticket balance, account tier)
- Arcade cabinet management (status, tokens per play, high score tracking)
- Virtual queue sessions with automatic token deduction
- High-score submission with ticket rewards
- Role-based access control using a request header
- Lounge statistics: token revenue, cabinet utilization, top high-score holder
- JSON file persistence (`gamers.json`, `cabinets.json`, `sessions.json`)
- CORS enabled

**Frontend (Dashboard)**
- Role switcher (Gamer / Arcade Floor Manager) with no login needed
- Live cabinet floor with status badges, token cost and high scores
- Gamers can queue up for a cabinet and submit scores
- Managers get a control center with live lounge stats, an add-cabinet form, cabinet status updates and deletion, and gamer token/ticket management
- Dark neon "arcade" theme built with Tailwind CSS

---

## 🧱 Tech Stack

| Component  | Technology                                   |
|------------|----------------------------------------------|
| Language   | Python 3.10+                                 |
| Framework  | FastAPI                                      |
| Validation | Pydantic                                     |
| Server     | Uvicorn                                      |
| Storage    | JSON files                                   |
| Frontend   | HTML, vanilla JavaScript, Tailwind CSS (CDN) |
| Packaging  | [uv](https://docs.astral.sh/uv/)             |

---

## 📁 Project Structure

```
.
├── main.py            # FastAPI application (models, rules, endpoints)
├── public/
│   └── index.html     # Frontend dashboard (served at "/")
├── gamers.json        # Gamer data store
├── cabinets.json      # Cabinet data store
├── sessions.json      # Queue session data store
├── Design_Note.txt    # Original design specification
├── pyproject.toml     # uv project configuration
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Install dependencies

```bash
uv sync
```

If you are setting the project up from scratch:

```bash
uv add fastapi "uvicorn[standard]"
```

### 3. Run the server

```bash
uv run uvicorn main:app --reload
```

### 4. Open the app

| What                         | URL                              |
|------------------------------|----------------------------------|
| Frontend dashboard           | http://127.0.0.1:8000/           |
| Swagger UI (interactive API) | http://127.0.0.1:8000/docs       |
| ReDoc                        | http://127.0.0.1:8000/redoc      |

> The dashboard loads Tailwind CSS from a CDN, so you need an internet connection the first time you open it.

---

## 🖥️ Frontend Dashboard

The dashboard is a single file, `public/index.html`. FastAPI serves it at `/`, and it talks to the API with `fetch()`.

### How to use it

1. **Pick a role** from the *Active Role* dropdown at the top. The choice is sent as the `X-Role` header with every request.
2. **Enter a Gamer ID.** Gamers use this ID when joining queues and submitting scores.
3. Use the **Cabinet Floor** to interact with the arcade.

### Gamer view

| Action        | What it does                                                                   |
|---------------|--------------------------------------------------------------------------------|
| Queue Up 🎟️   | Joins the queue for a cabinet and deducts the cabinet's tokens (`POST /sessions`) |
| Submit Score 🏆 | Submits a score for a cabinet (`PATCH /cabinets/{id}/score`)                  |

### Floor Manager view

Switching to *Arcade Floor Manager* reveals the **Control Center**:

| Section                      | What it does                                                                       |
|------------------------------|------------------------------------------------------------------------------------|
| Lounge stats                 | Shows total token revenue, cabinet utilization and the top crown holder (`GET /stats`) |
| Add New Arcade Cabinet       | Creates a cabinet with status `operational` (`POST /cabinets`)                     |
| Cabinet status / delete      | Changes a cabinet's status or removes it (`PATCH` / `DELETE /cabinets/{id}`)       |
| Gamer Accounts               | Loads all gamers, edits token and ticket balances, deletes gamers (`/gamers`)      |

### Pointing the frontend at a different server

The API address is set at the top of the script in `index.html`:

```js
const API_URL = "http://127.0.0.1:8000";
```

Change it if you deploy the backend somewhere else.

---

## 🔐 Authentication & Roles

There is no login. The role is sent in the **`X-Role`** request header (the dashboard sets this for you).

| Role value           | Description          |
|----------------------|----------------------|
| `gamer`              | Regular arcade gamer |
| `arcadefloormanager` | Arcade floor manager |

- Missing header → `401 Unauthorized`
- Role not permitted for the endpoint → `403 Forbidden`

```bash
curl -H "X-Role: arcadefloormanager" http://127.0.0.1:8000/gamers
```

### Permission Matrix

| Endpoint Category      | Gamer | Manager |
|------------------------|:-----:|:-------:|
| View Cabinets          | ✅    | ✅      |
| View Gamer Profile     | ✅    | ✅      |
| Create Cabinet         | ❌    | ✅      |
| Update Cabinet         | ❌    | ✅      |
| Create Gamer           | ❌    | ✅      |
| Join Queue             | ✅    | ✅      |
| Change Queue Status    | ❌    | ✅      |
| View Lounge Statistics | ❌    | ✅      |

---

## 🗂️ Data Models

### Arcade Cabinet
| Field                  | Type        | Notes                                          |
|------------------------|-------------|------------------------------------------------|
| `id`                   | int         | Auto-generated                                 |
| `game_title`           | string      | 2–100 chars, unique (case-insensitive)         |
| `genre`                | string      | 2–50 chars                                     |
| `tokens_per_play`      | int         | ≥ 0                                            |
| `status`               | enum        | `operational`, `in_use`, `maintenance`         |
| `high_score`           | int         | Starts at 0                                    |
| `high_score_holder_id` | int \| null | Gamer who holds the high score                 |

### Gamer Profile
| Field                 | Type   | Notes                          |
|-----------------------|--------|--------------------------------|
| `id`                  | int    | Auto-generated                 |
| `name`                | string | 2–50 chars, unique             |
| `token_balance`       | int    | ≥ 0                            |
| `tickets_won_balance` | int    | ≥ 0                            |
| `account_tier`        | enum   | `rookie`, `elite`              |

### Game Session Queue (linking model)
| Field             | Type | Notes                                                    |
|-------------------|------|----------------------------------------------------------|
| `id`              | int  | Auto-generated                                           |
| `cabinet_id`      | int  | References a cabinet                                     |
| `gamer_id`        | int  | References a gamer                                       |
| `tokens_deducted` | int  | Tokens charged when joining                              |
| `status`          | enum | `queued`, `playing`, `completed`, `abandoned`            |

### Relationships

```
GamerProfile ──(gamer_id)──▶ GameSessionQueue ◀──(cabinet_id)── ArcadeCabinet
```

---

## 📜 Business Rules

| # | Rule | Response |
|---|------|----------|
| 1 | A gamer must have enough tokens to join a queue | `409 Conflict` – "Insufficient balance of tokens" |
| 2 | A gamer may have only **one** active session (`queued` or `playing`), which prevents queue hoarding | `409 Conflict` |
| 3 | A high score can be updated only if the new score is strictly greater than the current one | `409 Conflict` |
| 4 | A cabinet under maintenance cannot be joined | `409 Conflict` |
| 5 | A queued session can move to `playing` only if the cabinet is `operational` | `409 Conflict` |

Beating a high score rewards the gamer with **50 tickets** (`DEFAULT_TICKET_REWARD`).

---

## 🔌 API Endpoints

### System
| Method | Path      | Role   |
|--------|-----------|--------|
| GET    | `/`       | Anyone (serves the dashboard) |
| GET    | `/health` | Anyone |

### Gamers
| Method | Path           | Role            |
|--------|----------------|-----------------|
| POST   | `/gamers`      | Manager         |
| GET    | `/gamers`      | Manager         |
| GET    | `/gamers/{id}` | Gamer, Manager  |
| PATCH  | `/gamers/{id}` | Manager         |
| DELETE | `/gamers/{id}` | Manager         |

### Cabinets
| Method | Path              | Role    |
|--------|-------------------|---------|
| POST   | `/cabinets`       | Manager |
| GET    | `/cabinets`       | Anyone  |
| GET    | `/cabinets/{id}`  | Anyone  |
| PATCH  | `/cabinets/{id}`  | Manager |
| DELETE | `/cabinets/{id}`  | Manager |

### Queue Sessions
| Method | Path                    | Role            |
|--------|-------------------------|-----------------|
| POST   | `/sessions`             | Gamer, Manager  |
| GET    | `/sessions`             | Manager         |
| GET    | `/sessions/{id}`        | Manager         |
| PATCH  | `/sessions/{id}/status` | Manager         |
| DELETE | `/sessions/{id}`        | Manager         |

### High Scores
| Method | Path                     | Role   |
|--------|--------------------------|--------|
| PATCH  | `/cabinets/{id}/score`   | Gamer  |

### Reports
| Method | Path     | Role    |
|--------|----------|---------|
| GET    | `/stats` | Manager |

---

## 📊 Stats Endpoint

`GET /stats` (Manager only) returns:

```json
{
  "total_token_revenue": 20,
  "cabinet_utilization_percentage": 0.0,
  "most_crowns_gamer_id": 1,
  "active_crowns_count": 1
}
```

- **Total token revenue:** sum of `tokens_deducted` across all sessions
- **Cabinet utilization:** percentage of cabinets with status `in_use`
- **Most crowns:** the gamer holding the most cabinet high scores

---

## 🧪 Example Requests

**Health check**
```bash
curl http://127.0.0.1:8000/health
```

**Create a gamer (manager)**
```bash
curl -X POST http://127.0.0.1:8000/gamers \
  -H "Content-Type: application/json" \
  -H "X-Role: arcadefloormanager" \
  -d '{"name": "Riley", "token_balance": 100, "tickets_won_balance": 0, "account_tier": "rookie"}'
```

**Create a cabinet (manager)**
```bash
curl -X POST http://127.0.0.1:8000/cabinets \
  -H "Content-Type: application/json" \
  -H "X-Role: arcadefloormanager" \
  -d '{"game_title": "Donkey Kong", "genre": "Platformer", "tokens_per_play": 10, "status": "operational"}'
```

**Join a queue**
```bash
curl -X POST http://127.0.0.1:8000/sessions \
  -H "Content-Type: application/json" \
  -H "X-Role: gamer" \
  -d '{"cabinet_id": 1, "gamer_id": 2}'
```

**Start a session (manager)**
```bash
curl -X PATCH http://127.0.0.1:8000/sessions/1/status \
  -H "Content-Type: application/json" \
  -H "X-Role: arcadefloormanager" \
  -d '{"status": "playing"}'
```

**Submit a high score**
```bash
curl -X PATCH http://127.0.0.1:8000/cabinets/1/score \
  -H "Content-Type: application/json" \
  -H "X-Role: gamer" \
  -d '{"score": 16000, "gamer_id": 2}'
```

---

## ✅ Basic Test Checklist

| #  | Request                                       | Expected |
|----|-----------------------------------------------|----------|
| 1  | `GET /health`                                 | 200      |
| 2  | `POST /gamers` as manager                     | 201      |
| 3  | `POST /cabinets` as manager                   | 201      |
| 4  | `GET /cabinets`                               | 200      |
| 5  | `POST /sessions` with sufficient tokens       | 201      |
| 6  | `POST /sessions` without enough tokens        | 409      |
| 7  | `POST /sessions` when an active session exists| 409      |
| 8  | `PATCH /sessions/{id}/status` to `playing`    | 200      |
| 9  | `PATCH /cabinets/{id}/score` with lower score | 409      |
| 10 | `PATCH /cabinets/{id}/score` with higher score| 200      |

---

## 🗃️ Seed Data

The repository includes sample data:

- **Gamers:** Alex (elite), Jordan (rookie), Sam (rookie)
- **Cabinets:** Pac-Man, Street Fighter II, Galaga
- **Sessions:** two queued sessions

Edit or delete the JSON files to reset the data.

---

## 📌 Notes

- JSON file storage is fine for learning and demos but is not safe for concurrent production use.
- Roles are header-based and are **not** real authentication.

## 📄 License

This project is for educational purposes.