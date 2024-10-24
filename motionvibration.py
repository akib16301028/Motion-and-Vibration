import pandas as pd
import streamlit as st
from datetime import datetime
import requests  # For sending Telegram notifications

# Function to merge Alarm Data and Current Alarms Data
def merge_alarm_data(alarm_df, current_alarm_df):
    current_alarm_df['Start Time'] = current_alarm_df['Alarm Time']
    current_alarm_df['End Time'] = pd.NaT  # No End Time in Current Alarms, set to NaT

    alarm_columns = ['Site', 'Site Alias', 'Zone', 'Cluster', 'Start Time', 'End Time']
    current_alarm_columns = ['Site', 'Site Alias', 'Zone', 'Cluster', 'Start Time', 'End Time']

    merged_df = pd.concat([alarm_df[alarm_columns], current_alarm_df[current_alarm_columns]], ignore_index=True)
    return merged_df

# Function to display grouped data by Cluster and Zone in a table
def display_grouped_data(grouped_df, title):
    st.write(title)
    clusters = grouped_df['Cluster'].unique()

    for cluster in clusters:
        st.markdown(f"**{cluster}**")
        cluster_df = grouped_df[grouped_df['Cluster'] == cluster]
        zones = cluster_df['Zone'].unique()

        for zone in zones:
            st.markdown(f"***<span style='font-size:14px;'>{zone}</span>***", unsafe_allow_html=True)
            zone_df = cluster_df[cluster_df['Zone'] == zone]
            display_df = zone_df[['Site Alias', 'Start Time', 'End Time']].copy()
            display_df['Site Alias'] = display_df['Site Alias'].where(display_df['Site Alias'] != display_df['Site Alias'].shift())
            display_df = display_df.fillna('')
            st.table(display_df)
        st.markdown("---")

# Function to send Telegram notification
def send_telegram_notification(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # Use Markdown for plain text
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200

# Streamlit app
st.title('Odin-s-Eye: Alarm Data Analysis')

# File upload for Vibration and Motion Alarm Data
vibration_alarm_file = st.file_uploader("Upload Vibration Alarm Data Excel", type=["xlsx"])
vibration_current_alarms_file = st.file_uploader("Upload Vibration Current Alarms Data Excel", type=["xlsx"])
motion_alarm_file = st.file_uploader("Upload Motion Alarm Data Excel", type=["xlsx"])
motion_current_alarms_file = st.file_uploader("Upload Motion Current Alarms Data Excel", type=["xlsx"])

# Initialize filters for date, time, and status
if "filter_time" not in st.session_state:
    st.session_state.filter_time = datetime.now().time()
if "filter_date" not in st.session_state:
    st.session_state.filter_date = datetime.now().date()
if "status_filter" not in st.session_state:
    st.session_state.status_filter = "All"

# Proceed if all files are uploaded
if vibration_alarm_file and vibration_current_alarms_file and motion_alarm_file and motion_current_alarms_file:
    # Read Excel files
    vibration_alarm_df = pd.read_excel(vibration_alarm_file, header=2)
    vibration_current_alarms_df = pd.read_excel(vibration_current_alarms_file, header=2)
    motion_alarm_df = pd.read_excel(motion_alarm_file, header=2)
    motion_current_alarms_df = pd.read_excel(motion_current_alarms_file, header=2)

    # Merge Vibration Alarm data
    merged_vibration_df = merge_alarm_data(vibration_alarm_df, vibration_current_alarms_df)
    # Merge Motion Alarm data
    merged_motion_df = merge_alarm_data(motion_alarm_df, motion_current_alarms_df)

    # Filter inputs (date and time)
    selected_date = st.date_input("Select Date", value=st.session_state.filter_date)
    selected_time = st.time_input("Select Time", value=st.session_state.filter_time)

    # Button to clear filters
    if st.button("Clear Filters"):
        st.session_state.filter_date = datetime.now().date()
        st.session_state.filter_time = datetime.now().time()
        st.session_state.status_filter = "All"

    # Update session state only when the user changes time or date
    if selected_date != st.session_state.filter_date:
        st.session_state.filter_date = selected_date
    if selected_time != st.session_state.filter_time:
        st.session_state.filter_time = selected_time

    # Combine selected date and time into a datetime object
    filter_datetime = datetime.combine(st.session_state.filter_date, st.session_state.filter_time)

    # Filter mismatches (start time after filter date and time)
    merged_vibration_df['Start Time'] = pd.to_datetime(merged_vibration_df['Start Time'], errors='coerce')
    filtered_vibration_df = merged_vibration_df[merged_vibration_df['Start Time'] > filter_datetime]

    merged_motion_df['Start Time'] = pd.to_datetime(merged_motion_df['Start Time'], errors='coerce')
    filtered_motion_df = merged_motion_df[merged_motion_df['Start Time'] > filter_datetime]

    # Display grouped Vibration Alarm data
    if not filtered_vibration_df.empty:
        st.write(f"Vibration Alarm Data (After {filter_datetime}) grouped by Cluster and Zone:")
        display_grouped_data(filtered_vibration_df, "Filtered Vibration Alarm Data")
    else:
        st.write(f"No vibration alarms found after {filter_datetime}. Showing all vibration alarms.")
        display_grouped_data(merged_vibration_df, "All Vibration Alarm Data")

    # Display grouped Motion Alarm data
    if not filtered_motion_df.empty:
        st.write(f"Motion Alarm Data (After {filter_datetime}) grouped by Cluster and Zone:")
        display_grouped_data(filtered_motion_df, "Filtered Motion Alarm Data")
    else:
        st.write(f"No motion alarms found after {filter_datetime}. Showing all motion alarms.")
        display_grouped_data(merged_motion_df, "All Motion Alarm Data")

    # Move the "Send Telegram Notification" button to the top
    if st.button("Send Telegram Notification"):
        # Send separate messages for each zone (Vibration data)
        zones = filtered_vibration_df['Zone'].unique()
        bot_token = "YOUR_BOT_TOKEN"  # Replace with your Telegram bot token
        chat_id = "YOUR_CHAT_ID"  # Replace with your Telegram chat/group ID

        for zone in zones:
            zone_df = filtered_vibration_df[filtered_vibration_df['Zone'] == zone]
            message = f"{zone}\n"  # Zone header

            # Group by Site Alias and append Start Time and End Time
            site_aliases = zone_df['Site Alias'].unique()
            for site_alias in site_aliases:
                site_df = zone_df[zone_df['Site Alias'] == site_alias]
                message += f"{site_alias}\n"
                for _, row in site_df.iterrows():
                    end_time_display = row['End Time'] if row['End Time'] != 'Not Closed' else 'Not Closed'
                    message += f"Start Time: {row['Start Time']} End Time: {end_time_display}\n"
                message += "\n"  # Blank line between different Site Aliases

            # Send message to Telegram
            if send_telegram_notification(message, bot_token, chat_id):
                st.success(f"Notification for zone '{zone}' sent successfully!")
            else:
                st.error(f"Failed to send notification for zone '{zone}'.")
