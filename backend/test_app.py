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


def test_module6_xp_award(monkeypatch):
    client = app.test_client()
    # create a user and login to obtain token
    client.post('/api/users/signup', json={
        'username': 'dave',
        'password': 'pass',
        'persona': 'coder'
    })
    login_resp = client.post('/api/users/login', json={
        'username': 'dave',
        'password': 'pass'
    })
    token = login_resp.get_json().get('token')
    assert token

    # call module6 complete with 30 xp
    resp = client.post('/api/module6/complete', json={'xp': 30}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert data['xp'] == 30

    # call again to ensure xp accumulates
    resp2 = client.post('/api/module6/complete', json={'xp': 20}, headers={'Authorization': f'Bearer {token}'})
    assert resp2.status_code == 200
    assert resp2.get_json()['xp'] == 50

    # missing token should fail
    resp3 = client.post('/api/module6/complete', json={'xp': 10})
    assert resp3.status_code == 401

    # negative xp should be rejected
    resp4 = client.post('/api/module6/complete', json={'xp': -5}, headers={'Authorization': f'Bearer {token}'})
    assert resp4.status_code == 400


def test_module6_page_renders():
    client = app.test_client()
    resp = client.get('/module6')
    assert resp.status_code == 200
    assert b'Confidence Calibration' in resp.data
