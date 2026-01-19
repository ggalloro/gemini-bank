from models import User

def test_user_password_hashing():
    u = User(firstname="Test", lastname="User", email="test@example.com")
    u.set_password("cat")
    assert u.check_password("cat")
    assert not u.check_password("dog")

def test_user_repr():
    u = User(firstname="Test", lastname="User", email="test@example.com")
    assert str(u) == "Test User"
