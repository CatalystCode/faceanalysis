from flask_httpauth import HTTPBasicAuth
from flask import g
from .models.models import User
from .models.models import DatabaseManager

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password):
    user = User.verify_auth_token(username_or_token)
    session = DatabaseManager().get_session()
    if not user:
        user = session.query(User).filter(
            User.username == username_or_token).first()
        if not user or not user.verify_password(password):
            session.close()
            return False
    g.user = user
    session.close()
    return True
