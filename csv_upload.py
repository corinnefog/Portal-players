import pandas as pd
import sqlite3
import os

csv_path = os.path.expanduser("~/Downloads/Tomsox Data/TomSox 6-27-2025_Eldridge.csv")

# Load as CSV, not Excel
df = pd.read_csv(csv_path, encoding='latin1', engine='python', on_bad_lines='skip')

df.columns = df.columns.str.strip().str.replace(r'\W+', '_', regex=True)

# Connect to (or create) the SQLite database
conn = sqlite3.connect('portalplayers.db')
cursor = conn.cursor()

df.to_sql('pitches', conn, if_exists='append', index=False)
print("CSV loaded into SQLite table 'pitches'")

conn.commit()
conn.close()
