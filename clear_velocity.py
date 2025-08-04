import sqlite3

DB_PATH = 'portalplayers.db'

dates_to_clear = ['2025-07-05', '2025-07-06', '2025-07-07', '2025-07-08', '2025-07-10', '2025-7-12', '2025-07-17', '2025-07-18' ]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

placeholders = ', '.join(['?'] * len(dates_to_clear))

query = f"""
    UPDATE pitches
    SET Velocity = NULL
    WHERE Date IN ({placeholders})
"""
cursor.execute(query, dates_to_clear)

conn.commit()
conn.close()

