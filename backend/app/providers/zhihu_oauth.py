"""Official Zhihu OAuth and authorized-user APIs; tokens never leave the server."""
import time
from urllib.parse import urlsplit

import httpx

from app.core.errors import AppError


class OAuthError(AppError):
    code = "ZHIHU_OAUTH_ERROR"
    safe_message = "知乎授权服务暂时不可用，请稍后重试。"
    status_code = 502


class LoginRequired(OAuthError):
    code = "LOGIN_REQUIRED"
    safe_message = "登录已失效，请重新使用知乎登录。"
    status_code = 401
    retryable = False


def public_url(value):
    value = str(value or "")
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme == "https" and parsed.hostname and not parsed.username else ""
    except ValueError:
        return ""


class ZhihuOAuthProvider:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport

    async def _request(self, method, url, **kwargs):
        try:
            async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
                response = await client.request(method, url, **kwargs)
            if response.status_code in (401, 403):
                raise LoginRequired()
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("Invalid upstream envelope")
            return body
        except (httpx.HTTPError, ValueError):
            # Do not propagate upstream bodies, request URLs or credential values.
            raise OAuthError() from None

    @staticmethod
    def _oauth_data(body):
        if body.get("code") not in (None, 0, 20000):
            raise OAuthError()
        data = body.get("data", body)
        if not isinstance(data, dict):
            raise OAuthError()
        return data

    async def exchange(self, code):
        body = await self._request("POST", "https://openapi.zhihu.com/access_token", data={
            "app_id": self.settings.zhihu_oauth_app_id,
            "app_key": self.settings.zhihu_oauth_app_key,
            "redirect_uri": self.settings.zhihu_oauth_redirect_uri,
            "grant_type": "authorization_code", "code": code,
        })
        data = self._oauth_data(body)
        token, lifetime = data.get("access_token"), data.get("expires_in")
        if not isinstance(token, str) or not token.strip():
            raise OAuthError()
        try:
            lifetime = int(lifetime)
            if lifetime <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise OAuthError() from None
        return token, min(lifetime, 86400)

    async def profile(self, token):
        if not token:
            raise LoginRequired()
        data = self._oauth_data(await self._request(
            "GET", "https://openapi.zhihu.com/user",
            headers={"Authorization": f"Bearer {token}"},
        ))
        uid, hash_id = data.get("uid"), data.get("hash_id")
        if not ((isinstance(uid, int) and not isinstance(uid, bool) and uid > 0)
                or (isinstance(uid, str) and uid.isdecimal() and int(uid) > 0)
                or (isinstance(hash_id, str) and hash_id.strip())):
            raise OAuthError()
        return {
            "id": str(uid or hash_id), "hash_id": str(hash_id or ""),
            "name": str(data.get("fullname") or "知乎用户"),
            "avatar_url": public_url(data.get("avatar_path")),
            "headline": str(data.get("headline") or ""),
            "description": str(data.get("description") or ""),
        }

    async def page(self, resource, token, offset="0", limit=20, content_type="all"):
        if not token:
            raise LoginRequired()
        if resource not in {"contents", "followees"}:
            raise ValueError("Unsupported resource")
        params = {"Offset": offset, "Limit": limit}
        if resource == "contents":
            params.update(ContentType=content_type, SortField="ts", SortOrder="desc")
        body = await self._request("GET", f"{self.settings.zhihu_api_base_url.rstrip('/')}/user/{resource}",
            params=params, headers={
                "Authorization": f"Bearer {self.settings.zhihu_access_secret}",
                "X-OAuth-Token": token,
                "X-Request-Timestamp": str(int(time.time())),
                "Content-Type": "application/json",
            })
        if body.get("Code") == 20001:
            raise LoginRequired()
        if body.get("Code") != 0:
            raise OAuthError()
        data = body.get("Data")
        if not isinstance(data, dict) or not isinstance(data.get("Items"), list):
            raise OAuthError()
        paging = data.get("Paging", {})
        if not isinstance(paging, dict) or not isinstance(paging.get("IsEnd"), bool):
            raise OAuthError()
        next_offset = None
        if not paging["IsEnd"]:
            next_offset = str(paging.get("NextOffset", ""))
            if (not next_offset.isascii() or not next_offset.isdecimal()
                    or len(next_offset) > 19 or int(next_offset) > 9223372036854775807
                    or int(next_offset) <= int(offset)):
                raise OAuthError()
        items = []
        for item in data["Items"]:
            if not isinstance(item, dict):
                raise OAuthError()
            if resource == "followees":
                items.append({"id": str(item.get("UrlToken") or ""),
                    "name": str(item.get("Fullname") or "知乎用户"),
                    "avatar_url": public_url(item.get("AvatarUrl")),
                    "url": public_url(item.get("Url")),
                    "headline": str(item.get("Headline") or ""),
                    "follower_count": item.get("FollowerCount", 0)})
            else:
                items.append({"url": public_url(item.get("Url")),
                    "type": str(item.get("ContentType") or ""),
                    "title": str(item.get("Title") or "未命名内容"),
                    "summary": str(item.get("Summary") or ""),
                    "created_at": item.get("CreatedAt"),
                    "like_count": item.get("LikeCount", 0),
                    "comment_count": item.get("CommentCount", 0)})
        return {"items": items, "has_more": not paging["IsEnd"],
                "next_offset": next_offset, "total": paging.get("Totals", 0)}
