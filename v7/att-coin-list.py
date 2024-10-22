# import ccxt
# import pandas as pd
# from datetime import datetime

# # Initialize an empty list to store market information
# all_markets = []

# # Get a list of all exchange IDs supported by ccxt
# exchange_ids = ccxt.exchanges

# # Iterate over each exchange
# for exchange_id in exchange_ids:
#     try:
#         # Initialize the exchange
#         exchange_class = getattr(ccxt, exchange_id)
#         exchange = exchange_class()

#         print(f'Fetching markets from {exchange_id}...')

#         # Load all markets for the exchange
#         markets = exchange.load_markets()

#         # Iterate over each market (trading pair)
#         for symbol, market in markets.items():
#             market_info = {
#                 'exchange': exchange_id,
#                 'symbol': symbol,
#                 'base': market.get('base'),
#                 'quote': market.get('quote'),
#                 'active': market.get('active'),
#                 'type': market.get('type'),
#                 'spot': market.get('spot'),
#                 'margin': market.get('margin'),
#                 'swap': market.get('swap'),
#                 'future': market.get('future'),
#                 'option': market.get('option'),
#                 'contract': market.get('contract'),
#                 'linear': market.get('linear'),
#                 'inverse': market.get('inverse'),
#                 'expiry': market.get('expiry'),
#                 'expiry_datetime': market.get('expiryDatetime'),
#                 'info': market.get('info'),
#             }

#             # Append the market info to the list
#             all_markets.append(market_info)

#     except Exception as e:
#         print(f'Error fetching markets from {exchange_id}: {e}')
#         continue

# # Convert the list to a DataFrame for easier handling
# df = pd.DataFrame(all_markets)

# # Save the DataFrame to a CSV file
# df.to_csv('all_exchanges_market_data.csv', index=False)

# print('Data fetching complete. The market data has been saved to "all_exchanges_market_data.csv".')

import pandas as pd

# Load the data from the CSV file generated previously
df = pd.read_csv('all_exchanges_market_data.csv')

# Ensure that 'base' and 'exchange' columns are present
required_columns = {'base', 'exchange', 'type'}
if not required_columns.issubset(df.columns):
    missing = required_columns - set(df.columns)
    print(f"The required columns {missing} are not present in the DataFrame.")
    exit()

# We will include all market types (spot, futures, swaps, options, etc.)
# For better clarity, let's create a 'coin_asset' column that represents the primary asset
# For spot markets, 'coin_asset' will be the 'base' currency
# For derivatives, 'coin_asset' can be derived from the 'base' or 'symbol' with adjustments

def get_coin_asset(row):
    if row['type'] == 'spot':
        return row['base']
    else:
        # For derivatives, extract the underlying asset from the symbol or base
        # This may vary between exchanges, so we'll attempt to extract it
        # Common patterns include 'BTC/USD', 'BTC-PERP', 'BTC-20211231', etc.
        symbol = row['symbol']
        base = row['base']
        # Remove common suffixes for perpetual and futures contracts
        for suffix in ['-PERP', 'PERP', 'USD', 'USDT']:
            if symbol.endswith(suffix):
                return symbol.replace(suffix, '')
        # If expiry date is available, use base asset
        if pd.notnull(row.get('base')):
            return row['base']
        else:
            return symbol  # Fallback to symbol if unable to parse

# Apply the function to create 'coin_asset' column
df['coin_asset'] = df.apply(get_coin_asset, axis=1)

# Create a pivot table with 'coin_asset' as rows and exchanges as columns
# Mark 'X' where the asset is listed on the exchange
coin_exchange_matrix = df.pivot_table(index='coin_asset', columns='exchange', values='symbol', aggfunc='first')
coin_presence = coin_exchange_matrix.notnull().astype(int)

# Replace 1 with 'X' and 0 with ''
coin_presence = coin_presence.replace({1: 'X', 0: ''})

# Identify assets that are not listed on Binance but are listed on other exchanges
if 'binance' in coin_presence.columns:
    # Filter assets not listed on Binance
    assets_not_on_binance = coin_presence[coin_presence['binance'] == ''].copy()
else:
    print("Binance exchange data is not present in the DataFrame.")
    assets_not_on_binance = coin_presence.copy()

# Remove the 'binance' column for counting
exchange_columns = [col for col in assets_not_on_binance.columns if col != 'binance']

# Count the number of exchanges each asset is listed on (excluding Binance)
assets_not_on_binance['exchange_count'] = assets_not_on_binance[exchange_columns].apply(lambda row: (row == 'X').sum(), axis=1)

# Remove assets that are not listed on any exchange (edge case)
assets_not_on_binance = assets_not_on_binance[assets_not_on_binance['exchange_count'] > 0]

# Sort the assets by the number of exchanges they are listed on (descending)
assets_sorted = assets_not_on_binance.sort_values(by='exchange_count', ascending=False)

# Move 'exchange_count' column to the front
cols = assets_sorted.columns.tolist()
cols.insert(0, cols.pop(cols.index('exchange_count')))
assets_sorted = assets_sorted[cols]

# Save the result to a CSV file
assets_sorted.to_csv('assets_not_on_binance_including_derivatives.csv')

print("The table has been saved to 'assets_not_on_binance_including_derivatives.csv'.")
