import asyncio
import logging
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import OAuthAccessLogFilter, create_app
from app.providers.zhihu_oauth import LoginRequired, OAuthError, ZhihuOAuthProvider
from app.services.oauth_service import OAuthService


def settings():
    return Settings(_env_file=None, zhihu_oauth_app_id="618", zhihu_oauth_app_key="test-app-key",
                    zhihu_access_secret="test-platform-secret", oauth_cookie_secure=False,
                    zhihu_oauth_redirect_uri="http://localhost:8000/api/auth/zhihu/callback")


def make_provider(config, calls):
    def respond(request):
        calls.append(request)
        if request.url.path == "/access_token":
            form = parse_qs(request.content.decode())
            assert form["code"] == ["authorized-code"]
            assert form["app_key"] == ["test-app-key"]
            return httpx.Response(200, json={"code": 20000, "data": {
                "access_token": "private-user-token", "expires_in": 3600}})
        if request.url.path == "/user":
            assert request.headers["Authorization"] == "Bearer private-user-token"
            return httpx.Response(200, json={"uid": 969570047710216201,
                "fullname": "测试用户", "avatar_path": "https://picx.zhimg.com/example.jpg",
                "email": "private@example.com", "phone_no": "secret-phone"})
        assert request.headers["Authorization"] == "Bearer test-platform-secret"
        assert request.headers["X-OAuth-Token"] == "private-user-token"
        offset = request.url.params["Offset"]
        return httpx.Response(200, json={"Code": 0, "Data": {
            "Items": [{"Fullname": "关注者", "UrlToken": "example", "Title": "我的创作",
                       "Url": "https://www.zhihu.com/people/example", "Summary": "摘要"}],
            "Paging": {"IsEnd": offset != "0", "NextOffset": "25", "Totals": 2}}})
    return ZhihuOAuthProvider(config, httpx.MockTransport(respond))


def test_complete_flow_profile_paging_logout_and_no_token_exposure():
    config, calls = settings(), []
    app = create_app(config)
    app.state.oauth.provider = make_provider(config, calls)
    with TestClient(app, base_url="http://localhost:8000") as client:
        assert client.get("/api/auth/session").json()["user"] is None
        started = client.get("/api/auth/zhihu/login", follow_redirects=False)
        state = parse_qs(urlsplit(started.headers["location"]).query)["state"][0]
        callback = client.get("/api/auth/zhihu/callback", params={
            "state": state, "authorization_code": "authorized-code"}, follow_redirects=False)
        assert callback.status_code == 303
        assert "HttpOnly" in callback.headers["set-cookie"]
        result = client.get("/api/auth/session")
        assert result.json()["user"]["id"] == "969570047710216201"
        assert result.json()["user"]["name"] == "测试用户"
        assert "private-user-token" not in result.text
        assert "private@example.com" not in result.text
        assert "secret-phone" not in result.text
        assert result.headers["cache-control"] == "no-store"
        first = client.get("/api/me/followees?limit=1").json()
        assert first["has_more"] and first["next_offset"] == "25"
        assert not client.get("/api/me/followees?offset=25&limit=1").json()["has_more"]
        assert client.get("/api/me/contents").json()["items"][0]["title"] == "我的创作"
        assert client.get("/api/me/contents?limit=51").status_code == 422
        assert client.get("/api/me/contents?offset=9999999999999999999").status_code == 422
        assert client.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403
        assert client.post("/api/auth/logout", headers={"Origin": "http://localhost:5173"}).status_code == 200
        assert client.get("/api/me/followees").status_code == 401


def test_state_required_bound_to_browser_and_consumed_once():
    config, calls = settings(), []
    service = OAuthService(config, make_provider(config, calls))
    url, browser = service.begin()
    state = parse_qs(urlsplit(url).query)["state"][0]
    for candidate, cookie in ((None, browser), (state, "wrong-browser")):
        with pytest.raises(LoginRequired):
            asyncio.run(service.complete("authorized-code", candidate, cookie))
    assert calls == []
    asyncio.run(service.complete("authorized-code", state, browser))
    with pytest.raises(LoginRequired):
        asyncio.run(service.complete("authorized-code", state, browser))


def test_missing_state_compatibility_is_explicit_and_development_only():
    config, calls = settings(), []
    config.zhihu_oauth_allow_missing_state = True
    service = OAuthService(config, make_provider(config, calls))
    _, browser = service.begin()
    asyncio.run(service.complete("authorized-code", None, browser))
    assert len(calls) == 2

    config.app_env = "production"
    config.zhihu_oauth_redirect_uri = "https://example.com/api/auth/zhihu/callback"
    config.oauth_cookie_secure = True
    service = OAuthService(config, make_provider(config, []))
    _, browser = service.begin()
    with pytest.raises(LoginRequired):
        asyncio.run(service.complete("authorized-code", None, browser))


def test_expired_or_rejected_token_does_not_read_owner_data():
    config, calls = settings(), []
    def rejected(request):
        calls.append(request)
        return httpx.Response(200, json={"Code": 20001})
    service = OAuthService(config, ZhihuOAuthProvider(config, httpx.MockTransport(rejected)))
    service.sessions["expired"] = {"token": "old", "expires": time.time() - 1, "profile": {}}
    with pytest.raises(LoginRequired):
        asyncio.run(service.page("expired", "followees"))
    assert not calls
    service.sessions["active"] = {"token": "user-token", "expires": time.time() + 60, "profile": {}}
    with pytest.raises(LoginRequired):
        asyncio.run(service.page("active", "followees"))
    assert len(calls) == 1 and calls[0].headers["X-OAuth-Token"] == "user-token"
    assert "active" not in service.sessions


def test_missing_pagination_cursor_is_error_not_invented():
    provider = ZhihuOAuthProvider(settings(), httpx.MockTransport(lambda request:
        httpx.Response(200, json={"Code": 0, "Data": {"Items": [], "Paging": {"IsEnd": False}}})))
    with pytest.raises(OAuthError):
        asyncio.run(provider.page("contents", "token"))


def test_invalid_profile_cannot_create_session():
    provider = ZhihuOAuthProvider(settings(), httpx.MockTransport(lambda request:
        httpx.Response(200, json={"code": 404, "data": "User don't exist"})))
    with pytest.raises(OAuthError):
        asyncio.run(provider.profile("token"))


def test_callback_access_log_redacts_code_and_state():
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s %s %s %s %s',
        ("127.0.0.1", "GET", "/api/auth/zhihu/callback?authorization_code=secret&state=secret", "1.1", 303), None)
    OAuthAccessLogFilter().filter(record)
    assert "secret" not in record.getMessage()


def test_unconfigured_login_is_disabled():
    assert not OAuthService(Settings(_env_file=None)).configured
    config = settings()
    config.app_env = "production"
    assert not OAuthService(config).configured
