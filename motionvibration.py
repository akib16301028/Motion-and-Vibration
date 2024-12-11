import pandas as pd
import streamlit as st
from datetime import datetime
import requests  # For sending Telegram notifications

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

# Function to load USER NAME file
def load_user_name_file():
    try:
        # Load the file from the Git repository
        user_name_df = pd.read_csv('USER NAME.csv')
        return user_name_df
    except FileNotFoundError:
        st.error("USER NAME file not found in the repository.")
        return None

# Streamlit app
st.title('Odin-s-Eye')

# Add a sidebar for displaying USER NAME file data
st.sidebar.title("User Information")
user_name_df = load_user_name_file()

if user_name_df is not None:
    st.sidebar.write("Information from the USER NAME file:")
    st.sidebar.dataframe(user_name_df)
else:
    st.sidebar.write("No data available in the USER NAME file.")

# Main app functionality
site_access_file = st.file_uploader("Upload the Site Access Excel", type=["xlsx"])
rms_file = st.file_uploader("Upload the RMS Excel", type=["xlsx"])
current_alarms_file = st.file_uploader("Upload the Current Alarms Excel", type=["xlsx"])

if "filter_time" not in st.session_state:
    st.session_state.filter_time = datetime.now().time()
if "filter_date" not in st.session_state:
    st.session_state.filter_date = datetime.now().date()
if "status_filter" not in st.session_state:
    st.session_state.status_filter = "All"

if site_access_file and rms_file and current_alarms_file:
    site_access_df = pd.read_excel(site_access_file)
    rms_df = pd.read_excel(rms_file, header=2)
    current_alarms_df = pd.read_excel(current_alarms_file, header=2)

    merged_rms_alarms_df = merge_rms_alarms(rms_df, current_alarms_df)

    # Filter inputs (date and time)
    selected_date = st.date_input("Select Date", value=st.session_state.filter_date)
    selected_time = st.time_input("Select Time", value=st.session_state.filter_time)

    # Button to clear filters
    if st.button("Clear Filters"):
        st.session_state.filter_date = datetime.now().date()
        st.session_state.filter_time = datetime.now().time()
        st.session_state.status_filter = "All"

    # Combine selected date and time into a datetime object
    filter_datetime = datetime.combine(st.session_state.filter_date, st.session_state.filter_time)

    # Process mismatches and matches
    mismatches_df = find_mismatches(site_access_df, merged_rms_alarms_df)
    matched_df = find_matched_sites(site_access_df, merged_rms_alarms_df)

    # Filters and displays
    # (Add filter and display logic here as per your existing application)

    st.write("Your application logic continues here.")

else:
    st.write("Please upload all required files.")
