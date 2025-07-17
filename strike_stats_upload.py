import pandas as pd
import sqlite3
import os

DB_PATH = 'portalplayers.db'
CSV_FOLDER = os.path.expanduser('~/Downloads/Tomsox Data/Merged')

strike_results = ['Strike-Take', 'Swing & Miss', 'Foul Ball', 'BIP', 'Strike Bunt']

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS strike_stats_game (
    Date TEXT,
    Pitcher TEXT,
    total_pitches INTEGER,
    strikes INTEGER,
    strike_pct REAL,
    PRIMARY KEY (Date, Pitcher)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS strike_stats_overall (
    Pitcher TEXT PRIMARY KEY,
    total_pitches INTEGER,
    strikes INTEGER,
    first_pitch_total INTEGER,
    first_pitch_strikes INTEGER,
    strike_pct REAL,
    first_strike_pct REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS strike_stats_pitch_type_overall (
    Pitcher TEXT,
    Pitch TEXT,
    total_pitches INTEGER,
    strikes INTEGER,
    strike_pct REAL,
    PRIMARY KEY (Pitcher, Pitch)
)   
''')

# Need for season totals later
all_data = []

for filename in os.listdir(CSV_FOLDER):
    if filename.endswith('.csv'):
        filepath = os.path.join(CSV_FOLDER, filename)
        df = pd.read_csv(filepath)

        required_cols = {'SB', 'Balls', 'Strikes', 'P_num', 'Pitcher', 'Date'}
        if not required_cols.issubset(df.columns):
            continue

        df['is_strike'] = df['SB'].isin(strike_results)

       
        grouped = df.groupby(['Date', 'Pitcher']).agg(
            total_pitches=('P_num', 'count'),
            strikes=('is_strike', 'sum'),
        ).reset_index()

        grouped['strike_pct'] = 100 * grouped['strikes'] / grouped['total_pitches']
        grouped = grouped.round(1)

        for _, row in grouped.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO strike_stats_game (
                    Date, Pitcher, total_pitches, strikes,
                    strike_pct
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                row['Date'], row['Pitcher'],
                int(row['total_pitches']), int(row['strikes']),
                float(row['strike_pct'])
            ))
  
        all_data.append(df)

# Calculate season totals
if all_data:
    all_df = pd.concat(all_data)

    all_df['is_strike'] = all_df['SB'].isin(strike_results)
    first_pitches = all_df[all_df['P_num'] == 1]
    first_pitch_total = first_pitches.groupby('Pitcher').size().astype(int)
    first_pitch_strikes = first_pitches[first_pitches['SB'].isin(strike_results)].groupby('Pitcher').size().astype(int)

    if 'Pitch' in all_df.columns:
        season = all_df.groupby(['Pitcher', 'Pitch']).agg(
            total_pitches=('P_num', 'count'),
            strikes=('is_strike', 'sum')
        ).reset_index()
            
        season['strike_pct'] = 100 * season['strikes'] / season['total_pitches']
        season = season.round(1)
        
        for _, row in season.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO strike_stats_pitch_type_overall (
                    Pitcher, Pitch, total_pitches, strikes, strike_pct
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                row['Pitcher'], row['Pitch'],
                int(row['total_pitches']), int(row['strikes']), float(row['strike_pct'])
            ))

    overall = all_df.groupby('Pitcher').agg(
        total_pitches=('P_num', 'count'),
        strikes=('is_strike', 'sum')
    ).reset_index()

    overall['first_pitch_total'] = overall['Pitcher'].map(first_pitch_total).fillna(0).astype(int)
    overall['first_pitch_strikes'] = overall['Pitcher'].map(first_pitch_strikes).fillna(0).astype(int)
    overall['strike_pct'] = 100 * overall['strikes'] / overall['total_pitches']
    overall['first_strike_pct'] = overall.apply(
        lambda row: 100 * row['first_pitch_strikes'] / row['first_pitch_total']
        if row['first_pitch_total'] > 0 else 0,
        axis=1
    )
    overall = overall.round(1)

    for _, row in overall.iterrows():
        cursor.execute('''
            INSERT OR REPLACE INTO strike_stats_overall (
                Pitcher, total_pitches, strikes,
                first_pitch_total, first_pitch_strikes,
                strike_pct, first_strike_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['Pitcher'],
            int(row['total_pitches']),
            int(row['strikes']),
            int(row['first_pitch_total']),
            int(row['first_pitch_strikes']),
	    float(row['strike_pct']),
            float(row['first_strike_pct'])
        ))

conn.commit()
conn.close()
print("Strike stats uploaded")

