import requests
import datetime
import pandas as pd
import csv
import os
import requests
import datetime
import pandas as pd
import numpy as np

def fetch_bitcoin_prices():
    params = {
        'ids': 'bitcoin',
        'vs_currency': 'usd',
        'days': 'max',
        'interval': 'daily'
    }

    response = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/", params=params).json()

    if 'prices' in response:
        return response['prices']
    else:
        print("Error fetching data.")
        return None

def convert_to_weekly(data):
    weekly_data = []
    current_week = []
    current_week_start = None
    weekly_averages = []

    for entry in data:
        timestamp = entry[0]
        price = entry[1]
        date = datetime.datetime.fromtimestamp(timestamp / 1000)

        # Check if it's the first entry
        if current_week_start is None:
            current_week_start = date - datetime.timedelta(days=date.weekday())

        # Check if the entry belongs to the current week
        if date - current_week_start < datetime.timedelta(days=7):
            current_week.append(price)
        else:
            # Calculate the average price for the current week
            if current_week:
                average_price = np.mean(current_week)
                weekly_averages.append(average_price)
            else:
                weekly_averages.append(np.nan)  # If no data for the week, append NaN
            # Start a new week
            current_week = [price]
            current_week_start = date - datetime.timedelta(days=date.weekday())

    # Calculate the average price for the last week
    if current_week:
        average_price = np.mean(current_week)
        weekly_averages.append(average_price)
    else:
        weekly_averages.append(np.nan)

    # Create a DataFrame with weekly averages and timestamp as index
    start_date = pd.to_datetime(data[0][0], unit='ms').date()
    end_date = start_date + pd.to_timedelta(len(weekly_averages) * 7 - 1, 'days')
    weekly_index = pd.date_range(start=start_date, end=end_date, freq='W')

    weekly_df = pd.DataFrame(weekly_averages, columns=["Average Price"], index=weekly_index)

    return weekly_df

def save_to_csv(data, filename):
    """
    Save data to a CSV file.

    Args:
    - data: List of lists where each inner list represents a row of data.
    - filename: Name of the CSV file to be saved.
    """
    directory = "raw_data"
    file_path = os.path.join(directory, filename)

    try:
        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")

def load_csv_to_dataframe(filename):
    """
    Load data from a CSV file into a pandas DataFrame.

    Args:
    - filename: Name of the CSV file to load.

    Returns:
    - df: Pandas DataFrame containing the loaded data.
    """
    try:
        # Load the CSV file skipping rows with invalid data
        df = pd.read_csv(filename, header=None, names=["Timestamp", "Value"], skiprows=1)
        # Convert timestamp to datetime and set as index
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"Error loading data from {filename}: {e}")
        return None

def main():
    # Fetch Bitcoin prices
    bitcoin_prices = fetch_bitcoin_prices()

    if bitcoin_prices:
        # Convert fetched prices to weekly intervals
        weekly_data = convert_to_weekly(bitcoin_prices)

        # Save the fetched prices to a CSV file
        save_to_csv(weekly_data, "bitcoin_prices.csv")

if __name__ == "__main__":
    main()
