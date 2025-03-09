# middleware/auth_middleware.py
from fastapi import Request, HTTPException
import jwt
import requests
import json
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any, List
import time


class CognitoAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.cognito_region = "aws-region"  # e.g., "us-east-1"
        self.cognito_user_pool_id = "user-pool-id"
        self.cognito_app_client_id = "client-id"

        # Public keys URL
        self.jwks_url = f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json"

        # Load and cache the public keys
        self.jwks = self._get_jwks()
        self.last_jwks_load = time.time()

    def _get_jwks(self) -> Dict[str, Any]:
        """Get the JSON Web Key Set from Cognito"""
        try:
            response = requests.get(self.jwks_url)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error loading JWKS: {str(e)}")
            return {"keys": []}

    def _get_public_key(self, kid: str) -> str:
        """Get the public key matching the key ID from the JWKS"""
        # Reload JWKS if it's been more than an hour
        if time.time() - self.last_jwks_load > 3600:
            self.jwks = self._get_jwks()
            self.last_jwks_load = time.time()

        for key in self.jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PEM format - this is a simplified version
                # In a real implementation, you'd use a library like python-jose
                # to properly convert the JWK to PEM
                return key
        return None

    async def dispatch(self, request: Request, call_next):
        # List of paths that don't need authentication
        public_paths = [
            "/v1/auth/signup",
            "/v1/auth/login",
            "/v1/auth/confirm",
            "/v1/auth/refresh",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        # Skip authentication for public paths
        if request.url.path in public_paths:
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return await call_next(request)  # Allow request without user info

        try:
            # Extract token
            token_type, token = auth_header.split()
            if token_type.lower() != "bearer":
                request.state.user_id = None
                return await call_next(request)

            # Get the key ID from the token header
            token_header = jwt.get_unverified_header(token)
            kid = token_header.get("kid")

            # Get the public key
            public_key = self._get_public_key(kid)
            if not public_key:
                request.state.user_id = None
                return await call_next(request)

            # Verify the token
            # In a real implementation, you'd use the python-jose library
            # to properly verify the JWT signature with the JWK
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.cognito_app_client_id,
                options={"verify_exp": True}
            )

            # Set user info in request state
            request.state.user_id = payload.get("sub")  # This is the Cognito user ID

        except Exception as e:
            # Failed to authenticate, but we'll still process the request
            # Just without user info
            request.state.user_id = None

        return await call_next(request)