# Odin-s-Eye: Alarm Data Analysis

This Streamlit app is designed to analyze and display Vibration and Motion Alarm Data, merging them with current alarms to provide real-time insights into alarm occurrences. It also supports sending Telegram notifications for each zone based on alarm activity.

## Features
- Upload and process Vibration and Motion Alarm Data.
- Merge alarm data with current alarm statuses.
- Filter data by custom date and time inputs.
- Display grouped data by Cluster and Zone.
- Send notifications to Telegram for zones with active alarms.

## Requirements

This project uses the following Python libraries:
- `pandas`
- `streamlit`
- `requests`
- `openpyxl`

## Setup Instructions

To run this project locally:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/odin-s-eye.git
    cd odin-s-eye
    ```

2. **Create a virtual environment (optional but recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

## How to Use

1. Upload the following datasets in `.xlsx` format:
    - Vibration Alarm Data
    - Vibration Current Alarms Data
    - Motion Alarm Data
    - Motion Current Alarms Data

2. Select the date and time filters to customize the alarm view.

3. View the grouped data by Cluster and Zone.

4. Optionally, send a Telegram notification for zones with active alarms.

## Telegram Notification

To enable Telegram notifications, update the `app.py` file with your Telegram bot token and chat ID:
```python
bot_token = "YOUR_BOT_TOKEN"
chat_id = "YOUR_CHAT_ID"
