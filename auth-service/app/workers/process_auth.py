import random
import string
from passlib.hash import bcrypt

def hash_password(password: str, salt: str) -> str:
    return bcrypt.using(salt=salt).hash(password)

def generate_salt() -> str:
    allowed_chars = "./" + string.ascii_letters + string.digits
    return ''.join(random.choices(allowed_chars, k=22))