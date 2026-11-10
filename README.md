# Retro-Arcade Smart-Token & Cabinet Management Network

A high-tech retro arcade lounge API designed to manage player token balances, virtual game session queues, cabinet statuses, high-score tracking, and lounge statistics.

---

## 1. Domain Overview & Roles

### Roles
* **`gamer`**: Can view arcade cabinets, view their own gamer profile, join session queues, play games, and submit high scores.
* **`arcadefloormanager`**: Administrative role. Can create and manage gamer profiles, add and modify cabinets, manage queues, change machine operational statuses, and view lounge analytics.

---

## 2. Core Models

1. **`GamerProfile`**
   * `id` (int): Unique identifier.
   * `name` (str): Gamer name.
   * `token_balance` (int): Current count of tokens available to spend.
   * `tickets_won_balance` (int): Reward tickets earned by setting high scores.
   * `account_tier` (str): Account level (`rookie` or `elite`).

2. **`ArcadeCabinet`**
   * `id` (int): Unique identifier.
   * `game_title` (str): Name of the arcade game.
   * `genre` (str): Game genre.
   * `tokens_per_play` (int): Tokens required to queue up for a play.
   * `status` (str): Current machine state (`operational`, `in_use`, `maintenance`).
   * `high_score` (int): Current lounge high score.
   * `high_score_holder_id` (int | null): ID of the gamer holding the record.

3. **`GameSessionQueue`** (Linking Model)
   * `id` (int): Unique identifier.
   * `cabinet_id` (int): Links to an `ArcadeCabinet`.
   * `gamer_id` (int): Links to a `GamerProfile`.
   * `tokens_deducted` (int): Number of tokens deducted upon joining.
   * `status` (str): Session status (`queued` → `playing` → `completed` / `abandoned`).

---

## 3. System Rules & Enforcement

* **Rule 1 (Token Deduction Interlock):** A gamer cannot join a cabinet queue if their `token_balance` is less than `tokens_per_play`. Tokens are deducted immediately upon joining. *(Returns `409 Conflict`)*
* **Rule 2 (Anti-Camping Queue Cap):** A gamer can only occupy one active (`queued` or `playing`) session across the lounge at any given time. *(Returns `409 Conflict`)*
* **Rule 3 (The Crown Protection Rule):** A request to update a high score is rejected unless the submitted score strictly exceeds the current stored high score. On success, it swaps the `high_score_holder_id` and awards a ticket bonus. *(Returns `409 Conflict`)*
* **Rule 4 (Maintenance Protection):** A gamer cannot join a cabinet's queue if its status is set to `maintenance`. *(Returns `409 Conflict`)*
* **Rule 5 (Operational Transition Rule):** A session status can only transition to `playing` if the cabinet is currently `operational`. *(Returns `409 Conflict`)*

---

## 4. How to Run the Project

