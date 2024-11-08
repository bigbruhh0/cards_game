from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
load_dotenv('vars.env')

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		print(payload)
		username: str = payload.get("sub")
		exp: str = payload.get("exp")
		if username is None:
			raise JWTError("Invalid token")
		if 'exp' in payload:
			print(datetime.utcnow(),datetime.utcfromtimestamp(payload['exp']))
			if datetime.utcnow() > datetime.utcfromtimestamp(payload['exp']):
				raise HTTPException(status_code=401, detail="Token has expired")


		return username
	except JWTError:
		raise JWTError("Invalid token")
