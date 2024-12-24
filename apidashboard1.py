import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import time

# API URL
API_URL = "https://api.thingspeak.com/channels/1596152/feeds.json?results=100"

# AQI Calculation Function (Assuming Field6 as PM2.5)
def calculate_aqi(pm25_value):
    if pm25_value <= 12:
        return (50 / 12) * pm25_value  # Good
    elif pm25_value <= 35.4:
        return (100 - 51) / (35.4 - 12) * (pm25_value - 12) + 51  # Moderate
    elif pm25_value <= 55.4:
        return (150 - 101) / (55.4 - 35.4) * (pm25_value - 35.4) + 101  # Unhealthy for sensitive groups
    elif pm25_value <= 150.4:
        return (200 - 151) / (150.4 - 55.4) * (pm25_value - 55.4) + 151  # Unhealthy
    elif pm25_value <= 250.4:
        return (300 - 201) / (250.4 - 150.4) * (pm25_value - 150.4) + 201  # Very unhealthy
    else:
        return (500 - 301) / (350.4 - 250.4) * (pm25_value - 250.4) + 301  # Hazardous

# Function to fetch data from API
def fetch_data(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        feeds = data.get("feeds", [])
        df = pd.DataFrame(feeds)
        if not df.empty:
            df["created_at"] = pd.to_datetime(df["created_at"])  # Convert timestamps
            # Convert field values to numeric
            for i in range(1, 7):
                field_name = f"field{i}"
                df[field_name] = pd.to_numeric(df[field_name], errors="coerce")
        return df
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

# Function to get the latest 10 values for each field
def get_latest_data(data, field):
    return data[["created_at", field]].dropna().tail(10)

# Main Streamlit app
def main():
    st.set_page_config(
        page_title="Enhanced Dashboard with AQI and Auto Refresh",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 Enhanced Dashboard with AQI and Auto Refresh")
    st.markdown("This dashboard provides labeled graphs, real-time AQI calculation, and automatic refresh every hour.")

    # Fetch data
    data = fetch_data(API_URL)

    if not data.empty:
        # Field Labels
        field_labels = {
            "field1": "Temperature (°C)",
            "field2": "Humidity (%)",
            "field3": "Pressure (hPa)",
            "field4": "Light Intensity (Lux)",
            "field5": "CO2 Levels (ppm)",
            "field6": "PM2.5 (µg/m³) & AQI",
        }

        # Graphs for each field
        st.write("### Interactive Graphs with Labels and Insights")
        zoom_states = {f"zoom_field_{i}": False for i in range(1, 7)}

        # Arrange graphs in a 2x3 grid layout
        cols = st.columns(3)

        for i, field_name in enumerate(field_labels.keys(), start=1):
            if field_name in data.columns:
                latest_data = get_latest_data(data, field_name)

                # Plot the graph
                y_label = field_labels[field_name]
                title = f"{y_label} - Latest 10 Values"

                # If AQI graph, calculate AQI
                if field_name == "field6":
                    latest_data["AQI"] = latest_data[field_name].apply(calculate_aqi)
                    y_label = "AQI"
                    title = f"{field_labels[field_name]} - Latest 10 Values"

                fig = px.line(
                    latest_data,
                    x="created_at",
                    y="AQI" if field_name == "field6" else field_name,
                    title=title,
                    labels={"created_at": "Time", field_name: y_label},
                )
                fig.update_traces(mode="lines+markers")

                # Display the AQI value for the AQI graph
                if field_name == "field6" and not latest_data.empty:
                    latest_aqi = latest_data["AQI"].iloc[-1]
                    st.markdown(f"**Latest AQI Value:** {latest_aqi:.2f}")

                # Display graphs in the grid layout
                col = cols[(i - 1) % 3]
                with col:
                    if st.button(f"Zoom {field_labels[field_name]}", key=f"zoom_field_{i}"):
                        zoom_states[f"zoom_field_{i}"] = not zoom_states[f"zoom_field_{i}"]

                    # Show the graph with toggle effect
                    if zoom_states[f"zoom_field_{i}"]:
                        st.write(f"### Detailed View for {field_labels[field_name]}")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available to display.")

# Add automatic refresh every hour
def periodic_refresh():
    while True:
        main()  # Run the main app
        time.sleep(3600)  # Wait for 1 hour (3600 seconds) before rerunning

if __name__ == "__main__":
    periodic_refresh()
