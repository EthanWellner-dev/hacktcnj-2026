import os
import tempfile
import pytest
from app import app, users_col

@pytest.fixture(autouse=True)
def clear_db():
    # drop users collection before each test
    # users_col.delete_many({})
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


def test_training_submit_records_results(monkeypatch):
    client = app.test_client()
    # create and login user
    client.post('/api/users/signup', json={
        'username': 'eve',
        'password': 'xyz',
        'persona': 'tester'
    })
    login_resp = client.post('/api/users/login', json={
        'username': 'eve',
        'password': 'xyz'
    })
    token = login_resp.get_json().get('token')
    assert token

    # send training result without xp
    resp = client.post('/api/training/submit', json={'module': 'foo', 'results': {'foo': 'bar'}}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert data['xp'] == 0

    # send with xp and some metrics
    resp2 = client.post('/api/training/submit', json={'module': 'foo', 'results': {'xp': 15, 'confidence': 80}}, headers={'Authorization': f'Bearer {token}'})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2['status'] == 'success'
    assert data2['xp'] == 15

    # bad payloads
    resp3 = client.post('/api/training/submit', json={'module': '', 'results': {}}, headers={'Authorization': f'Bearer {token}'})
    assert resp3.status_code == 400
    resp4 = client.post('/api/training/submit', json={'module': 'foo', 'results': 'notadict'}, headers={'Authorization': f'Bearer {token}'})
    assert resp4.status_code == 400


def test_chat_evaluate(monkeypatch):
    client = app.test_client()
    # set up user and token
    client.post('/api/users/signup', json={'username':'test','password':'pw','persona':'dev'})
    login = client.post('/api/users/login', json={'username':'test','password':'pw'})
    token = login.get_json()['token']

    # mock the Gemini model call to return predictable JSON text
    class DummyModel:
        def generate_content(self, prompt):
            class Resp: pass
            resp = Resp()
            resp.text = '{"passed": true, "score": 80, "xp": 50, "feedback": "nice", "ai_response": "hello"}'
            return resp
    monkeypatch.setattr('google.generativeai.GenerativeModel', lambda name: DummyModel())

    resp = client.post('/api/chat/evaluate',
                       headers={'Authorization': f'Bearer {token}'},
                       json={'module':'icebreaker','user_message':'hi','context':''})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status']=='success'
    assert data['passed'] is True
    assert data['xp']==50
    assert 'ai_response' in data
    # ensure xp recorded in user doc
    u = users_col.find_one({'username':'test'})
    assert u['xp'] == 50


def test_module6_page_renders():
    client = app.test_client()
    resp = client.get('/module6')
    assert resp.status_code == 200
    assert b'Confidence Calibration' in resp.data
