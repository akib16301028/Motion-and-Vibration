import pandas as pd
import streamlit as st
from datetime import datetime, time

# Function to preprocess current alarm files to match expected column names
def preprocess_current_alarm(df, alarm_type):
    df = df.rename(columns={"Alarm Time": "Start Time"})
    df["End Time"] = None  # Set End Time as None for current alarm entries
    df["Type"] = alarm_type  # Specify type as either 'Motion' or 'Vibration'
    return df

# Function to merge motion and vibration data from reports and current alarms
def merge_motion_vibration(report_motion_df, current_motion_df, report_vibration_df, current_vibration_df):
    report_motion_df['Type'] = 'Motion'
    report_vibration_df['Type'] = 'Vibration'
    
    for df in [report_motion_df, report_vibration_df]:
        df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
        df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')

    current_motion_df = preprocess_current_alarm(current_motion_df, 'Motion')
    current_vibration_df = preprocess_current_alarm(current_vibration_df, 'Vibration')

    merged_df = pd.concat([report_motion_df, current_motion_df, report_vibration_df, current_vibration_df], ignore_index=True)
    return merged_df

# Function to count occurrences of Motion and Vibration events per Site Alias and Zone
def count_entries_by_zone(merged_df, start_time_filter=None):
    if start_time_filter:
        merged_df = merged_df[merged_df['Start Time'] > start_time_filter]

    motion_count = merged_df[merged_df['Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = merged_df[merged_df['Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    
    final_df = pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0)
    final_df['Motion Count'] = final_df['Motion Count'].astype(int)
    final_df['Vibration Count'] = final_df['Vibration Count'].astype(int)
    
    # Group by Zone and add a total row for each zone
    final_df_list = []
    for zone, zone_df in final_df.groupby('Zone'):
        # Calculate total for the current zone
        total_row = pd.DataFrame({
            'Zone': [''],  # Omit the zone name for the total row
            'Site Alias': ['Total'],
            'Motion Count': [zone_df['Motion Count'].sum()],
            'Vibration Count': [zone_df['Vibration Count'].sum()]
        })
        # Append the total row to the zone-specific DataFrame
        zone_df = pd.concat([zone_df, total_row], ignore_index=True)
        final_df_list.append(zone_df)

    # Combine all zones' DataFrames back into one
    return pd.concat(final_df_list, ignore_index=True)

# Function to display detailed entries for a specific site alias
def display_detailed_entries(merged_df, site_alias):
    filtered = merged_df[merged_df['Site Alias'] == site_alias][['Site Alias', 'Start Time', 'End Time', 'Type']]
    if not filtered.empty:
        st.sidebar.write(f"Detailed entries for Site Alias: {site_alias}")
        st.sidebar.table(filtered)
    else:
        st.sidebar.write("No data for this site.")

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

# File upload section
report_motion_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
current_motion_file = st.file_uploader("Upload the Motion Current Alarms Data", type=["xlsx"])
report_vibration_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])
current_vibration_file = st.file_uploader("Upload the Vibration Current Alarms Data", type=["xlsx"])

if report_motion_file and current_motion_file and report_vibration_file and current_vibration_file:
    report_motion_df = pd.read_excel(report_motion_file, header=2)
    current_motion_df = pd.read_excel(current_motion_file, header=2)
    report_vibration_df = pd.read_excel(report_vibration_file, header=2)
    current_vibration_df = pd.read_excel(current_vibration_file, header=2)

    merged_df = merge_motion_vibration(report_motion_df, current_motion_df, report_vibration_df, current_vibration_df)

    selected_date = st.sidebar.date_input("Select Start Date", value=datetime.now().date())
    selected_time = st.sidebar.time_input("Select Start Time", value=time(0, 0))
    start_time_filter = datetime.combine(selected_date, selected_time)

    summary_df = count_entries_by_zone(merged_df, start_time_filter)

    zones = summary_df['Zone'].unique()
    for zone in zones:
        st.write(f"### Zone: {zone}")
        zone_df = summary_df[summary_df['Zone'] == zone]

        # Bold headers and total rows, and display as a single table
        styled_table = zone_df.style.set_table_attributes('style="font-weight: bold;"').set_table_styles(
            [{'selector': 'thead th', 'props': [('font-weight', 'bold')]}]
        ).set_properties(subset=['Site Alias'], **{'font-weight': 'bold'}, subset=['Motion Count', 'Vibration Count'])
        
        st.table(styled_table)

    site_search = st.sidebar.text_input("Search for a specific site alias")
    if site_search:
        display_detailed_entries(merged_df, site_search)
else:
    st.write("Please upload all required files.")
