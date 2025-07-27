import os
import jwt
import secrets
import smtplib
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from models import User, UserResponse
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Security scheme
security = HTTPBearer()

# Get database connection directly
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'test_database')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_reset_token(email: str) -> str:
    """Cria token para reset de senha (válido por 1 hora)"""
    data = {
        "email": email,
        "type": "password_reset",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str) -> Optional[str]:
    """Verifica token de reset e retorna email se válido"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("email")
    except jwt.PyJWTError:
        return None

async def send_reset_email(email: str, reset_token: str):
    """Envia email de reset de senha (versão simplificada)"""
    try:
        # Para desenvolvimento, vamos apenas logar o token
        # Em produção, você configuraria SMTP real
        reset_url = f"https://xzenpress.com/reset-password?token={reset_token}"
        
        print(f"🔑 RESET DE SENHA SOLICITADO:")
        print(f"📧 Email: {email}")
        print(f"🔗 Link de reset: {reset_url}")
        print(f"⏰ Válido por: 1 hora")
        
        # TODO: Implementar envio real de email
        # smtp_server = "smtp.gmail.com"
        # smtp_port = 587
        # smtp_user = os.environ.get("SMTP_USER")
        # smtp_pass = os.environ.get("SMTP_PASS")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email de reset: {str(e)}")
        return False

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserResponse(**user)

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[UserResponse]:
    """Get current user if authenticated, return None if not"""
    if not credentials:
        return None
        
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except jwt.PyJWTError:
        return None
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        return None
    
    return UserResponse(**user)

async def get_premium_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    
    # Check if subscription is still valid
    if current_user.subscription_expires and current_user.subscription_expires < datetime.utcnow():
        # Update user to non-premium
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"is_premium": False, "subscription_expires": None}}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription expired"
        )
    
    return current_user

async def authenticate_user(email: str, password: str):
    user = await db.users.find_one({"email": email})
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user