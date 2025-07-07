import pandas as pd
import sqlite3

df = pd.read_csv('~/Downloads/Tomsox Data/Game Averages.csv')
conn = sqlite3.connect('portalplayers.db')
df.to_sql('averages', conn, if_exists='replace', index=False) 
conn.close()
print("Averages uploaded")
