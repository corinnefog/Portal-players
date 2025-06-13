import pandas as pd
import glob
import os


folder_path = '/Users/corinnefogarty/Downloads/Conferences/Conferences/05_06/Grouped/GWBush'


csv_files = glob.glob(os.path.join(folder_path, '*HWBush*.csv'))  

combined_df = pd.concat((pd.read_csv(file) for file in csv_files), ignore_index=True)

output_path = '/Users/corinnefogarty/Downloads/Conferences/Conferences/05_06/Combined/georgebushcombined.csv'
combined_df.to_csv(output_path, index=False)

print(f"Combined {len(csv_files)} files and saved to: {output_path}")
