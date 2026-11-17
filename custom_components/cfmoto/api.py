"""Minimal async client for the CFMOTO RIDE cloud (no Home Assistant imports).

Protocol documented by github.com/jhonsbaracaldo/open-cfmoto.
"""
from __future__ import annotations

import hashlib
import json
import random
import string
import time
from typing import Any
from urllib.parse import quote_plus

import aiohttp

APP_ID = "rRrIs3ID"
APP_SECRET = "6c1936f85ecb23508c02ceb7a6e3fd0e33eb8bd2"
APP_INFO = "MOBILE|Android|35|CFMOTO_INTERNATIONAL_APP|2.2.14"
VIRTUAL_TOKEN = "cfmoto_virtual_vehicle_token"

LOGIN = "/fuel-user/serveruser/app/auth/user/login_by_idcard"
VEHICLES = "/fuel-vehicle/servervehicle/app/vehicle/mine"
VEHICLE = "/fuel-vehicle/servervehicle/app/vehicle"


class CfmotoError(Exception):
    """Request failed."""


class CfmotoAuthError(CfmotoError):
    """Login rejected."""


def _nonce(n: int = 16) -> str:
    pools = (string.digits, string.ascii_uppercase[:25], string.ascii_lowercase[:25])
    return "".join(random.choice(random.choice(pools)) for _ in range(n))


def _signed(payload: str) -> dict[str, str]:
    n, ts = _nonce(), str(int(time.time() * 1000))
    params = f"appId={APP_ID}&nonce={n}&timestamp={ts}"
    sha1 = hashlib.sha1((payload + params + APP_SECRET).encode()).hexdigest()
    sig = hashlib.md5(sha1.encode()).hexdigest()
    return {
        "appId": APP_ID, "nonce": n, "timestamp": ts, "sign": sig, "signature": sig,
        "Cfmoto-X-Param": params, "Cfmoto-X-Sign": sig, "Cfmoto-X-Sign-Type": "0",
    }


def _hash_password(pw: str) -> str:
    if len(pw) == 32 and all(c in "0123456789abcdefABCDEF" for c in pw):
        return pw.lower()
    return hashlib.md5(pw.encode()).hexdigest()


class CfmotoApi:
    """Talks to tapi.cfmoto-oversea.com."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str,
                 area: str, base_url: str, time_zone: str = "UTC") -> None:
        self._session = session
        self._email = email
        self._password = password
        self._area = area
        self._base = base_url.rstrip("/")
        self._tz = time_zone
        self._token: str | None = None
        self._user_id = ""

    def _headers(self, token: str, user_id: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}", "user_id": user_id, "lang": "en_US",
            "ZoneId": self._tz, "X-App-Info": APP_INFO, "User-Agent": APP_INFO,
            "Content-Type": "application/json; charset=UTF-8",
        }

    async def _request(self, method: str, url: str, headers: dict, body: str | None = None) -> Any:
        try:
            async with self._session.request(
                method, url, headers=headers, data=body.encode() if body is not None else None,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                text = await resp.text()
                status = resp.status
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CfmotoError(f"Connection error: {err}") from err
        try:
            data = json.loads(text)
        except ValueError as err:
            raise CfmotoError(f"HTTP {status}: non-JSON response") from err
        if status >= 400 or str(data.get("code")) not in ("0", "200") or data.get("success") is False:
            msg = data.get("msg") or data.get("message") or f"HTTP {status}"
            raise CfmotoError(f"code={data.get('code')} {msg}")
        return data.get("data")

    async def login(self) -> dict:
        body = json.dumps({
            "idcard": self._email,
            "idcardType": "email" if "@" in self._email else "phone",
            "password": _hash_password(self._password),
            "thirdpartyId": "", "thirdpartyType": "", "areaCode": "",
            "areaNo": self._area, "emailMarketingAlarm": False, "verifyCode": "",
        }, separators=(",", ":"))
        headers = {**_signed(body), **self._headers(VIRTUAL_TOKEN, "")}
        try:
            data = await self._request("POST", self._base + LOGIN, headers, body)
        except CfmotoError as err:
            raise CfmotoAuthError(str(err)) from err
        token = (data.get("tokenInfo") or {}).get("accessToken") or data.get("token")
        if not token:
            raise CfmotoAuthError("Login response had no token")
        self._token = token
        self._user_id = str(data.get("userId", ""))
        return data

    async def _get(self, path: str, query: dict[str, str]) -> Any:
        """Signed GET; logs in first if needed and retries once after a fresh login."""
        q = "&".join(f"{k}={quote_plus(str(v))}" for k, v in sorted(query.items()))
        for attempt in (0, 1):
            if self._token is None:
                await self.login()
            headers = {**_signed(q), **self._headers(self._token, self._user_id)}
            try:
                return await self._request("GET", f"{self._base}{path}?{q}", headers)
            except CfmotoError:
                if attempt:
                    raise
                self._token = None  # token may have expired: log in again and retry

    async def vehicles(self) -> list[dict]:
        data = await self._get(VEHICLES, {"position": "2"}) or []
        return [v for v in data if str(v.get("vehicleId")) != "-1"
                and str(v.get("virtualFlag", "0")) in ("0", "False", "false")]

    async def status(self, vehicle_id: str) -> dict:
        return await self._get(VEHICLE, {"vehicleId": str(vehicle_id)}) or {}
