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
    # Set 'Type' for report data
    report_motion_df['Type'] = 'Motion'
    report_vibration_df['Type'] = 'Vibration'
    
    # Standardize columns across all files
    for df in [report_motion_df, report_vibration_df]:
        df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
        df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')

    # Process current alarm data with renamed Start Time and null End Time
    current_motion_df = preprocess_current_alarm(current_motion_df, 'Motion')
    current_vibration_df = preprocess_current_alarm(current_vibration_df, 'Vibration')

    # Concatenate all data into a single dataframe
    merged_df = pd.concat([report_motion_df, current_motion_df, report_vibration_df, current_vibration_df], ignore_index=True)
    return merged_df

# Function to count occurrences of Motion and Vibration events per Site Alias and Zone
def count_entries_by_zone(merged_df, start_time_filter=None):
    if start_time_filter:
        merged_df = merged_df[merged_df['Start Time'] > start_time_filter]

    motion_count = merged_df[merged_df['Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = merged_df[merged_df['Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    
    # Merge counts for motion and vibration by Zone and Site Alias
    final_df = pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0)
    final_df['Motion Count'] = final_df['Motion Count'].astype(int)
    final_df['Vibration Count'] = final_df['Vibration Count'].astype(int)

    # Add Total Row within each table
    total_row = final_df[['Motion Count', 'Vibration Count']].sum().to_frame().T
    total_row['Zone'] = 'Total'
    total_row['Site Alias'] = 'All'
    final_df = pd.concat([final_df, total_row], ignore_index=True)

    return final_df

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
    # Load data from files
    report_motion_df = pd.read_excel(report_motion_file, header=2)
    current_motion_df = pd.read_excel(current_motion_file, header=2)
    report_vibration_df = pd.read_excel(report_vibration_file, header=2)
    current_vibration_df = pd.read_excel(current_vibration_file, header=2)

    # Merge data
    merged_df = merge_motion_vibration(report_motion_df, current_motion_df, report_vibration_df, current_vibration_df)

    # Date and time filter input with persistence
    selected_date = st.sidebar.date_input("Select Start Date", value=datetime.now().date())
    selected_time = st.sidebar.time_input("Select Start Time", value=time(0, 0))
    start_time_filter = datetime.combine(selected_date, selected_time)

    # Display summarized count table for each zone with inline total row
    summary_df = count_entries_by_zone(merged_df, start_time_filter)

    zones = summary_df['Zone'].unique()
    for zone in zones:
        st.write(f"### Zone: {zone}")
        zone_df = summary_df[summary_df['Zone'] == zone]
        st.table(zone_df)

    # Interactive search for specific sites
    site_search = st.sidebar.text_input("Search for a specific site alias")
    if site_search:
        display_detailed_entries(merged_df, site_search)
else:
    st.write("Please upload all required files.")
