from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.config.settings import settings
from backend.app.security.auth import issue_demo_token

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class DemoLoginRequest(BaseModel):
    customer_id: Literal["CUS-1001", "CUS-1002"]


@router.post("/demo")
def demo_login(request: DemoLoginRequest) -> dict[str, str]:
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")
    return {"access_token": issue_demo_token(request.customer_id), "token_type": "bearer"}