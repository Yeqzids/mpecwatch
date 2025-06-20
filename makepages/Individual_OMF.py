import sqlite3
import plotly.express as px
import pandas as pd
import json
import numpy as np
import datetime
import os # Import os for path manipulation

# --- Configuration/Constants ---
DB_PATH = "../mpecwatch_v3.db"
MPC_CODE_PATH = '../mpccode.json'
OUTPUT_BASE_DIR = "../www/byStation/OMF/"
TOP_N_LIMIT = 10 # N = 10

# --- Helper Functions ---
def sanitize_name(name, max_len=30):
    """Truncates long names and appends '...'"""
    return name[:max_len] + "..." if len(name) > max_len else name

def generate_pie_chart(data_dict, title, station_code, filename_suffix, include_na=False):
    """Generates and saves a pie chart."""
    if include_na:
        if '' in data_dict:
            data_dict['N/A'] = data_dict.pop('')
    else:
        if '' in data_dict:
            del data_dict['']

    if 0 in data_dict: # Assuming 0 is a special key to be excluded
        del data_dict[0]

    processed_data = {}
    if len(data_dict) > TOP_N_LIMIT:
        sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        top_objects = dict(sorted_items[:TOP_N_LIMIT])
        others_sum = sum(data_dict.values()) - sum(top_objects.values())
        processed_data = top_objects
        if others_sum > 0: # Only add "Others" if there's something to sum
            processed_data["Others"] = others_sum
    else:
        processed_data = dict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))

    df = pd.DataFrame(list(processed_data.items()), columns=['Objects', 'Count'])
    chart_title = f"{station_code} {mpccode[station_code]['name']} | {title}"
    fig = px.pie(df, values='Count', names='Objects', title=chart_title)

    if not processed_data: # Check if dictionary is empty after processing
        fig.add_annotation(text="No Data Available",
                           xref="paper", yref="paper",
                           x=0.3, y=0.3, showarrow=False)

    na_suffix = "+NA" if include_na else ""
    output_path = os.path.join(OUTPUT_BASE_DIR,
                               f"{station_code}_{filename_suffix.replace(' ', '_')}{na_suffix}.html")
    fig.write_html(output_path)

def generate_bar_chart(x_data, y_data, title, x_axis_title, y_axis_title, station_code, filename_suffix):
    """Generates and saves a bar chart."""
    chart_title = f"{station_code} {mpccode[station_code]['name']} | {title}"
    fig = px.bar(x=x_data, y=y_data, title=chart_title)
    fig.update_layout(xaxis_title=x_axis_title, yaxis_title=y_axis_title)
    output_path = os.path.join(OUTPUT_BASE_DIR,
                               f"{station_code}_{filename_suffix.replace(' ', '_')}.html")
    fig.write_html(output_path)

# --- Main Execution ---
if __name__ == "__main__":
    with open(MPC_CODE_PATH) as f:
        mpccode = json.load(f)

    with sqlite3.connect(DB_PATH) as mpecconn:
        cursor = mpecconn.cursor()

        #for station_code in mpccode.keys():
        for i in range(1):
            station_code = 'G96' # Example station code for testing
            station_table_name = f"station_{station_code}"
            
            print(f"Processing {station_table_name}...")

            observers = {}
            measurers = {}
            facilities = {}
            objects = {}
            
            try:
                # Using f-string for table name, but be cautious with untrusted input
                cursor.execute(f"SELECT Observer, Measurer, Facility, Object, Time FROM {station_table_name}")
                
                yearly = np.zeros(366)
                hourly = np.zeros(24)
                weekly = np.zeros(7)

                for mpec_data in cursor.fetchall():
                    observer_name = sanitize_name(mpec_data[0])
                    measurer_name = sanitize_name(mpec_data[1])
                    facility_name = sanitize_name(mpec_data[2])
                    object_name = sanitize_name(mpec_data[3])
                    timestamp = int(mpec_data[4])

                    observers[observer_name] = observers.get(observer_name, 0) + 1
                    measurers[measurer_name] = measurers.get(measurer_name, 0) + 1
                    facilities[facility_name] = facilities.get(facility_name, 0) + 1
                    objects[object_name] = objects.get(object_name, 0) + 1
                    
                    # Time frequency data
                    day = datetime.date.fromtimestamp(timestamp).timetuple().tm_yday
                    hour = datetime.datetime.fromtimestamp(timestamp).hour
                    weekday = datetime.date.fromtimestamp(timestamp).weekday()
                    
                    yearly[day-1] += 1
                    hourly[hour] += 1
                    weekly[weekday] += 1

                # Generate Pie Charts
                generate_pie_chart(observers, f"Top {TOP_N_LIMIT} Observers", station_code, "Top_Observers")
                generate_pie_chart(measurers, f"Top {TOP_N_LIMIT} Measurers", station_code, "Top_Measurers")
                generate_pie_chart(facilities, f"Top {TOP_N_LIMIT} Facilities", station_code, "Top_Facilities")
                generate_pie_chart(objects, f"Top {TOP_N_LIMIT} Objects", station_code, "Top_Objects")

                # Generate Time Frequency Charts
                generate_bar_chart(np.arange(1, 367), yearly, "Yearly Frequency", "Day of the Year", "Number of Observations", station_code, "yearly")
                generate_bar_chart(np.arange(0, 24), hourly, "Hourly Frequency", "Hour of the Day", "Number of Observations", station_code, "hourly")
                generate_bar_chart(np.arange(0, 7), weekly, "Weekly Frequency", "Day of the Week", "Number of Observations", station_code, "weekly")

            except sqlite3.OperationalError as e:
                print(f"Error for {station_table_name}: Table does not exist. {e}")
            except Exception as e:
                print(f"An unexpected error occurred for {station_table_name}: {e}")

    print('Finished processing all stations.')