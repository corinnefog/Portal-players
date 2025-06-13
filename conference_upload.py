import os
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

db_config = {
    'host': 'baseball.ccn6cuic2uah.us-east-1.rds.amazonaws.com',  
    'user': 'admin',  
    'password': 'Tomsoxsummer25!',
    'database': 'conferences'
}

connection = mysql.connector.connect(**db_config)

engine = create_engine(f'mysql+mysqlconnector://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}/{db_config["database"]}')

folder_path = "/Users/corinnefogarty/Downloads/Conferences/Conferences/ACC/Virginia/Combined"

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        
        df = pd.read_csv(file_path)
        
        table_name = os.path.splitext(filename)[0]
        
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Uploaded {filename} to the database.")

connection.close()

