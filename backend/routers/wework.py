from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import bcrypt
import secrets
import httpx
from backend.models import get_db, User, RoleEnum
from backend.models.schemas import LoginResponse, UserResponse
from backend.services.auth_service import create_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 企业微信SSO配置（需要替换为实际值）
WEWORK_CORP_ID = "your-corp-id"
WEWORK_AGENT_ID = "your-agent-id"
WEWORK_AGENT_SECRET = "your-agent-secret"

@router.get("/wework/redirect")
async def wework_redirect():
    """生成企业微信授权跳转URL"""
    redirect_uri = "http://your-domain.com/api/auth/wework/callback"
    url = f"https://open.work.weixin.qq.com/wwopen/sso/qq_connect?appid={WEWORK_CORP_ID}&agentid={WEWORK_AGENT_ID}&redirect_uri={redirect_uri}&state=1"
    return {"redirect_url": url}

@router.get("/wework/callback")
async def wework_callback(code: str, db: Session = Depends(get_db)):
    """企业微信OAuth2回调，处理单点登录"""
    user_info = await get_wework_user_info(code)
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from WeChat Work")

    phone = user_info.get("mobile")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number not provided")

    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(
            username=phone,
            phone=phone,
            password_hash=_generate_random_hash(),
            roles=RoleEnum.FILLER
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.username})
    departments = [ud.department.name for ud in user.user_departments]
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            roles=[user.roles.value] if user.roles else [],
            departments=departments
        )
    )

async def get_wework_user_info(code: str) -> dict:
    """通过code获取企业微信用户信息"""
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"
    params = {
        "access_token": await get_wework_access_token(),
        "code": code
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        if data.get("errcode") != 0:
            return None
        return data

async def get_wework_access_token() -> str:
    """获取企业微信access_token"""
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    params = {
        "corpid": WEWORK_CORP_ID,
        "corpsecret": WEWORK_AGENT_SECRET
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        if data.get("errcode") != 0:
            raise HTTPException(status_code=500, detail="Failed to get WeChat Work access token")
        return data.get("access_token")

def _generate_random_hash():
    """为SSO用户生成随机密码hash"""
    random_password = secrets.token_hex(16)
    return bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
