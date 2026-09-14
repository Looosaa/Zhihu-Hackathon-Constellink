"""Single-process session storage for the hackathon; shared storage required for replicas."""
import secrets
import time
from urllib.parse import urlencode, urlsplit

from app.providers.zhihu_oauth import LoginRequired, OAuthError, ZhihuOAuthProvider


class OAuthService:
    def __init__(self, settings, provider=None):
        self.settings = settings
        self.provider = provider or ZhihuOAuthProvider(settings)
        self.pending = {}
        self.sessions = {}

    @property
    def configured(self):
        uri = urlsplit(self.settings.zhihu_oauth_redirect_uri)
        secure = self.settings.oauth_cookie_secure
        return bool(self.settings.zhihu_oauth_app_id and self.settings.zhihu_oauth_app_key
                    and uri.netloc and uri.path == "/api/auth/zhihu/callback"
                    and not uri.query and not uri.fragment and not uri.username
                    and (uri.scheme == "https" or
                         (uri.scheme == "http" and uri.hostname in {"localhost", "127.0.0.1"}
                          and self.settings.app_env == "development" and not secure))
                    and (secure or self.settings.app_env == "development"))

    def _prune(self):
        now = time.time()
        for mapping in (self.pending, self.sessions):
            for key in list(mapping):
                if mapping[key]["expires"] <= now:
                    del mapping[key]

    def begin(self):
        self._prune()
        if not self.configured or len(self.pending) >= 1000:
            raise OAuthError()
        state, browser = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self.pending[state] = {"browser": browser, "expires": time.time() + 600}
        url = "https://openapi.zhihu.com/authorize?" + urlencode({
            "app_id": self.settings.zhihu_oauth_app_id,
            "redirect_uri": self.settings.zhihu_oauth_redirect_uri,
            "response_type": "code", "state": state,
        })
        return url, browser

    async def complete(self, code, state, browser):
        self._prune()
        pending = self.pending.get(state or "")
        if not pending or not browser or not secrets.compare_digest(pending["browser"], browser):
            raise LoginRequired()
        # State is consumed before network calls; a callback cannot be replayed.
        del self.pending[state]
        if not code or len(self.sessions) >= 1000:
            raise LoginRequired()
        token, lifetime = await self.provider.exchange(code)
        profile = await self.provider.profile(token)
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {"token": token, "profile": profile,
                                     "expires": time.time() + lifetime}
        return session_id, lifetime

    def require(self, session_id):
        self._prune()
        session = self.sessions.get(session_id or "")
        if not session:
            raise LoginRequired()
        return session

    def logout(self, session_id):
        self.sessions.pop(session_id or "", None)

    async def page(self, session_id, *args, **kwargs):
        session = self.require(session_id)
        if not self.settings.zhihu_access_secret:
            raise OAuthError()
        try:
            return await self.provider.page(*args, token=session["token"], **kwargs)
        except LoginRequired:
            self.logout(session_id)
            raise
