from fastapi import FastAPI, Request, Form, HTTPException, APIRouter, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from passlib.context import CryptContext

from models.users import UserCreate, UserResponse
from models.jwt_token import Token
from jose import jwt
from token_settings import SECRET_KEY, ALGORITHM
from token_settings import create_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from api.config import templates, get_db_connection

router = APIRouter()

def hash_password(password: str) -> str:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

@router.post("/register")
async def register_user(request: Request, reglogin: str = Form(...), email: str = Form(...), regpassword: str = Form(...)):
    role_id, balance = 2, 0
    hashed_password = hash_password(regpassword)

    if (reglogin.split('.')[0] == 'admin'):
        role_id = 1
    
    user = UserCreate(username=reglogin, email=email, hashed_password=hashed_password, role_id=role_id, balance=balance)

    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO users (username, email, hashed_password, role_id, balance)
                VALUES (%s, %s, %s, %s, %s)
                """
            cursor.execute(query, (user.username, user.email, user.hashed_password, role_id, balance))
            conn.commit()
        
    response = RedirectResponse(url="/", status_code=303)
    return response

@router.post("/login", response_model= Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):

    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            query = """
                SELECT id, hashed_password, role_id FROM users WHERE username = %s
                """
            cursor.execute(query, (form_data.username, ))
            res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=401, detail="Wrong login or password")

    user_id, hashed_password, role_id = res

    token = create_access_token({"id": user_id, "username": form_data.username, "role": role_id})

    # print(f"Generated token: {token}")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not pwd_context.verify(form_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="Wrong login or password")

    response = RedirectResponse(url="/main" if role_id == 2 else "/admin", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response
