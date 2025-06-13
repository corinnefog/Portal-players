import os
import pandas as pd
import pymysql
from sqlalchemy import create_engine

db_config = {
    'host': 'tomsox.clswuu2wk825.us-east-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Tomsoxsummer25!',
    'database': 'Conferences',
    'port': 3306
}

parent_directory = '/Users/corinnefogarty/Conferences/05_06/05/01'

engine_str = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
engine = create_engine(engine_str)

for root, dirs, files in os.walk(parent_directory):
    for file in files:
        if file.lower().endswith('.csv'):
            csv_path = os.path.join(root, file)
            table_name = os.path.splitext(file)[0].lower().replace(' ', '_')
            try:
                print(f"Uploading {csv_path}...")
                df = pd.read_csv(csv_path, encoding='utf-8')  # Try adding encoding if needed
                df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
                print(f"✅ Successfully uploaded {file} as table `{table_name}`")
            except Exception as e:
                print(f"❌ Error uploading {file}: {e}")
