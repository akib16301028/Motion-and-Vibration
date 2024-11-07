import pandas as pd
import streamlit as st
from datetime import datetime, time
import requests

# Define priority zones
zone_priority = ["Sylhet", "Gazipur", "Shariatpur", "Narayanganj", "Faridpur", "Mymensingh"]

# Function to preprocess report files
def preprocess_report(df, alarm_type):
    df["Type"] = alarm_type
    df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
    df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')
    return df

# Function to merge and process data
def merge_report_files(report_motion_df, report_vibration_df):
    report_motion_df = preprocess_report(report_motion_df, 'Motion')
    report_vibration_df = preprocess_report(report_vibration_df, 'Vibration')
    return pd.concat([report_motion_df, report_vibration_df], ignore_index=True)

# Count occurrences of Motion and Vibration per Site Alias and Zone
def count_entries_by_zone(merged_df, start_time_filter=None):
    if start_time_filter:
        merged_df = merged_df[merged_df['Start Time'] >= start_time_filter]

    motion_count = merged_df[merged_df['Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = merged_df[merged_df['Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    
    return pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0).astype(int)

# Function to send data to Telegram
def send_to_telegram(message, chat_id, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    return requests.post(url, data=payload).ok

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

# Upload files
report_motion_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
report_vibration_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])

if report_motion_file and report_vibration_file:
    report_motion_df = pd.read_excel(report_motion_file, header=2)
    report_vibration_df = pd.read_excel(report_vibration_file, header=2)

    merged_df = merge_report_files(report_motion_df, report_vibration_df)

    # Sidebar for date filter and button
    with st.sidebar:
        selected_date = st.date_input("Select Start Date", value=datetime.now().date())
        selected_time = st.time_input("Select Start Time", value=time(0, 0))
        start_time_filter = datetime.combine(selected_date, selected_time)
        
        # Button to send data to Telegram
        if st.button("Send Data to Telegram"):
            summary_df = count_entries_by_zone(merged_df, start_time_filter)
            
            # Filter prioritized zones
            prioritized_df = summary_df[summary_df['Zone'].isin(zone_priority)]
            prioritized_df['Zone'] = pd.Categorical(prioritized_df['Zone'], categories=zone_priority, ordered=True)
            prioritized_df = prioritized_df.sort_values('Zone')
            
            # Prepare message format for each prioritized zone
            message = f"<b>Alarm Summary Report</b>\n\nStart Date: {selected_date}\nStart Time: {selected_time}\n\n"
            
            for zone in zone_priority:
                zone_df = prioritized_df[prioritized_df['Zone'] == zone]
                if not zone_df.empty:
                    total_motion = zone_df['Motion Count'].sum()
                    total_vibration = zone_df['Vibration Count'].sum()

                    # Append zone details
                    message += f"<b>{zone} Zone</b>:\n"
                    message += f"Total Motion Alarm count: {total_motion}\nTotal Vibration Alarm count: {total_vibration}\n\n"

                    # Append each site alias's counts
                    for _, row in zone_df.iterrows():
                        message += f"Site: {row['Site Alias']} | Motion: {row['Motion Count']} | Vibration: {row['Vibration Count']}\n"
                    message += "\n"

            # Send message to Telegram
            success = send_to_telegram(message, chat_id="-4537588687", bot_token="7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME")
            if success:
                st.sidebar.success("Data sent to Telegram successfully!")
            else:
                st.sidebar.error("Failed to send data to Telegram.")

    # Display tables
    summary_df = count_entries_by_zone(merged_df, start_time_filter)
    prioritized_df = summary_df[summary_df['Zone'].isin(zone_priority)]
    non_prioritized_df = summary_df[~summary_df['Zone'].isin(zone_priority)]
    prioritized_df['Zone'] = pd.Categorical(prioritized_df['Zone'], categories=zone_priority, ordered=True)
    prioritized_df = prioritized_df.sort_values('Zone')

    for zone in prioritized_df['Zone'].unique():
        st.write(f"### {zone}")
        zone_df = prioritized_df[prioritized_df['Zone'] == zone]
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()
        st.write(f"Total Motion Alarm count: {total_motion}")
        st.write(f"Total Vibration Alarm count: {total_vibration}")
        st.table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])

    for zone in sorted(non_prioritized_df['Zone'].unique()):
        st.write(f"### {zone}")
        zone_df = non_prioritized_df[non_prioritized_df['Zone'] == zone]
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()
        st.write(f"Total Motion Alarm count: {total_motion}")
        st.write(f"Total Vibration Alarm count: {total_vibration}")
        st.table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])
else:
    st.write("Please upload both Motion and Vibration Report Data files.")
