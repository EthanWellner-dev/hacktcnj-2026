import os
import tempfile
import pytest
from app import app, users_col

@pytest.fixture(autouse=True)
def clear_db():
    # drop users collection before each test
    users_col.delete_many({})
    yield


def test_signup_and_login(monkeypatch):
    client = app.test_client()

    # signup new user
    resp = client.post('/api/users/signup', json={
        'username': 'alice',
        'password': 'secret',
        'persona': 'student'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'

    # duplicate signup returns conflict
    resp2 = client.post('/api/users/signup', json={
        'username': 'alice',
        'password': 'secret',
        'persona': 'student'
    })
    assert resp2.status_code == 409

    # login with wrong password
    resp3 = client.post('/api/users/login', json={
        'username': 'alice',
        'password': 'wrong',
        'persona': 'student'
    })
    assert resp3.status_code == 401

    # login with correct
    resp4 = client.post('/api/users/login', json={
        'username': 'alice',
        'password': 'secret',
        'persona': 'student'
    })
    assert resp4.status_code == 200
    login_data = resp4.get_json()
    assert login_data['status'] == 'success'
    assert login_data['xp'] == 0


def test_leaderboard():
    client = app.test_client()
    # insert fake users
    users_col.insert_many([
        {'username': 'bob', 'password_hash': 'x', 'persona': 'student', 'xp': 5},
        {'username': 'carol', 'password_hash': 'y', 'persona': 'student', 'xp': 10}
    ])
    resp = client.get('/api/users/leaderboard')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]['name'] == 'carol'
    assert data[1]['name'] == 'bob'
