import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

DB_PATH = "inventory.db"
GOOGLE_SHEET_ID = "1YYsTX_pXMlBSv4JeWUQHBHX78iSeaKGyf91nzlBLX1A"
CREDENTIALS_FILE = "service_account.json"

def sync_sqlite_to_sheets():
    print("Reading database schema...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    if not tables:
        print("No tables found in the database!")
        conn.close()
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    for table_name in tables:
        print(f"Processing table: '{table_name}'...")
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        df = df.fillna("")

        try:
            worksheet = spreadsheet.worksheet(table_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=table_name, rows=100, cols=20)

        worksheet.clear()
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data_to_upload)

    # Record Last Updated Timestamp
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    try:
        meta_ws = spreadsheet.worksheet("sync_meta")
    except gspread.exceptions.WorksheetNotFound:
        meta_ws = spreadsheet.add_worksheet(title="sync_meta", rows=5, cols=2)
    
    meta_ws.clear()
    meta_ws.update([["last_updated"], [now_str]])
    print(f"Recorded update timestamp: {now_str}")

    conn.close()
    print("Sync complete!")

if __name__ == "__main__":
    sync_sqlite_to_sheets()
