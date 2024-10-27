import pandas as pd
import streamlit as st
from datetime import datetime

# Function to extract the first part of the SiteName before the first underscore
def extract_site(site_name):
    return site_name.split('_')[0] if pd.notnull(site_name) and '_' in site_name else site_name

# Function to merge motion and vibration data from reports and current alarms
def merge_motion_vibration(report_motion_df, current_motion_df, report_vibration_df, current_vibration_df):
    # Add 'Type' column to identify data source
    report_motion_df['Type'] = 'Motion'
    current_motion_df['Type'] = 'Motion'
    report_vibration_df['Type'] = 'Vibration'
    current_vibration_df['Type'] = 'Vibration'
    
    # Standardize columns across files
    for df in [report_motion_df, current_motion_df, report_vibration_df, current_vibration_df]:
        df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
        df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')
    
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

    return final_df

# Function to display detailed entries for a specific site alias
def display_detailed_entries(merged_df, site_alias):
    filtered = merged_df[merged_df['Site Alias'] == site_alias][['Site Alias', 'Start Time', 'End Time', 'Type']]
    if not filtered.empty:
        st.write(f"Detailed entries for Site Alias: {site_alias}")
        st.table(filtered)
    else:
        st.write("No data for this site.")

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

    # Date and time filter input
    selected_date = st.sidebar.date_input("Select Start Date", value=datetime.now().date())
    selected_time = st.sidebar.time_input("Select Start Time", value=datetime.now().time())
    start_time_filter = datetime.combine(selected_date, selected_time)

    # Display summarized count table for each zone
    summary_df = count_entries_by_zone(merged_df, start_time_filter)

    zones = summary_df['Zone'].unique()
    for zone in zones:
        st.write(f"### Zone: {zone}")
        zone_df = summary_df[summary_df['Zone'] == zone]
        st.table(zone_df)
        total_row = pd.DataFrame(zone_df[['Motion Count', 'Vibration Count']].sum()).T
        total_row.index = ['Total']
        st.table(total_row)

    # Interactive search for specific sites
    site_search = st.sidebar.text_input("Search for a specific site alias")
    if site_search:
        display_detailed_entries(merged_df, site_search)
else:
    st.write("Please upload all required files.")
