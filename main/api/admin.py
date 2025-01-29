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
from api.gen_matches import add_teams_db, gen_events, set_events, gen_results, set_coeff
from api.pages import get_results

router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
    

@router.post("/admin")
async def add_match(request: Request, league: str = Form(...), team1: str = Form(...), team2: str = Form(...), odds1: str = Form(...), 
                     oddsX: str = Form(...), odds2: str = Form(...), oddsOver25: str = Form(...), oddsUnder25: str = Form(...)):
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
                INSERT INTO events (league, team1, team2, match_status)
                VALUES (%s, %s, %s, %s)
                RETURNING id
        """
        cursor.execute(query, (league, team1, team2, 1))
        event_id = cursor.fetchone()[0]

        query = """
                INSERT INTO market (event_id, market_name, coeff_val)
                VALUES (%s, %s, %s)
        """
        cursor.executemany(query, [
            (event_id, "П1", odds1),
            (event_id, "Х", oddsX),
            (event_id, "П2", odds2),
            (event_id, "ТБ2_5", oddsOver25),
            (event_id, "ТМ2_5", oddsUnder25)
        ])
        conn.commit()
    
    return templates.TemplateResponse("admin.html", {"request": request})

@router.post("/add_teams", response_class=HTMLResponse)
async def add_teams(request: Request):
    await add_teams_db()
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/add_tour", response_class=HTMLResponse)
async def add_tour(request: Request):
    await set_events(gen_events())
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/add_results", response_class=HTMLResponse)
async def add_results(request: Request):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT events.team1, events.team2, results.goal1, results.goal2
            FROM events
            LEFT JOIN results ON events.id = results.event_id
        """
        cursor.execute(query, ())
        results = cursor.fetchall()

        query = """
            UPDATE events
            SET match_status = 0
        """
        cursor.execute(query, ())


        query = """
            SELECT bets.user_id, bets.event_id, bets.market_id, bets.sum, market.market_name, market.coeff_val, results.goal1, results.goal2
            FROM bets
            LEFT JOIN market ON bets.market_id = market.id
            LEFT JOIN results ON bets.event_id = results.event_id
            WHERE bet_status = 0
        """
        cursor.execute(query, ())
        all_bets = cursor.fetchall()

        query = """
            UPDATE users
            SET balance = balance + %s
            WHERE id = %s
        """
        query2 = """
            UPDATE bets
            SET bet_result = 1
            WHERE user_id = %s AND market_id = %s
        """

        for bet in all_bets:
            if (bet[4] == 'П1'):
                if (bet[6] > bet[7]):
                    cursor.execute(query, (bet[5] * bet[3], bet[0]))
                    cursor.execute(query2, (bet[0], bet[2]))
                else:
                    cursor.execute(query, (0, bet[0]))
            elif (bet[4] == 'Х'):
                if (bet[6] == bet[7]):
                    cursor.execute(query, (bet[5] * bet[3], bet[0]))
                    cursor.execute(query2, (bet[0], bet[2]))
                else:
                    cursor.execute(query, (0, bet[0]))
            elif (bet[4] == 'П2'):
                if (bet[6] < bet[7]):
                    cursor.execute(query, (bet[5] * bet[3], bet[0]))
                    cursor.execute(query2, (bet[0], bet[2]))
                else:
                    cursor.execute(query, (0, bet[0]))
            elif (bet[4] == 'ТБ2_5'):
                if (int(bet[6]) + int(bet[7]) > 2.5):
                    cursor.execute(query, (bet[5] * bet[3], bet[0]))
                    cursor.execute(query2, (bet[0], bet[2]))
                else:
                    cursor.execute(query, (0, bet[0]))
            else:
                if (int(bet[6]) + int(bet[7]) < 2.5):
                    cursor.execute(query, (bet[5] * bet[3], bet[0]))
                    cursor.execute(query2, (bet[0], bet[2]))
                else:
                    cursor.execute(query, (0, bet[0]))
                    
        query = """
            UPDATE bets
            SET bet_status = 1
        """
        cursor.execute(query, ())

        conn.commit()
    return await get_results(request, results)
