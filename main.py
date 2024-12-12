import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# TODO
# 1. Data Acquisition - Yahoo Finance probably
# 2. Candlestick data Preprocesssing
# 3. Identifying FVGs
# 4. Price Proximity to FVGs
# 5. Color-Coding Based on Proximity
# 6. Visualization




# 1 Data Acquisition
def fetchStockData(tickerSymbol=["AAPL", "TSLA", "GOOGL", "MBLY"], startDate="2023-01-01", endDate="2023-12-31"):
    """
    Fetch stock data from Yahoo Finance for a specific ticker symbol and date range.
    
    Args:
    ticker_symbol (str): Stock ticker symbol (e.g., 'AAPL').
    start_date (str): Start date for the data in 'YYYY-MM-DD' format.
    end_date (str): End date for the data in 'YYYY-MM-DD' format.
    
    Returns:
    pd.DataFrame: A DataFrame containing the relevant stock fields.
    """
    # Fetch historical market data
    stockData = yf.download(tickerSymbol, start=startDate, end=endDate, group_by="ticker")

    return stockData.loc[:, (slice(None), ['Open', 'High', 'Low', 'Close'])]

# Example usage
ticker = "AAPL"  # Replace with desired stock ticker


# Fetch data
# stock_info = fetch_stock_data(ticker, start, end)
stock_info = fetchStockData().round(2)

stock_info.to_csv("FVGResults.csv", index=True)

# Display fetched data
print(stock_info)


# 2 Candlestick Preprocessing
def candlestickPreprocessing(stockData):
    """
    Add features for candlestick analysis and to identify FVGs
    
    Args:
        stockData (pd.DataFrame): multi-index DataFrame containing the stock data.
    
    Returns:
        pd.DataFrame: preprocessed DataFrame with FVG labels.
    """
    processedData = []
    for ticker in stockData.columns.levels[0]:  # Loop through each stock
        df = stockData[ticker].copy()
        df['Body Size'] = abs(df['Close'] - df['Open'])
        df['Upper Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        df['Lower Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
        df['Direction'] = df['Close'] > df['Open']  # True = Uptrend, False = Downtrend
        df['Prev High'] = df['High'].shift(1)
        df['Prev Low'] = df['Low'].shift(1)
        df['Prev Direction'] = df['Direction'].shift(1).where(df['Direction'].shift(1).notna(), False)

        # Identify FVGs
        df['Bullish FVG'] = (  df['Direction'] & ~df['Prev Direction'].astype(bool)) & (df['Low']  > df['Prev High'] )
        df['Bearish FVG'] = ( ~df['Direction'] &  df['Prev Direction'].astype(bool)) & (df['High'] < df['Prev Low']  )

        # Determine proximity to FVG
        df['Status'] = 'No FVG'
        df.loc[df['Bullish FVG'], 'Status'] = 'Bullish FVG'
        df.loc[df['Bearish FVG'], 'Status'] = 'Bearish FVG'
        df['Proximity'] = 'Far'
        df.loc[(df['Low'] < df['Prev High']) & (df['High'] > df['Prev Low']), 'Proximity'] = 'Near'
        df.loc[(df['High'] >= df['Prev High']), 'Proximity'] = 'In FVG'

        df['Ticker'] = ticker  # Add ticker for multi-stock processing
        processedData.append(df)

    return pd.concat(processedData)


# 3. Color Coding and CSV Export
def export_color_coded_excel(data, outputFileName):
    """
    Export preprocessed data to an Excel file with color-coded rows.

    Args:
        data (pd.DataFrame): Preprocessed stock data.
        outputFileName (str): Name of the output Excel file.
    """
    # Create a Pandas Excel writer using XlsxWriter engine
    with pd.ExcelWriter(outputFileName, engine='xlsxwriter') as writer:
        # Write data to Excel
        data.to_excel(writer, sheet_name='FVG Data', index=True)

        # Access the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['FVG Data']

        # Define formats for each proximity level
        formatRed = workbook.add_format({'bg_color': '#FF9999', 'font_color': '#000000'})
        formatYellow = workbook.add_format({'bg_color': '#FFFF99', 'font_color': '#000000'})
        formatGreen = workbook.add_format({'bg_color': '#99FF99', 'font_color': '#000000'})
        formatWhite = workbook.add_format({'bg_color': '#FFFFFF', 'font_color': '#000000'})

        # Apply conditional formatting for the entire dataset
        for rowIndex, (_, rowData) in enumerate(data.iterrows(), start=1):
            # Select format based on Proximity
            if rowData['Proximity'] == 'Far':
                worksheet.set_row(rowIndex, None, formatRed)
            elif rowData['Proximity'] == 'Near':
                worksheet.set_row(rowIndex, None, formatYellow)
            elif rowData['Proximity'] == 'In FVG':
                worksheet.set_row(rowIndex, None, formatGreen)
            else:
                worksheet.set_row(rowIndex, None, formatWhite)

        print(f"Data exported to {outputFileName} with color-coding.")



if __name__ == "__main__":
    tickers = ["AAPL", "TSLA", "GOOGL", "MBLY"]
    start = "2023-01-01"
    end = "2023-12-31"
    excelFileName = "FVGResults.xlsx"

    # 1. Fetch Data
    stockData = fetchStockData(tickers, start, end)

    # 2. Preprocess Candlestick Data
    preprocessedData = candlestickPreprocessing(stockData)

    # 3. Export FVG results to CSV
    export_color_coded_excel(preprocessedData, excelFileName)