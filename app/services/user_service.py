import jwt
import bcrypt
from datetime import datetime, timedelta
from app.services.logger import client, settings

db = client["SSA_Security"]
users_collection = db["users"]

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def register_user_db(email: str, password: str, name: str, role: str, department: str):
    try:
        existing_user = await users_collection.find_one({"email": email})
        if existing_user:
            return {"status": "error", "message": "User already exists"}
            
        hashed_pw = get_password_hash(password)
        user_data = {
            "email": email,
            "password": hashed_pw,
            "name": name,
            "role": role,
            "department": department
        }
        
        await users_collection.insert_one(user_data)
        
        user_data.pop("password")
        user_data["id"] = str(user_data.pop("_id"))
        
        access_token = create_access_token(data={
            "sub": user_data["email"], 
            "name": user_data["name"],
            "role": user_data["role"],
            "department": user_data["department"]
        })
        refresh_token = create_refresh_token(data={"sub": user_data["email"]})
        
        return {"status": "success", "access_token": access_token, "refresh_token": refresh_token, "user": user_data}
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": "An internal server error occurred during registration."}

async def authenticate_user_db(email: str, password: str):
    user = await users_collection.find_one({"email": email})
    if not user:
         return {"status": "error", "message": "User not found"}
         
    if not verify_password(password, user["password"]):
         return {"status": "error", "message": "Invalid password"}
         
    user.pop("password")
    user["id"] = str(user.pop("_id"))
    
    access_token = create_access_token(data={
        "sub": user["email"], 
        "name": user["name"],
        "role": user["role"],
        "department": user["department"]
    })
    refresh_token = create_refresh_token(data={"sub": user["email"]})
    
    return {"status": "success", "access_token": access_token, "refresh_token": refresh_token, "user": user}

async def refresh_token_db(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return {"status": "error", "message": "Invalid token payload"}
            
        user = await users_collection.find_one({"email": email})
        if not user:
            return {"status": "error", "message": "User not found"}
            
        user.pop("password", None)
        user["id"] = str(user.pop("_id", ""))
        
        new_access_token = create_access_token(data={
            "sub": user["email"], 
            "name": user.get("name", "Unknown"),
            "role": user.get("role", "User"),
            "department": user.get("department", "Unassigned")
        })
        new_refresh_token = create_refresh_token(data={"sub": user["email"]})
        
        return {"status": "success", "access_token": new_access_token, "refresh_token": new_refresh_token, "user": user}
    except jwt.ExpiredSignatureError:
        return {"status": "error", "message": "Refresh token expired"}
    except jwt.InvalidTokenError:
        return {"status": "error", "message": "Invalid refresh token"}

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        name: str = payload.get("name")
        role: str = payload.get("role")
        department: str = payload.get("department")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid auth token")
        return {"email": email, "name": name, "role": role, "department": department}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        
async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "Super Admin":
        raise HTTPException(status_code=403, detail="Access denied. Super Admin role required.")
    return current_user

async def require_any_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=403, detail="Access denied. Admin privileges required.")
    return current_user

