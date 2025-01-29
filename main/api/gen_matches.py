import csv
import random
from api.config import get_db_connection

async def add_teams_db():
    with open("db_teams.csv", "r") as file:
        csvreader = csv.reader(file)
        all_teams = []
        for row in file:
            if (row != "\n"):
                lst = row.split(',')
                all_teams.append(lst)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            INSERT INTO teams (team, power, results, coeff, normalized)
            VALUES (%s, %s, %s, %s, %s)
        """
        for team in all_teams:
            cursor.execute(query, (team[0], float(team[1]), int(team[2]), int(team[3]), float(team[4])))
            conn.commit()
    return

def set_coeff(norm1 : float, norm2 : float):

    win = round((norm1 + norm2 + 0.1) / norm1, 2)
    lose = round((norm1 + norm2 - 0.1) / norm2, 2)
    if (abs(win - lose) < 0.3):
        draw = round(1 / (0.33 + round(random.uniform(0.05, 0.12), 2)), 2)
    else:
        draw = round((abs(1 - win - lose)), 2)

    tb2 = 2.0 + round(random.uniform(-0.1, 0.1), 2)
    tm2 = round(1 / (1 - 1 / tb2), 2)
    return [win, draw, lose, tb2, tm2]

def gen_events():
    teams_id = [x for x in range(1, 21)]

    random.shuffle(teams_id)

    matches = [(teams_id[i], teams_id[i+1]) for i in range(0, len(teams_id), 2)]

    return matches

def gen_results(teams, coeffs):
    goal1, goal2 = 0, 0
    ver1 = round(1 / coeffs[0], 2)
    verx = round(1 / coeffs[1], 2)
    ver2 = round(1 / coeffs[2], 2)
    vertb = round(1 / coeffs[3], 2)
    vertm = round(1 / coeffs[4], 2)

    goal1, goal2 = 0, 0
    if (ver1 - ver2 > 0.4):
        goal1 += round(5 * (ver1 - ver2))
        ost = 2.5 - goal1
        if (vertb + round(random.uniform(-0.15, 0.15), 2) > vertm + round(random.uniform(-0.15, 0.15), 2)):
            goal2 += round(ost + 1 * random.choice([1, 0]))
        else:
            goal2 += round(1 * random.choice([1, 0, -1]))
    elif (ver1 - ver2 > 0 and ver1 - ver2 < 0.4):
        goal1 += round(10 * (ver1 - ver2))
        ost = 2.5 - goal1
        goal2 += round(round(ost) - 1 * random.uniform(-0.5, 0.5))
    res_match = [teams[0][0], goal1, teams[1][0], goal2]
    return res_match

async def set_events(matches: tuple):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT team
            FROM teams
            WHERE id = %s OR id = %s
        """
        query1 = """
            INSERT INTO events (league, team1, team2, match_status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
        
        query2 = """
                SELECT normalized
                FROM teams
                WHERE id = %s OR id = %s
            """
        
        query3 = """
            INSERT INTO market (event_id, market_name, coeff_val)
            VALUES (%s, %s, %s)
        """

        query4 = """
            INSERT INTO results (event_id, goal1, goal2)
            VALUES (%s, %s, %s)
        """
        
        for pair in matches:
            cursor.execute(query, (pair[0], pair[1]))
            teams = cursor.fetchall()

            cursor.execute(query1, ("Англия", teams[0][0], teams[1][0], 1))
            event_id = cursor.fetchone()[0]
            
            cursor.execute(query2, (pair[0], pair[1]))
            norms = cursor.fetchall()
            
            coeffs = set_coeff(float(norms[0][0]), float(norms[1][0]))

            cursor.executemany(query3, [
            (event_id, "П1", coeffs[0]),
            (event_id, "Х", coeffs[1]),
            (event_id, "П2", coeffs[2]),
            (event_id, "ТБ2_5", coeffs[3]),
            (event_id, "ТМ2_5", coeffs[4])
            ])

            res = (gen_results(teams, coeffs))
            cursor.execute(query4, (event_id, res[1], res[3]))

        conn.commit()