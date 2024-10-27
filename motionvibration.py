import pandas as pd
import streamlit as st
import requests

# Function to extract the first part of the SiteName before the first underscore
def extract_site(site_name):
    return site_name.split('_')[0] if pd.notnull(site_name) and '_' in site_name else site_name

# Function to merge Motion and Vibration data
def merge_motion_vibration(motion_df, vibration_df):
    motion_df['Start Time'] = pd.to_datetime(motion_df['Start Time'], errors='coerce')
    motion_df['End Time'] = pd.to_datetime(motion_df['End Time'], errors='coerce')

    vibration_df['Start Time'] = pd.to_datetime(vibration_df['Start Time'], errors='coerce')
    vibration_df['End Time'] = pd.to_datetime(vibration_df['End Time'], errors='coerce')

    motion_df['Type'] = 'Motion'
    vibration_df['Type'] = 'Vibration'
    
    merged_df = pd.concat([motion_df, vibration_df], ignore_index=True)
    return merged_df

# Function to count entries for Motion and Vibration per site alias and zone
def count_entries_by_zone(merged_df, start_time_filter=None):
    # Apply start time filter if provided
    if start_time_filter:
        merged_df = merged_df[merged_df['Start Time'] > start_time_filter]

    motion_count = merged_df[merged_df['Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = merged_df[merged_df['Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    
    # Merge motion and vibration counts by Zone and Site Alias
    final_df = pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0)
    final_df['Motion Count'] = final_df['Motion Count'].astype(int)
    final_df['Vibration Count'] = final_df['Vibration Count'].astype(int)

    # Add a total row for each zone with bold formatting
    total_row = pd.DataFrame({
        'Zone': [''],  # Leave Zone empty in the total row
        'Site Alias': ['Total'],
        'Motion Count': [final_df['Motion Count'].sum()],
        'Vibration Count': [final_df['Vibration Count'].sum()]
    })
    
    final_df = pd.concat([final_df, total_row], ignore_index=True)
    return final_df

# Function to display detailed entries for a specific site
def display_detailed_entries(merged_df, site_alias):
    filtered = merged_df[merged_df['Site Alias'] == site_alias][['Site Alias', 'Start Time', 'End Time']]
    if not filtered.empty:
        st.table(filtered)
    else:
        st.write("No data for this site.")

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

motion_alarm_file = st.file_uploader("Upload the Motion Alarm Data", type=["xlsx"])
vibration_alarm_file = st.file_uploader("Upload the Vibration Alarm Data", type=["xlsx"])

if motion_alarm_file and vibration_alarm_file:
    # Load the data
    motion_df = pd.read_excel(motion_alarm_file, header=2)
    vibration_df = pd.read_excel(vibration_alarm_file, header=2)

    # Merge data
    merged_df = merge_motion_vibration(motion_df, vibration_df)

    # Start time filter input
    start_time_input = st.sidebar.text_input("Enter Start Time (YYYY-MM-DD HH:MM:SS)", "")
    start_time_filter = pd.to_datetime(start_time_input, errors='coerce') if start_time_input else None

    # Display summarized count table for each zone
    summary_df = count_entries_by_zone(merged_df, start_time_filter)

    zones = summary_df['Zone'].unique()
    for zone in zones:
        if zone:
            st.write(f"### Zone: {zone}")
            zone_df = summary_df[summary_df['Zone'] == zone].copy()
            zone_df.style.set_properties(subset=pd.IndexSlice[0, :], **{'font-weight': 'bold'})  # Bold header row
            st.table(zone_df.style.format("{:.0f}"))  # Format for integer counts only
    
    # Interactive search for specific sites
    site_search = st.sidebar.text_input("Search for a specific site alias (case-sensitive)")
    if site_search:
        st.sidebar.write("Showing detailed data for:", site_search)
        display_detailed_entries(merged_df, site_search)

else:
    st.write("Please upload all required files.")
