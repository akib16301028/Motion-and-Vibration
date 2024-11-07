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

# Function to send data to Telegram
def send_to_telegram(message, chat_id, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    return response.ok

# Streamlit app
st.title('Odin-s-Eye - Motion & Vibration Alarm Monitoring')

# File upload section (only for report data)
report_motion_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
report_vibration_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])

if report_motion_file and report_vibration_file:
    report_motion_df = pd.read_excel(report_motion_file, header=2)
    report_vibration_df = pd.read_excel(report_vibration_file, header=2)

    merged_df = merge_report_files(report_motion_df, report_vibration_df)

    # Sidebar options for date filter
    with st.sidebar:
        # Date and time filter
        selected_date = st.date_input("Select Start Date", value=datetime.now().date())
        selected_time = st.time_input("Select Start Time", value=time(0, 0))
        start_time_filter = datetime.combine(selected_date, selected_time)
        
        # Button to send data to Telegram
        if st.button("Send Data to Telegram"):
            for zone in zone_priority:
                # Filter the merged_df for each zone and send a message
                zone_df = merged_df[(merged_df['Zone'] == zone) & (merged_df['Start Time'] >= start_time_filter)]
                if not zone_df.empty:
                    message = f"<b>{zone}</b>\n"
                    site_summary = count_entries_by_zone(zone_df, start_time_filter)

                    for _, row in site_summary.iterrows():
                        message += f"{row['Site Alias']}\n"
                        message += f"Motion Count: {row['Motion Count']}, Vibration Count: {row['Vibration Count']}\n\n"

                    # Send the Telegram message
                    success = send_to_telegram(message, chat_id="-4537588687", bot_token="7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME")
                    if success:
                        st.sidebar.success(f"Data for {zone} sent to Telegram successfully!")
                    else:
                        st.sidebar.error(f"Failed to send data for {zone} to Telegram.")

    # Filtered summary based on selected time filter
    summary_df = count_entries_by_zone(merged_df, start_time_filter)

    # Separate prioritized and non-prioritized zones
    prioritized_df = summary_df[summary_df['Zone'].isin(zone_priority)]
    non_prioritized_df = summary_df[~summary_df['Zone'].isin(zone_priority)]

    # Sort prioritized zones according to the order in zone_priority
    prioritized_df['Zone'] = pd.Categorical(prioritized_df['Zone'], categories=zone_priority, ordered=True)
    prioritized_df = prioritized_df.sort_values('Zone')

    # Display prioritized zones first, sorted by total motion and vibration counts in descending order
    for zone in prioritized_df['Zone'].unique():
        st.write(f"### {zone}")
        zone_df = prioritized_df[prioritized_df['Zone'] == zone]

        # Sort by total motion and vibration counts (sum of both)
        zone_df['Total Alarm Count'] = zone_df['Motion Count'] + zone_df['Vibration Count']
        zone_df = zone_df.sort_values('Total Alarm Count', ascending=False)

        # Display the total alarm count as in the original format
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()
        st.write(f"Total Motion Alarm count: {total_motion}")
        st.write(f"Total Vibration Alarm count: {total_vibration}")

        # Render and display the HTML table with color formatting
        styled_table_html = render_styled_table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])
        st.markdown(styled_table_html, unsafe_allow_html=True)

    # Display non-prioritized zones in alphabetical order, sorted by total motion and vibration counts
    for zone in sorted(non_prioritized_df['Zone'].unique()):
        st.write(f"### {zone}")
        zone_df = non_prioritized_df[non_prioritized_df['Zone'] == zone]

        # Sort by total motion and vibration counts (sum of both)
        zone_df['Total Alarm Count'] = zone_df['Motion Count'] + zone_df['Vibration Count']
        zone_df = zone_df.sort_values('Total Alarm Count', ascending=False)

        # Display the total alarm count as in the original format
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()
        st.write(f"Total Motion Alarm count: {total_motion}")
        st.write(f"Total Vibration Alarm count: {total_vibration}")

        # Render and display the HTML table with color formatting
        styled_table_html = render_styled_table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])
        st.markdown(styled_table_html, unsafe_allow_html=True)
else:
    st.write("Please upload both Motion and Vibration Report Data files.")
