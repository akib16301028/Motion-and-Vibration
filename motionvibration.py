# Streamlit app
st.title('PulseForge')

# File upload section (only for report data)
report_motion_file = st.file_uploader("Upload the Motion Report Data", type=["xlsx"])
report_vibration_file = st.file_uploader("Upload the Vibration Report Data", type=["xlsx"])

if report_motion_file and report_vibration_file:
    report_motion_df = pd.read_excel(report_motion_file, header=2)
    report_vibration_df = pd.read_excel(report_vibration_file, header=2)

    merged_df = merge_report_files(report_motion_df, report_vibration_df)

    # Sidebar options
    with st.sidebar:
        # Date and time filter
        selected_date = st.date_input("Select Start Date", value=datetime.now().date())
        selected_time = st.time_input("Select Start Time", value=time(0, 0))
        start_time_filter = datetime.combine(selected_date, selected_time)

        # Option to send notifications for prioritized zones
        st.write("### Notifications for Prioritized Zones")
        if st.button("Send to Prioritized Zones"):
            for zone in zone_priority:
                concern = username_df[username_df['Zone'] == zone]['Name'].values
                zonal_concern = concern[0] if len(concern) > 0 else "Unknown Concern"
                zone_df = merged_df[(merged_df['Zone'] == zone) & (merged_df['Start Time'] >= start_time_filter)]
                if not zone_df.empty:
                    message = f"<b>{zone}:</b>\nAlarm came after: {start_time_filter.strftime('%Y-%m-%d %I:%M %p')}\n\n"
                    site_summary = count_entries_by_zone(zone_df, start_time_filter)
                    site_summary['Total Alarm Count'] = site_summary['Motion Count'] + site_summary['Vibration Count']
                    site_summary = site_summary.sort_values(by='Total Alarm Count', ascending=False)
                    for _, row in site_summary.iterrows():
                        message += f"{row['Site Alias']}: Vibration: {row['Vibration Count']}, Motion: {row['Motion Count']} \n"
                    message += f"\n@{zonal_concern}, please take care."
                    success = send_to_telegram(message, chat_id="-1001509039244", bot_token="7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME")
                    if success:
                        st.sidebar.success(f"Data for {zone} sent to Telegram successfully!")
                    else:
                        st.sidebar.error(f"Failed to send data for {zone} to Telegram.")

        # Option to send notifications for other zones
        st.write("### Notifications for Other Zones")
        additional_zones = st.multiselect(
            "Select Zones for Notifications",
            options=merged_df['Zone'].unique(),
            default=[]
        )
        if st.button("Send to Selected Zones"):
            for zone in additional_zones:
                concern = username_df[username_df['Zone'] == zone]['Name'].values
                zonal_concern = concern[0] if len(concern) > 0 else "Unknown Concern"
                zone_df = merged_df[(merged_df['Zone'] == zone) & (merged_df['Start Time'] >= start_time_filter)]
                if not zone_df.empty:
                    message = f"<b>{zone}:</b>\nAlarm came after: {start_time_filter.strftime('%Y-%m-%d %I:%M %p')}\n\n"
                    site_summary = count_entries_by_zone(zone_df, start_time_filter)
                    site_summary['Total Alarm Count'] = site_summary['Motion Count'] + site_summary['Vibration Count']
                    site_summary = site_summary.sort_values(by='Total Alarm Count', ascending=False)
                    for _, row in site_summary.iterrows():
                        message += f"{row['Site Alias']}: Vibration: {row['Vibration Count']}, Motion: {row['Motion Count']} \n"
                    message += f"\n@{zonal_concern}, please take care."
                    success = send_to_telegram(message, chat_id="-1001509039244", bot_token="7145427044:AAGb-CcT8zF_XYkutnqqCdNLqf6qw4KgqME")
                    if success:
                        st.sidebar.success(f"Data for {zone} sent to Telegram successfully!")
                    else:
                        st.sidebar.error(f"Failed to send data for {zone} to Telegram.")

    # Main display logic for zones remains unchanged
    summary_df = count_entries_by_zone(merged_df, start_time_filter)
    prioritized_df = summary_df[summary_df['Zone'].isin(zone_priority)]
    non_prioritized_df = summary_df[~summary_df['Zone'].isin(zone_priority)]
    prioritized_df['Zone'] = pd.Categorical(prioritized_df['Zone'], categories=zone_priority, ordered=True)
    prioritized_df = prioritized_df.sort_values('Zone')

    for zone in prioritized_df['Zone'].unique():
        st.write(f"### {zone}")
        zone_df = prioritized_df[prioritized_df['Zone'] == zone]
        zone_df['Total Alarm Count'] = zone_df['Motion Count'] + zone_df['Vibration Count']
        zone_df = zone_df.sort_values('Total Alarm Count', ascending=False)
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()
        st.write(f"Total Motion Alarm count: {total_motion}")
        st.write(f"Total Vibration Alarm count: {total_vibration}")
        styled_table_html = render_styled_table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])
        st.markdown(styled_table_html, unsafe_allow_html=True)

    for zone in sorted(non_prioritized_df['Zone'].unique()):
        st.write(f"### {zone}")
        zone_df = non_prioritized_df[non_prioritized_df['Zone'] == zone]
        zone_df['Total Alarm Count'] = zone_df['Motion Count'] + zone_df['Vibration Count']
        zone_df = zone_df.sort_values('Total Alarm Count', ascending=False)
        total_motion = zone_df['Motion Count'].sum()
        total_vibration = zone_df['Vibration Count'].sum()
        st.write(f"Total Motion Alarm count: {total_motion}")
        st.write(f"Total Vibration Alarm count: {total_vibration}")
        styled_table_html = render_styled_table(zone_df[['Site Alias', 'Motion Count', 'Vibration Count']])
        st.markdown(styled_table_html, unsafe_allow_html=True)
else:
    st.write("Please upload both Motion and Vibration Report Data files.")
