from itsdangerous import BadSignature
from itsdangerous import SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from passlib.apps import custom_app_context as password_context

from faceanalysis.models import User
from faceanalysis.models import get_db_session
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

    with get_db_session() as session:
        user = session.query(User)\
            .filter(User.id == data['id'])\
            .first()
    return user


def load_user(username: str, password: str) -> User:
    with get_db_session() as session:
        user = session.query(User) \
            .filter(User.username == username) \
            .first()

    if not user:
        raise UserDoesNotExist()

    if not password_context.verify(password, user.password_hash):
        raise InvalidPassword()

    return user


def register_user(username: str, password: str):
    with get_db_session() as session:
        user = session.query(User) \
            .filter(User.username == username) \
            .first()

    if user is not None:
        raise DuplicateUser()

    user = User()
    user.username = username
    user.password_hash = password_context.encrypt(password)

    with get_db_session(commit=True) as session:
        session.add(user)
