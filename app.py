from flask import Flask, render_template_string
import pandas as pd

app = Flask(__name__)

SHEET_ID = "1YYsTX_pXMlBSv4JeWUQHBHX78iSeaKGyf91nzlBLX1A"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=products"

HTML_TEMPLATE = """
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
            max-width: 1150px; 
            margin: 0 auto; 
            background: #ffffff; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.06); 
        }
        h2 { margin-top: 0; margin-bottom: 18px; font-size: 22px; display: flex; align-items: center; gap: 8px; }
        
        /* Filter Grid Layout */
        .filter-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
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
            transition: border-color 0.2s;
        }
        .search-box:focus, .select-box:focus {
            border-color: #0066cc;
        }
        
        .count { font-size: 13px; color: #666; margin-bottom: 15px; font-weight: 500; }
        
        /* Desktop Table Styling */
        .table-wrapper { width: 100%; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 5px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #edf2f7; }
        th { background-color: #f7fafc; font-weight: 600; font-size: 14px; color: #4a5568; }
        
        /* Responsive Mobile Layout (Cards) */
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
                padding: 12px;
                margin-bottom: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            }
            td {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 6px 0;
                border-bottom: 1px solid #f7fafc;
                font-size: 14px;
            }
            td:last-child { border-bottom: none; }
            
            /* Add field labels on mobile view */
            td::before {
                content: attr(data-label);
                font-weight: 600;
                color: #718096;
                font-size: 13px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>📦 Products Inventory</h2>
        
        <div class="filter-grid">
            <input type="text" id="searchInput" class="search-box" placeholder="🔍 Search Code or Description..." oninput="filterTable()">
            
            <select id="categoryFilter" class="select-box" onchange="filterTable()">
                <option value="">All Categories</option>
                {% for cat in categories %}
                <option value="{{ cat }}">{{ cat }}</option>
                {% endfor %}
            </select>
            
            <select id="locationFilter" class="select-box" onchange="filterTable()">
                <option value="">All Locations</option>
                {% for loc in locations %}
                <option value="{{ loc }}">{{ loc }}</option>
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
                        <th>Limit Qty</th>
                        <th>Location</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in items %}
                    <tr class="item-row" 
                        data-code="{{ row.id|lower }}" 
                        data-name="{{ row.name|lower }}" 
                        data-category="{{ row.category }}" 
                        data-location="{{ row.location }}">
                        <td data-label="Item Code"><strong>{{ row.id }}</strong></td>
                        <td data-label="Description">{{ row.name }}</td>
                        <td data-label="Category">{{ row.category }}</td>
                        <td data-label="Qty">{{ row.qty }}</td>
                        <td data-label="Limit Qty">{{ row.limit_qty }}</td>
                        <td data-label="Location">{{ row.location }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Client-Side Instant Filter Script -->
    <script>
        function filterTable() {
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const selectedCategory = document.getElementById('categoryFilter').value;
            const selectedLocation = document.getElementById('locationFilter').value;
            
            const rows = document.querySelectorAll('.item-row');
            let visibleCount = 0;

            rows.forEach(row => {
                const code = row.getAttribute('data-code');
                const name = row.getAttribute('data-name');
                const category = row.getAttribute('data-category');
                const location = row.getAttribute('data-location');

                const matchesQuery = !query || code.includes(query) || name.includes(query);
                const matchesCategory = !selectedCategory || category === selectedCategory;
                const matchesLocation = !selectedLocation || location === selectedLocation;

                if (matchesQuery && matchesCategory && matchesLocation) {
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

@app.route("/", methods=["GET"])
def index():
    try:
        df = pd.read_csv(CSV_URL).fillna("")
        
        categories = sorted([c for c in df['category'].unique() if c])
        locations = sorted([l for l in df['location'].unique() if l])
        
        items = df.to_dict(orient="records")
        
        return render_template_string(
            HTML_TEMPLATE,
            items=items,
            categories=categories,
            locations=locations
        )
    except Exception as e:
        return f"<h3>Error loading products data from Google Sheet.</h3><p>{e}</p>", 500

if __name__ == "__main__":
    app.run(debug=True)
