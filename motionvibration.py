import pandas as pd
import streamlit as st
from datetime import datetime, time
import requests

# Load username data from repository
username_df = pd.read_excel("USER NAME.xlsx")

# Define zone priority order for Telegram notifications
zone_priority = ["Sylhet", "Gazipur", "Shariatpur", "Narayanganj", "Faridpur", "Mymensingh"]

# Function to preprocess report files
def preprocess_report(df, alarm_type):
    df["Type"] = alarm_type  # Specify type as either 'Motion' or 'Vibration'
    df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
    df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')
    return df

# Function to merge motion and vibration data from report files
def merge_report_files(report_motion_df, report_vibration_df):
    report_motion_df = preprocess_report(report_motion_df, 'Motion')
    report_vibration_df = preprocess_report(report_vibration_df, 'Vibration')
    
    merged_df = pd.concat([report_motion_df, report_vibration_df], ignore_index=True)
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
    
    return final_df

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

# File upload section
report_motion_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
report_vibration_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])

if report_motion_file and report_vibration_file:
    report_motion_df = pd.read_excel(report_motion_file, header=2)
    report_vibration_df = pd.read_excel(report_vibration_file, header=2)

    merged_df = merge_report_files(report_motion_df, report_vibration_df)

    # Sidebar options for date filter and notifications
    with st.sidebar:
        # Date and time filter
        selected_date = st.date_input("Select Start Date", value=datetime.now().date())
        selected_time = st.time_input("Select Start Time", value=time(0, 0))
        start_time_filter = datetime.combine(selected_date, selected_time)

        # Zone filter option
        zone_filter = st.selectbox("Select Zone to Filter", options=["All"] + zone_priority)

    # Filtered summary based on selected zone
    summary_df = count_entries_by_zone(merged_df, start_time_filter)
    if zone_filter != "All":
        summary_df = summary_df[summary_df['Zone'] == zone_filter]

    zones = summary_df['Zone'].unique()
    for zone in zones:
        st.write(f"### {zone}")
        zone_df = summary_df[summary_df['Zone'] == zone]

        # Calculate total counts for the zone
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()

        # Display total counts
        st.write(f"Total Motion Alarm count: {total_motion}")
        st.write(f"Total Vibration Alarm count: {total_vibration}")

        # Display the detailed table without the Zone column
        st.table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])

else:
    st.write("Please upload all required files.")
