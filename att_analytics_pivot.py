import sqlite3
import pandas as pd

def export_data_to_csv(db_path, output_csv_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    # Query the database (modify the query as needed for your specific requirements)
    query = '''
    SELECT 
        DATE(datetime(timestamp/1000, 'unixepoch')) as Date,
        symbol,
        max(balance) as TotalBalance
    FROM 
        longs
    GROUP BY 
        Date, symbol
    '''
    # Load data into a DataFrame
    df = pd.read_sql_query(query, conn)

    # Pivot the DataFrame so that each symbol becomes a column
    pivot_df = df.pivot(index='Date', columns='symbol', values='TotalBalance')
    pivot_df = df.rename(columns={"Date":"date"})
    pivot_df.fillna(0, inplace=True)  # Fill missing values with 0
    
    for column in pivot_df.columns:
        # Mask to identify leading zeros
        mask = pivot_df[column] == 0
        # cumsum to create groups that ignore zeros after the first non-zero value
        cumsum = (~mask).cumsum()
        # Where groups are non-zero, replace zeros by forward fill
        pivot_df[column] = pivot_df[column].mask(mask).groupby(cumsum).ffill().fillna(0)
        pivot_df[column] = pivot_df[column].replace(0, pd.NA)
        # Identify and mark leading zeros as NaN (which will be blank in CSV)
        # if pivot_df[column].first_valid_index() is not None:
        #     first_valid_index = pivot_df[column].first_valid_index()
        #     pivot_df.loc[:first_valid_index, column] = pivot_df.loc[:first_valid_index, column].replace(0, pd.NA)
    
    # Save the pivoted DataFrame to a CSV file
    pivot_df.to_csv(output_csv_path, index=True)  # Keep the index as Date column
    print(f'Pivoted data exported successfully to {output_csv_path}')

# Define the database path and output CSV path
db_path = '/Users/att/passivbot_configs/att_analytics.db'
output_csv_path = '/Users/att/passivbot_configs/att_analytics_output_longs2.csv'

# Call the function
export_data_to_csv(db_path, output_csv_path)
