#!/usr/bin/env python3
"""
🔐 REAL AUTHENTICATION MODULE
=============================
Provides production-grade authentication logic with JWT and bcrypt.
"""

import os
import datetime
import bcrypt
import jwt
from typing import Dict, Any, Optional

class RealAuth:
    def __init__(self, secret_key: str = None):
        # In production, this would come from a secure vault
        self.secret_key = secret_key or os.environ.get("JWT_SECRET", "production_fallback_secret_777_AAA_PLUS")
        self.algorithm = "HS256"

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    def create_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        """Create a JWT token"""
        to_encode = payload.copy()
        expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

# Singleton instance for global use
real_auth = RealAuth()
