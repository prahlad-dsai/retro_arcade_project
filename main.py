import os
import json
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
app = FastAPI(title="Retro-Arcade Management Network")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
DEFAULT_TICKET_REWARD = 50


GAMERS_FILE = "gamers.json"
CABINETS_FILE = "cabinets.json"
SESSIONS_FILE = "sessions.json"

def load_data(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception:
        return []
def save_data(filepath: str, data: list):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

gamers_db = load_data(GAMERS_FILE)
cabinets_db = load_data(CABINETS_FILE)
sessions_db = load_data(SESSIONS_FILE)

class GamerIn(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    token_balance: int = Field(ge=0)
    tickets_won_balance: int = Field(ge=0)
    account_tier: Literal["rookie", "elite"]
class GamerOut(GamerIn):
    id: int
class CabinetIn(BaseModel):
    game_title: str = Field(min_length=2, max_length=100)
    genre: str = Field(min_length=2, max_length=50)
    tokens_per_play: int = Field(ge=0)
    status: Literal["operational", "in_use", "maintenance"]
class CabinetOut(CabinetIn):
    id: int
    high_score: int
    high_score_holder_id: int | None
class SessionIn(BaseModel):
    cabinet_id: int = Field(ge=0)
    gamer_id: int = Field(gt=0)
class SessionOut(SessionIn):
    id: int
    cabinet_id: int
    gamer_id: int
    tokens_deducted: int
    status: Literal["queued", "playing","completed","abandoned"]
class StatusUpdateIn(BaseModel):
    status: Literal["queued", "playing", "completed", "abandoned"]
class ScoreUpdateIn(BaseModel):
    score: int = Field(ge=0)
    gamer_id: int = Field(ge=1)

def check_role(x_role: Optional[str], allowed_roles: List[str]):
    if not x_role or x_role not in allowed_roles:
        if not x_role:
            raise HTTPException(status_code=401, detail="Send the header X-role with a valid role.")
        raise HTTPException(status_code=403, detail=f"The role {x_role} is not allowed to do this.")
def next_id(db: list) -> int:
    if not db:
        return 1
    return max(item["id"] for item in db) + 1
def find_gamer(gamer_id: int) -> dict:
    for g in gamers_db:
        if g["id"] == gamer_id:
            return g
    raise HTTPException(status_code=404, detail=f"Gamer {gamer_id} not found")
def find_cabinet(cabinet_id: int) -> dict:
    for c in cabinets_db:
        if c["id"] == cabinet_id:
            return c
    raise HTTPException(status_code=404, detail=f"Cainet {cabinet_id} not found")
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/gamers", response_model=GamerOut, status_code=201)
def create_gamer(payload: GamerIn, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])

    for g in gamers_db:
        if g["name"].lower() == payload.name.lower():
            raise HTTPException(status_code=409, detail="A gamer with this name already exists")
    new_gamer = {
        "id": next_id(gamers_db),
        "name": payload.name,
        "token_balance": payload.token_balance,
        "tickets_won_balance": payload.tickets_won_balance,
        "account_tier": payload.account_tier
    }
    gamers_db.append(new_gamer)
    save_data(GAMERS_FILE, gamers_db)
    return new_gamer
@app.get("/gamers", response_model=List[GamerOut])
def list_gamer(x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    return gamers_db
@app.get("/gamers/{id}", response_model=GamerOut)
def get_gamer(id: int, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["gamer", "arcadefloormanager"])
    return find_gamer(id)
@app.patch("/gamers/{id}")
def update_gamer(id: int, payload: GamerIn, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    gamer = find_gamer(id)
    gamer["name"] = payload.name
    gamer["token_balance"] = payload.token_balance
    gamer["tickets_won balance"] = payload.tickets_won_balance
    gamer["account_tier"] = payload.account_tier

    save_data(GAMERS_FILE, gamers_db)
    return gamer
@app.delete("/gamers/{id}", status_code=204)
def delete_gamer(id: int, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    gamer = find_gamer(id)
    gamers_db.remove(gamer)
    save_data(GAMERS_FILE, gamers_db)
    return None
@app.post("/cabinets", response_model=CabinetOut, status_code=201)
def create_cabinet(payload: CabinetIn, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    for c in cabinets_db:
        if c["game_title"].lower() == payload.game_title.lower():
            raise HTTPException(status_code=409, detail="A cabinet with that name already exists")
    new_cabinet = {
        "id": next_id(cabinets_db),
        "game_title": payload.game_title,
        "genre": payload.genre,
        "tokens_per_play": payload.tokens_per_play,
        "status": payload.status,
        "high_score": 0,
        "high_score_holder": None
    }
    cabinets_db.append(new_cabinet)
    save_data(CABINETS_FILE, cabinets_db)
    return new_cabinet
@app.get("/cabinets", response_model=List[CabinetOut])
def list_cabinets():
    return cabinets_db
@app.get("/cabinets/{id}", response_model=CabinetOut)
def get_cabinet(id: int):
    return find_cabinet(id)
@app.patch("/cabinets/{id}", response_model=CabinetOut)
def update_cabinet(id: int,payload: CabinetIn, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    cabinet = find_cabinet(id)

    cabinet["game_title"] = payload.game_title
    cabinet["genre"] = payload.genre
    cabinet["tokens_per_play"] = payload.tokens_per_play
    cabinet["status"] = payload.status

    save_data(CABINETS_FILE, cabinets_db)
    return cabinet
@app.delete("/cabinets/{id}", status_code=204)
def delete_cabinet(id: int, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    cabinet = find_cabinet(id)
    cabinets_db.remove(cabinet)
    save_data(CABINETS_FILE, cabinets_db)
    return None
@app.post("/sessions", status_code=201)
def create_session(payload: SessionIn, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["gamer", "arcadefloormanager"])
    cabinet = find_cabinet(payload.cabinet_id)
    gamer = find_gamer(payload.gamer_id)
    if cabinet["status"] == "maintenance":
        raise HTTPException(status_code=409, detail="Cabinet is currently under maintenance")
    if gamer["token_balance"] < cabinet["tokens_per_play"]:
        raise HTTPException(status_code=409, detail="Insufficient balance of tokens")
    for s in sessions_db:
        if s["gamer_id"] == gamer["id"] and s["status"] in ["queued", "playing"]:
            raise HTTPException(status_code=409, detail="Gamer already has an active session")
    gamer["token_balance"] -= cabinet["tokens_per_play"]
    new_session = {
        "id": next_id(sessions_db),
        "cabinet_id": payload.cabinet_id,
        "gamer_id": payload.gamer_id,
        "tokens_deducted": cabinet["tokens_per_play"],
        "status": "queued"
    }
    sessions_db.append(new_session)
    save_data(SESSIONS_FILE, sessions_db)
    save_data(GAMERS_FILE, gamers_db)
    return new_session
@app.get("/sessions", response_model=List[SessionOut])
def list_sessions(x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    return sessions_db
@app.get("/sessions/{id}", response_model=SessionOut)
def get_sessions(id: int, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    for s in sessions_db:
        if s["id"] == id:
            return s
    raise HTTPException(status_code=404, detail=f"Session {id} not found")
@app.patch("/sessions/{id}/status", response_model=SessionOut)
def update_session(id: int, payload: StatusUpdateIn, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    session = None
    for s in sessions_db:
        if s["id"] == id:
            session = s
            break
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {id} not found")
    cabinet = find_cabinet(session["cabinet_id"])
    if payload.status == "playing" and cabinet["status"] != "operational":
        raise HTTPException(status_code=409, detail="Cabinet must be operational to start a session")
    session["status"] = payload.status
    save_data(SESSIONS_FILE, sessions_db)
    return session
@app.delete("/sessions/{id}", status_code=204)
def delete_session(id: int, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    session = None
    for s in sessions_db:
        if s["id"] == id:
            session = s
            break
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {id} not found")
    sessions_db.remove(session)
    save_data(SESSIONS_FILE, sessions_db)
    return None
@app.patch("/cabinets/{id}/score", response_model=CabinetOut)
def update_high_score(id: int, payload: ScoreUpdateIn, x_role: Optional[str] = Header(None)):
    check_role(x_role, ["gamer", "arcadefloormanager"])
    cabinet = find_cabinet(id)
    gamer = find_gamer(payload.gamer_id)
    if payload.score <= cabinet["high_score"]:
        raise HTTPException(status_code=409, detail="New score must strictly exceed the current high score")
    cabinet["high_score"] = payload.score
    cabinet["high_score_holder_id"] = gamer["id"]
    gamer["ticket_won_balance"] += DEFAULT_TICKET_REWARD
    save_data(CABINETS_FILE, cabinets_db)
    save_data(GAMERS_FILE, gamers_db)
    return cabinet
@app.get("/stats")
def get_lounge_stats(x_role: Optional[str] = Header(None)):
    check_role(x_role, ["arcadefloormanager"])
    total_token_revenue = sum(s.get("tokens_deducted", 0) for s in sessions_db)
    total_cabinets = len(cabinets_db)
    if total_cabinets > 0:
        in_use_count = sum(1 for c in cabinets_db if c["status"] == "in_use")
        utilization_percentage = (in_use_count/total_cabinets) * 100
    else:
        utilization_percentage = 0.0
    crown_counts = {}
    for c in cabinets_db:
        holder_id = c.get("high_score_holder_id")
        if holder_id is not None:
            crown_counts[holder_id] = crown_counts.get(holder_id, 0) + 1
    top_gamer_id = None
    max_crowns = 0
    if crown_counts:
        top_gamer_id = max(crown_counts, key=crown_counts.get)
        max_crowns = crown_counts[top_gamer_id]
    return {
        "total_token_revenue": total_token_revenue,
        "cabinet_utilization_percentage": round(utilization_percentage, 2),
        "most_crowns_gamer_id": top_gamer_id,
        "active_crowns_count": max_crowns
    }
app.mount("/", StaticFiles(directory="public", html=True), name="public")