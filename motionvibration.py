import pandas as pd
import streamlit as st
from datetime import datetime
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
def count_entries_by_zone(merged_df):
    motion_count = merged_df[merged_df['Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = merged_df[merged_df['Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    
    # Merge motion and vibration counts by Zone and Site Alias
    final_df = pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0)
    final_df['Motion Count'] = final_df['Motion Count'].astype(int)
    final_df['Vibration Count'] = final_df['Vibration Count'].astype(int)
    
    # Calculate the totals
    total_motion = final_df['Motion Count'].sum()
    total_vibration = final_df['Vibration Count'].sum()
    
    # Add the total row
    total_row = pd.DataFrame([['Total', '', total_motion, total_vibration]], columns=['Zone', 'Site Alias', 'Motion Count', 'Vibration Count'])
    final_df = pd.concat([final_df, total_row], ignore_index=True)
    
    return final_df

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

# File upload sections
motion_alarm_file = st.file_uploader("Upload the Motion Alarm Data", type=["xlsx"])
vibration_alarm_file = st.file_uploader("Upload the Vibration Alarm Data", type=["xlsx"])
motion_current_file = st.file_uploader("Upload the Motion Current Alarms Data", type=["xlsx"])
vibration_current_file = st.file_uploader("Upload the Vibration Current Alarms Data", type=["xlsx"])

# Date and Time widgets
selected_date = st.date_input("Select Date", value=datetime.now().date())
selected_time = st.time_input("Select Time", value=datetime.now().time())

if motion_alarm_file and vibration_alarm_file and motion_current_file and vibration_current_file:
    # Load the data
    motion_df = pd.read_excel(motion_alarm_file, header=2)
    vibration_df = pd.read_excel(vibration_alarm_file, header=2)
    motion_current_df = pd.read_excel(motion_current_file, header=2)
    vibration_current_df = pd.read_excel(vibration_current_file, header=2)

    # Merge data
    merged_df = merge_motion_vibration(motion_df, vibration_df)

    # Display summarized table with counts
    st.write("### Motion and Vibration Counts by Zone and Site Alias")
    summary_df = count_entries_by_zone(merged_df)
    
    # Filter based on selected date and time
    filter_datetime = datetime.combine(selected_date, selected_time)
    filtered_summary_df = summary_df[summary_df['Start Time'] > filter_datetime]

    # Show the filtered summary
    st.table(filtered_summary_df)

    # Add a download button for the summary (optional)
    csv = summary_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download Summary Data as CSV", data=csv, file_name='summary_data.csv', mime='text/csv')

else:
    st.write("Please upload all required files.")
