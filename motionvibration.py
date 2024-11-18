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
def merge_report_files(report_motion_df=None, report_vibration_df=None):
    dfs = []
    if report_motion_df is not None:
        report_motion_df = preprocess_report(report_motion_df, 'Motion')
        dfs.append(report_motion_df)
    if report_vibration_df is not None:
        report_vibration_df = preprocess_report(report_vibration_df, 'Vibration')
        dfs.append(report_vibration_df)
    
    merged_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
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
st.title('PulseForge')

# File upload section (for Motion or Vibration report data)
report_motion_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
report_vibration_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])

if report_motion_file or report_vibration_file:
    report_motion_df = pd.read_excel(report_motion_file, header=2) if report_motion_file else None
    report_vibration_df = pd.read_excel(report_vibration_file, header=2) if report_vibration_file else None

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
                # Get the zonal concern for the current zone
                concern = username_df[username_df['Zone'] == zone]['Name'].values
                zonal_concern = concern[0] if len(concern) > 0 else "Unknown Concern"
                
                # Filter the merged_df for each zone and send a message
                zone_df = merged_df[(merged_df['Zone'] == zone) & (merged_df['Start Time'] >= start_time_filter)]
                if not zone_df.empty:
                    # Message header with zone name and filter time
                    message = f"<b>{zone}:</b>\nAlarm came after: {start_time_filter.strftime('%Y-%m-%d %I:%M %p')}\n\n"
                    
                    site_summary = count_entries_by_zone(zone_df, start_time_filter)

                    # Sort site summary by total alarm count (Motion + Vibration) in descending order
                    site_summary['Total Alarm Count'] = site_summary['Motion Count'] + site_summary['Vibration Count']
                    site_summary = site_summary.sort_values(by='Total Alarm Count', ascending=False)

                    # Add each site’s alarm details in sorted order
                    for _, row in site_summary.iterrows():
                        message += f"{row['Site Alias']}: Vibration: {row['Vibration Count']}, Motion: {row['Motion Count']} \n"
                        
                    # Add the zonal concern at the end of the message
                    message += f"\n@{zonal_concern}, please take care."

                    # Send the Telegram message
                    success = send_to_telegram(message, chat_id="-4537588687", bot_token="7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME")
                    if success:
                        st.sidebar.success(f"Data for {zone} sent to Telegram successfully!")
                    else:
                        st.sidebar.error(f"Failed to send data for {zone} to Telegram.")

    # Filtered summary based on selected time filter
    summary_df = count_entries_by_zone(merged_df, start_time_filter)

    # Display the data
    for zone in zone_priority:
        zone_df = summary_df[summary_df['Zone'] == zone]
        if not zone_df.empty:
            st.write(f"### {zone}")
            st.dataframe(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])
else:
    st.write("Please upload Motion or Vibration Report Data files.")
