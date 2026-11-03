from flask import Flask, render_template_string, request, session, redirect, url_for
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)

# Encrypted password hash for NS786110
PASSWORD_HASH = generate_password_hash("NS786110")

SHEET_ID = "1YYsTX_pXMlBSv4JeWUQHBHX78iSeaKGyf91nzlBLX1A"
PRODUCTS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=products"
META_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=sync_meta"

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>NS Inventory - Login</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f6f8; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-card { background: #fff; padding: 30px 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); width: 100%; max-width: 360px; text-align: center; }
        h2 { margin-top: 0; margin-bottom: 20px; font-size: 20px; color: #333; }
        input[type="password"] { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #dcdfe6; border-radius: 8px; margin-bottom: 15px; outline: none; text-align: center; }
        input[type="password"]:focus { border-color: #0066cc; }
        button { width: 100%; padding: 12px; background: #0066cc; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
        button:hover { background: #0052a3; }
        .error { color: #d9534f; font-size: 14px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 Enter Access Password</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <!-- Form allows submitting via Enter key as well as button click -->
        <form method="POST" action="/login">
            <input type="password" name="password" placeholder="Password" required autofocus autocomplete="current-password">
            <button type="submit">Access Inventory</button>
        </form>
    </div>
</body>
</html>
"""

MAIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Products Inventory</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 15px; 
            background-color: #f4f6f8; 
            color: #333; 
        }
        .container { 
            max-width: 1100px; 
            margin: 0 auto; 
            background: #ffffff; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.06); 
        }
        .header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; flex-wrap: wrap; gap: 10px; }
        h2 { margin: 0; font-size: 22px; display: flex; align-items: center; gap: 8px; }
        .logout-btn { color: #d9534f; text-decoration: none; font-size: 14px; font-weight: 600; }
        
        .meta-info { font-size: 13px; color: #555; margin-bottom: 18px; }
        
        /* Filter Grid */
        .filter-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 12px;
            margin-bottom: 18px;
        }
        .search-box, .select-box {
            width: 100%;
            padding: 12px 14px;
            font-size: 15px;
            border: 1px solid #dcdfe6;
            border-radius: 8px;
            background-color: #fff;
            outline: none;
        }
        .search-box:focus, .select-box:focus { border-color: #0066cc; }
        
        .count { font-size: 13px; color: #666; margin-bottom: 15px; font-weight: 500; }
        
        /* Desktop Table Styling */
        .table-wrapper { width: 100%; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 5px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #edf2f7; }
        th { background-color: #f7fafc; font-weight: 600; font-size: 14px; color: #4a5568; }
        
        /* Highlighted Quantity Styling */
        .qty-badge {
            font-weight: 700;
            color: #0066cc;
            background-color: #eef6ff;
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-block;
            font-size: 15px;
        }

        /* Mobile Responsive Card View */
        @media (max-width: 768px) {
            body { padding: 10px; }
            .container { padding: 15px; }
            .filter-grid { grid-template-columns: 1fr; gap: 10px; }
            
            table, thead, tbody, th, td, tr { display: block; }
            thead { display: none; }
            
            tr.item-row {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 14px;
                margin-bottom: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            }
            
            td {
                display: flex;
                flex-direction: row;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid #f7fafc;
                font-size: 14px;
            }
            td:last-child { border-bottom: none; }
            
            td[data-label="Description"] {
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;
            }
            
            td::before {
                content: attr(data-label);
                font-weight: 600;
                color: #718096;
                font-size: 13px;
                min-width: 90px;
            }
            
            .desc-text { text-align: left; word-break: break-word; }
            .qty-badge { font-size: 16px; padding: 5px 12px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-row">
            <h2>📦 Products Inventory</h2>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
        <div class="meta-info">🕒 Last Google Sheet Update: <strong>{{ last_updated }}</strong></div>
        
        <div class="filter-grid">
            <input type="text" id="searchInput" class="search-box" placeholder="🔍 Search Code or Description..." oninput="filterTable()">
            
            <select id="categoryFilter" class="select-box" onchange="filterTable()">
                <option value="">All Categories</option>
                {% for cat in categories %}
                <option value="{{ cat }}">{{ cat }}</option>
                {% endfor %}
            </select>
        </div>

        <div class="count">Showing <strong id="showingCount">{{ items|length }}</strong> of <strong>{{ items|length }}</strong> total items</div>
        
        <div class="table-wrapper">
            <table id="inventoryTable">
                <thead>
                    <tr>
                        <th>Item Code</th>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Qty</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in items %}
                    <tr class="item-row" 
                        data-code="{{ row.id|lower }}" 
                        data-name="{{ row.name|lower }}" 
                        data-category="{{ row.category }}">
                        <td data-label="Item Code"><strong>{{ row.id }}</strong></td>
                        <td data-label="Description"><span class="desc-text">{{ row.name }}</span></td>
                        <td data-label="Category">{{ row.category }}</td>
                        <td data-label="Qty"><span class="qty-badge">{{ row.qty }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function filterTable() {
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const selectedCategory = document.getElementById('categoryFilter').value;
            
            const rows = document.querySelectorAll('.item-row');
            let visibleCount = 0;

            rows.forEach(row => {
                const code = row.getAttribute('data-code');
                const name = row.getAttribute('data-name');
                const category = row.getAttribute('data-category');

                const matchesQuery = !query || code.includes(query) || name.includes(query);
                const matchesCategory = !selectedCategory || category === selectedCategory;

                if (matchesQuery && matchesCategory) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            document.getElementById('showingCount').innerText = visibleCount;
        }
    </script>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if check_password_hash(PASSWORD_HASH, pwd):
            session["authenticated"] = True
            return redirect(url_for("index"))
        return render_template_string(LOGIN_HTML, error="Invalid Password. Try again.")
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
def index():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
        
    try:
        df = pd.read_csv(PRODUCTS_CSV_URL).fillna("")
        categories = sorted([c for c in df['category'].unique() if c])
        items = df.to_dict(orient="records")

        # Correct Timestamp Extraction
        last_updated = "N/A"
        try:
            meta_df = pd.read_csv(META_CSV_URL, header=None)
            # Row 0 is 'last_updated', Row 1 is the actual date/time string
            if len(meta_df) > 1:
                last_updated = str(meta_df.iloc[1, 0]).strip()
            elif len(meta_df) == 1:
                last_updated = str(meta_df.iloc[0, 0]).strip()
        except Exception:
            pass

        return render_template_string(
            MAIN_HTML,
            items=items,
            categories=categories,
            last_updated=last_updated
        )
    except Exception as e:
        return f"<h3>Error loading products data from Google Sheet.</h3><p>{e}</p>", 500

if __name__ == "__main__":
    app.run(debug=True)
