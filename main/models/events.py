from pydantic import BaseModel

class EventCreate(BaseModel):
    league: str
    team1: str
    team2: str
    match_status: str

class EventResponse():
    id: int
    match_status: str
    