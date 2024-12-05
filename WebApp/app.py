from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file, Response
import os
import bcrypt
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "5c354f218df7fc8404628facdcf6b76e923be3546f082185bf76aef1dade3d45"
app.secret_key = os.getenv("SECRET_KEY", "your_default_secret_key")

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
        return redirect(url_for('add_expense'))
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
        return redirect("/")
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
    session['username'] = username
    return redirect("/")

# Profile
@app.route('/profile', methods=['GET'])
def profile():
    if 'username' not in session:
        return redirect(url_for('auth'))

    # Fetch user information from the database
    user = users_collection.find_one({'username': session['username']})
    if not user:
        return "User not found", 404

    # Pass user data to the profile.html template
    return render_template(
        'profile.html',
        profile_picture=user.get('profile_picture', '/WebApp/img/default.png'),
        username=user['username'],
        email=user['email'],
        birthday=user.get('birthday', 'Not Set')
        current_page='user'
    )

DEFAULT_PROFILE_PIC = os.path.join(os.path.dirname(__file__), 'img', 'default.png')

@app.route('/get-pic', methods=['GET'])
def get_profile_pic():
    if 'username' not in session:
        return redirect(url_for('auth'))
    user = users_collection.find_one({'username': session['username']})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile_pic = user.get('profile_picture')
    if profile_pic:
        try:
            image_data = base64.b64decode(profile_pic)
            mime_type = user.get('profile_picture_mime_type', 'image/jpeg')
            # Return the image data with appropriate headers
            return Response(image_data, mimetype=mime_type)
        except Exception as e:
            print(f"Error decoding image data: {e}")
            return send_file(DEFAULT_PROFILE_PIC, mimetype='image/png')
    else:
        return send_file(DEFAULT_PROFILE_PIC, mimetype='image/png')

@app.route('/upload-pic', methods=['POST'])
def upload_profile_pic():
    if 'username' not in session:
        return redirect(url_for('auth'))

    file = request.files.get('profilePic')
    if file:
        file_data = file.read()
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        mime_type = file.mimetype

        users_collection.update_one(
            {'username': session['username']},
            {'$set': {
                'profile_picture': encoded_data,
                'profile_picture_mime_type': mime_type
            }}
        )
        return redirect('/profile')
    return redirect('/profile')


# Update Username and Birthday
@app.route('/update-username', methods=['POST'])
def update_username():
    if 'username' not in session:
        return redirect(url_for('auth'))

    new_username = request.form.get('newUsername')
    if new_username:
        existing_user = users_collection.find_one({'username': new_username})
        if existing_user:
            return jsonify({'message': 'Username already exists.'}), 400
        users_collection.update_one(
            {'username': session['username']},
            {'$set': {'username': new_username}}
        )
        session['username'] = new_username
        return redirect('/profile')
    return redirect('/profile')


@app.route('/update-birthday', methods=['POST'])
def update_birthday():
    if 'username' not in session:
        return redirect(url_for('auth'))

    new_birthday = request.form.get('newBirthday')
    if new_birthday:
        # Update the birthday in the database
        users_collection.update_one(
            {'username': session['username']},
            {'$set': {'birthday': new_birthday}}
        )
        return redirect('/profile')
    return redirect('/profile')

# Delete Account
@app.route('/delete-account', methods=['GET','POST'])
def delete_account():
    if 'username' not in session:
        return redirect(url_for('auth'))
    users_collection.delete_one({'username': session['username']})
    session.pop('username', None)
    return redirect(url_for('auth'))

# Sign Out
@app.route('/logout', methods=['GET','POST'])
def logout():
    # Clear the session
    session.pop('username', None)
    return redirect(url_for('auth'))


### Add Expense Route
@app.route('/add-expense', methods=['GET','POST'])
def add_expense():
    if 'username' not in session:
        return redirect(url_for('auth'))

    if request.method == 'POST':
        try:
            # Validate and parse input data
            date_str = request.form.get('date')
            category = request.form.get('category')
            amount_str = request.form.get('amount')
            notes = request.form.get('note', '')

            if not date_str or not category or not amount_str:
                return "All fields (except notes) are required.", 400

            if category not in EXPENSE_CATEGORIES:
                return "Invalid category.", 400

            try:
                amount = float(amount_str)
            except ValueError:
                return "Invalid amount format.", 400

            # Parse the date
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return "Invalid date format.", 400

            # Insert the expense into the database
            expense = {
                'username': session['username'], 
                'amount': amount,
                'category': category,
                'date': date,
                'notes': notes,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            expenses_collection.insert_one(expense)

            return redirect(url_for('view_expenses'))
        except Exception as e:
            return str(e), 500

    return render_template('add.html', current_page='add')

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
    return render_template('set_budget.html', current_budget=current_budget，current_page='add')

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

@app.route('/edit_expense/<expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'username' not in session:
        return redirect(url_for('auth'))

    try:
        expense_id = ObjectId(expense_id)
    except:
        return "Invalid expense ID", 400

    if request.method == 'POST':
        try:
            # Validate category
            category = request.form.get('category')
            if category not in EXPENSE_CATEGORIES:
                return "Invalid category", 400

            # Update expense
            expenses_collection.update_one(
                {
                    '_id': expense_id,
                    'username': session['username']
                },
                {
                    '$set': {
                        'amount': float(request.form.get('amount')),
                        'category': category,
                        'date': datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
                        'notes': request.form.get('notes', ''),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return redirect(url_for('view_expenses'))
        except (ValueError, KeyError) as e:
            return str(e), 400
    
    # Get expense for editing
    expense = expenses_collection.find_one({
        '_id': expense_id,
        'username': session['username']
    })
    
    if not expense:
        return "Expense not found", 404
        
    return jsonify({
        'id': str(expense['_id']),
        'amount': expense['amount'],
        'category': expense['category'],
        'date': expense['date'].strftime('%Y-%m-%d'),
        'notes': expense.get('notes', '')
    })

@app.route('/api/expense_data/<date_range>', methods=['GET'])
def get_expense_data(date_range):
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    username = session['username']
    start_date, end_date = get_date_range(date_range)

    expenses = list(expenses_collection.find({
        "username": username,
        "date": {"$gte": start_date, "$lt": end_date}
    }, {"_id": 0, "amount": 1}))
    
    data = [expense['amount'] for expense in expenses]
    return jsonify(data)

@app.route('/api/expense_details/<date_range>', methods=['GET'])
def get_expense_details(date_range):
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    username = session['username']
    start_date, end_date = get_date_range(date_range)

    pipeline = [
        {
            "$match": {
                "username": username,
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

    result = list(expenses_collection.aggregate(pipeline))
    details = [
        {
            "category": r["_id"],
            "num_transactions": r["num_transactions"],
            "amount_spent": r["total_amount"]
        }
        for r in result
    ]
    return jsonify(details)

def get_date_range(date_range):
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

    return start_date, end_date

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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=3000)