import os
import glob
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
GOOGLE_SHEET_ID = "1YYsTX_pXMlBSv4JeWUQHBHX78iSeaKGyf91nzlBLX1A"

# Dynamically locate files relative to where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "service_account.json")

def get_latest_auto_backup():
    """Finds the most recently modified auto_backup file in the current folder."""
    search_pattern = os.path.join(SCRIPT_DIR, "auto_backup_*")
    files = glob.glob(search_pattern)
    
    if not files:
        return None
    
    # Sort files by last modification date (newest first)
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def sync_sqlite_to_sheets():
    # 1. Find the latest auto_backup file
    db_path = get_latest_auto_backup()
    
    if not db_path:
        print("❌ Error: No 'auto_backup_' files found in the folder!")
        return
        
    print(f"📦 Found latest auto backup: {os.path.basename(db_path)}")

    # 2. Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Extract all user-created tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    if not tables:
        print("❌ No tables found in the database!")
        conn.close()
        return

    print(f"Found {len(tables)} table(s): {', '.join(tables)}")

    # 3. Authenticate with Google Sheets API
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: '{CREDENTIALS_FILE}' not found in the script folder!")
        conn.close()
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    # 4. Process and upload each database table
    for table_name in tables:
        print(f"\nProcessing table: '{table_name}'...")
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        df = df.fillna("")

        try:
            worksheet = spreadsheet.worksheet(table_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"Creating new tab: '{table_name}'...")
            worksheet = spreadsheet.add_worksheet(title=table_name, rows=100, cols=20)

        worksheet.clear()
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data_to_upload)
        print(f"Successfully synced {len(df)} rows to tab '{table_name}'!")

    # 5. Update 'sync_meta' tab with Last Updated Timestamp
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    print(f"\nRecording last updated timestamp: {now_str}...")

    try:
        meta_ws = spreadsheet.worksheet("sync_meta")
    except gspread.exceptions.WorksheetNotFound:
        print("Creating 'sync_meta' tab...")
        meta_ws = spreadsheet.add_worksheet(title="sync_meta", rows=5, cols=2)

    meta_ws.clear()
    meta_ws.update([["last_updated"], [now_str]])

    conn.close()
    print("\n✅ All tables and sync metadata successfully uploaded to Google Sheets!")

if __name__ == "__main__":
    sync_sqlite_to_sheets()
