import pytest
from WebApp.app import app, users_collection, expenses_collection, budgets_collection
from datetime import datetime, timedelta  # Import datetime and timedelta as they are used in the tested functions
import bcrypt  # Import bcrypt for hashing passwords

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def add_test_data():
    # Add test data before running tests
    username = "test_user"
    if not users_collection.find_one({"username": username}):
        users_collection.insert_one({
            "username": username,
            "email": "test_user@example.com",
            "password": bcrypt.hashpw(b"password", bcrypt.gensalt())
        })
    # Insert a sample expense
    expenses_collection.insert_one({
        "username": username,
        "amount": 50.0,
        "category": "Food",
        "date": datetime.now(),
        "notes": "Test Expense",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    yield
    # Clean up test data after the test
    users_collection.delete_one({"username": username})
    expenses_collection.delete_many({"username": username})

def test_home_page(client, add_test_data):
    # Case 1: No user logged in, expect a redirect to the auth page
    response = client.get('/')
    assert response.status_code == 302  # Redirect expected
    assert response.location.endswith('/auth')  # Redirect should go to the auth page

    # Case 2: User logged in, expect a redirect to add_expense page
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    response = client.get('/')
    assert response.status_code == 302  # Redirect expected when logged in
    assert response.location.endswith('/add-expense')  # Redirect should go to the add_expense page

def test_view_expenses(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'  # Mock a logged-in user

    response = client.get('/view_expenses')
    assert response.status_code == 200
    assert b'Edit Expenses' in response.data  # Check that the view_expenses page is rendered

def test_display_dashboard(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'  # Mock a logged-in user

    # Testing weekly display
    response = client.get('/display?date_range=week')
    assert response.status_code == 200
    assert b'Spent Dashboard' in response.data  # Check that the display page is rendered for week
    assert b'Food' in response.data  # Verify that "Food" category is displayed in the HTML

    # Testing monthly display
    response = client.get('/display?date_range=month')
    assert response.status_code == 200
    assert b'Spent Dashboard' in response.data  # Check that the display page is rendered for month
    assert b'Food' in response.data  # Verify that "Food" category is displayed in the HTML

    # Testing yearly display
    response = client.get('/display?date_range=year')
    assert response.status_code == 200
    assert b'Spent Dashboard' in response.data  # Check that the display page is rendered for year
    assert b'Food' in response.data  # Verify that "Food" category is displayed in the HTML

def test_set_budget(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'  # Mock a logged-in user

    response = client.post('/set_budget', data={'budget_amount': 500})
    assert response.status_code == 302  # Should redirect after setting budget
    assert '/set_budget' in response.location

def test_add_expense(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'  # Mock a logged-in user

    response = client.post('/add-expense', data={
        'date': '2024-12-01',
        'category': 'Food',
        'amount': '50.5',
        'note': 'Lunch'
    })
    assert response.status_code == 302  # Should redirect after adding expense
    assert '/view_expenses' in response.location
