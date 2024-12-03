import unittest
from app import app, users_collection, budgets_collection, expenses_collection
from flask import session
import bcrypt
from datetime import datetime

class TestExpenseTracker(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Create a test user
        self.username = 'testuser'
        self.password = 'password'
        self.hashed_password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({
            'username': self.username,
            'email': 'testuser@example.com',
            'password': self.hashed_password
        })

        # Set up session for testing
        with self.app as c:
            with c.session_transaction() as sess:
                sess['username'] = self.username

    def tearDown(self):
        # Clean up collections after each test
        users_collection.delete_many({'username': self.username})
        budgets_collection.delete_many({'username': self.username})
        expenses_collection.delete_many({'username': self.username})

    def test_signup(self):
        response = self.app.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Signup successful!', response.data)

    def test_login(self):
        response = self.app.post('/login', data={
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful!', response.data)

    def test_set_budget(self):
        response = self.app.post('/set_budget', data={
            'budget_amount': '1500'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        budget = budgets_collection.find_one({'username': self.username})
        self.assertIsNotNone(budget)
        self.assertEqual(budget['amount'], 1500.0)

    def test_view_expenses(self):
        # Insert a test expense
        expenses_collection.insert_one({
            'username': self.username,
            'amount': 100,
            'category': 'Food',
            'date': datetime.now()
        })

        response = self.app.get('/view_expenses')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Food', response.data)
        self.assertIn(b'100', response.data)

    def test_edit_expense(self):
        # Insert a test expense
        expense = {
            'username': self.username,
            'amount': 100,
            'category': 'Food',
            'date': datetime.now()
        }
        expense_id = expenses_collection.insert_one(expense).inserted_id

        # Edit the expense
        response = self.app.post(f'/edit_expense/{expense_id}', data={
            'amount': '200',
            'category': 'Grocery',
            'date': '2023-12-01',
            'notes': 'Updated expense'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check if the expense has been updated
        updated_expense = expenses_collection.find_one({'_id': expense_id})
        self.assertEqual(updated_expense['amount'], 200.0)
        self.assertEqual(updated_expense['category'], 'Grocery')

    def test_get_expense_data(self):
        # Insert test expenses
        expenses_collection.insert_many([
            {'username': self.username, 'amount': 100, 'category': 'Food', 'date': datetime.now()},
            {'username': self.username, 'amount': 150, 'category': 'Transportation', 'date': datetime.now()}
        ])

        response = self.app.get('/api/expense_data/week')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_expense_details(self):
        # Insert test expenses
        expenses_collection.insert_many([
            {'username': self.username, 'amount': 100, 'category': 'Food', 'date': datetime.now()},
            {'username': self.username, 'amount': 150, 'category': 'Transportation', 'date': datetime.now()}
        ])

        response = self.app.get('/api/expense_details/week')
        self.assertEqual(response.status_code, 200)
        details = response.get_json()
        self.assertIsInstance(details, list)
        self.assertGreater(len(details), 0)

if __name__ == '__main__':
    unittest.main()
