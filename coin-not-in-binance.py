import pandas as pd
import ccxt
import os
import requests
from datetime import datetime
import pickle

# Telegram Bot Configurations
TELEGRAM_BOT_TOKEN = '7882419887:AAGtPnp07ItbpiPL85xItBTUj64ucBFQap0'
TELEGRAM_CHAT_ID = '6757461113'

# File paths
DATA_FILE = 'assets_not_on_binance.pkl'
PREVIOUS_TOP50_FILE = 'previous_top50.pkl'

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, data=payload)
    return response.json()

def collect_market_data():
    # Similar to previous data collection scripts, but adjusted for daily runs
    # Initialize an empty list to store market information
    all_markets = []

    # Get a list of all exchange IDs supported by ccxt
    exchange_ids = ccxt.exchanges

    # Optionally, filter for specific exchanges if needed
    # exchange_ids = ['binance', 'okx', 'huobi', 'ftx', 'kraken', 'coinbasepro', 'bitfinex', 'bitstamp', 'bittrex', 'kucoin']

    # Iterate over each exchange
    for exchange_id in exchange_ids:
        try:
            # Initialize the exchange
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class()

            print(f'Fetching markets from {exchange_id}...')

            # Load all markets for the exchange
            markets = exchange.load_markets()

            # Iterate over each market
            for market in markets.values():
                market_info = {
                    'exchange': exchange_id,
                    'symbol': market.get('symbol'),
                    'base': market.get('base'),
                    'quote': market.get('quote'),
                    'type': market.get('type'),
                    'active': market.get('active'),
                }

                # Append the market info to the list
                all_markets.append(market_info)

        except Exception as e:
            print(f'Error fetching markets from {exchange_id}: {e}')
            continue

    # Convert the list to a DataFrame
    df = pd.DataFrame(all_markets)
    return df

def create_coin_exchange_matrix(df):
    # Create 'coin_asset' column
    df['coin_asset'] = df['base']

    # Create a pivot table
    coin_exchange_matrix = df.pivot_table(index='coin_asset', columns='exchange', values='symbol', aggfunc='first')
    coin_presence = coin_exchange_matrix.notnull().astype(int)

    # Replace 1 with 'X' and 0 with ''
    coin_presence = coin_presence.replace({1: 'X', 0: ''})

    return coin_presence

def get_assets_not_on_binance(coin_presence):
    # Filter assets not listed on Binance
    if 'binance' in coin_presence.columns:
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

    return assets_sorted

def main():
    # Step 1: Collect market data
    df = collect_market_data()

    # Save the data to a file for debugging (optional)
    df.to_pickle(DATA_FILE)

    # Step 2: Create coin-exchange matrix
    coin_presence = create_coin_exchange_matrix(df)

    # Step 3: Get assets not on Binance
    assets_sorted = get_assets_not_on_binance(coin_presence)

    # Step 4: Get top 50 assets
    top_50_assets = assets_sorted.head(50)

    # Step 5: Check for changes compared to previous day
    if os.path.exists(PREVIOUS_TOP50_FILE):
        with open(PREVIOUS_TOP50_FILE, 'rb') as f:
            previous_top50 = pickle.load(f)
    else:
        previous_top50 = pd.DataFrame()

    # Save current top 50 for next day's comparison
    with open(PREVIOUS_TOP50_FILE, 'wb') as f:
        pickle.dump(top_50_assets, f)

    # Identify changes
    new_assets = top_50_assets.index.difference(previous_top50.index)
    removed_assets = previous_top50.index.difference(top_50_assets.index)

    # Step 6: Prepare message
    if not new_assets.empty or not removed_assets.empty:
        message_lines = []
        message_lines.append(f"*Top 50 Coins Not on Binance as of {datetime.now().strftime('%Y-%m-%d')}*")

        for asset in top_50_assets.index:
            status = ""
            if asset in new_assets:
                status = "🆕"  # New asset
            elif asset in removed_assets:
                status = "❌"  # Asset removed (unlikely in top_50_assets, but included for completeness)

            # Check if the asset is available on OKX
            is_on_okx = top_50_assets.loc[asset].get('okx', '') == 'X'
            okx_status = "✅ Available on OKX" if is_on_okx else "❌ Not on OKX"

            # Construct the line
            line = f"{status} *{asset}*: {okx_status}"
            message_lines.append(line)

        # Send the message via Telegram
        message = '\n'.join(message_lines)
        send_telegram_message(message)
    else:
        print("No changes in the top 50 assets. No message sent.")

if __name__ == "__main__":
    main()
