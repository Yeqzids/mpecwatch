#!/usr/bin/env python3
import csv
import sqlite3
import sys
import datetime
import os
import json
import plotly.express as px
import pandas as pd

# Configuration
DB_PATH = '../mpecwatch_v4.db'
MPCCODE_PATH = '../mpccode.json'
OUTPUT_BASE_DIR = '../www/byObject/'
OBSCODE_STAT_PATH = 'obscode_stat.json'

def get_related_designations(cursor, object_designation):
    """
    Retrieve all related designations for a specific object from the DOUIdentifier table.
    
    Args:
        cursor: Database cursor
        object_designation: The packed designation to look up (e.g., "J97W07A")
        
    Returns:
        list: List of tuples containing related designations and metadata
    """
    cursor.execute("""
        SELECT RelatedDOU, RelationType, Author, MPECId, IsRetracted
        FROM DOUIdentifier
        WHERE DOU = ? AND IsRetracted = 0
        ORDER BY RelationType, RelatedDOU
    """, (object_designation,))
    
    return cursor.fetchall()

def unpack_designation(packed):
    """Convert packed designation to readable format."""
    if len(packed) != 7:
        return packed
        
    century = ""
    if packed[0] == "J":
        century = "19"
    elif packed[0] == "K":
        century = "20"
    else:
        return packed  # Not a standard packed designation
        
    year = century + packed[1:3]
    
    half_months = {
        "A": "01A", "B": "01B", "C": "02A", "D": "02B", "E": "03A", "F": "03B",
        "G": "04A", "H": "04B", "J": "05A", "K": "05B", "L": "06A", "M": "06B",
        "N": "07A", "O": "07B", "P": "08A", "Q": "08B", "R": "09A", "S": "09B",
        "T": "10A", "U": "10B", "V": "11A", "W": "11B", "X": "12A", "Y": "12B"
    }
    
    month_period = half_months.get(packed[3], "??")
    number = packed[4:6]
    letter = packed[6]
    
    return f"{year} {month_period[0:2]}{letter}{number} ({month_period[2]} half)"

def get_object_mpecs(cursor, object_designation):
    """Get all MPECs related to this object."""
    cursor.execute("""
        SELECT MPECId, Title, Time, Station, DiscStation, MPECType, ObjectType
        FROM MPEC
        WHERE ObjectId = ? OR Station LIKE ?
        ORDER BY Time
    """, (object_designation, f'%{object_designation}%'))
    
    return cursor.fetchall()

def get_object_observations(cursor, object_designation):
    """Get observation details from station tables."""
    observations = []
    
    # Try to find observations in station tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'station_%'")
    station_tables = cursor.fetchall()
    
    for (table_name,) in station_tables:
        try:
            cursor.execute(f"""
                SELECT Object, Time, Observer, Measurer, Facility, MPEC, MPECType, ObjectType, Discovery
                FROM {table_name}
                WHERE Object = ?
                ORDER BY Time
            """, (object_designation,))
            
            station_obs = cursor.fetchall()
            station_code = table_name.replace('station_', '')
            
            for obs in station_obs:
                observations.append({
                    'station': station_code,
                    'object': obs[0],
                    'time': obs[1],
                    'observer': obs[2],
                    'measurer': obs[3],
                    'facility': obs[4],
                    'mpec': obs[5],
                    'mpec_type': obs[6],
                    'object_type': obs[7],
                    'discovery': obs[8]
                })
        except sqlite3.OperationalError:
            # Table might not have the expected schema
            continue
    
    return observations

def create_observation_timeline(observations):
    """Create a timeline plot of observations."""
    if not observations:
        return None
    
    df = pd.DataFrame(observations)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df['year'] = df['datetime'].dt.year
    
    # Create timeline figure
    fig = px.scatter(df, x='datetime', y='station', 
                     color='mpec_type', size_max=10,
                     title=f"Observation Timeline",
                     labels={'datetime': 'Date', 'station': 'Observatory Station'})
    
    # Mark discoveries
    discoveries = df[df['discovery'] == 1]
    if not discoveries.empty:
        fig.add_scatter(x=discoveries['datetime'], y=discoveries['station'],
                       mode='markers', marker=dict(symbol='star', size=15, color='gold'),
                       name='Discovery', showlegend=True)
    
    fig.update_layout(height=400, showlegend=True)
    return fig

def create_station_contribution_chart(observations):
    """Create a chart showing station contributions."""
    if not observations:
        return None
    
    df = pd.DataFrame(observations)
    station_counts = df['station'].value_counts()
    
    fig = px.bar(x=station_counts.index, y=station_counts.values,
                 title="Observatory Station Contributions",
                 labels={'x': 'Observatory Station', 'y': 'Number of Observations'})
    
    fig.update_layout(height=400)
    return fig

