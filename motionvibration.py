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

# Function to display detailed entries for a specific site
def display_detailed_entries(motion_df, vibration_df, site_alias):
    st.write(f"Details for site alias: {site_alias}")
    
    motion_filtered = motion_df[motion_df['Site Alias'] == site_alias][['Site Alias', 'Start Time', 'End Time']]
    vibration_filtered = vibration_df[vibration_df['Site Alias'] == site_alias][['Site Alias', 'Start Time', 'End Time']]
    
    st.write("**Motion**")
    if not motion_filtered.empty:
        st.table(motion_filtered)
    else:
        st.write("No motion alarms for this site.")
    
    st.write("**Vibration**")
    if not vibration_filtered.empty:
        st.table(vibration_filtered)
    else:
        st.write("No vibration alarms for this site.")

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
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

motion_alarm_file = st.file_uploader("Upload the Motion Alarm Data", type=["xlsx"])
vibration_alarm_file = st.file_uploader("Upload the Vibration Alarm Data", type=["xlsx"])
motion_current_file = st.file_uploader("Upload the Motion Current Alarms Data", type=["xlsx"])
vibration_current_file = st.file_uploader("Upload the Vibration Current Alarms Data", type=["xlsx"])

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
    st.table(summary_df)

    # Interactive search for specific sites
    site_search = st.sidebar.text_input("Search for a specific site alias (case-sensitive)")

    if site_search:
        st.sidebar.write("Showing detailed data for:", site_search)
        display_detailed_entries(motion_df, vibration_df, site_search)

    # Telegram notification feature
    if st.sidebar.button("Send Telegram Notification"):
        # Prepare notification message
        zones = summary_df['Zone'].unique()
        bot_token = "7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME"  # Your bot token
        chat_id = "-1001509039244"  # Your group ID

        for zone in zones:
            zone_df = summary_df[summary_df['Zone'] == zone]
            message = f"{zone}\n"

            for _, row in zone_df.iterrows():
                message += f"{row['Site Alias']} - Motion: {row['Motion Count']}, Vibration: {row['Vibration Count']}\n"

            # Send message to Telegram
            if send_telegram_notification(message, bot_token, chat_id):
                st.sidebar.success(f"Notification for zone '{zone}' sent successfully!")
            else:
                st.sidebar.error(f"Failed to send notification for zone '{zone}'.")

else:
    st.write("Please upload all required files.")
