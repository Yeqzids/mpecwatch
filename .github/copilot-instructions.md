# GitHub Copilot Instructions for MPEC Watch

## Project Overview
MPEC Watch is a Python project that processes, analyzes, and visualizes statistical data from Minor Planet Electronic Circulars (MPECs) provided by the International Astronomical Union's Minor Planet Center. The project generates web pages with various statistical metrics and plots about astronomical observations, discoveries, and updates related to minor planets.

## Key Components
- **Data Processing**: Scripts that fetch MPEC data, process it, and store in SQLite databases (`mpecwatch_v3.db`)
- **Web Page Generation**: Scripts in `makepages/` folder that generate HTML pages with statistics and visualizations
- **Visualization**: Generation of charts and plots showing observatory statistics, observer activity, and discovery metrics

## Main Files and Their Purposes
- `mpccode.py`: Processes Minor Planet Center observatory codes and location data
- `proc.py`: Main MPEC data processing script that populates the database
- `makepages/*.py`: Collection of scripts that generate different parts of the website
  - `home.py`: Generates the main index page
  - `Individual_OMF.py`: Creates figures for individual observatories (Observers, Measurers, Facilities)
  - `Overall_OMF.py`: Aggregates data across all observatories
  - `StationMPECGraph.py`: Generates web pages for individual observatory stations

## Code Structure and Style Guidelines
- Python 3.x with standard indentation (4 spaces)
- Database interactions using SQLite3
- Web page generation using HTML/Bootstrap
- Data visualization primarily with Plotly
- Follows scientific computing conventions for astronomy data

## Dependencies
- BeautifulSoup4 for HTML parsing
- Pandas for data manipulation
- Plotly for interactive visualizations
- NumPy for numerical operations
- Other dependencies listed in requirements.txt

## Common Tasks
- Adding new statistical metrics to the dashboard
- Updating data processing logic as MPEC format changes
- Creating new visualization types
- Enhancing web page generation with new features
- Optimizing database queries for performance
- Adding support for new types of astronomical objects or MPECs

## Project-Specific Terminology
- **MPEC**: Minor Planet Electronic Circular - announcements from the MPC
- **MPC**: Minor Planet Center - the organization that publishes MPECs
- **Observatory Code/Station**: 3-character code identifying an observatory
- **OMF**: Observers, Measurers, and Facilities
- **NEA**: Near-Earth Asteroid
- **TNO**: Trans-Neptunian Object
- **DOU**: Daily Orbit Update

## Important Notes
- When modifying database code, maintain compatibility with the existing schema
- Simplify logic whenever possible to improve maintainability
- HTML templates follow Bootstrap conventions and should maintain consistent styling
- MPEC parsing logic may need to handle edge cases in MPEC formatting
- New visualizations should match the style of existing charts
- The project has dependencies on external data sources that may change format over time