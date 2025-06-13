import os
import csv
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

db_config = {
    'host': 'tomsox.clswuu2wk825.us-east-2.rds.amazonaws.com',  
    'user': 'admin',  
    'password': 'Tomsoxsummer25!',
    'database': 'Conferences'
}

connection = mysql.connector.connect(**db_config)

engine = create_engine(f'mysql+mysqlconnector://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}/{db_config["database"]}')

folder_path = "/Users/corinnefogarty/Downloads/Conferences/Conferences/05_06/Combined/10"

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        
        df = pd.read_csv(file_path, low_memory=False, on_bad_lines='skip', quoting=csv.QUOTE_NONE)
        
        table_name = os.path.splitext(filename)[0]
        
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Uploaded {filename} to the database.")

connection.close()


