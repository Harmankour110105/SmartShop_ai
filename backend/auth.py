# backend/auth.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from db import User
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configurations
SECRET_KEY = "your-secret-key-keep-it-secret"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await User.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return {"username": user.username}

@router.post("/signup")
async def signup(user: UserCreate):
    try:
        # Check if user exists
        existing_user = await User.find_one({"username": user.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        new_user = User(username=user.username, hashed_password=hashed_password)
        await new_user.insert()
        logger.info(f"User {user.username} registered successfully")
        
        return {"message": "User registered successfully"}
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Find user
        user = await User.find_one({"username": form_data.username})
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        logger.info(f"User {form_data.username} logged in successfully")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return {"username": current_user["username"]}
