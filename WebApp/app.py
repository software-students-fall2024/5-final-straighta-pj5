from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import bcrypt
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
# Setup database for users
db = client['p5_user_database']
users_collection = db['p5_users']
budgets_collection = db['p5_budgets']
expenses_collection = db['p5_expenses']

# Constants
EXPENSE_CATEGORIES = ['Food', 'Transportation', 'Entertainment', 'Housing', 'Grocery', 'Shopping']

# User authentication using session
@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('auth'))

@app.route('/auth')
def auth():
    if 'username' in session:
        return redirect('/') 
    return render_template('login.html')

# Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = users_collection.find_one({'username': username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        session['username'] = username 
        return jsonify(message="Login successful!"), 200
    else:
        return jsonify(message="Invalid username or password."), 401

# Signup
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if users_collection.find_one({'username': username}):
        return jsonify(message="Username already exists."), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    users_collection.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password
    })

    return jsonify(message="Signup successful!"), 201

# Budget
@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():
    if 'username' not in session:
        return redirect(url_for('auth'))

    if request.method == 'POST':
        try:
            new_amount = float(request.form.get('budget_amount', 0))
            budgets_collection.update_one(
                {'username': session['username']},
                {
                    '$set': {
                        'amount': new_amount,
                        'updated_at': datetime.utcnow()
                    },
                    '$setOnInsert': {
                        'created_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            return redirect(url_for('set_budget'))
        except ValueError:
            return "Invalid amount", 400

    current_budget = budgets_collection.find_one({'username': session['username']})
    return render_template('set_budget.html', current_budget=current_budget)

# Expense
@app.route('/view_expenses')
def view_expenses():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    category = request.args.get('category')
    
    # Build query
    query = {'username': session['username']}
    if category:
        query['category'] = category
    
    # Get expenses
    expenses = list(expenses_collection.find(query).sort('date', -1))
    
    # Get current budget
    current_budget = budgets_collection.find_one({'username': session['username']})
    
    return render_template('view_expenses.html', 
                         expenses=expenses,
                         current_budget=current_budget,
                         categories=EXPENSE_CATEGORIES)

# Helper function to calculate monthly total
def get_monthly_total(username, year, month):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    pipeline = [
        {
            '$match': {
                'username': username,
                'date': {
                    '$gte': start_date,
                    '$lt': end_date
                }
            }
        },
        {
            '$group': {
                '_id': None,
                'total': {'$sum': '$amount'}
            }
        }
    ]
    
    result = list(expenses_collection.aggregate(pipeline))
    return result[0]['total'] if result else 0

# Display route for spent dashboard
@app.route('/display', methods=['GET'])
def display():
    if 'username' not in session:
        return redirect(url_for('auth'))

    date_range = request.args.get('date_range', 'week')
    today = datetime.today()

    if date_range == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(weeks=1)
    elif date_range == 'month':
        start_date = today.replace(day=1)
        next_month = (today.month % 12) + 1
        end_date = today.replace(month=next_month, day=1)
    elif date_range == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(year=today.year + 1, month=1, day=1)
    else:
        start_date = end_date = today

    # Fetch expenses in the selected date range
    expenses = expenses_collection.find({
        "username": session['username'],
        "date": {"$gte": start_date, "$lt": end_date}
    })

    # Prepare expense data for chart
    expense_data = {}
    for expense in expenses:
        day = expense['date'].strftime('%Y-%m-%d')
        if day not in expense_data:
            expense_data[day] = 0
        expense_data[day] += expense['amount']

    # Fetch detailed expense data by category
    pipeline = [
        {
            "$match": {
                "username": session['username'],
                "date": {"$gte": start_date, "$lt": end_date}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "num_transactions": {"$sum": 1},
                "total_amount": {"$sum": "$amount"}
            }
        }
    ]
    expense_details = list(expenses_collection.aggregate(pipeline))
    expense_details = [
        {
            "category": detail["_id"],
            "num_transactions": detail["num_transactions"],
            "amount_spent": detail["total_amount"]
        }
        for detail in expense_details
    ]

    # Fetch budget information
    budget = budgets_collection.find_one({'username': session['username']})
    budget_amount = budget['amount'] if budget else 0

    # Calculate total spent
    total_spent = sum(detail['amount_spent'] for detail in expense_details)

    return render_template(
        'display.html',
        date_range=date_range,
        expense_data=expense_data,
        expense_details=expense_details,
        budget=budget_amount,
        total_spent=total_spent
    )

if __name__ == '__main__':
    app.run(debug=True)