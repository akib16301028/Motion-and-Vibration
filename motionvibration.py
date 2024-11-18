import pandas as pd
import streamlit as st
from datetime import datetime, time
import requests

# Load username data from repository
username_df = pd.read_excel("USER NAME.xlsx")

# Define zone priority order for display
zone_priority = ["Sylhet", "Gazipur", "Shariatpur", "Narayanganj", "Faridpur", "Mymensingh"]

# Function to preprocess report files
def preprocess_report(df, alarm_type):
    df["Type"] = alarm_type  # Specify type as either 'Motion' or 'Vibration'
    df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
    df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')
    return df

# Function to count occurrences of Motion and Vibration events per Site Alias and Zone
def count_entries_by_zone(merged_df, start_time_filter=None):
    if start_time_filter:
        merged_df = merged_df[merged_df['Start Time'] >= start_time_filter]

    motion_count = merged_df[merged_df['Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = merged_df[merged_df['Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    
    final_df = pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0)
    final_df['Motion Count'] = final_df['Motion Count'].astype(int)
    final_df['Vibration Count'] = final_df['Vibration Count'].astype(int)
    
    return final_df

# Streamlit app
st.title('PulseForge')

# File upload section
motion_report_data = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
if motion_report_data and st.button("Generate Motion Report"):
    motion_report_df = pd.read_excel(motion_report_data, header=2)
    motion_report_df = preprocess_report(motion_report_df, 'Motion')
    st.success("Motion report generated successfully!")
    st.dataframe(motion_report_df)

vibration_report_data = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])
if vibration_report_data and st.button("Generate Vibration Report"):
    vibration_report_df = pd.read_excel(vibration_report_data, header=2)
    vibration_report_df = preprocess_report(vibration_report_df, 'Vibration')
    st.success("Vibration report generated successfully!")
    st.dataframe(vibration_report_df)

if motion_report_data or vibration_report_data:
    # Button for generating combined report
    if st.button("Generate Combined Report"):
        dfs = []
        if motion_report_data:
            motion_report_df = preprocess_report(pd.read_excel(motion_report_data, header=2), 'Motion')
            dfs.append(motion_report_df)
        if vibration_report_data:
            vibration_report_df = preprocess_report(pd.read_excel(vibration_report_data, header=2), 'Vibration')
            dfs.append(vibration_report_df)
        combined_report_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        
        # Sidebar options for filtering
        with st.sidebar:
            selected_date = st.date_input("Select Start Date", value=datetime.now().date())
            selected_time = st.time_input("Select Start Time", value=time(0, 0))
            start_time_filter = datetime.combine(selected_date, selected_time)

        summary_df = count_entries_by_zone(combined_report_df, start_time_filter)
        st.success("Combined report generated successfully!")
        st.dataframe(summary_df)
else:
    st.write("Please upload a report file to generate a report.")
