import pytest
from app import app, users_collection, budgets_collection, expenses_collection
from flask import session
from datetime import datetime
import bcrypt

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        with app.app_context():
            # Clear test database collections before each test
            users_collection.delete_many({})
            budgets_collection.delete_many({})
            expenses_collection.delete_many({})
        yield client

# Helper functions to create test data
def create_test_user(username, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({
        'username': username,
        'email': f'{username}@example.com',
        'password': hashed_password
    })

def login_user(client, username, password):
    return client.post('/login', data={'username': username, 'password': password})

# Tests for user authentication
def test_signup(client):
    response = client.post('/signup', data={'username': 'testuser', 'email': 'testuser@example.com', 'password': 'password123'})
    assert response.status_code == 201
    assert response.json['message'] == 'Signup successful!'
    user = users_collection.find_one({'username': 'testuser'})
    assert user is not None

def test_login_success(client):
    create_test_user('testuser', 'password123')
    response = login_user(client, 'testuser', 'password123')
    assert response.status_code == 200
    assert response.json['message'] == 'Login successful!'

def test_login_failure(client):
    create_test_user('testuser', 'password123')
    response = login_user(client, 'testuser', 'wrongpassword')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid username or password.'

# Tests for budget functionality
def test_set_budget(client):
    create_test_user('testuser', 'password123')
    login_user(client, 'testuser', 'password123')

    response = client.post('/set_budget', data={'budget_amount': '500.0'})
    assert response.status_code == 302  # Redirect to the budget page

    budget = budgets_collection.find_one({'username': 'testuser'})
    assert budget is not None
    assert budget['amount'] == 500.0

# Tests for expense functionality
def test_add_expense(client):
    create_test_user('testuser', 'password123')
    login_user(client, 'testuser', 'password123')

    expenses_collection.insert_one({
        'username': 'testuser',
        'amount': 100.0,
        'category': 'Food',
        'date': datetime.now(),
        'notes': 'Test expense'
    })

    expenses = list(expenses_collection.find({'username': 'testuser'}))
    assert len(expenses) == 1
    assert expenses[0]['category'] == 'Food'
    assert expenses[0]['amount'] == 100.0

# Tests for viewing expenses
def test_view_expenses(client):
    create_test_user('testuser', 'password123')
    login_user(client, 'testuser', 'password123')

    expenses_collection.insert_one({
        'username': 'testuser',
        'amount': 100.0,
        'category': 'Food',
        'date': datetime.now(),
        'notes': 'Test expense'
    })

    response = client.get('/view_expenses')
    assert response.status_code == 200
    assert b'Test expense' in response.data

# Tests for editing expenses
def test_edit_expense(client):
    create_test_user('testuser', 'password123')
    login_user(client, 'testuser', 'password123')

    expense_id = expenses_collection.insert_one({
        'username': 'testuser',
        'amount': 100.0,
        'category': 'Food',
        'date': datetime.now(),
        'notes': 'Old expense'
    }).inserted_id

    response = client.post(f'/edit_expense/{expense_id}', data={
        'amount': '200.0',
        'category': 'Food',
        'date': '2023-12-31',
        'notes': 'Updated expense'
    })
    assert response.status_code == 302  # Redirect to the expenses page

    updated_expense = expenses_collection.find_one({'_id': expense_id})
    assert updated_expense['amount'] == 200.0
    assert updated_expense['notes'] == 'Updated expense'
