from typing import Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.providers.zhihu_oauth import LoginRequired, OAuthError

router = APIRouter(tags=["account"])
SESSION_COOKIE = "zhijing_session"
STATE_COOKIE = "zhijing_oauth_browser"


def private(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.get("/api/auth/session")
async def session(request: Request):
    service = request.app.state.oauth
    try:
        user = service.require(request.cookies.get(SESSION_COOKIE))["profile"]
    except LoginRequired:
        user = None
    return private(JSONResponse({"user": user, "login_available": service.configured}))


@router.get("/api/auth/zhihu/login")
async def login(request: Request):
    service = request.app.state.oauth
    if not service.configured:
        raise HTTPException(503, "知乎登录尚未配置，请先确认已登记的回调地址。")
    url, browser = service.begin()
    response = private(RedirectResponse(url, status_code=302))
    response.set_cookie(STATE_COOKIE, browser, max_age=600, httponly=True,
                        secure=service.settings.oauth_cookie_secure, samesite="lax", path="/api/auth/zhihu")
    return response


@router.get("/api/auth/zhihu/callback")
async def callback(request: Request, authorization_code: str | None = None,
                   code: str | None = None, state: str | None = None, error: str | None = None):
    service = request.app.state.oauth
    target = service.settings.frontend_origin.rstrip("/")
    try:
        if error or not state:
            raise LoginRequired()
        session_id, lifetime = await service.complete(
            authorization_code or code, state, request.cookies.get(STATE_COOKIE))
        service.logout(request.cookies.get(SESSION_COOKIE))
        response = private(RedirectResponse(target + "/?account=1", status_code=303))
        response.set_cookie(SESSION_COOKIE, session_id, max_age=lifetime,
                            httponly=True, secure=service.settings.oauth_cookie_secure,
                            samesite="lax", path="/api")
    except OAuthError:
        # Never include upstream errors, codes or tokens in a redirect.
        response = private(RedirectResponse(target + "/?login_error=authorization_failed", status_code=303))
    response.delete_cookie(STATE_COOKIE, path="/api/auth/zhihu")
    return response


@router.post("/api/auth/logout")
async def logout(request: Request):
    service = request.app.state.oauth
    callback = urlsplit(service.settings.zhihu_oauth_redirect_uri)
    allowed = {service.settings.frontend_origin.rstrip("/"), f"{callback.scheme}://{callback.netloc}"}
    if request.headers.get("origin") not in allowed:
        raise HTTPException(403, "请求来源无效。")
    service.logout(request.cookies.get(SESSION_COOKIE))
    response = private(JSONResponse({"ok": True}))
    response.delete_cookie(SESSION_COOKIE, path="/api")
    response.delete_cookie(STATE_COOKIE, path="/api/auth/zhihu")
    return response


async def page(request, resource, offset, limit, content_type="all"):
    if int(offset) > 9223372036854775807:
        raise HTTPException(422, "分页偏移量超出范围。")
    result = await request.app.state.oauth.page(request.cookies.get(SESSION_COOKIE),
        resource, offset=offset, limit=limit, content_type=content_type)
    return private(JSONResponse(result))


@router.get("/api/me/followees")
async def followees(request: Request, offset: str = Query("0", pattern=r"^[0-9]{1,19}$"),
                    limit: int = Query(20, ge=1, le=50)):
    return await page(request, "followees", offset, limit)


@router.get("/api/me/contents")
async def contents(request: Request, offset: str = Query("0", pattern=r"^[0-9]{1,19}$"),
                   limit: int = Query(20, ge=1, le=50),
                   content_type: Literal["all", "answer", "article", "zvideo", "pin", "question"] = "all"):
    return await page(request, "contents", offset, limit, content_type)
