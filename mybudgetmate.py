# app.py - Complete Python Flask Backend for Budget Tracker
from flask import Flask, request, render_template_string, jsonify, send_from_directory
import os
import json
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create data directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load existing data or create empty file
DATA_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'budgets.json')
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/submit-budget', methods=['POST'])
def submit_budget():
    try:
        # Get form data
        data = {
            'timestamp': datetime.now().isoformat(),
            'income': float(request.form.get('income', 0)),
            'rent': float(request.form.get('rent', 0)),
            'utilities': float(request.form.get('utilities', 0)),
            'groceries': float(request.form.get('groceries', 0)),
            'recharge': float(request.form.get('recharge', 0)),
            'transport': float(request.form.get('transport', 0)),
            'dining': float(request.form.get('dining', 0)),
            'ott': float(request.form.get('ott', 0)),
            'shopping': float(request.form.get('shopping', 0)),
            'goal_price': float(request.form.get('goal_price', 0))
        }
        
        # Calculate metrics
        needs = data['rent'] + data['utilities'] + data['groceries'] + data['recharge'] + data['transport']
        wants = data['dining'] + data['ott'] + data['shopping']
        total_expenses = needs + wants
        savings = data['income'] - total_expenses
        savings_rate = (savings / data['income'] * 100) if data['income'] > 0 else 0
        
        data.update({
            'needs_total': needs,
            'wants_total': wants,
            'total_expenses': total_expenses,
            'savings': max(0, savings),
            'savings_rate': round(savings_rate, 2)
        })
        
        # Load existing data
        budgets = load_data()
        budgets.append(data)
        
        # Keep only last 100 entries
        if len(budgets) > 100:
            budgets = budgets[-100:]
        
        save_data(budgets)
        
        return jsonify({
            'status': 'success',
            'message': 'Budget saved successfully!',
            'data': data,
            'total_entries': len(budgets)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/budgets')
def get_budgets():
    budgets = load_data()
    return jsonify(budgets[-10:])  # Last 10 entries

@app.route('/api/summary')
def get_summary():
    budgets = load_data()
    if not budgets:
        return jsonify({'message': 'No data available'})
    
    df = pd.DataFrame(budgets)
    summary = {
        'total_entries': len(df),
        'avg_income': round(df['income'].mean(), 2),
        'avg_savings': round(df['savings'].mean(), 2),
        'avg_savings_rate': round(df['savings_rate'].mean(), 2),
        'best_month': df.loc[df['savings_rate'].idxmax()]['timestamp'] if len(df) > 0 else None
    }
    return jsonify(summary)

@app.route('/download/csv')
def download_csv():
    budgets = load_data()
    if not budgets:
        return "No data available", 404
    
    df = pd.DataFrame(budgets)
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'budgets_export.csv')
    df.to_csv(csv_path, index=False)
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], 'budgets_export.csv', as_attachment=True)

@app.route('/data/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
