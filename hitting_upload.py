import pandas as pd
import sqlite3

df = pd.read_csv('~/Downloads/Tomsox Data/Hitting.csv')
conn = sqlite3.connect('portalplayers.db')
df.to_sql('hitting_stats', conn, if_exists='replace', index=False)
conn.close()
print("Hitting uploaded")
