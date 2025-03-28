# --- IMPORTS ---
import yfinance as yf
import pandas as pd
import datetime as dt
import warnings
import io
import sys

# Dash related imports
import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc

# Plotting imports
import plotly.graph_objects as go

# --- FUNCTION TO GET VOLATILITY SURFACE DATA (Unchanged) ---
def get_volatility_surface_data(ticker, min_volume=10, min_open_interest=10):
    
    log_messages = [] # Store messages to potentially return

    log_messages.append(f"--- Fetching Volatility Surface Data for Ticker: {ticker} ---")
    stock = yf.Ticker(ticker)

    try:
        expirations = stock.options
        if not expirations:
            log_messages.append(f"Error: No options expiration dates found for {ticker}.")
            return None, log_messages
        log_messages.append(f"Found {len(expirations)} expiration dates.")

    except Exception as e:
        log_messages.append(f"Error fetching expiration dates for {ticker}. It might be an invalid ticker or delisted. Error: {e}")
        return None, log_messages

    all_options_data = []
    today = dt.date.today()

    for i, exp_date_str in enumerate(expirations):
        try:
            opt_chain = stock.option_chain(exp_date_str)
            exp_date = dt.datetime.strptime(exp_date_str, '%Y-%m-%d').date()
            time_to_expiration = max((exp_date - today).days, 0) / 365.25

            calls = opt_chain.calls
            if not calls.empty:
                calls['OptionType'] = 'Call'
                calls['ExpirationDate'] = exp_date_str
                calls['TimeToExpiration'] = time_to_expiration
                all_options_data.append(calls)

            puts = opt_chain.puts
            if not puts.empty:
                puts['OptionType'] = 'Put'
                puts['ExpirationDate'] = exp_date_str
                puts['TimeToExpiration'] = time_to_expiration
                all_options_data.append(puts)

        except Exception as e:
            log_messages.append(f"  Warning: Could not process options for {exp_date_str}. Error: {e}")
            continue

    if not all_options_data:
        log_messages.append(f"Error: No valid option data could be retrieved across all expirations for {ticker}.")
        return None, log_messages

    combined_df = pd.concat(all_options_data, ignore_index=True)
    log_messages.append(f"\nTotal options contracts fetched (before filtering): {len(combined_df)}")

    required_cols = ['strike', 'ExpirationDate', 'TimeToExpiration', 'OptionType', 'impliedVolatility']
    optional_cols = ['volume', 'openInterest', 'lastPrice', 'bid', 'ask']
    available_cols = [col for col in required_cols + optional_cols if col in combined_df.columns]

    if 'impliedVolatility' not in available_cols:
         log_messages.append("Error: 'impliedVolatility' column not found in the downloaded data. Cannot proceed.")
         return None, log_messages

    final_df = combined_df[available_cols].copy()

    final_df = final_df.rename(columns={
        'strike': 'Strike',
        'impliedVolatility': 'ImpliedVolatility',
        'volume': 'Volume',
        'openInterest': 'OpenInterest',
        'lastPrice': 'LastPrice',
        'bid':'Bid',
        'ask':'Ask'
    })

    log_messages.append("\n--- Cleaning and Filtering Data ---")

    numeric_cols = ['ImpliedVolatility', 'Volume', 'OpenInterest', 'LastPrice', 'Bid', 'Ask']
    for col in numeric_cols:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')

    if 'Volume' in final_df.columns:
        final_df['Volume'] = final_df['Volume'].fillna(0).astype(int)
    if 'OpenInterest' in final_df.columns:
        final_df['OpenInterest'] = final_df['OpenInterest'].fillna(0).astype(int)

    initial_rows = len(final_df)
    final_df = final_df.dropna(subset=['ImpliedVolatility'])
    final_df = final_df[final_df['ImpliedVolatility'] > 0.0001]
    rows_after_iv_filter = len(final_df)
    if initial_rows - rows_after_iv_filter > 0:
        log_messages.append(f"Removed {initial_rows - rows_after_iv_filter} rows with invalid Implied Volatility.")

    rows_before_liquidity_filter = len(final_df)
    if 'Volume' in final_df.columns and 'OpenInterest' in final_df.columns:
        final_df = final_df[
            (final_df['Volume'] >= min_volume) &
            (final_df['OpenInterest'] >= min_open_interest)
        ]
        rows_after_liquidity_filter = len(final_df)
        removed_count = rows_before_liquidity_filter - rows_after_liquidity_filter
        if removed_count > 0:
             log_messages.append(f"Removed {removed_count} rows based on Volume >= {min_volume} and Open Interest >= {min_open_interest}.")

    if final_df.empty:
        log_messages.append("Warning: No data remaining after filtering.")
        return None, log_messages

    final_df = final_df.sort_values(by=['TimeToExpiration', 'OptionType', 'Strike'])

    log_messages.append(f"\nFinal dataset contains {len(final_df)} options contracts.")
    # log_messages.append(f"Columns: {final_df.columns.tolist()}")

    return final_df, log_messages


