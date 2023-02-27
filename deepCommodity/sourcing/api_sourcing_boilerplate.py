import requests
import csv
import pandas as pd
import fredapi
from datetime import datetime, timedelta
from google.cloud import bigquery

import os
import pandas as pd
import fredapi
from google.cloud import bigquery


def retrieve_fred_data(series_ids,
                       start_date,
                       end_date,
                       frequency='d',
                       api_key=None,
                       csv_filename=None,
                       bq_dataset=None,
                       bq_table=None):
    # Check if API key is provided
    if api_key is None:
        api_key = os.environ.get('FRED_API_KEY')
    if api_key is None:
        raise ValueError('No API key provided')

    # Initialize FRED API
    fred = fredapi.Fred(api_key=api_key)

    # Create empty dataframe to store all the data
    df_all = pd.DataFrame()

    # Check if CSV file exists and if so, read the last date collected
    last_date_collected = None
    if csv_filename and os.path.exists(csv_filename):
        try:
            df_csv = pd.read_csv(csv_filename, index_col=0)
            last_date_collected = df_csv.index[-1]
        except FileNotFoundError:
            pass

    # Loop through the series IDs and retrieve their data
    for series_id in series_ids:
        # Retrieve data for the series
        series_data = fred.get_series(series_id,
                                      start_date=start_date,
                                      end_date=end_date,
                                      frequency=frequency)

        # Create dataframe for the series data
        df = pd.DataFrame(series_data)

        # Rename the column to the series ID
        df.rename(columns={0: series_id}, inplace=True)

        # Check if there is existing data and drop any overlapping rows
        if last_date_collected:
            df = df.loc[df.index > last_date_collected]

        # Concatenate the series dataframe to the overall dataframe
        df_all = pd.concat([df_all, df], axis=1)

    # Drop any rows with missing values
    df_all.dropna(inplace=True)

    # Sort the rows by date
    df_all.sort_index(inplace=True)

    # Write data to CSV file
    if csv_filename:
        df_csv = pd.DataFrame()
        if os.path.exists(csv_filename):
            df_csv = pd.read_csv(csv_filename, index_col=0)
        df_concat = pd.concat([df_csv, df_all]).drop_duplicates()
        df_concat.to_csv(csv_filename)

    # Upload data to Google BigQuery
    if bq_dataset and bq_table:
        # Initialize BigQuery client and dataset
        client = bigquery.Client()
        dataset_ref = client.dataset(bq_dataset)

        # Check if dataset exists, and create it if not
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            client.create_dataset(dataset)

        # Create BigQuery table schema
        schema = []
        for col in df_all.columns:
            schema.append(bigquery.SchemaField(col, 'FLOAT'))

        # Create BigQuery table reference
        table_ref = dataset_ref.table(bq_table)

        # Check if table exists, and create it if not
        try:
            client.get_table(table_ref)
        except Exception:
            table = bigquery.Table(table_ref, schema=schema)
            client.create_table(table)

        # Load data into BigQuery table
        job_config = bigquery.LoadJobConfig(schema=schema)
        job = client.load_table_from_dataframe(
            df_all,
            table_ref,
            job_config=job_config,
            write_disposition='WRITE_APPEND')
        job.result()

    return df_all


def retrieve_alphavantage_data(api_key, csv_filename, symbols, interval, start_date,
                       end_date):
    """
    Retrieves historical data for given symbols and interval from Alpha Vantage API
    and saves it to a CSV file.

    api_key: string, your Alpha Vantage API key
    csv_filename: string, the filename to save the CSV data to
    symbols: list of strings, the symbols to retrieve data for
    interval: string, the time interval to retrieve data for. Possible values are '1min',
              '5min', '15min', '30min', '60min', 'daily', 'weekly', and 'monthly'.
    start_date: string, the start date of the historical data in format 'yyyy-mm-dd'
    end_date: string, the end date of the historical data in format 'yyyy-mm-dd'

    Returns: pandas dataframe
    """

    # Check if CSV file exists and get last date collected
    last_date_collected = None
    try:
        last_date_collected = pd.read_csv(csv_filename,
                                          nrows=1)['timestamp'][0]
    except FileNotFoundError:
        pass

    # Initialize CSV file
    with open(csv_filename, mode='a', newline='') as csv_file:
        fieldnames = ['timestamp', 'symbol', 'price']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # Write header if file is empty
        if csv_file.tell() == 0:
            writer.writeheader()

        # Make API requests to Alpha Vantage for each symbol
        for symbol in symbols:
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&interval={interval}&symbol={symbol}&apikey={api_key}&outputsize=full'
            response = requests.get(url)

            # Check for successful API response
            if response.status_code != 200:
                raise Exception(
                    f'Failed to retrieve {symbol} historical data from Alpha Vantage API'
                )

            # Parse API response JSON
            data = response.json()

            # print(data)

            prices = data[f'Meta Data']

            # Write data to CSV file
            for timestamp, price_data in prices.items():
                if start_date <= timestamp <= end_date:
                    # Check if this timestamp has already been collected
                    if last_date_collected is not None and timestamp <= last_date_collected:
                        continue
                    timestamp = datetime.strptime(timestamp,
                                                  '%Y-%m-%d %H:%M:%S')
                    price = price_data['4. close']
                    writer.writerow({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'price': price
                    })

    # Read CSV file into a pandas dataframe
    df = pd.read_csv(csv_filename, parse_dates=['timestamp'])
    df = df.set_index('timestamp')

    print(
        f'Successfully wrote historical data for {len(symbols)} symbols to {csv_filename}'
    )
    return df


def retrieve_gecko_data(crypto_ids, start_date, end_date, csv_filename):
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


def retrieve_exchange_rates_data(start_date, end_date, symbols, api_key):
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


def get_multi_technical_indicators(symbols,
                                   indicators,
                                   interval,
                                   api_key,
                                   start_date=None,
                                   end_date=None):
    result = {}
    for symbol in symbols:
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_{interval}&symbol={symbol}&apikey={api_key}'
        if start_date is not None:
            url += f'&start_date={start_date}'
        if end_date is not None:
            url += f'&end_date={end_date}'
        response = requests.get(url)
        if response.status_code != 200:
            print(
                f'Request failed for {symbol} with status code {response.status_code}'
            )
            continue
        data = response.json()[f'Time Series ({interval})']
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        for indicator in indicators:
            if indicator == 'BBANDS':
                if 'Real Middle Band' not in data:
                    continue
                df['bbands_middle'] = pd.DataFrame.from_dict(
                    data['Real Middle Band']).astype(float)
            else:
                try:
                    indicator_data = pd.DataFrame.from_dict(
                        data[indicator.upper()]).iloc[:, 0].astype(float)
                except KeyError:
                    print(f'{indicator} not found for {symbol}')
                    continue
                indicator_data.name = indicator.lower()
                df = pd.concat([df, indicator_data], axis=1)
        result[symbol] = df
    return result
