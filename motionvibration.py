import pandas as pd
import streamlit as st
from datetime import datetime, time
import requests

# Load username data from repository
username_df = pd.read_excel("USER NAME.xlsx")

# Define zone priority order for Telegram notifications
zone_priority = ["Sylhet", "Gazipur", "Shariatpur", "Narayanganj", "Faridpur", "Mymensingh"]

# Function to preprocess current alarm files to match expected column names
def preprocess_current_alarm(df, alarm_type):
    df = df.rename(columns={"Alarm Time": "Start Time"})
    df["End Time"] = None  # Set End Time as None for current alarm entries
    df["Type"] = alarm_type  # Specify type as either 'Motion' or 'Vibration'
    return df

# Function to merge motion and vibration data from reports and current alarms
def merge_motion_vibration(report_motion_df, current_motion_df, report_vibration_df, current_vibration_df):
    report_motion_df['Type'] = 'Motion'
    report_vibration_df['Type'] = 'Vibration'
    
    for df in [report_motion_df, report_vibration_df]:
        df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
        df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')

    current_motion_df = preprocess_current_alarm(current_motion_df, 'Motion')
    current_vibration_df = preprocess_current_alarm(current_vibration_df, 'Vibration')

    merged_df = pd.concat([report_motion_df, current_motion_df, report_vibration_df, current_vibration_df], ignore_index=True)
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

# Function to generate the Telegram message for each zone
def generate_telegram_message(zone, zone_df, total_motion, total_vibration, usernames):
    # Construct message with multiple contacts if needed
    username_mentions = " ".join([f"@{name}" for name in usernames])
    
    message = f"**{zone}**\n\n"
    message += f"Total Motion Alarm count: {total_motion}\nTotal Vibration Alarm count: {total_vibration}\n\n"

    for _, row in zone_df.iterrows():
        message += f"{row['Site Alias']} : \n"
        message += f"Motion Count: {row['Motion Count']}\n"
        message += f"Vibration Count: {row['Vibration Count']}\n\n"

    message += f"{username_mentions} please take care."
    
    return message

# Function to send Telegram notification for specified zones only
def send_telegram_notification(messages):
    chat_id = "-4537588687"
    bot_token = "7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME"
    
    # Sending all messages via Telegram API
    for zone, message in messages.items():
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, data=data)
        
        if response.status_code != 200:
            st.error(f"Failed to send notification for {zone}.")
            return

    st.success("Notifications sent successfully!")

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

# File upload section
report_motion_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
current_motion_file = st.file_uploader("Upload the Motion Current Alarms Data", type=["xlsx"])
report_vibration_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])
current_vibration_file = st.file_uploader("Upload the Vibration Current Alarms Data", type=["xlsx"])

if report_motion_file and current_motion_file and report_vibration_file and current_vibration_file:
    report_motion_df = pd.read_excel(report_motion_file, header=2)
    current_motion_df = pd.read_excel(current_motion_file, header=2)
    report_vibration_df = pd.read_excel(report_vibration_file, header=2)
    current_vibration_df = pd.read_excel(current_vibration_file, header=2)

    merged_df = merge_motion_vibration(report_motion_df, current_motion_df, report_vibration_df, current_vibration_df)

    # Sidebar options for download, zone filter, and notifications
    with st.sidebar:
        # Send notification button at the top
        if st.button("Send Telegram Notification", help="Send alarm summaries to Telegram"):
            if 'messages' in st.session_state and st.session_state.messages:
                # Send generated messages to Telegram
                send_telegram_notification(st.session_state.messages)
            else:
                st.error("No messages to send. Please generate the messages first.")

        # Date and time filter
        selected_date = st.date_input("Select Start Date", value=datetime.now().date())
        selected_time = st.time_input("Select Start Time", value=time(0, 0))
        start_time_filter = datetime.combine(selected_date, selected_time)

        # Zone filter option
        zone_filter = st.selectbox("Select Zone to Filter", options=["All"] + list(zone_priority))

        # Generate message button
        if st.button("Generate Message", help="Generate alarm summaries for each zone"):
            summary_df = count_entries_by_zone(merged_df, start_time_filter)
            if zone_filter != "All":
                summary_df = summary_df[summary_df['Zone'] == zone_filter]

            zones = sorted(summary_df['Zone'].unique(), key=lambda z: (zone_priority.index(z) if z in zone_priority else float('inf')))
            
            st.session_state.messages = {}  # Clear previous messages
            for zone in zones:
                zone_df = summary_df[summary_df['Zone'] == zone]
                total_motion = zone_df['Motion Count'].sum()
                total_vibration = zone_df['Vibration Count'].sum()

                # Get all usernames for the zone
                usernames = username_df[username_df['Zone'] == zone]['Name'].dropna().unique()
                
                # Generate the message for this zone
                st.session_state.messages[zone] = generate_telegram_message(zone, zone_df, total_motion, total_vibration, usernames)

            # Display generated messages
            st.subheader("Generated Messages")
            for zone, message in st.session_state.messages.items():
                st.text(f"Message for {zone}:")
                st.text(message)
                st.text("---")

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

    site_search = st.sidebar.text_input("Search for a specific site alias")
    if site_search:
        display_detailed_entries(merged_df, site_search)
else:
    st.write("Please upload all required files.")
