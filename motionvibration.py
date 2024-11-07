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
        merged_df = merged_df[merged_df['Start Time'] >= start_time_filter]

    motion_count = merged_df[merged_df['Type'] == 'Motion'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Motion Count')
    vibration_count = merged_df[merged_df['Type'] == 'Vibration'].groupby(['Zone', 'Site Alias']).size().reset_index(name='Vibration Count')
    
    final_df = pd.merge(motion_count, vibration_count, on=['Zone', 'Site Alias'], how='outer').fillna(0)
    final_df['Motion Count'] = final_df['Motion Count'].astype(int)
    final_df['Vibration Count'] = final_df['Vibration Count'].astype(int)
    
    return final_df

# Function to generate the Telegram message for each zone
def generate_telegram_message(zone, zone_df, total_motion, total_vibration, usernames):
    username_mentions = " ".join([f"@{name}" for name in usernames])
    
    # Construct the message based on the specified template
    message = f"{zone}\n\n"  # Zone name at the top
    message += f"Total Motion Alarm count: {total_motion}\nTotal Vibration Alarm count: {total_vibration}\n\n"  # Total counts
    
    for _, row in zone_df.iterrows():
        message += f"{row['Site Alias']} : \n"  # Site Alias
        message += f"Motion Count: {row['Motion Count']}, Vibration Count: {row['Vibration Count']}\n\n"  # Counts for each site

    message += f"{username_mentions} please take care."
    
    return message

# Function to send a single Telegram message
def send_telegram_message(message):
    chat_id = "-4537588687"
    bot_token = "7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=data)
    
    return response.status_code == 200  # Return True if successful

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

# File upload section (only for report data)
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

        # Generate message button
        if st.button("Generate Message", help="Generate alarm summaries for selected zone"):
            if zone_filter == "All":
                selected_zones = zone_priority  # All zones if "All" is selected
            else:
                selected_zones = [zone_filter]  # Only the selected zone

            summary_df = count_entries_by_zone(merged_df, start_time_filter)
            summary_df = summary_df[summary_df['Zone'].isin(selected_zones)]  # Filter for selected zones
            
            # Clear previous messages from session state
            st.session_state.messages = {}  # Dictionary to hold messages

            for zone in selected_zones:
                if zone in summary_df['Zone'].values:
                    zone_df = summary_df[summary_df['Zone'] == zone]
                    total_motion = zone_df['Motion Count'].sum()
                    total_vibration = zone_df['Vibration Count'].sum()

                    # Get all usernames for the zone
                    usernames = username_df[username_df['Zone'] == zone]['Name'].dropna().unique()
                    
                    # Generate the message for this zone
                    message = generate_telegram_message(zone, zone_df, total_motion, total_vibration, usernames)
                    st.session_state.messages[zone] = message  # Store message in session state

            if st.session_state.messages:
                st.success("Messages generated successfully!")
                st.subheader("Generated Messages")
                for zone, message in st.session_state.messages.items():
                    st.text(f"Message for {zone}:")
                    st.text(message)
                    st.text("---")
            else:
                st.error("No alarms found for the selected zone.")

        # Send notification button
        if st.button("Send Telegram Notification", help="Send alarm summaries to Telegram"):
            for zone, message in st.session_state.messages.items():
                if send_telegram_message(message):
                    st.success(f"Message sent successfully for {zone}!")
                else:
                    st.error(f"Failed to send message for {zone}.")
        
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
    st.write("Please upload both Motion and Vibration Report Data files.")
