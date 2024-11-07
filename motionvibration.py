import pandas as pd
import streamlit as st
from datetime import datetime
import requests

# Function to extract the first part of the SiteName before the first underscore
def extract_site(site_name):
    return site_name.split('_')[0] if pd.notnull(site_name) and '_' in site_name else site_name

# Function to merge RMS and Current Alarms data
def merge_rms_alarms(rms_df, alarms_df):
    alarms_df['Start Time'] = alarms_df['Alarm Time']
    alarms_df['End Time'] = pd.NaT  # No End Time in Current Alarms, set to NaT

    rms_columns = ['Site', 'Site Alias', 'Zone', 'Cluster', 'Start Time', 'End Time']
    alarms_columns = ['Site', 'Site Alias', 'Zone', 'Cluster', 'Start Time', 'End Time']

    merged_df = pd.concat([rms_df[rms_columns], alarms_df[alarms_columns]], ignore_index=True)
    return merged_df

# Function to count entries by zone and site alias
def count_entries_by_zone(df, start_time_filter):
    filtered_df = df[pd.to_datetime(df['Start Time'], errors='coerce') > start_time_filter]
    motion_count = filtered_df[filtered_df['Alarm Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = filtered_df[filtered_df['Alarm Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    summary_df = pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0).astype({'Motion Count': 'int', 'Vibration Count': 'int'})
    return summary_df

# Function to send a Telegram notification
def send_telegram_notification(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200

# Function to display and send notifications
def display_and_notify(df, bot_token, chat_id):
    zones = df['Zone'].unique()

    for zone in zones:
        zone_df = df[df['Zone'] == zone]
        # Display data in Streamlit
        st.write(f"Zone: {zone}")
        st.table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])

        # Build the message
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()
        message = f"Zone: {zone}\nTotal Motion Alarm Count: {total_motion}\nTotal Vibration Alarm Count: {total_vibration}\n\n"
        for _, row in zone_df.iterrows():
            message += f"{row['Site Alias']}\nMotion: {row['Motion Count']}, Vibration: {row['Vibration Count']}\n"
        
        # Send message to Telegram
        if send_telegram_notification(message, bot_token, chat_id):
            st.success(f"Notification for zone '{zone}' sent successfully!")
        else:
            st.error(f"Failed to send notification for zone '{zone}'.")

# Streamlit app
st.title("Alarm Data Notification App")

# File Uploads
site_access_file = st.file_uploader("Upload the Site Access Excel", type=["xlsx"])
rms_file = st.file_uploader("Upload the RMS Excel", type=["xlsx"])
current_alarms_file = st.file_uploader("Upload the Current Alarms Excel", type=["xlsx"])

# Check if all files are uploaded
if site_access_file and rms_file and current_alarms_file:
    site_access_df = pd.read_excel(site_access_file)
    rms_df = pd.read_excel(rms_file, header=2)
    current_alarms_df = pd.read_excel(current_alarms_file, header=2)

    # Merge RMS and Current Alarms
    merged_rms_alarms_df = merge_rms_alarms(rms_df, current_alarms_df)

    # Filter inputs (date and time)
    selected_date = st.date_input("Select Date", value=datetime.now().date())
    selected_time = st.time_input("Select Time", value=datetime.now().time())
    filter_datetime = datetime.combine(selected_date, selected_time)

    # Get the summary data by zone
    summary_df = count_entries_by_zone(merged_rms_alarms_df, filter_datetime)

    # Telegram Bot Token and Chat ID
    bot_token = "7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME"
    chat_id = "-4537588687"
    
    # Button to send the Telegram notifications
    if st.button("Send Notifications"):
        display_and_notify(summary_df, bot_token, chat_id)
