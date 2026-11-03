import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuration
DB_PATH = "inventory.db"  # Path to your local .db file
GOOGLE_SHEET_ID = "1YYsTX_pXMlBSv4JeWUQHBHX78iSeaKGyf91nzlBLX1A"
CREDENTIALS_FILE = "service_account.json"

def sync_sqlite_to_sheets():
    # 2. Extract all table names from SQLite
    print("Reading database schema...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query all user-created tables (excluding SQLite internal tables)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    if not tables:
        print("No tables found in the database!")
        conn.close()
        return

    print(f"Found {len(tables)} table(s): {', '.join(tables)}")

    # 3. Authenticate with Google Sheets API
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    # 4. Process each table
    for table_name in tables:
        print(f"\nProcessing table: '{table_name}'...")
        
        # Read table into DataFrame
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        df = df.fillna("")  # Replace NaN values with empty strings

        # Get existing tab or create a new one
        try:
            worksheet = spreadsheet.worksheet(table_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"Creating new tab: '{table_name}'...")
            worksheet = spreadsheet.add_worksheet(title=table_name, rows=100, cols=20)

        # Clear existing tab contents and upload new dataset
        worksheet.clear()
        
        # Prepare header + rows
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data_to_upload)

        print(f"Successfully synced {len(df)} rows to tab '{table_name}'!")

    conn.close()
    print("\nAll tables successfully uploaded to Google Sheets!")

if __name__ == "__main__":
    sync_sqlite_to_sheets()