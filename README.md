# Swiss Territory Planner

Interactive tool for reassigning IQVIA blocks between sales territories.

## Setup (one time)

1. Install Python 3.10+ if you don't have it
2. Open terminal in this folder
3. Run:
```bash
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run territory_planner.py
```

The app opens in your browser at http://localhost:8501

## How to use

1. **View the map** — blocks are colored by territory
2. **Reassign blocks:**
   - In the sidebar, filter by "From territory" to find blocks
   - Select one or more blocks in the multiselect
   - Choose the target territory
   - Click "Apply Reassignment"
3. **Add a new rep/territory** — type a name and pick a color in the sidebar
4. **Track changes** — all reassignments are shown at the bottom
5. **Export** — download the new assignments as CSV

## Files

- `territory_planner.py` — the app
- `blocks.geojson` — block boundary map (generated from swisstopo PLZ data)
- `block_data.csv` — block metadata and KPIs
- `Territory_for_Claude.xlsx` — original source data

## Adding real KPIs

Edit `block_data.csv` and add/replace columns (e.g., real sales, pharmacy counts).
The app reads this file on startup — just add columns and they'll appear.

To add new KPIs to the dashboard, edit the `summary = block_df.groupby(...)` section
in `territory_planner.py`.
