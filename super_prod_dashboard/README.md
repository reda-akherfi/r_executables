# Super Productivity Dashboard

A comprehensive dashboard for visualizing SuperProductivity data with interactive charts and analytics.

## Features

- **Interactive Calendar**: Visualize daily work time with calendar view
- **Time Tracking Analytics**: Multiple charts showing time spent per day, project, and tag
- **Health Metrics**: Track water intake, media consumption, and workout time
- **Project Analysis**: Detailed breakdown of time spent across projects
- **Tag Distribution**: Visualize how time is distributed across different tags
- **Color & Icon Sync**: Automatic synchronization of project and tag colors/icons from SuperProductivity

## Data Loading

The dashboard automatically finds and loads the most recent SuperProductivity backup file from:

1. **SuperProductivity Backup Directory**: `C:\Users\redaa\AppData\Roaming\superProductivity\backups`
2. **Project Root Directory**: Any JSON files in the current project directory

The system will:
- Search for all JSON files in both locations
- Validate that files are valid SuperProductivity backups
- Select the most recent file based on modification time
- Normalize the data structure for consistent processing

## Files

- `dashboard_script.py`: Main Streamlit dashboard application
- `data_loader.py`: Modular data loading and validation logic
- `color_sync.py`: Color and icon synchronization between SuperProductivity and dashboard
- `requirements.txt`: Python dependencies

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the dashboard:
   ```bash
   streamlit run dashboard_script.py
   ```

3. Test color synchronization:
   ```bash
   python color_sync.py
   ```

## TODO

* [ ] a button to toggle limiting time data to the last 30 days in both pie charts
* [ ] a way to make sure time is being tracked in sp
* [ ] change to 1/4 etc.
* [x] synchronize colors for projects and tags between sp and the dashboard
* [ ] human readable time in daily media watching and workout graphs
* [ ] maybe incorporate the icons and images themselves
