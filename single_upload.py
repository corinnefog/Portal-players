from sqlalchemy import create_engine
import pandas as pd

username = "admin"  
password = "Tomsoxsummer25!"  
host = "tomsox.clswuu2wk825.us-east-2.rds.amazonaws.com"  
port = "3306"  
database = "Conferences"

connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

engine = create_engine(connection_string)

df = pd.read_csv("/Users/corinnefogarty/Downloads/Conferences/Combined_CSV/combo_errors/bccombined copy2.csv")


df.to_sql('gtcombined', con=engine, if_exists='replace', index=False)


