from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from backend.app.config.settings import settings

bearer_scheme = HTTPBearer(auto_error=False)


def issue_demo_token(customer_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": customer_id, "iss": "delivery-support-agent", "aud": "delivery-support-api", "iat": now, "exp": now + timedelta(hours=1)},
        settings.auth_secret,
        algorithm="HS256",
    )


def authenticated_customer(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer authentication is required.", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.auth_secret,
            algorithms=["HS256"],
            issuer="delivery-support-agent",
            audience="delivery-support-api",
        )
        customer_id = claims.get("sub")
        if not isinstance(customer_id, str) or not customer_id:
            raise InvalidTokenError("Missing subject")
        return customer_id
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired bearer token.", headers={"WWW-Authenticate": "Bearer"}) from exc