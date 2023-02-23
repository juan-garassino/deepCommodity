import requests
import csv
from datetime import datetime
import pandas as pd
import fredapi

def get_multi_historical_data_to_csv(api_key, csv_filename, start_date, end_date):
    """
    Retrieves historical hourly data for S&P 500, gold, silver, and petrol prices
    from Alpha Vantage API and saves it to a CSV file.

    api_key: string, your Alpha Vantage API key
    csv_filename: string, the filename to save the CSV data to
    start_date: string, the start date of the historical data in format 'yyyy-mm-dd'
    end_date: string, the end date of the historical data in format 'yyyy-mm-dd'

    Returns: None
    """

    # Define symbols and their mappings to API function names
    symbols = {
        'S&P 500': ('^GSPC', 'Time Series (60min)'),
        'Gold': ('XAU', 'Time Series (60min)'),
        'Silver': ('XAG', 'Time Series (60min)'),
        'Petrol': ('CL', 'Time Series (60min)')
    }

    # Initialize CSV file
    with open(csv_filename, mode='w', newline='') as csv_file:
        fieldnames = ['timestamp', 'symbol', 'price']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

    # Make API requests to Alpha Vantage for each symbol
    for symbol, (symbol_id, function_name) in symbols.items():
        url = f'https://www.alphavantage.co/query?function={function_name}&symbol={symbol_id}&apikey={api_key}&outputsize=full'
        response = requests.get(url)

        # Check for successful API response
        if response.status_code != 200:
            raise Exception(
                f'Failed to retrieve {symbol} historical data from Alpha Vantage API'
            )

        # Parse API response JSON
        data = response.json()
        prices = data[function_name]

        # Write data to CSV file
        with open(csv_filename, mode='a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            for timestamp, price_data in prices.items():
                if start_date <= timestamp <= end_date:
                    timestamp = datetime.strptime(
                        timestamp,
                        '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                    price = price_data['4. close']
                    writer.writerow({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'price': price
                    })

    print(
        f'Successfully wrote historical hourly data for {len(symbols)} symbols to {csv_filename}'
    )

def get_bond_yields(start_date, end_date, api_key):
    # initialize FRED API
    fred = fredapi.Fred(api_key)

    # define series ID for 10-year treasury constant maturity rate
    series_id = 'DGS10'

    # retrieve hourly data for the series
    df = fred.get_series(series_id,
                         start=start_date,
                         end=end_date,
                         frequency='H')

    # convert index to datetime and rename column
    df.index = pd.to_datetime(df.index)
    df.rename(columns={0: 'yield'}, inplace=True)

    # save data to CSV file
    df.to_csv('bond_yield.csv')

    return df

def get_economic_indicators(start_date, end_date, api_key):
    # initialize FRED API
    fred = fredapi.Fred(api_key)

    # define series IDs for GDP, CPI, and unemployment rate
    gdp_id = 'GDPC1'
    cpi_id = 'CPALTT01USM657N'
    unemployment_id = 'UNRATE'

    # retrieve hourly data for the series
    gdp_df = fred.get_series(gdp_id,
                             start=start_date,
                             end=end_date,
                             frequency='H')
    cpi_df = fred.get_series(cpi_id,
                             start=start_date,
                             end=end_date,
                             frequency='H')
    unemployment_df = fred.get_series(unemployment_id,
                                      start=start_date,
                                      end=end_date,
                                      frequency='H')

    # concatenate the dataframes
    df = pd.concat([gdp_df, cpi_df, unemployment_df], axis=1)

    # convert index to datetime and rename columns
    df.index = pd.to_datetime(df.index)
    df.columns = ['gdp', 'cpi', 'unemployment']

    # save data to CSV file
    df.to_csv('economic_indicators.csv')

    return df

def get_commodity_prices(start_date, end_date, symbols):
    # define list of cryptocurrency symbols and start/end timestamps
    start_timestamp = pd.Timestamp(start_date).timestamp()
    end_timestamp = pd.Timestamp(end_date).timestamp()

    # retrieve hourly data for the cryptocurrencies
    df_list = []
    for symbol in symbols:
        url = f'https://api.coingecko.com/api/v3/coins/{symbol}/market_chart/range?vs_currency=usd&from={start_timestamp}&to={end_timestamp}&interval=hourly'
        response = requests.get(url)
        data = response.json()

        # create dataframe and add to list
        df = pd.DataFrame(data['prices'],
                          columns=['timestamp', f'{symbol}_price'])
        df[f'{symbol}_price'] = df[f'{symbol}_price'].astype(float)
        df_list.append(df)

    # join dataframes on timestamp and save to CSV file
    df = pd.concat(df_list, axis=1)
    df.drop('timestamp', axis=1, inplace=True)
    df.to_csv('commodity_prices.csv')

    return df

def get_exchange_rates(start_date, end_date, symbols, api_key):
    # define list of currency symbols and start/end timestamps
    start_timestamp = pd.Timestamp(start_date).strftime('%Y-%m-%d %H:%M:%S')
    end_timestamp = pd.Timestamp(end_date).strftime('%Y-%m-%d %H:%M:%S')

    # retrieve hourly data for the currencies
    df_list = []
    for symbol in symbols:
        url = f'https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={symbol[:3]}&to_symbol={symbol[3:]}&interval=60min&apikey={api_key}&outputsize=full'
        response = requests.get(url)
        data = response.json()

        # create dataframe and add to list
        df = pd.DataFrame.from_dict(data['Time Series FX (60min)'],
                                    orient='index')
        df = df[['4. close']].astype(float)
        df.columns = [symbol]
        df_list.append(df)

    # join dataframes on timestamp and save to CSV file
    df = pd.concat(df_list, axis=1)
    df.index = pd.to_datetime(df.index)
    df.to_csv('exchange_rates.csv')

    return df

def get_technical_indicators(symbol, interval, api_key):
    # retrieve hourly data for the symbol
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={api_key}&outputsize=full'
    response = requests.get(url)
    data = response.json()

    # create dataframe
    df = pd.DataFrame.from_dict(data['Time Series ({})'.format(interval)],
                                orient='index')
    df = df[['4. close']].astype(float)
    df.columns = [symbol]

    # retrieve technical indicators for the symbol
    indicators = [
        'SMA', 'EMA', 'STOCH', 'RSI', 'ADX', 'CCI', 'AROON', 'BBANDS', 'MACD'
    ]
    for indicator in indicators:
        url = f'https://www.alphavantage.co/query?function={indicator}&symbol={symbol}&interval={interval}&time_period=10&series_type=close&apikey={api_key}'
        response = requests.get(url)
        data = response.json()

        # create columns for each technical indicator
        if indicator == 'STOCH':
            df[f'stoch_k'] = pd.DataFrame.from_dict(
                data[f'STOCH ({interval},10,3)']).iloc[:, 0].astype(float)
            df[f'stoch_d'] = pd.DataFrame.from_dict(
                data[f'STOCH ({interval},10,3)']).iloc[:, 1].astype(float)
        elif indicator == 'BBANDS':
            df[f'bbands_lower'] = pd.DataFrame.from_dict(
                data['Real Lower Band']).astype(float)
            df[f'bbands_upper'] = pd.DataFrame.from_dict(
                data['Real Upper Band']).astype(float)
            df[f'bbands_middle'] = pd.DataFrame.from_dict(
                data['Real Middle Band']).astype(float)
        else:
            df[f'{indicator.lower()}'] = pd.DataFrame.from_dict(
                data[f'{indicator}']).iloc[:, 0].astype(float)

    # save data to CSV file
    df.to_csv(f'{symbol}_technical_indicators.csv')

    return df

def get_historical_data_to_csv(crypto_ids, start_date, end_date, csv_filename):
    """
    Retrieves historical hourly data for given cryptocurrencies from CoinGecko API
    and saves it to a CSV file.

    crypto_ids: list of strings, the IDs of the cryptocurrencies on CoinGecko e.g. ['bitcoin', 'ethereum']
    start_date: string, the start date of the historical data in format 'dd-mm-yyyy'
    end_date: string, the end date of the historical data in format 'dd-mm-yyyy'
    csv_filename: string, the filename to save the CSV data to

    Returns: pandas DataFrame
    """

    # Convert date strings to datetime objects
    start_date = datetime.strptime(start_date, '%d-%m-%Y').strftime('%s')
    end_date = datetime.strptime(end_date, '%d-%m-%Y').strftime('%s')

    # Create empty DataFrame to store data
    data_df = pd.DataFrame()

    # Loop through each crypto ID and make API request to CoinGecko
    for crypto_id in crypto_ids:
        url = f'https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart/range?vs_currency=usd&from={start_date}&to={end_date}&interval=hourly'
        response = requests.get(url)

        # Check for successful API response
        if response.status_code != 200:
            raise Exception(
                f'Failed to retrieve historical data for {crypto_id} from CoinGecko API'
            )

        # Parse API response JSON
        data = response.json()
        prices = data['prices']
        market_caps = data['market_caps']
        total_volumes = data['total_volumes']

        # Create DataFrame for this crypto and add to main DataFrame
        crypto_df = pd.DataFrame(prices,
                                 columns=['timestamp', f'{crypto_id}_price'])
        crypto_df[f'{crypto_id}_market_cap'] = [
            market_cap[1] for market_cap in market_caps
        ]
        crypto_df[f'{crypto_id}_total_volume'] = [
            total_volume[1] for total_volume in total_volumes
        ]
        crypto_df['timestamp'] = crypto_df['timestamp'].apply(
            lambda x: datetime.fromtimestamp(x / 1000))
        crypto_df.set_index('timestamp', inplace=True)
        data_df = pd.concat([data_df, crypto_df], axis=1)

    # Add total volumes to DataFrame
    volume_columns = [col for col in data_df.columns if '_total_volume' in col]
    data_df['total_volume'] = data_df[volume_columns].sum(axis=1)

    # Save DataFrame to CSV file
    data_df.to_csv(csv_filename)
    print(
        f'Successfully wrote {len(data_df)} rows of historical hourly data to {csv_filename}'
    )

    return data_df
