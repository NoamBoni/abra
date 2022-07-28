import jwt
from .settings import SECRET

algorithm = "HS256"

def generate_jwt(payload):
    return jwt.encode(payload, SECRET, algorithm=algorithm)

def parse_jwt(token):
    return jwt.decode(token, SECRET, algorithms=algorithm)
