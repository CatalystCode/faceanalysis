from itsdangerous import BadSignature
from itsdangerous import SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from passlib.apps import custom_app_context as password_context

from faceanalysis.models.database_manager import get_database_manager
from faceanalysis.models.models import User
from faceanalysis.settings import TOKEN_EXPIRATION
from faceanalysis.settings import TOKEN_SECRET_KEY


class AuthError(Exception):
    pass


class InvalidPassword(AuthError):
    pass


class InvalidAuthToken(AuthError):
    pass


class UserDoesNotExist(AuthError):
    pass


class DuplicateUser(AuthError):
    pass


def generate_auth_token(user: User) -> str:
    serializer = Serializer(TOKEN_SECRET_KEY, expires_in=TOKEN_EXPIRATION)
    token = serializer.dumps({'id': user.id})
    return token.decode('ascii')  # type: ignore


def load_user_from_auth_token(token: str) -> User:
    serializer = Serializer(TOKEN_SECRET_KEY)
    try:
        data = serializer.loads(token)
    except (BadSignature, SignatureExpired):
        raise InvalidAuthToken()

    db = get_database_manager()
    session = db.get_session()
    user = session.query(User)\
        .filter(User.id == data['id'])\
        .first()
    session.close()
    return user


def load_user(username: str, password: str) -> User:
    db = get_database_manager()
    session = db.get_session()
    user = session.query(User) \
        .filter(User.username == username) \
        .first()
    session.close()

    if not user:
        raise UserDoesNotExist()

    if not password_context.verify(password, user.password_hash):
        raise InvalidPassword()

    return user


def register_user(username: str, password: str):
    db = get_database_manager()
    session = db.get_session()
    user = session.query(User) \
        .filter(User.username == username) \
        .first()
    session.close()

    if user is not None:
        raise DuplicateUser()

    user = User()
    user.username = username
    user.password_hash = password_context.encrypt(password)
    session = db.get_session()
    session.add(user)
    db.safe_commit(session)
