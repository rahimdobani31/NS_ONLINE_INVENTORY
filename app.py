from flask import Flask, render_template_string, request
import pandas as pd

app = Flask(__name__)

SHEET_ID = "1YYsTX_pXMlBSv4JeWUQHBHX78iSeaKGyf91nzlBLX1A"
TAB_NAME = "products"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={TAB_NAME}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Products Inventory</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 30px; background-color: #f8f9fa; color: #333; }
        .container { max-width: 1100px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        h2 { margin-top: 0; }
        .search-box { width: 100%; padding: 12px 16px; font-size: 16px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; margin-bottom: 20px; }
        .count { font-size: 14px; color: #666; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
        th { background-color: #f1f3f5; font-weight: 600; }
        tr:hover { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📦 Products Inventory</h2>
        <form method="GET" action="/">
            <input type="text" name="q" class="search-box" placeholder="🔍 Search by Item Code or Description..." value="{{ query }}" oninput="this.form.submit()">
        </form>
        <div class="count">Showing <strong>{{ total_showing }}</strong> of <strong>{{ total_all }}</strong> items</div>
        <table>
            <thead>
                <tr>
                    <th>Item Code</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Qty</th>
                    <th>Limit Qty</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody>
                {% for row in items %}
                <tr>
                    <td><strong>{{ row.id }}</strong></td>
                    <td>{{ row.name }}</td>
                    <td>{{ row.category }}</td>
                    <td>{{ row.qty }}</td>
                    <td>{{ row.limit_qty }}</td>
                    <td>{{ row.location }}</td>
                </tr>
                {% else %}
                <tr><td colspan="6" style="text-align:center; padding: 20px; color: #888;">No items found matching your search.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    try:
        df = pd.read_csv(CSV_URL).fillna("")
        
        if query:
            q_lower = query.lower()
            mask = (
                df['id'].astype(str).str.lower().str.contains(q_lower, na=False) |
                df['name'].astype(str).str.lower().str.contains(q_lower, na=False)
            )
            filtered_df = df[mask]
        else:
            filtered_df = df

        items = filtered_df.to_dict(orient="records")
        return render_template_string(
            HTML_TEMPLATE,
            items=items,
            query=query,
            total_showing=len(filtered_df),
            total_all=len(df)
        )
    except Exception as e:
        return f"<h3>Error loading products data from Google Sheet.</h3><p>{e}</p>", 500

if __name__ == "__main__":
    app.run(debug=True)
