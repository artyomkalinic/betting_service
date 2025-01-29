CREATE TABLE users (
    id SERIAL PRIMARY KEY, 
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(128) UNIQUE NOT NULL,
    role_id INTEGER NOT NULL,
    balance INTEGER NOT NULL
);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    league VARCHAR(50) NOT NULL,
    team1 VARCHAR(50) NOT NULL,
    team2 VARCHAR(50) NOT NULL,
    match_status INTEGER NOT NULL
);

CREATE TABLE market (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL,
    market_name VARCHAR NOT NULL,
    coeff_val DECIMAL(4, 2) NOT NULL
);

CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    market_id INTEGER NOT NULL,
    sum INTEGER NOT NULL,
    bet_status INTEGER NOT NULL,
    bet_result INTEGER NOT NULL
);

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    team VARCHAR NOT NULL,
    power DECIMAL(3, 2) NOT NULL,
    results INTEGER NOT NULL,
    coeff INTEGER NOT NULL,
    normalized DECIMAL(3, 2) NOT NULL
);

CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL,
    goal1 INTEGER NOT NULL,
    goal2 INTEGER NOT NULL
);

-- Связь между users и bets
ALTER TABLE bets
ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;

-- Связь между events и market
ALTER TABLE market
ADD CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE;

-- Связь между bets и market
ALTER TABLE bets
ADD CONSTRAINT fk_market_id FOREIGN KEY (market_id) REFERENCES market (id) ON DELETE CASCADE;

-- Связь между results и events
ALTER TABLE results
ADD CONSTRAINT fk_event_results FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE;
