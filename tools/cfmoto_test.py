#!/usr/bin/env python3
"""Proof-of-concept: log in to the CFMOTO RIDE cloud and print the bike's fuel/range data.

Protocol from github.com/jhonsbaracaldo/open-cfmoto (docs/cloud-auth.md, packages/cloud-client).
Standard library only. Credentials come from a KEY=VALUE file (default ~/.config/cfmoto/credentials.env):

    CFMOTO_EMAIL=you@example.com
    CFMOTO_PASSWORD=yourpassword
    CFMOTO_AREA=PT                 # country code used when you registered
    # CFMOTO_BASE_URL=https://tapi.cfmoto-oversea.com/v1.0   (optional override)

Usage:  python3 cfmoto_test.py [--creds PATH] [--raw]
  --raw  also dump the full vehicle JSON (sensitive fields are still redacted)
"""
import argparse
import hashlib
import json
import os
import random
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

APP_ID = "rRrIs3ID"
APP_SECRET = "6c1936f85ecb23508c02ceb7a6e3fd0e33eb8bd2"
DEFAULT_BASE = "https://tapi.cfmoto-oversea.com/v1.0"
APP_INFO = "MOBILE|Android|35|CFMOTO_INTERNATIONAL_APP|2.2.14"

LOGIN = "/fuel-user/serveruser/app/auth/user/login_by_idcard"
VEHICLES = "/fuel-vehicle/servervehicle/app/vehicle/mine"
VEHICLE = "/fuel-vehicle/servervehicle/app/vehicle"

REDACT = {"encryptInfo", "vin", "btMac", "geoLocation", "accessToken", "refreshToken",
          "token", "tboxNumber", "motorNo", "licensePlate", "iccid", "imei", "imsi",
          "latitude", "longitude", "lat", "lng", "lon", "address", "qrInf", "hmiBleMac"}
INTERESTING = ("oil", "fuel", "range", "endur", "remain", "mile", "soc", "online", "kl", "speed")


def load_creds(path):
    creds = {}
    with open(os.path.expanduser(path)) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip()] = v.split(" #")[0].strip().strip('"').strip("'")
    for k in ("CFMOTO_EMAIL", "CFMOTO_PASSWORD"):
        if not creds.get(k):
            sys.exit(f"Missing {k} in {path}")
    return creds


def nonce(n=16):
    # Mirrors the app: digits, A..Y, a..y
    pools = (string.digits, string.ascii_uppercase[:25], string.ascii_lowercase[:25])
    return "".join(random.choice(random.choice(pools)) for _ in range(n))


def signed_headers(payload: str):
    n, ts = nonce(), str(int(time.time() * 1000))
    params = f"appId={APP_ID}&nonce={n}&timestamp={ts}"
    sig = hashlib.md5(hashlib.sha1((payload + params + APP_SECRET).encode()).hexdigest().encode()).hexdigest()
    return {
        "appId": APP_ID, "nonce": n, "timestamp": ts, "sign": sig, "signature": sig,
        "Cfmoto-X-Param": params, "Cfmoto-X-Sign": sig, "Cfmoto-X-Sign-Type": "0",
    }


def common_headers(token="cfmoto_virtual_vehicle_token", user_id=""):
    tz = time.tzname[0] if not os.environ.get("TZ") else os.environ["TZ"]
    try:
        tz = os.path.realpath("/etc/localtime").split("zoneinfo/")[1]
    except IndexError:
        pass
    return {
        "Authorization": f"Bearer {token}", "user_id": user_id, "lang": "en_US",
        "ZoneId": tz, "X-App-Info": APP_INFO, "User-Agent": APP_INFO,
        "Content-Type": "application/json; charset=UTF-8",
    }


def call(method, url, headers, body=None):
    req = urllib.request.Request(url, data=body.encode() if body is not None else None,
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            text = r.read().decode()
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        sys.exit(f"HTTP {e.code} from {url}\n{text[:500]}")
    data = json.loads(text)
    if str(data.get("code")) not in ("0", "200") or data.get("success") is False:
        sys.exit(f"API error from {url}: code={data.get('code')} msg={data.get('msg') or data.get('message')}")
    return data["data"]


def get(base, path, query, token, user_id):
    q = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted(query.items()))
    headers = {**signed_headers(q), **common_headers(token, user_id)}
    return call("GET", f"{base}{path}?{q}", headers)


def redact(obj):
    if isinstance(obj, dict):
        return {k: ("<redacted>" if k in REDACT else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from flatten(v, f"{prefix}{k}.")
    elif not isinstance(obj, list):
        yield prefix[:-1], obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--creds", default="~/.config/cfmoto/credentials.env")
    ap.add_argument("--raw", action="store_true")
    args = ap.parse_args()
    c = load_creds(args.creds)
    base = c.get("CFMOTO_BASE_URL", DEFAULT_BASE).rstrip("/")

    email = c["CFMOTO_EMAIL"]
    pw = c["CFMOTO_PASSWORD"]
    body = json.dumps({
        "idcard": email, "idcardType": "email" if "@" in email else "phone",
        "password": pw.lower() if len(pw) == 32 and all(ch in "0123456789abcdefABCDEF" for ch in pw)
        else hashlib.md5(pw.encode()).hexdigest(),
        "thirdpartyId": "", "thirdpartyType": "", "areaCode": "",
        "areaNo": c.get("CFMOTO_AREA", ""), "emailMarketingAlarm": False, "verifyCode": "",
    }, separators=(",", ":"))
    login = call("POST", base + LOGIN, {**signed_headers(body), **common_headers()}, body)
    token = (login.get("tokenInfo") or {}).get("accessToken") or login.get("token")
    user_id = str(login.get("userId", ""))
    print(f"[1] Login OK (region={login.get('region')}, areaNo={login.get('areaNo')})")

    vehicles = get(base, VEHICLES, {"position": "2"}, token, user_id)
    print(f"[2] {len(vehicles)} vehicle(s):")
    for v in vehicles:
        print(f"    - id={v.get('vehicleId')} name={v.get('vehicleName')!r} type={v.get('vehicleType')!r} "
              f"virtual={v.get('virtualFlag')} remainOil={v.get('remainOil')} oilInfo={v.get('oilInfo')}")
    real = [v for v in vehicles if str(v.get("virtualFlag", "0")) in ("0", "False", "false")
            and str(v.get("vehicleId")) != "-1"] or vehicles
    if not real:
        sys.exit("No vehicles on this account.")

    for v in real:
        info = get(base, VEHICLE, {"vehicleId": str(v["vehicleId"])}, token, user_id)
        print(f"\n[3] Live status for {v.get('vehicleName')!r}:")
        for k, val in flatten(redact(info)):
            if any(w in k.lower() for w in INTERESTING):
                print(f"    {k:40} = {val!r}")
        if args.raw:
            print(json.dumps(redact(info), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
