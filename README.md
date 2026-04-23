# Portal Players Dashboard

A Flask web app for baseball players to view their pitching and hitting stats, 
including velocity, spin rate, and strike percentage charts.

---

## Requirements

- Python 3.8+
- pip

Install dependencies:

```bash
pip install flask plotly werkzeug
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/corinnefog/Portal-players.git
cd Portal-players
```

### 2. Create the database

Run the following in a Python shell or script to create `portalplayers.db`:

```python
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('portalplayers.db')
c = conn.cursor()

# Pitcher users table
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
''')

# Hitter users table
c.execute('''
    CREATE TABLE IF NOT EXISTS hitting_users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
''')

# Add a pitcher user
c.execute('INSERT INTO users VALUES (?, ?)', 
    ('pitcher_username', generate_password_hash('your_password')))

# Add a hitter user
c.execute('INSERT INTO hitting_users VALUES (?, ?)', 
    ('hitter_username', generate_password_hash('your_password')))

conn.commit()
conn.close()
```

Replace `'pitcher_username'`, `'hitter_username'`, and `'your_password'` with 
real credentials. Repeat the INSERT lines for each player.

### 3. Create the stat tables

The app expects these tables in `portalplayers.db`:

**For pitchers:**
- `pitches` — raw game-by-game pitch data
- `averages` — game-by-game pitch averages
- `strike_stats_game` — per-game strike stats
- `strike_stats_overall` — season strike stats
- `strike_stats_pitch_type_overall` — strike stats by pitch type

**For hitters:**
- `hitting_stats` — season hitting stats

You can create and populate these by importing CSVs:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('portalplayers.db')

df = pd.read_csv('your_file.csv')
df.to_sql('table_name', conn, if_exists='append', index=False)

conn.close()
```

### 4. Expected CSV column names

**pitches:** `Date, P_num, Pitcher, Inning, Outs, LR, Pitch, SB, Result, RBalls, Strikes, pitch_ab, pitch_IP, COUNT, Velocity, Spin_Rate`

**averages:** `Date, Pitcher, FB_Velo_Avg, FB_Spin_Avg, CH_Velo_Avg, CH_Spin_Avg, SL_Velo_Avg, SL_Spin_Avg, CB_Velo_Avg, CB_Spin_Avg, SNK_Velo_Avg, SNK_Spin_Avg`

**strike_stats_game:** `Date, Pitcher, total_pitches, strikes, strike_pct`

**strike_stats_overall:** `Pitcher, total_pitches, strikes, first_pitch_total, first_pitch_strikes, strike_pct, first_strike_pct`

**strike_stats_pitch_type_overall:** `Pitcher, Pitch, total_pitches, strikes, strike_pct`

**hitting_stats:** `Hitter, AB, XBH%, SLG%, ISO, OPS, AVG, RBI, HR`

### 5. Set a secret key

In `app.py`, change the secret key to something unique and private:

```python
app.secret_key = 'your_secret_key_here'
```

### 6. Run the app

```bash
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

- Pitchers log in at `/login`
- Hitters log in at `/hitter_login`

---

## Notes

- Pitch types supported: `FB`, `SL`, `CH`, `CB`, `SNK`
- `strike_pct` and `first_strike_pct` should be stored as whole numbers (e.g. `63.2` not `0.632`)
- Pitcher usernames in the `users` table must match exactly the `Pitcher` 
  column values in the stat tables (case-sensitive)
- Same rule applies for hitters — `hitting_users` username must match `Hitter` column
- To set up secret key in app.py use this line to set up an environment variable on your local computer export ```SECRET_KEY='some_long_random_string_here'```
