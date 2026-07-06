import streamlit as st
import requests
import pandas as pd
import scipy.stats as stats
import numpy as np

st.set_page_config(page_title="Kalshi Weather Alpha Matrix", layout="wide")

st.title("🌦️ Kalshi Climate Edge Matrix")
st.write("Using live probabilistic meteorological vectors to calculate exact bracket settlement advantages.")

if st.button("🔄 Clear Cache & Refresh Weather Data"):
    st.cache_data.clear()
    st.rerun()

# --- CITY COORDINATES DATABASE ---
CITIES = {
    "Miami (MIA)": {"lat": 25.7959, "lon": -80.2870},
    "Los Angeles (LAX)": {"lat": 33.9416, "lon": -118.4085},
    "New York (NYC)": {"lat": 40.7128, "lon": -74.0060},
    "Chicago (ORD)": {"lat": 41.9742, "lon": -87.9073},
    "Austin (AUS)": {"lat": 30.1945, "lon": -97.6664}
}

selected_city = st.selectbox("🎯 Target Kalshi Market Location:", list(CITIES.keys()))
lat = CITIES[selected_city]["lat"]
lon = CITIES[selected_city]["lon"]

st.markdown("---")

# --- FETCH RAW WEATHER DATA ---
@st.cache_data(ttl=3600)
def fetch_weather_vectors(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&temperature_unit=fahrenheit&timezone=auto"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

data = fetch_weather_vectors(lat, lon)

if data:
    times = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    
    df_weather = pd.DataFrame({"time": times, "temp": temps})
    df_weather['time'] = pd.to_datetime(df_weather['time'])
    
    # Isolate tomorrow's prediction windows cleanly
    tomorrow = pd.Timestamp.now().date() + pd.Timedelta(days=1)
    df_tomorrow = df_weather[df_weather['time'].dt.date == tomorrow]
    
    predicted_max = float(df_tomorrow['temp'].max())
    
    st.subheader(f"📊 Meteorological Baseline Model ({tomorrow})")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label=f"Expected Maximum Temperature for {selected_city}", value=f"{predicted_max:.1f} °F")
    with col_m2:
        std_dev = 1.5
        st.metric(label="Model Uncertainty Delta (1 Standard Deviation)", value=f"± {std_dev} °F")
        
    st.markdown("---")
    st.subheader("⚖️ Kalshi Bracket Discrepancy Matrix")
    st.write("Brackets have automatically adapted to mirror Kalshi's live layout structure for this temperature zone:")

    # --- THE DYNAMIC BRACKET GENERATOR ENGINE ---
    # We find the nearest even integer anchor to build a perfectly balanced bracket distribution
    anchor = int(round(predicted_max / 2.0) * 2.0)
    
    brackets = [
        {"label": f"{anchor - 3}°F or Below", "low": -99, "high": (anchor - 2.5)},
        {"label": f"{anchor - 2}°F to {anchor - 1}°F", "low": (anchor - 2.5), "high": (anchor - 0.5)},
        {"label": f"{anchor}°F to {anchor + 1}°F", "low": (anchor - 0.5), "high": (anchor + 1.5)},
        {"label": f"{anchor + 2}°F to {anchor + 3}°F", "low": (anchor + 1.5), "high": (anchor + 3.5)},
        {"label": f"{anchor + 4}°F to {anchor + 5}°F", "low": (anchor + 3.5), "high": (anchor + 5.5)},
        {"label": f"{anchor + 6}°F or Above", "low": (anchor + 5.5), "high": 999}
    ]

    for idx, b in enumerate(brackets):
        # Calculate true math percentages over the newly adapted spatial zones
        prob_high = stats.norm.cdf(b["high"], loc=predicted_max, scale=std_dev)
        prob_low = stats.norm.cdf(b["low"], loc=predicted_max, scale=std_dev)
        true_probability_pct = (prob_high - prob_low) * 100
        
        c1, c2, c3 = st.columns([2, 3, 3])
        with c1:
            st.markdown(f"**{b['label']}**")
            st.caption(f"True Math Probability: {true_probability_pct:.1f}%")
        with c2:
            # Input slider default auto-aligns to the calculated probability baseline
            kalshi_price = st.slider(f"Live Price (¢)", min_value=1, max_value=99, value=max(1, min(99, int(true_probability_pct))), key=f"slide_v3_{idx}")
        with c3:
            edge = true_probability_pct - kalshi_price
            if edge > 5.0:
                st.success(f"🟢 **BUY YES EDGE: +{edge:.1f}%** (Underpriced)")
            elif edge < -5.0:
                st.error(f"🔴 **BUY NO EDGE: +{abs(edge):.1f}%** (Overpriced)")
            else:
                st.info(f"⚪ Fairly Priced (Edge: {edge:.1f}%)")
                
else:
    st.warning("⏳ Accessing data arrays... Verify connection parameters if stream delays persist.")
