import yfinance as yf
import pandas as pd
import gradio as gr
import matplotlib.pyplot as plt
import io
from PIL import Image

# Function to format large numbers
def format_large_number(num):
    if isinstance(num, (int, float)):
        if num >= 1_000_000_000_000:
            return f"₹{num / 1_000_000_000_000:.2f} Trillion"
        elif num >= 1_000_000_000:
            return f"₹{num / 1_000_000_000:.2f} Billion"
        elif num >= 1_000_000:
            return f"₹{num / 1_000_000:.2f} Million"
        else:
            return f"₹{num:.2f}"
    return "N/A"

# Fetch quarterly financials (last 3 quarters)
def get_quarterly_financials(ticker):
    stock = yf.Ticker(ticker)
    quarterly_financials = stock.quarterly_financials
    if not quarterly_financials.empty:
        latest_quarters = quarterly_financials.iloc[:, :3]
        net_profit = latest_quarters.loc["Net Income"].values
        sales = latest_quarters.loc["Total Revenue"].values
        operating_income = latest_quarters.loc["Operating Income"].values
    else:
        net_profit = sales = operating_income = ["N/A"] * 3
    return net_profit, sales, operating_income

# Fetch stock information
def get_stock_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    name = info.get('longName', 'N/A')
    market_cap = info.get('marketCap', 'N/A')
    current_price = stock.history(period="1d")["Close"].iloc[-1] if not stock.history(period="1d").empty else "N/A"
    pe_ratio = info.get('forwardPE', 'N/A')
    dividend_yield = info.get('dividendYield', 'N/A')
    eps = info.get('trailingEps', 'N/A')
    revenue = info.get('totalRevenue', 'N/A')
    beta = info.get('beta', 'N/A')
    sector = info.get('sector', 'N/A')
    recommendation = info.get('recommendationKey', 'N/A')
    fifty_two_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
    fifty_two_week_low = info.get('fiftyTwoWeekLow', 'N/A')

    net_profit, sales, operating_income = get_quarterly_financials(ticker)

    return {
        "Company Name": name,
        "Ticker": ticker,
        "Current Price": format_large_number(current_price),
        "Market Cap": format_large_number(market_cap),
        "PE Ratio": pe_ratio,
        "Dividend Yield": f"{dividend_yield:.2%}" if dividend_yield else "N/A",
        "EPS": format_large_number(eps),
        "Revenue": format_large_number(revenue),
        "Net Profit (Last Quarter)": format_large_number(net_profit[0]),
        "Sales (Last Quarter)": format_large_number(sales[0]),
        "Operating Income (Last Quarter)": format_large_number(operating_income[0]),
        "Beta": beta,
        "52-Week High": format_large_number(fifty_two_week_high),
        "52-Week Low": format_large_number(fifty_two_week_low),
        "Sector": sector,
        "Recommendation": recommendation
    }

# Calculate quarterly averages for high and low prices
def calculate_quarterly_averages(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")  # Fetch 1-year data
    hist['Quarter'] = hist.index.to_period('Q')  # Add a 'Quarter' column

    # Calculate quarterly averages for High and Low prices
    quarterly_data = hist.groupby('Quarter')[['High', 'Low']].mean()
    return quarterly_data

# Function to generate visualizations
def plot_visualizations(ticker, net_profit, sales, quarterly_high_low):
    fig, axes = plt.subplots(3, 1, figsize=(10, 15))

    # Quarterly Net Profit
    axes[0].bar(['Q1', 'Q2', 'Q3'], net_profit, color='blue')
    axes[0].set_title(f"{ticker} - Net Profit (Last 3 Quarters)")
    axes[0].set_ylabel("₹")
    for i, v in enumerate(net_profit):
        axes[0].text(i, v, f"₹{v:.2f}", ha='center', va='bottom', fontsize=9)

    # Quarterly Sales
    axes[1].bar(['Q1', 'Q2', 'Q3'], sales, color='orange')
    axes[1].set_title(f"{ticker} - Sales (Last 3 Quarters)")
    axes[1].set_ylabel("₹")
    for i, v in enumerate(sales):
        axes[1].text(i, v, f"₹{v:.2f}", ha='center', va='bottom', fontsize=9)

    # Quarterly 52-Week High/Low Line Graph
    quarters = quarterly_high_low.index.strftime('%Y-Q%q')  # Format quarter names
    axes[2].plot(quarters, quarterly_high_low['High'], label="High", color="green", marker='o')
    axes[2].plot(quarters, quarterly_high_low['Low'], label="Low", color="red", marker='o')
    axes[2].set_title(f"{ticker} - 52-Week High/Low Averages by Quarter")
    axes[2].set_ylabel("₹")
    axes[2].legend()

    # Save plot to a BytesIO object
    plt.tight_layout()
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="PNG")
    image_stream.seek(0)

    # Convert to Image
    image = Image.open(image_stream)
    return image

# Main function
def main(ticker_symbol):
    ticker = f"{ticker_symbol}.NS"  # Assuming the tickers follow NSE convention
    try:
        stock_info = get_stock_info(ticker)
        net_profit, sales, _ = get_quarterly_financials(ticker)
        quarterly_high_low = calculate_quarterly_averages(ticker)

        # Create visualizations
        visual_image = plot_visualizations(ticker, net_profit, sales, quarterly_high_low)

        # Format stock info for display (column-style markdown table)
        stock_info_md = "\n\n".join([f"**{key}**: {value}" for key, value in stock_info.items()])
        return stock_info_md, visual_image
    except Exception as e:
        return f"Error fetching data for {ticker}: {e}", None

# Load stock symbols from a CSV file
def load_stocks():
    try:
        nse_data = pd.read_csv('nse_stocks.csv')
        return nse_data['SYMBOL'].tolist()
    except FileNotFoundError:
        return []

# Get stock symbols
stocks = load_stocks()

# Gradio Interface
iface = gr.Interface(
    fn=main,
    inputs=[gr.Dropdown(choices=stocks, label="Select a Stock Ticker")],
    outputs=[gr.Markdown(label="Stock Information"), gr.Image(label="Visualizations")],
    title="NSE Stock Info and Visualizations",
    description="Get detailed stock information and financial visualizations for NSE-listed companies."
)

# Launch the app
iface.launch()