### Prerequisites
* Python 3.10+
* [uv](https://docs.astral.sh/uv/)

### Installation & Setup

1. **Clone the repository and enter the folder:**
   ```bash
   git clone https://github.com/prahlad-dsai/retro_arcade_project.git
   cd retro_arcade_project
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Start the server:**
   ```bash
   uv run uvicorn main:app --reload
   ```

4. **Access Interactive Docs:**
   Open your browser and visit: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

5. **Clean Start / Reset Data:**
   * Stop the server (`Ctrl+C`).
   * Restore the starter data:
     ```bash
     git restore gamers.json cabinets.json sessions.json
     ```
   * Restart the server.

## 5. Complete Test Checklist

Run these requests in order from a **clean start**. Pass `X-Role` in the HTTP headers as specified.

| # | Method & Path | Header `X-Role` | Request Body / Params | Expected Status | Description / Notes |
|---|---|---|---|---|---|
| **1** | `GET /health` | None | None | **200 OK** | Server availability check. |
| **2** | `GET /cabinets` | None | None | **200 OK** | Anyone can browse the arcade catalogue. |
| **3** | `GET /cabinets/1` | None | None | **200 OK** | Anyone can inspect a specific cabinet. |
| **4** | `GET /cabinets/99` | None | None | **404 Not Found** | Cabinet ID 99 does not exist. |
| **5** | `POST /gamers` | None | `{"name":"Racer", "token_balance":30, "tickets_won_balance":0, "account_tier":"rookie"}` | **401 Unauthorized** | Missing `X-Role` header. |
| **6** | `POST /gamers` | `gamer` | `{"name":"Racer", "token_balance":30, "tickets_won_balance":0, "account_tier":"rookie"}` | **403 Forbidden** | Gamers cannot create profiles. |
| **7** | `POST /gamers` | `arcadefloormanager` | `{"name":"A", "token_balance":30, "tickets_won_balance":0, "account_tier":"rookie"}` | **422 Unprocessable** | Name too short (min 2 chars). |
| **8** | `POST /gamers` | `arcadefloormanager` | `{"name":"RacerX", "token_balance":30, "tickets_won_balance":0, "account_tier":"rookie"}` | **201 Created** | Creates Gamer ID 4. |
| **9** | `POST /gamers` | `arcadefloormanager` | `{"name":"RacerX", "token_balance":50, "tickets_won_balance":0, "account_tier":"rookie"}` | **409 Conflict** | Duplicate gamer name prevented. |
| **10** | `GET /gamers` | `arcadefloormanager` | None | **200 OK** | Lists all gamers. |
| **11** | `GET /gamers/1` | `gamer` | None | **200 OK** | Gamer views their profile. |
| **12** | `PATCH /gamers/1` | `arcadefloormanager` | `{"name":"Alex", "token_balance":100, "tickets_won_balance":120, "account_tier":"elite"}` | **200 OK** | Manager updates token balance. |
| **13** | `DELETE /gamers/3` | `arcadefloormanager` | None | **204 No Content** | Manager deletes Gamer ID 3. |
| **14** | `POST /cabinets` | `arcadefloormanager` | `{"game_title":"Donkey Kong", "genre":"Platformer", "tokens_per_play":10, "status":"operational"}` | **201 Created** | Manager adds a new cabinet (ID 4). |
| **15** | `PATCH /cabinets/1` | `arcadefloormanager` | `{"game_title":"Pac-Man", "genre":"Maze", "tokens_per_play":10, "status":"maintenance"}` | **200 OK** | Changes cabinet status to maintenance. |
| **16** | `DELETE /cabinets/4` | `arcadefloormanager` | None | **204 No Content** | Deletes cabinet ID 4. |
| **17** | `POST /sessions` | `gamer` | `{"cabinet_id":1, "gamer_id":2}` | **409 Conflict** | **Rule 4:** Blocked because Cabinet 1 is in maintenance. |
| **18** | `PATCH /cabinets/1` | `arcadefloormanager` | `{"game_title":"Pac-Man", "genre":"Maze", "tokens_per_play":10, "status":"operational"}` | **200 OK** | Restore Cabinet 1 to operational. |
| **19** | `POST /sessions` | `gamer` | `{"cabinet_id":1, "gamer_id":2}` | **409 Conflict** | **Rule 1:** Jordan (ID 2) has only 5 tokens (needs 10). |
| **20** | `POST /sessions` | `gamer` | `{"cabinet_id":1, "gamer_id":1}` | **409 Conflict** | **Rule 2:** Alex (ID 1) already has an active queue session. |
| **21** | `POST /sessions` | `gamer` | `{"cabinet_id":2, "gamer_id":4}` | **201 Created** | RacerX (ID 4) joins queue; tokens deducted (30 → 15). |
| **22** | `GET /sessions` | `arcadefloormanager` | None | **200 OK** | Manager views active lounge sessions. |
| **23** | `GET /sessions/2` | `arcadefloormanager` | None | **200 OK** | Gets specific session details. |
| **24** | `PATCH /sessions/2/status` | `arcadefloormanager` | `{"status":"playing"}` | **200 OK** | Updates session status from queued to playing. |
| **25** | `PATCH /cabinets/2/score` | `gamer` | `{"score":5000, "gamer_id":4}` | **409 Conflict** | **Rule 3:** Score 5000 is lower than high score 8500. |
| **26** | `PATCH /cabinets/2/score` | `gamer` | `{"score":9999, "gamer_id":4}` | **200 OK** | **Rule 3:** Score beats record! High score updated, tickets awarded. |
| **27** | `PATCH /sessions/2/status` | `arcadefloormanager` | `{"status":"completed"}` | **200 OK** | Session completed. |
| **28** | `DELETE /sessions/2` | `arcadefloormanager` | None | **204 No Content** | Manager deletes session record. |
| **29** | `GET /stats` | `arcadefloormanager` | None | **200 OK** | Generates total revenue, utilization %, and crown holder summary. |
| **30** | Restart Server | N/A | Stop server (`Ctrl+C`), start again, run `GET /cabinets/2` | **200 OK** | **Persistence Check:** Data intact after restart without deleting JSON files. |