from fastapi import FastAPI, Request, Form, HTTPException, APIRouter, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from passlib.context import CryptContext

from models.users import UserCreate, UserResponse
from models.jwt_token import Token
from jose import jwt, JWTError
from token_settings import SECRET_KEY, ALGORITHM
from token_settings import create_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from api.config import templates, get_db_connection
from api.gen_matches import add_teams_db, set_coeff, set_events, gen_events

router = APIRouter()

def get_current_user(request: Request):
    # Извлекаем токен из cookies
    token = request.cookies.get("access_token")
   
    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

    # Убираем префикс "Bearer " из токена, если он есть
    token = token.replace("Bearer ", "")

    try:
        # Проверяем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        user_id: int = payload.get("id")
        # balance: int = payload.get("balance")
        
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid token")

        return [username, user_id]  # Возвращаем пользователя или его данные

    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

@router.get("/main", response_class=HTMLResponse)
async def main_page(request: Request):
    try:
        user_data = get_current_user(request)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT username, balance FROM users WHERE username = %s;
            """

            cursor.execute(query, (user_data[0], ))
            res = cursor.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="User not found")
            username, balance = res
            # balance = int(balance)
            
            user = {
                "username": username,
                "balance": balance
            }

            query = """
                SELECT 
                events.id AS event_id,
                events.league,
                events.team1,
                events.team2,
                string_agg(market.market_name || ':' || market.coeff_val, ', ') AS markets_and_coeffs
                FROM 
                    events
                JOIN 
                    market 
                ON 
                    events.id = market.event_id
                WHERE events.match_status = 1
                GROUP BY 
                    events.id, events.league, events.team1, events.team2;
                
            """
            cursor.execute(query, )
            res = cursor.fetchall()
            matches = []
            for item in res:
                id, league, team1, team2, odds = item[0], item[1], item[2], item[3], item[4]
                list_odds = odds.replace(' ', '').split(',')
                for i in range(len(list_odds)):
                    list_odds[i] = list(list_odds[i].split(':'))
                game_data = {
                    "event_id" : id,
                    "league" : league,
                    "team1" : team1,
                    "team2" : team2
                }
                for i in range(len(list_odds)):
                    game_data[list_odds[i][0]] = list_odds[i][1]
                matches.append(game_data)

            query = """
                    SELECT events.team1, events.team2, market.market_name, bets.sum
                    FROM bets
                    LEFT JOIN market ON bets.market_id = market.id
                    LEFT JOIN events ON bets.event_id = events.id
                    WHERE bets.user_id = %s and bets.bet_status = 0
                """
            cursor.execute(query, (user_data[1], ))
            current_bets = cursor.fetchall()

            query = """
                    SELECT events.team1, events.team2, market.market_name, bets.sum, bets.bet_result
                    FROM bets
                    LEFT JOIN market ON bets.market_id = market.id
                    LEFT JOIN events ON bets.event_id = events.id
                    WHERE bets.user_id = %s and bets.bet_status = 1
                """
            cursor.execute(query, (user_data[1], ))
            stored_bets = cursor.fetchall()
            
            return templates.TemplateResponse("main.html", {"request": request, "user_data": user, "matches" : matches, "current_bets" : current_bets, "stored_bets" : stored_bets})
    
    except:
        return HTTPException(status_code=404, detail="User not found")

@router.post("/add_bet")
async def add_bet(request: Request, event_id: int = Form(...), market: str = Form(...), sum: int = Form(...)):
    bet_status, bet_result = 0, 0
    try:
        user = get_current_user(request)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id
                FROM market
                WHERE event_id = %s and market_name = %s
            """
            cursor.execute(query, (event_id, market, ))
            market_id = cursor.fetchone()[0]
            query = """
                SELECT balance FROM users WHERE id = %s
            """
            cursor.execute(query, (user[1],))
            balance = int(cursor.fetchone()[0])
            if (balance >= sum):
                query = """
                    INSERT INTO bets (user_id, event_id, market_id, sum, bet_status, bet_result)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (user[1], event_id, market_id, sum, bet_status, bet_result))

                query = """
                    UPDATE users
                    SET balance = balance - %s
                    WHERE id = %s
                """
                cursor.execute(query, (sum, user[1], ))

            conn.commit()
            return RedirectResponse(url='/main', status_code=303)  
    except:
        return HTTPException(status_code=404, detail="Something went wrong")
    
@router.post("/add_balance")
async def add_balance(request: Request, added_balance: int = Form(...)):

    user = get_current_user(request)
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            UPDATE users
            SET balance = balance + %s
            WHERE id = %s
        """

        cursor.execute(query, (added_balance, user[1], ))
        conn.commit()

    return RedirectResponse(url='/main', status_code=303)

@router.get("/results", response_class=HTMLResponse)
async def get_results(request: Request, results=[]):
    return templates.TemplateResponse("results.html", {"request": request, "results": results})
