import argparse
import pandas as pd
from datetime import datetime, timedelta

def parse_markers(csv_file):
    df = pd.read_csv(csv_file,sep='\s+',header=None,names=['date','time','value','trace'])
    df['time'] = df['date']+'T'+df['time'] # adjusting format
    df['time'] = pd.to_datetime(df['time'])
    return df

def parse_gpd_picks(csv_file):
    df = pd.read_csv(csv_file,sep='\s+',header=None,names=['code','station','wave','time'])
    df['time'] = pd.to_datetime(df['time'])
    return df

def find_matching_values(df1, df2, tolerance_seconds=3):
    # returns a list of matching values
    matching_values = []
    for _, row in df1.iterrows():
        time = row['time']
        matching_rows = df2[
            (df2['time'] >= time - timedelta(seconds=tolerance_seconds)) &
            (df2['time'] <= time + timedelta(seconds=tolerance_seconds))
        ]
        for _, matching_row in matching_rows.iterrows():
            matching_values.append((matching_row['time']))
    return matching_values

def main(file_1, file_2,output_file):
    df1 = parse_markers(file_1)
    df2 = parse_gpd_picks(file_2)
    matching_values = find_matching_values(df1, df2)
    #output = pd.DataFrame({'matching_values':matching_values})
    output = pd.DataFrame(matching_values)
    output.to_csv(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '-F1',
        type=str)
    parser.add_argument(
        '-F2',
        type=str)
    parser.add_argument(
        '-O',
        type=str)
    args = parser.parse_args()
        
    main(args.F1, args.F2, args.O)