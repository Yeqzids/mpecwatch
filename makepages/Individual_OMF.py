import plotly.express as px
import pandas as pd
import json
import numpy as np
import datetime
import os
import sys

# --- Configuration/Constants ---
MPC_CODE_PATH = '../mpccode.json'
OBSCODE_STAT_PATH = 'obscode_stat.json'
OUTPUT_BASE_DIR = "../www/byStation/OMF/"
TOP_N_LIMIT = 10

def sanitize_name(name, max_len=30):
    """Truncates long names and appends '...'"""
    return name[:max_len] + "..." if len(name) > max_len else name

def generate_pie_chart(data_dict, station_code, filename_suffix, include_other=True):
    """Generates and saves a pie chart."""
    if 0 in data_dict:
        print(f"Warning: Key '0' found in data_dict for {station_code}. Removing it.")
        del data_dict[0]

    # Get the top N items
    sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    top_items = dict(sorted_items[:TOP_N_LIMIT])

    if include_other and len(data_dict) > TOP_N_LIMIT:
        others_sum = sum(data_dict.values()) - sum(top_items.values())
        if others_sum > 0:
            top_items["Others"] = others_sum

    df = pd.DataFrame(list(top_items.items()), columns=['Objects', 'Count'])
    fig = px.pie(df, values='Count', names='Objects')

    if not top_items:
        fig.add_annotation(text="No Data Available",
                           xref="paper", yref="paper",
                           x=0.3, y=0.3, showarrow=False)

    output_path = os.path.join(OUTPUT_BASE_DIR,
                               f"{station_code}_{filename_suffix.replace(' ', '_')}.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path)

def generate_bar_chart(x_data, y_data, x_axis_title, y_axis_title, station_code, filename_suffix):
    """Generates and saves a bar chart."""
    fig = px.bar(x=x_data, y=y_data)
    fig.update_layout(xaxis_title=x_axis_title, yaxis_title=y_axis_title)
    output_path = os.path.join(OUTPUT_BASE_DIR,
                               f"{station_code}_{filename_suffix.replace(' ', '_')}.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path)

def process_time_frequencies(mpecs_data):
    """Process MPEC data to extract observation time frequencies"""
    yearly = np.zeros(366)
    hourly = np.zeros(24)
    weekly = np.zeros(7)
    
    for entry in mpecs_data:
        if len(entry) > 1:  # Ensure entry has timestamp
            timestamp = entry[1]  # Position based on obscode_stat.json structure
            
            day = datetime.date.fromtimestamp(timestamp).timetuple().tm_yday
            hour = datetime.datetime.fromtimestamp(timestamp).hour
            weekday = datetime.date.fromtimestamp(timestamp).weekday()
            
            yearly[day-1] += 1
            hourly[hour] += 1
            weekly[weekday] += 1
    
    return yearly, hourly, weekly

def process_station(station_code, station_data):
    """Process a single station's data from obscode_stat.json"""
    print(f"Processing {station_code}...")
    
    # Extract OMF data from the station's JSON data
    observers = station_data.get('OBS', {})
    measurers = station_data.get('MEA', {})
    facilities = station_data.get('FAC', {})
    objects = station_data.get('OBJ', {})

    # Sanitize names for better display in pie charts
    sanitized_observers = {sanitize_name(name): count for name, count in observers.items()}
    sanitized_measurers = {sanitize_name(name): count for name, count in measurers.items()}
    sanitized_facilities = {sanitize_name(name): count for name, count in facilities.items()}
    sanitized_objects = {sanitize_name(name): count for name, count in objects.items()}

    # Get MPECs data for time analysis
    mpecs_data = station_data.get('MPECs', [])
    
    # Process time frequencies
    yearly, hourly, weekly = process_time_frequencies(mpecs_data)
    
    # Generate Pie Charts
    generate_pie_chart(sanitized_observers, station_code, "Top_Observers")
    generate_pie_chart(sanitized_measurers, station_code, "Top_Measurers")
    generate_pie_chart(sanitized_facilities, station_code, "Top_Facilities")
    generate_pie_chart(sanitized_objects, station_code, "Top_Objects")

    # Generate Time Frequency Charts
    generate_bar_chart(np.arange(1, 367), yearly, "Day of the Year", "Number of Observations", station_code, "yearly")
    generate_bar_chart(np.arange(0, 24), hourly, "Hour of the Day", "Number of Observations", station_code, "hourly")
    generate_bar_chart(np.arange(0, 7), weekly, "Day of the Week", "Number of Observations", station_code, "weekly")

# --- Main Execution ---
if __name__ == "__main__":
    print("Loading MPC codes...")
    with open(MPC_CODE_PATH) as f:
        mpccode = json.load(f)
    
    print("Loading observatory statistics...")
    with open(OBSCODE_STAT_PATH) as f:
        obscode_stat = json.load(f)
    
    print(f"Processing observatory OMF visualizations...")
    
    # Get station code from command line if provided, otherwise process all stations
    if len(sys.argv) > 1:
        station_codes = [sys.argv[1]]
    else:
        station_codes = list(mpccode.keys())
    
    # Process each station
    for station_code in station_codes:
        if station_code in obscode_stat:
            process_station(station_code, obscode_stat[station_code])
        else:
            print(f"Warning: Station {station_code} not found in obscode_stat.json")
    
    print('Finished processing all stations.')