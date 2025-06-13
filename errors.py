import pandas as pd
import os

folder_path = "/Users/corinnefogarty/Downloads/Conferences/Conferences/05_06/Combined/1"

for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(folder_path, filename)
        print(f"Reading {filename}...")
        try:
            df = pd.read_csv(file_path, low_memory=False)
            print(f"{filename} loaded successfully with {len(df)} rows.")
        except pd.errors.ParserError as e:
            print(f"ParserError in {filename}: {e}")