# --- DASH APP SETUP ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server

# Ignore yfinance/pandas warnings in app output
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- DASH LAYOUT ---
app.layout = dbc.Container([
    # Invisible components
    dcc.Store(id='volatility-data-store'),
    dcc.Download(id='download-dataframe-csv'),

    dbc.Row(dbc.Col(html.H1("Volatility Surface Data Fetcher"), width=12)),

    dbc.Row([
        # Input Controls Column
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Inputs"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Label("Ticker Symbol:", html_for="ticker-input", width=4),
                        dbc.Col(dbc.Input(id="ticker-input", type="text", value="MSFT", placeholder="e.g., AAPL, MSFT"), width=8),
                    ], className="mb-3"),
                    # ... (Min Volume and Min OI inputs remain the same) ...
                    dbc.Row([
                         dbc.Label("Min Volume:", html_for="min-volume-input", width=4),
                         dbc.Col(dbc.Input(id="min-volume-input", type="number", value=10, min=0, step=1), width=8),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Label("Min Open Interest:", html_for="min-oi-input", width=4),
                        dbc.Col(dbc.Input(id="min-oi-input", type="number", value=20, min=0, step=1), width=8),
                    ], className="mb-3"),

                    dbc.Button("Fetch Data", id="fetch-button", color="primary", n_clicks=0, className="mt-3 me-2"),
                    dbc.Button("Download CSV", id="download-button", color="success", n_clicks=0, className="mt-3", disabled=True),
                ])
            ])
        ], md=4),

        # Output Area Column (Table and Status)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Output Table & Status"), # Changed header slightly
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-indicator",
                        type="default",
                        children=[
                            html.Div(id="status-message", children="Enter parameters and click 'Fetch Data'."),
                            html.Hr(),
                            html.Div(id="output-table-div") # Table will appear here
                        ]
                    )
                ])
            ])
        ], md=8)
    ]),

    # --- NEW ROW FOR THE 3D PLOT ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Interactive Volatility Surface"),
                dbc.CardBody([
                    dcc.Loading( # Add loading indicator for the plot as well
                        id="loading-plot-indicator",
                        type="default",
                        children=[
                             dcc.Graph(id='volatility-surface-plot', style={'height': '600px'}) # Placeholder for the plot
                        ]
                    )
                ])
            ])
        ], width=12) # Use full width for the plot
    ], className="mt-4"), # Add margin top to separate from the row above

    dbc.Row(dbc.Col(html.Small("Data sourced from Yahoo Finance via yfinance."), width=12), className="mt-4 text-center text-muted")

], fluid=True)

# --- DASH CALLBACKS ---

# Callback 1: Fetch data, update status, table, store, and download button state (Unchanged Logic)
@callback(
    Output("status-message", "children"),
    Output("output-table-div", "children"),
    Output("volatility-data-store", "data"),
    Output("download-button", "disabled"),
    Input("fetch-button", "n_clicks"),
    State("ticker-input", "value"),
    State("min-volume-input", "value"),
    State("min-oi-input", "value"),
    prevent_initial_call=True
)
def update_output(n_clicks, ticker, min_volume, min_oi):
    # ... (Callback logic remains exactly the same as before) ...
    if not ticker:
        return dbc.Alert("Please enter a ticker symbol.", color="warning"), None, None, True # Keep button disabled

    if min_volume is None or min_volume < 0:
         return dbc.Alert("Please enter a valid non-negative minimum volume.", color="warning"), None, None, True

    if min_oi is None or min_oi < 0:
        return dbc.Alert("Please enter a valid non-negative minimum open interest.", color="warning"), None, None, True

    ticker = ticker.strip().upper()

    try:
        vol_surface_df, log_msgs = get_volatility_surface_data(
            ticker,
            min_volume=min_volume,
            min_open_interest=min_oi
        )

        final_status = []
        has_error = any("Error:" in msg for msg in log_msgs)

        if vol_surface_df is not None and not vol_surface_df.empty:
             final_status.append(dbc.Alert(f"Successfully fetched and processed {len(vol_surface_df)} option contracts for {ticker}.", color="success"))
             warnings_found = [msg for msg in log_msgs if "Warning:" in msg]
             if warnings_found:
                 final_status.append(dbc.Alert("Processing warnings occurred:\n" + "\n".join(warnings_found), color="warning"))

             data_table = dash_table.DataTable(
                 id='vol-table',
                 columns=[{"name": i, "id": i} for i in vol_surface_df.columns],
                 data=vol_surface_df.to_dict('records'),
                 page_size=15,
                 style_table={'overflowX': 'auto'},
                 style_cell={'textAlign': 'left', 'fontSize': '12px', 'fontFamily': 'sans-serif', 'padding': '5px'},
                 style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                 filter_action="native",
                 sort_action="native",
                 sort_mode="multi",
             )
             stored_data = vol_surface_df.to_json(date_format='iso', orient='split')
             return final_status, data_table, stored_data, False # Enable download

        elif has_error:
             error_msg = next((msg for msg in log_msgs if "Error:" in msg), "An unspecified error occurred.")
             final_status.append(dbc.Alert(f"Failed to fetch data for {ticker}. {error_msg}", color="danger"))
             return final_status, None, None, True # Keep button disabled
        else:
             final_status.append(dbc.Alert(f"No valid option data found for {ticker} matching the criteria.", color="warning"))
             return final_status, None, None, True # Keep button disabled

    except Exception as e:
        error_message = dbc.Alert(f"An unexpected application error occurred: {str(e)}", color="danger")
        return error_message, None, None, True # Keep button disabled


