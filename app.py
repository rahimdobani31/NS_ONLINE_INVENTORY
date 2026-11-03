import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
SHEET_ID = "1YYsTX_pXMlBSv4JeWUQHBHX78iSeaKGyf91nzlBLX1A"
TAB_NAME = "products"  # Directly targets your products sheet tab

# Public CSV URL for Google Sheets
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={TAB_NAME}"

# Page Configuration
st.set_page_config(page_title="Product Inventory Search", page_icon="📦", layout="wide")
st.title("📦 Products Inventory")

@st.cache_data(ttl=60)  # Caches data for 60 seconds
def load_data():
    return pd.read_csv(CSV_URL)

try:
    df = load_data()

    # Search Bar for Code (id) or Description (name)
    search_query = st.text_input(
        "🔍 Search by Item Code or Description:",
        placeholder="Type code (e.g. CE34) or description (e.g. CPVC ELBOW)..."
    )

    # Filter Logic
    if search_query:
        # Convert search query to string and lowercase
        query = search_query.strip().lower()

        # Check if query matches 'id' or 'name' columns
        mask = (
            df['id'].astype(str).str.lower().str.contains(query, na=False) |
            df['name'].astype(str).str.lower().str.contains(query, na=False)
        )
        filtered_df = df[mask]
    else:
        filtered_df = df

    # Display total items count
    st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** total items")

    # Display Interactive Data Table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.TextColumn("Item Code"),
            "name": st.column_config.TextColumn("Description"),
            "category": st.column_config.TextColumn("Category"),
            "qty": st.column_config.NumberColumn("Quantity"),
            "limit_qty": st.column_config.NumberColumn("Limit Qty"),
            "location": st.column_config.TextColumn("Location"),
        }
    )

except Exception as e:
    st.error(f"Error loading products data. Ensure the Google Sheet tab named '{TAB_NAME}' is published to the web.")