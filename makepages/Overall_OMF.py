#!/usr/bin/env python3
'''
MPEC Watch - Overall Observer, Measurer, Facility Statistics

Creates pie/bar charts and breakdown tables showing the overall occurrence of each 
"observer", "measurer" and "facility" across all observatory stations.

(C) Quanzhi Ye
'''

import plotly.express as px
import pandas as pd
import json
import os
from collections import Counter

# Configuration constants
MAX_CHAR_LEN = 30  # Maximum length for display names
TOP_N = 10         # Number of top items to display in charts
OUTPUT_DIR = '../www/stats/'

def sanitize_name(name, max_len=MAX_CHAR_LEN):
    if not name or len(name) <= max_len:
        return name
    return name[:max_len] + "..."

def aggregate_omf_data(observatory_data):
    """
    Aggregates Observer, Measurer, Facility, and Object data from obscode_stat.json.
    """
    observers = Counter()
    measurers = Counter()
    facilities = Counter()
    objects = Counter()
    stations = {}
    
    for station_code, station_data in observatory_data.items():
        # Count station observations (total MPECs)
        stations[station_code] = station_data.get('total', 0)
        
        # Aggregate observer counts
        for observer, count in station_data.get('OBS', {}).items():
            observers[observer] += count
            
        # Aggregate measurer counts
        for measurer, count in station_data.get('MEA', {}).items():
            measurers[measurer] += count
            
        # Aggregate facility counts
        for facility, count in station_data.get('FAC', {}).items():
            facilities[facility] += count

        # Aggregate object counts
        for obj, count in station_data.get('OBJ', {}).items():
            objects[obj] += count

    return dict(observers), dict(measurers), dict(facilities), dict(objects), stations

def generate_top_n_chart(data_dict, title, n=TOP_N, include_other=True):
    """
    Generates a pie chart of the top N items from the provided dictionary.
    
    Args:
        data_dict: Dictionary of items and their counts
        title: Title for the chart
        n: Number of top items to include
        include_other: Whether to include an "Others" category for items beyond the top N
    """
    suffix = ''
    
    # Get the top N items
    sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    top_items = dict(sorted_items[:n])
    
    # Sanitize long names
    sanitized_items = {}
    for key, value in top_items.items():
        sanitized_key = sanitize_name(key)
        sanitized_items[sanitized_key] = value
    
    # Add "Others" category if requested
    if include_other:
        suffix += "+O"
        others_count = sum(data_dict.values()) - sum(sanitized_items.values())
        if others_count > 0:
            sanitized_items["Others"] = others_count
    
    # Create DataFrame for Plotly
    df = pd.DataFrame(list(sanitized_items.items()), columns=['Item', 'Count'])
    
    # Generate pie chart
    fig = px.pie(
        df, 
        values='Count', 
        names='Item', 
        title=f"{title} (Top {n})",
        hover_data=['Count']
    )
    
    # Improve layout
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="center", x=0.5),
        margin=dict(t=50, b=50, l=10, r=10)
    )
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save the chart
    safe_title = title.replace(' ', '_').replace('/', '_')
    output_path = os.path.join(OUTPUT_DIR, f"{safe_title}{suffix}.html")
    fig.write_html(output_path)
    
    print(f"Generated chart: {os.path.basename(output_path)}")
    
    return fig

def main():
    """Main function to generate overall OMF statistics"""
    print("MPEC Watch - Generating Overall OMF Statistics...")
    
    # Load MPC observatory codes
    with open('../mpccode.json') as f:
        mpccode = json.load(f)
    
    # Load observatory statistics
    try:
        with open('obscode_stat.json') as f:
            observatory_data = json.load(f)
    except FileNotFoundError:
        print("Error: obscode_stat.json not found. Run obscode_stat.py first.")
        return
    
    # Aggregate data across all observatories
    observers, measurers, facilities, objects, stations = aggregate_omf_data(observatory_data)
    
    print(f"Found {len(observers)} unique observers")
    print(f"Found {len(measurers)} unique measurers")
    print(f"Found {len(facilities)} unique facilities")
    print(f"Found {len(objects)} unique objects")

    print(f"Found {len(stations)} observatory stations with data")
    
    # Generate visualization charts
    generate_top_n_chart(observers, "Fraction of each observer group among all MPECs")
    generate_top_n_chart(measurers, "Fraction of each measurer group among all MPECs")
    generate_top_n_chart(facilities, "Fraction of each facility among all MPECs")
    generate_top_n_chart(objects, "Fraction of each object among all MPECs")
    generate_top_n_chart(stations, "Fraction of each observatory code among all MPECs")

    print("Overall OMF statistics generation complete.")

if __name__ == "__main__":
    main()