# Callback 2: Handle Download Button Click (Unchanged)
@callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State("volatility-data-store", "data"),
    State("ticker-input", "value"),
    prevent_initial_call=True,
)
def download_csv(n_clicks, stored_data, ticker):
    # ... (Callback logic remains exactly the same as before) ...
    if not stored_data:
        return None

    df = pd.read_json(stored_data, orient='split')
    ticker_str = str(ticker).strip().upper() if ticker else "data"
    today_str = dt.date.today().strftime("%Y%m%d")
    filename = f"{ticker_str}_volatility_surface_{today_str}.csv"
    return dcc.send_data_frame(df.to_csv, filename=filename, index=False)


# --- NEW CALLBACK ---
# Callback 3: Update the 3D Volatility Surface Plot
@callback(
    Output("volatility-surface-plot", "figure"),
    Input("volatility-data-store", "data"), # Triggered when data store changes
    State("ticker-input", "value"),         # Get ticker for title
    prevent_initial_call=True
)
def update_plot(stored_data, ticker):
    if not stored_data:
        # No data available, return an empty figure
        return go.Figure() # Returns an empty plot

    # Reconstruct DataFrame from stored JSON
    df = pd.read_json(stored_data, orient='split')
    ticker = str(ticker).strip().upper() if ticker else "Data"

    # Create the 3D scatter plot figure
    fig = go.Figure()

    # Add the 3D scatter trace
    fig.add_trace(go.Scatter3d(
        x=df['TimeToExpiration'],
        y=df['Strike'],
        z=df['ImpliedVolatility'],
        mode='markers',
        marker=dict(
            size=3, # Adjust marker size if needed
            color=df['ImpliedVolatility'],  # Color points by IV
            colorscale='Viridis',           # Choose a colorscale (e.g., 'Viridis', 'Plasma', 'Jet')
            colorbar=dict(title='Implied Volatility', thickness=15, len=0.7), # Add color bar legend
            opacity=0.8
        ),
        # Custom hover text for each point
        text=df.apply(
            lambda row: f"Type: {row['OptionType']}<br>"
                        f"Strike: {row['Strike']}<br>"
                        f"Expiry: {row['ExpirationDate']}<br>"
                        f"TTE: {row['TimeToExpiration']:.3f} yrs<br>"
                        f"IV: {row['ImpliedVolatility']:.2%}<br>"
                        f"Volume: {row.get('Volume', 'N/A')}<br>" # Use .get for optional cols
                        f"Open Int: {row.get('OpenInterest', 'N/A')}",
            axis=1
        ),
        hoverinfo='text' # Use the custom text for hover info
    ))

    # Update plot layout for titles and axis labels
    fig.update_layout(
        title=f'{ticker} Volatility Surface',
        scene=dict(
            xaxis_title='Time to Expiration (Years)',
            yaxis_title='Strike Price',
            zaxis_title='Implied Volatility (%)' # You might want to multiply IV by 100 if preferred
        ),
        # Adjust Z-axis format if IV is kept as decimal
        scene_zaxis_tickformat='.1%',
        margin=dict(l=10, r=10, b=10, t=50), # Adjust margins
        # height=600 # Height is set in the dcc.Graph component style
    )

    return fig


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    app.run(debug=True)