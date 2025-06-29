#
# SmartCare Insight - auth.py
#
# Copyright 2025 SmartCare Insight Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from dotenv import load_dotenv

from models import User, UserInDB, TokenData

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "patients:read": "Read patient information",
        "patients:write": "Modify patient information",
        "vitals:read": "Read vital signs data",
        "alerts:read": "Read alerts",
        "alerts:write": "Modify alerts",
        "analysis:read": "Read analysis results",
        "analysis:write": "Request new analyses",
        "admin": "Administrative access"
    }
)

# Mock user database - in a real system, this would be stored in a database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin"),
        "disabled": False,
        "role": "admin"
    },
    "doctor": {
        "username": "doctor",
        "full_name": "Doctor Example",
        "email": "doctor@example.com",
        "hashed_password": pwd_context.hash("doctor"),
        "disabled": False,
        "role": "doctor"
    },
    "nurse": {
        "username": "nurse",
        "full_name": "Nurse Example",
        "email": "nurse@example.com",
        "hashed_password": pwd_context.hash("nurse"),
        "disabled": False,
        "role": "nurse"
    }
}

# Role-based scope mapping
role_scopes = {
    "admin": [
        "patients:read", "patients:write",
        "vitals:read",
        "alerts:read", "alerts:write",
        "analysis:read", "analysis:write",
        "admin"
    ],
    "doctor": [
        "patients:read", "patients:write",
        "vitals:read",
        "alerts:read", "alerts:write",
        "analysis:read", "analysis:write"
    ],
    "nurse": [
        "patients:read",
        "vitals:read",
        "alerts:read",
        "analysis:read"
    ]
}


def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash a password."""
    return pwd_context.hash(password)


def get_user(db, username: str):
    """Get a user from the database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(fake_db, username: str, password: str):
    """Authenticate a user."""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create an access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """Create a refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_scopes_for_role(role: str) -> List[str]:
    """Get scopes for a role."""
    return role_scopes.get(role, [])


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
):
    """Get the current user from a token."""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except (JWTError, ValidationError):
        raise credentials_exception
        
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
        
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    # Check if the user has the required scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
            
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    """Get the current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
