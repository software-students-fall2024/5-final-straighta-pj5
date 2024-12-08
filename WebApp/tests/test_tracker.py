import pytest
from WebApp.app import app, users_collection, expenses_collection, budgets_collection, get_monthly_total
from datetime import datetime, timedelta  # Import datetime and timedelta as they are used in the tested functions
import bcrypt  # Import bcrypt for hashing passwords
import io
import base64
from bson import ObjectId

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

def test_login_invalid_credentials(client):
    response = client.post('/login', data={"username": "invalid_user", "password": "wrong_password"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password." in response.data

def test_view_expenses_with_category(client, add_test_data):
    expenses_collection.insert_one({
        "username": "test_user",
        "amount": 100.0,
        "category": "Food",
        "date": datetime.now()
    })

    with client.session_transaction() as session:
        session['username'] = 'test_user'

    # Filter by category
    response = client.get('/view_expenses?category=Food')
    assert response.status_code == 200
    assert b"Food" in response.data

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

def test_auth_page(client):
    # Case 1: No user logged in, should render the login page
    response = client.get('/auth')
    assert response.status_code == 200
    assert b'Login' in response.data  # Check if the login page is rendered

    # Case 2: User already logged in, should redirect to the home page
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    response = client.get('/auth')
    assert response.status_code == 302
    assert response.location.endswith('/')

def test_profile_page(client, add_test_data):
    # Case 1: User is not logged in, expect a redirect to auth
    response = client.get('/profile')
    assert response.status_code == 302
    assert '/auth' in response.location

    # Case 2: User is logged in, profile page should load
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Profile' in response.data  # Check if the profile page is rendered

def test_get_profile_pic(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    # Case 1: No profile picture, return default image
    response = client.get('/get-pic')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

    # Case 2: User has a profile picture
    users_collection.update_one(
        {"username": "test_user"},
        {"$set": {"profile_picture": base64.b64encode(b"test image content").decode("utf-8"),
                  "profile_picture_mime_type": "image/jpeg"}}
    )
    response = client.get('/get-pic')
    assert response.status_code == 200
    assert response.mimetype == 'image/jpeg'


def test_upload_pic(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    # Create a mock file
    data = {
        'profilePic': (io.BytesIO(b'test image content'), 'test_image.png')
    }
    response = client.post('/upload-pic', data=data, content_type='multipart/form-data')
    assert response.status_code == 302
    assert '/profile' in response.location

def test_update_username(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    # Case 1: Successful update
    response = client.post('/update-username', data={'newUsername': 'new_test_user'})
    assert response.status_code == 302  # Should redirect to /profile
    assert '/profile' in response.location

    # Case 2: Username already exists
    users_collection.insert_one({'username': 'existing_user'})
    response = client.post('/update-username', data={'newUsername': 'existing_user'}, follow_redirects=True)
    assert b'Username already exists.' in response.data
    users_collection.delete_one({'username': 'existing_user'})

def test_update_birthday(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    # Case 1: Valid birthday update
    response = client.post('/update-birthday', data={'newBirthday': '2000-01-01'})
    assert response.status_code == 302  # Should redirect to /profile
    assert '/profile' in response.location

    # Case 2: Invalid birthday (empty field)
    response = client.post('/update-birthday', data={'newBirthday': ''}, follow_redirects=True)
    assert b'Please provide a valid birthday.' in response.data

def test_delete_account(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    response = client.post('/delete-account')
    assert response.status_code == 302  # Should redirect to /auth
    assert '/auth' in response.location

    # Check that the user is removed from the database
    user = users_collection.find_one({'username': 'test_user'})
    assert user is None

def test_logout(client, add_test_data):
    with client.session_transaction() as session:
        session['username'] = 'test_user'

    response = client.post('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data  # Verify the auth page is rendered

    # Verify session is cleared
    with client.session_transaction() as session:
        assert 'username' not in session

def test_edit_expense(client, add_test_data):
    # Insert a sample expense to edit
    expense_id = str(expenses_collection.insert_one({
        "username": "test_user",
        "amount": 100.0,
        "category": "Food",
        "date": datetime.now(),
        "notes": "Sample Expense",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }).inserted_id)

    with client.session_transaction() as session:
        session['username'] = 'test_user'

    # Case 1: Edit page loads successfully
    response = client.get(f'/edit_expense/{expense_id}')
    assert response.status_code == 200
    assert b"Edit Expense" in response.data

    # Case 2: Valid POST request updates the expense
    response = client.post(f'/edit_expense/{expense_id}', data={
        "date": "2024-12-01",
        "category": "Transportation",
        "amount": "150.0",
        "notes": "Updated Expense"
    })
    assert response.status_code == 302
    assert '/view_expenses' in response.location

    # Case 3: Invalid POST request (invalid date format)
    response = client.post(f'/edit_expense/{expense_id}', data={
        "date": "invalid-date",
        "category": "Food",
        "amount": "50.0",
        "notes": "Invalid Date"
    })
    assert response.status_code == 400
    assert b"Invalid date format" in response.data

    # Cleanup
    expenses_collection.delete_one({"_id": ObjectId(expense_id)})

def test_get_monthly_total(client):
    # Insert specific expenses for the test
    expenses_collection.insert_many([
        {"username": "test_user", "amount": 50.0, "category": "Food", "date": datetime(2024, 12, 1)},
        {"username": "test_user", "amount": 30.0, "category": "Transportation", "date": datetime(2024, 12, 15)},
        {"username": "other_user", "amount": 50.0, "category": "Food", "date": datetime(2024, 12, 1)}  # Different user
    ])

    # Call the function and assert the result
    total = get_monthly_total("test_user", 2024, 12)
    assert total == 80.0  # 50.0 + 30.0 for "test_user" only

    # Clean up test data
    expenses_collection.delete_many({"username": "test_user"})

def test_delete_account_not_logged_in(client):
    response = client.get('/delete-account')
    assert response.status_code == 302  # Should redirect to /auth
    assert '/auth' in response.location



