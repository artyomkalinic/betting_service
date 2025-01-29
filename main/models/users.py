from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str 
    email: str
    hashed_password: str 
    role_id: int
    balance: int

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    balance: int
