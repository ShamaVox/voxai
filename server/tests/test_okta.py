# import pytest
# from flask import url_for
# from unittest.mock import patch, Mock
# from server.app import app as flask_app
# from server.src.database import Account, db

# # TODO: Update these unit tests for the new multi-tab functionality

# @pytest.fixture
# def client():
#     flask_app.config['TESTING'] = True
#     with flask_app.test_client() as client:
#         yield client

# @patch('requests.post')
# def test_okta_callback_success_existing_user(mock_post, client):
#     # Mock the token exchange
#     mock_post.return_value.json.return_value = {
#         'access_token': 'fake_access_token'
#     }
    
#     # Mock the userinfo request
#     with patch('requests.get') as mock_get:
#         mock_get.return_value.json.return_value = {
#             'email': 'existing@example.com',
#             'name': 'Existing User'
#         }
        
#         # Create an existing user
#         with flask_app.app_context():
#             existing_account = Account(email='existing@example.com', name='Existing User')
#             db.session.add(existing_account)
#             db.session.commit()
        
#         response = client.get('/okta?code=fake_code')
        
#         assert response.status_code == 302  # Should redirect
#         assert response.headers['Location'] == url_for('serve')
#         assert 'authToken' in response.headers['Set-Cookie']

# @patch('requests.post')
# def test_okta_callback_success_new_user(mock_post, client):
#     # Mock the token exchange
#     mock_post.return_value.json.return_value = {
#         'access_token': 'fake_access_token'
#     }
    
#     # Mock the userinfo request
#     with patch('requests.get') as mock_get:
#         mock_get.return_value.json.return_value = {
#             'email': 'new@example.com',
#             'name': 'New User'
#         }
        
#         response = client.get('/okta?code=fake_code')
        
#         assert response.status_code == 302  # Should redirect
#         assert response.headers['Location'] == url_for('serve')
#         assert 'authToken' in response.headers['Set-Cookie']
        
#         # Check if new user was created
#         with flask_app.app_context():
#             new_account = Account.query.filter_by(email='new@example.com').first()
#             assert new_account is not None
#             assert new_account.name == 'New User'

# def test_okta_callback_no_code(client):
#     response = client.get('/okta')
#     assert response.status_code == 400
#     assert b'Error: No code provided' in response.data

# @patch('requests.post')
# def test_okta_callback_token_exchange_failure(mock_post, client):
#     mock_response = Mock()
#     mock_response.json.return_value = {}
#     mock_post.return_value = mock_response
    
#     response = client.get('/okta?code=fake_code')
    
#     assert response.status_code == 500
#     assert b'Error during token exchange' in response.data

# @patch('requests.post')
# @patch('requests.get')
# def test_okta_callback_userinfo_failure(mock_get, mock_post, client):
#     # Mock the token exchange response
#     mock_post_response = Mock()
#     mock_post_response.json.return_value = {
#         'access_token': 'fake_access_token'
#     }
#     mock_post.return_value = mock_post_response

#     # Mock the userinfo request failure
#     mock_get_response = Mock()
#     mock_get_response.json.return_value = {}
#     mock_get_response.raise_for_status.side_effect = Exception('Userinfo request failed')
#     mock_get.return_value = mock_get_response

#     response = client.get('/okta?code=fake_code')
#     assert response.status_code == 500
#     assert b'Error: Unable to get user email' in response.data
