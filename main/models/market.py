from pydantic import BaseModel

class MarketCreate(BaseModel):
    event_id: int
    market_name: str
    result: str

class MarketResponse():
    id: int
    result: str
    
