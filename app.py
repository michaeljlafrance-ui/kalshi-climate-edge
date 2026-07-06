import streamlit as st
import requests
import pandas as pd
import scipy.stats as stats
import numpy as np

st.set_page_config(page_title="Kalshi Weather Alpha Matrix", layout="wide")

st.title("🌦️ Kalshi Climate Edge Matrix")
st.write("Using live probabilistic meteorological vectors to calculate exact bracket settlement advantages.")

# --- CITY COORDINATES DATABASE ---
CITIES = {
    "Los Angeles (LAX)": {"lat": 33.9416, "lon": -118.4085},
    "New York (NYC)": {"lat": 40.7128, "lon": -74.0060},
    "Chicago (ORD)": {"lat": 41.9742, "lon": -87.9073},
    "Miami (MIA)": {"lat": 25.7959, "lon": -80.2870},
    "Austin (AUS)": {"lat": 30.1945, "lon": -97.6664}
}

selected_city = st.selectbox("🎯 Target Kalshi Market Location:", list(CITIES.keys()))
lat = CITIES[selected_city]["lat"]
lon = CITIES[selected_city]["lon"]

st.markdown("---")

# --- FETCH RAW WEATHER DATA ---
@st.cache_data(ttl=3600)
def fetch_weather_vectors(lat, lon):
    # Pulling hourly high-resolution data from open-meteo arrays
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&temperature_unit=fahrenheit&timezone=auto"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

data = fetch_weather_vectors(lat, lon)

if data:
    # Extract the maximum temperature forecasted for tomorrow
    times = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    
    df_weather = pd.DataFrame({"time": times, "temp": temps})
    df_weather['time'] = pd.to_datetime(df_weather['time'])
    
    # Isolate tomorrow's dataset rows safely
    tomorrow = pd.Timestamp.now().date() + pd.Timedelta(days=1)
    df_tomorrow = df_weather[df_weather['time'].dt.date == tomorrow]
    
    predicted_max = float(df_tomorrow['temp'].max())
    
    st.subheader(f"📊 Meteorological Baseline Model ({tomorrow})")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="Expected Maximum Temperature (Mean)", value=f"{predicted_max:.1f} °F")
    with col_m2:
        # Standard deviation representing standard short-term forecast variance/error model (typically 1.5°F for 24h lookaheads)
        std_dev = 1.5
        st.metric(label="Model Uncertainty Delta (1 Standard Deviation)", value=f"± {std_dev} °F")
        
    st.markdown("---")
    st.subheader("⚖️ Kalshi Bracket Discrepancy Matrix")
    st.write("Adjust the current Kalshi market price sliders below to instantly find your mathematical edge:")

    # --- CORE KALSHI BRACKET DEFINITION GRID ---
    # Replicating the exact multi-bracket layout requested by user
    brackets = [
        {"label": "69°F or Below", "low": -99, "high": 69.5},
        {"label": "70°F to 71°F", "low": 69.5, "high": 71.5},
        {"label": "72°F to 73°F", "low": 71.5, "high": 73.5},
        {"label": "74°F to 75°F", "low": 73.5, "high": 75.5},
        {"label": "76°F to 77°F", "low": 75.5, "high": 77.5},
        {"label": "78°F or Above", "low": 77.5, "high": 999}
    ]

    analysis_rows = []
    
    for idx, b in enumerate(brackets):
        # Calculate true probability using Normal Distribution Cumulative Distribution Functions (CDF)
        prob_high = stats.norm.cdf(b["high"], loc=predicted_max, scale=std_dev)
        prob_low = stats.norm.cdf(b["low"], loc=predicted_max, scale=std_dev)
        true_probability_pct = (prob_high - prob_low) * 100
        
        # Render a clean layout column for real-time manual price entry mapping
        c1, c2, c3 = st.columns([2, 3, 3])
        with c1:
            st.markdown(f"**{b['label']}**")
            st.caption(f"True Math Probability: {true_probability_pct:.1f}%")
        with c2:
            # Slider to input Kalshi's live contract price (cents = implied percentage)
            kalshi_price = st.slider(f"Live Price (¢)", min_value=1, max_value=99, value=int(true_probability_pct), key=f"slide_{idx}")
        with c3:
            # Mathematical Edge = True Probability - Implied Market Price Probability
            edge = true_probability_pct - kalshi_price
            
            if edge > 5.0:
                st.success(f"🟢 **BUY YES EDGE: +{edge:.1f}%** (Underpriced)")
            elif edge < -5.0:
                st.error(f"🔴 **BUY NO EDGE: +{abs(edge):.1f}%** (Overpriced)")
            else:
                st.info(f"⚪ Fairly Priced (Edge: {edge:.1f}%)")
                
else:
    st.warning("⏳ Accessing data arrays... Verify connection parameters if stream delays persist.")