def generate_object_page(object_designation, mpccode_data, cursor):
    """Generate an HTML page for the specified object."""
    
    # Get basic object information
    cursor.execute("""
        SELECT COUNT(*) FROM MPEC WHERE ObjectId = ?
    """, (object_designation,))
    
    mpec_count = cursor.fetchone()[0]
    if mpec_count == 0:
        print(f"No MPECs found for object {object_designation}")
        return
    
    # Get object MPECs and observations
    mpecs = get_object_mpecs(cursor, object_designation)
    observations = get_object_observations(cursor, object_designation)
    related_designations = get_related_designations(cursor, object_designation)
    
    # Get discovery information
    discovery_mpec = None
    discovery_station = None
    discovery_date = None
    object_type = "Unknown"
    
    for mpec in mpecs:
        if mpec[4] and mpec[5] == 'Discovery':  # DiscStation exists and it's a discovery
            discovery_mpec = mpec[0]
            discovery_station = mpec[4]
            discovery_date = datetime.datetime.fromtimestamp(mpec[2])
            object_type = mpec[6] or "Unknown"
            break
    
    # Create visualizations
    timeline_fig = create_observation_timeline(observations)
    station_fig = create_station_contribution_chart(observations)
    
    # Generate HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MPEC Watch - Object {object_designation}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding-top: 20px; }}
        .section-header {{ margin-top: 30px; margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Object {object_designation}</h1>
        <p class="lead">{unpack_designation(object_designation)}</p>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Object Information</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <tr><td><strong>Designation:</strong></td><td>{object_designation}</td></tr>
                            <tr><td><strong>Unpacked:</strong></td><td>{unpack_designation(object_designation)}</td></tr>
                            <tr><td><strong>Object Type:</strong></td><td>{object_type}</td></tr>
                            <tr><td><strong>Total MPECs:</strong></td><td>{len(mpecs)}</td></tr>
                            <tr><td><strong>Total Observations:</strong></td><td>{len(observations)}</td></tr>
    """
    
    if discovery_station:
        station_name = mpccode_data.get(discovery_station, {}).get('name', discovery_station)
        html_content += f"""
                            <tr><td><strong>Discovered by:</strong></td><td>{discovery_station} ({station_name})</td></tr>
                            <tr><td><strong>Discovery Date:</strong></td><td>{discovery_date.strftime('%Y-%m-%d') if discovery_date else 'Unknown'}</td></tr>
                            <tr><td><strong>Discovery MPEC:</strong></td><td>{discovery_mpec}</td></tr>
        """
    
    html_content += """
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Related Designations</h5>
                    </div>
                    <div class="card-body">
    """
    
    if related_designations:
        html_content += """
                        <table class="table table-striped table-sm">
                            <thead>
                                <tr>
                                    <th>Designation</th>
                                    <th>Relationship</th>
                                    <th>Author</th>
                                    <th>MPEC</th>
                                </tr>
                            </thead>
                            <tbody>
        """
        
        for rel_dou, rel_type, author, mpec_id, is_retracted in related_designations:
            html_content += f"""
                                <tr>
                                    <td>{rel_dou}</td>
                                    <td>{rel_type.capitalize()}</td>
                                    <td>{author}</td>
                                    <td>{mpec_id}</td>
                                </tr>
            """
        
        html_content += """
                            </tbody>
                        </table>
        """
    else:
        html_content += "<p>No related designations found.</p>"
    
    html_content += """
                    </div>
                </div>
            </div>
        </div>
        
        <h3 class="section-header">Observation Timeline</h3>
    """
    
    if timeline_fig:
        timeline_html = timeline_fig.to_html(include_plotlyjs='cdn', div_id="timeline")
        html_content += timeline_html
    else:
        html_content += "<p>No observation data available for timeline.</p>"
    
    html_content += """
        <h3 class="section-header">Observatory Contributions</h3>
    """
    
    if station_fig:
        station_html = station_fig.to_html(include_plotlyjs='cdn', div_id="stations")
        html_content += station_html
    else:
        html_content += "<p>No station contribution data available.</p>"
    
    html_content += """
        <h3 class="section-header">MPEC History</h3>
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>MPEC ID</th>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Title</th>
                        <th>Stations</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for mpec in mpecs:
        mpec_date = datetime.datetime.fromtimestamp(mpec[2]).strftime('%Y-%m-%d')
        # mpec url structure: 'https://www.minorplanetcenter.net/mpec/' + century + ym[2:4] + '/' + century + ym[2:4] + halfmonth + str(tens_digit) + str(int(ones_digit)) + '.html'
        url = get_mpec_url(mpec[0])
        html_content += f"""
                    <tr>
                        <td><a href="{url}">{mpec[0]}</a></td>
                        <td>{mpec_date}</td>
                        <td>{mpec[5]}</td>
                        <td>{mpec[1][:80]}{'...' if len(mpec[1]) > 80 else ''}</td>
                        <td>{mpec[3][:50]}{'...' if len(mpec[3]) > 50 else ''}</td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
        </div>
        
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    # Write the HTML file
    output_path = os.path.join(OUTPUT_BASE_DIR, f"object_{object_designation}.html")
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated object page: {output_path}")

def get_mpec_url(mpec_id):
    """
    Generate the proper URL for an MPEC based on its ID.
    
    Args:
        mpec_id: The MPEC identifier (e.g., "MPEC 2023-A01", "MPEC 2024-B123")
        
    Returns:
        str: Full URL to the MPEC on the Minor Planet Center website
    """
    if not mpec_id or len(mpec_id) < 10:
        return "#"  # Return placeholder if invalid ID
    
    try:
        # Remove "MPEC " prefix if present
        if mpec_id.startswith("MPEC "):
            mpec_id = mpec_id[5:]
        
        # Parse MPEC ID format: YYYY-XNN where X is letter, NN is number
        parts = mpec_id.split('-')
        year = parts[0]
        letter_number = parts[1]
        letter = letter_number[0]
        number = int(letter_number[1:])
        
        # Convert year to century prefix
        if year.startswith('19'):
            century = 'J'
        elif year.startswith('20'):
            century = 'K'
        else:
            return "#"  # Unsupported year range
        
        # Use the same base-62 encoding as in proc.py
        BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        
        def encode(num, alphabet=BASE62):
            if num == 0:
                return alphabet[0]
            arr = []
            base = len(alphabet)
            while num:
                num, rem = divmod(num, base)
                arr.append(alphabet[rem])
            arr.reverse()
            return ''.join(arr)
        
        # Calculate tens and ones digits using the same logic as proc.py
        tens_digit = encode(int(number // 10))
        ones_digit = number - (number // 10) * 10
        
        # Format: https://www.minorplanetcenter.net/mpec/K24/K24A01.html
        # Pattern: /mpec/{century}{yy}/{century}{yy}{letter}{tens_digit}{ones_digit}.html
        year_suffix = year[2:4]
        filename = f"{century}{year_suffix}{letter}{tens_digit}{int(ones_digit)}"
        url = f"https://www.minorplanetcenter.net/mpec/{century}{year_suffix}/{filename}.html"
        
        return url
        
    except (IndexError, ValueError, TypeError):
        # If parsing fails, return a search URL
        return f"https://www.minorplanetcenter.net/mpec/"

def log_error_to_csv(object_designation, error_message, context=""):
    """Log errors to CSV file with timestamp."""
    log_dir = "../logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create filename with current date
    log_file = os.path.join(log_dir, f"object_page_errors_{datetime.now().strftime('%Y%m%d')}.csv")
    
    # Check if file exists to write header
    file_exists = os.path.exists(log_file)
    
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(['Timestamp', 'Object', 'Error', 'Context'])
        
        # Write error row
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            object_designation,
            str(error_message),
            context
        ])

def get_all_objects(cursor):
    """Get all unique object designations from the database."""
    cursor.execute("""
        SELECT DISTINCT ObjectId 
        FROM Objects 
        WHERE ObjectId IS NOT NULL AND ObjectId != ''
        ORDER BY ObjectId
    """)
    return [row[0] for row in cursor.fetchall()]


def main():
    # Check for command line argument
    if len(sys.argv) > 1:
        test_object = sys.argv[1]
        print(f"MPEC Watch - Object Page Generator")
        print(f"Testing mode: Generating page for object: {test_object}")
        objects_to_process = [test_object]
    else:
        print(f"MPEC Watch - Object Page Generator")
        print(f"Production mode: Generating pages for all objects")
        objects_to_process = None  # Will be set after DB connection
    
    # Connect to database
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Load MPC codes
    try:
        with open(MPCCODE_PATH) as f:
            mpccode_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: MPC code file {MPCCODE_PATH} not found. Using empty data.")
        mpccode_data = {}
    
    # Get all objects if not in test mode
    if objects_to_process is None:
        objects_to_process = get_all_objects(cursor)
        print(f"Found {len(objects_to_process)} objects to process")
    
    # Process objects
    successful = 0
    failed = 0
    
    for i, object_designation in enumerate(objects_to_process, 1):
        try:
            if len(objects_to_process) > 1:
                print(f"Processing {i}/{len(objects_to_process)}: {object_designation}")
            
            generate_object_page(object_designation, mpccode_data, cursor)
            successful += 1
            
        except Exception as e:
            print(f"Error generating page for {object_designation}: {e}")
            failed += 1
            # Log error but continue with next object
            log_error_to_csv(object_designation, e, context=f"Page generation failed at step {i}")
    
    conn.close()
    
    print(f"\nObject page generation complete!")
    print(f"Successfully generated: {successful} pages")
    if failed > 0:
        print(f"Failed: {failed} pages")

if __name__ == "__main__":
    main()
