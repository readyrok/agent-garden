from fastapi import APIRouter, HTTPException
from domain.models.auth import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    # Stub — real implementation on Day 7
    # For now, accept demo/demo123 and return a fake token
    if request.username == "demo" and request.password == "demo123":
        return TokenResponse(access_token="dev-token-placeholder")
    raise HTTPException(status_code=401, detail="Invalid credentials")