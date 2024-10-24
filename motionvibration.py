import pandas as pd
import streamlit as st
from datetime import datetime
import requests

# Function to merge Current Alarms data for Motion and Vibration
def merge_current_alarms(motion_current_df, vibration_current_df):
    motion_current_df['Type'] = 'Motion'
    vibration_current_df['Type'] = 'Vibration'
    
    merged_df = pd.concat([motion_current_df, vibration_current_df], ignore_index=True)
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
def display_detailed_entries(merged_df, site_alias):
    st.write(f"Details for site alias: {site_alias}")
    
    site_filtered = merged_df[merged_df['Site Alias'] == site_alias][['Site Alias', 'Start Time', 'End Time', 'Type']]
    
    if not site_filtered.empty:
        st.table(site_filtered)
    else:
        st.write("No alarms for this site.")

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

# File upload sections
motion_current_file = st.file_uploader("Upload the Motion Current Alarms Data", type=["xlsx"])
vibration_current_file = st.file_uploader("Upload the Vibration Current Alarms Data", type=["xlsx"])
motion_report_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
vibration_report_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])

if motion_current_file and vibration_current_file and motion_report_file and vibration_report_file:
    # Load the data
    motion_current_df = pd.read_excel(motion_current_file, header=2)
    vibration_current_df = pd.read_excel(vibration_current_file, header=2)
    motion_report_df = pd.read_excel(motion_report_file, header=2)
    vibration_report_df = pd.read_excel(vibration_report_file, header=2)

    # Merge Current Alarms data
    merged_df = merge_current_alarms(motion_current_df, vibration_current_df)

    # Display summarized table with counts
    st.write("### Motion and Vibration Counts by Zone and Site Alias")
    summary_df = count_entries_by_zone(merged_df)
    st.table(summary_df)

    # Interactive search for specific sites
    site_search = st.sidebar.text_input("Search for a specific site alias (case-sensitive)")

    if site_search:
        st.sidebar.write("Showing detailed data for:", site_search)
        display_detailed_entries(merged_df, site_search)

    # Telegram notification feature
    if st.sidebar.button("Send Telegram Notification"):
        # Prepare notification message
        zones = summary_df['Zone'].unique()
        bot_token = "YOUR_BOT_TOKEN"  # Your bot token
        chat_id = "YOUR_CHAT_ID"  # Your group ID

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
