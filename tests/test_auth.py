from app.auth import login


def test_login_success():
    assert login("demo", "password") is True


def test_login_failure():
    assert login("demo", "wrong") is False