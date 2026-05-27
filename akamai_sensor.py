#!/usr/bin/env python3
"""
akamai_sensor.py  -  Python port of the Go Akamai BMP 3.3.4 sensor generator
==============================================================================
Ported from: akamai-bmp-generator-main/bm/3.3.4/bm.go + sdk/sdk.go

This generates valid Akamai Bot Manager sensor data that can be submitted
to /_bm/async_api to get real _abck / bm_sv cookies - enabling direct
API calls from your own laptop at ~200-400ms (vs 3-8s from scrapers).

Usage:
    from akamai_sensor import AkamaiSession
    session = AkamaiSession()
    await session.build()          # visit homepage + submit sensor
    data = await session.fetch(url) # direct API call with valid cookies
"""

import asyncio
import base64
import hashlib
import hmac
import json
import math
import os
import random
import re
import struct
import time
import urllib.parse
from typing import Optional

# ── RSA / AES (pure Python via cryptography package) ─────────────────────────
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ── curl_cffi for TLS fingerprint ─────────────────────────────────────────────
try:
    from curl_cffi.requests import AsyncSession as CurlSession
    HAS_CURL = True
except ImportError:
    HAS_CURL = False

import aiohttp

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
BMP_VERSION = "3.3.4"
RSA_KEY_B64 = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDMUymkqr6SQfxqefXMdkI6E1tDzHisp"
    "Em4WhZAfIWjhvEqfStzy16HvCjIBX2SRpn5pqW2w1TxqyxRnJOe4NEskWGdYY2y4JiD9v"
    "pYpWB54u6TOnKutXn2LzjMrvfIJpVXYZ5LYtD1ZUaeTKPz6qELXmBNcSfh/kGLiP8AH4e"
    "WKwIDAQAB"
)

GOETHE_HOME      = "https://www.goethe.de/"
GOETHE_EXAM_PAGE = "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm"
# Akamai BM script path (from goethe.de page source — the obfuscated JS)
# The sensor POST goes to the same path with /api suffix
BM_SCRIPT_PATH   = "/Aavh/tiZ8/LFiX9/TLOxA/QVD9VtiJf1/EVllKRseAg/Mz4A/TGwYEBYG"
SENSOR_URL       = f"https://www.goethe.de{BM_SCRIPT_PATH}"  # POST sensor here

# ── DEVICE DATABASE (subset of devices.json) ─────────────────────────────────
DEVICES = [
    {
        "brand": "samsung", "model": "SM-A107F", "device": "a10s",
        "manufacturer": "samsung", "hardware": "mt6762",
        "product": "a10sxx", "board": "S96116RA1",
        "bootloader": "A107FXXU8CVE3",
        "fingerprint": "samsung/a10sxx/a10s:11/RP1A.200720.012/A107FXXU8CVE3:user/release-keys",
        "host": "21DJ6B09", "id": "RP1A.200720.012",
        "display": "RP1A.200720.012.A107FXXU8CVE3",
        "tags": "release-keys", "type": "user", "user": "dpi",
        "release": "11", "codename": "REL", "incremental": "A107FXXU8CVE3",
        "sdk_int": 30,
        "width": 720, "height": 1381,
        "perf_bench": "17,906,59,822,89000,898,46300,462,3269",
    },
    {
        "brand": "realme", "model": "RMX3201", "device": "RMX3201",
        "manufacturer": "realme", "hardware": "mt6765",
        "product": "RMX3201RU", "board": "RM6765",
        "bootloader": "unknown",
        "fingerprint": "realme/RMX3201RU/RMX3201:11/RP1A.200720.011/1641524502945:user/release-keys",
        "host": "CP-ubuntu-123-174", "id": "RP1A.200720.011",
        "display": "RMX3201_11_C.07",
        "tags": "release-keys", "type": "user", "user": "root",
        "release": "11", "codename": "REL", "incremental": "1641524502945",
        "sdk_int": 30,
        "width": 720, "height": 1448,
        "perf_bench": "16,504,59,826,148000,1488,91300,912,16",
    },
    {
        "brand": "xiaomi", "model": "Redmi Note 9", "device": "merlin",
        "manufacturer": "Xiaomi", "hardware": "mt6768",
        "product": "merlin_eea", "board": "merlin",
        "bootloader": "unknown",
        "fingerprint": "Xiaomi/merlin_eea/merlin:10/QKQ1.200628.002/V12.0.1.0.QJREUXM:user/release-keys",
        "host": "pangu-build-component-system-304", "id": "QKQ1.200628.002",
        "display": "QKQ1.200628.002",
        "tags": "release-keys", "type": "user", "user": "builder",
        "release": "10", "codename": "REL", "incremental": "V12.0.1.0.QJREUXM",
        "sdk_int": 29,
        "width": 1080, "height": 2340,
        "perf_bench": "17,906,59,822,89000,898,46300,462,3269",
    },
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def _now_ms() -> int:
    return int(time.time() * 1000)

def _rand_int(lo: int, hi: int) -> int:
    return random.randint(lo, hi - 1)

def _rand_bool() -> bool:
    return random.random() < 0.5

def _rand_bytes(n: int) -> bytes:
    return os.urandom(n)

def _url_encode(s: str) -> str:
    result = []
    for ch in s:
        c = ord(ch)
        if 33 <= c <= 126 and c not in (34, 37, 39, 44, 92):
            result.append(ch)
        else:
            hi = (c >> 4) & 0xF
            lo = c & 0xF
            result.append('%')
            result.append(chr(ord('0') + hi) if hi < 10 else chr(ord('A') - 10 + hi))
            result.append(chr(ord('0') + lo) if lo < 10 else chr(ord('A') - 10 + lo))
    return ''.join(result)

def _ab(s: str) -> int:
    return sum(ord(c) for c in s if ord(c) < 128)

def _gen_android_id() -> str:
    return '%016x' % random.getrandbits(64)

def _feistel_encode(long_val: int, event_count: int, key: int) -> int:
    var0 = ((event_count & 0xFFFFFFFF) | (long_val << 32))
    var2 = key & 0xFFFFFFFF
    var3 = var0 & 0xFFFFFFFF
    var5 = (var0 >> 32) & 0xFFFFFFFF
    for _ in range(16):
        var6 = (var5 ^ var2 ^ var3) & 0xFFFFFFFF
        var2 = (var2 * 2) & 0xFFFFFFFF
        var5 = var3
        var3 = var6
    return ((var5 & 0xFFFFFFFF) << 32) | (var3 & 0xFFFFFFFF)

# ── CRYPTO ────────────────────────────────────────────────────────────────────

def _rsa_encrypt(data: bytes) -> bytes:
    if not HAS_CRYPTO:
        raise RuntimeError("pip install cryptography")
    raw = base64.b64decode(RSA_KEY_B64)
    pub = serialization.load_der_public_key(raw, backend=default_backend())
    return pub.encrypt(data, padding.PKCS1v15())

def _aes_cbc_encrypt(plaintext: str, key: bytes) -> tuple:
    if not HAS_CRYPTO:
        raise RuntimeError("pip install cryptography")
    iv = _rand_bytes(16)
    # PKCS5 padding
    pad_len = 16 - (len(plaintext.encode()) % 16)
    padded  = plaintext.encode() + bytes([pad_len] * pad_len)
    cipher  = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    enc     = cipher.encryptor()
    ct      = enc.update(padded) + enc.finalize()
    return ct, iv

def _hmac_sha256(data: bytes, key: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()

def encrypt_sensor(plaintext: str) -> str:
    aes_key  = _rand_bytes(16)
    hmac_key = _rand_bytes(16)

    aes_key_enc  = base64.b64encode(_rsa_encrypt(aes_key)).decode()
    hmac_key_enc = base64.b64encode(_rsa_encrypt(hmac_key)).decode()

    ct, iv = _aes_cbc_encrypt(plaintext, aes_key)
    obj    = iv + ct
    mac    = _hmac_sha256(obj, hmac_key)
    final  = base64.b64encode(obj + mac).decode()

    return f"3,a,{aes_key_enc},{hmac_key_enc}${final}$1000,1000,1000"

# ── SENSOR GENERATION ─────────────────────────────────────────────────────────

def _gen_touch_events() -> tuple:
    count = _rand_int(1, 7)
    tact  = ""
    vel   = 0
    for i in range(count):
        t      = round(300 * random.random())
        action = 1
        if i == 0 or random.random() >= 0.55:
            t      = round(2300 * random.random())
            action = 2
        elif _rand_bool():
            action = 3
        tact += f"{action},{t},0,0,1,1,1,-1;"
        vel  += t + action
    return tact, vel, count

def _gen_background_events(start_ts: int) -> str:
    actions  = [2, 3]
    steps    = _rand_int(1, 5)
    if _rand_bool():
        steps = max(1, steps // 2)
    data = ""
    ts   = start_ts
    for _ in range(steps):
        dx  = _rand_int(100, 1495)
        act = random.choice(actions)
        data += f"{act},{ts + dx};"
        ts  += dx
    if not data:
        dx  = _rand_int(100, 1495)
        data = f"{random.choice(actions)},{ts + dx};"
    return data

def _gen_motion_time_data(count: int) -> tuple:
    arr = [200.0] * count
    # CreateMotionPair simplified
    lo  = min(arr)
    hi  = max(arr)
    f3  = (hi - lo) / 60.0 if (hi - lo) > 0 else 1.0
    bmp_hash = ""
    for v in arr:
        idx = math.floor((v - lo) / f3) + 65
        ch  = chr(int(idx))
        if ch == '\\': ch = '.'
        elif ch == '.': ch = '\\'
        bmp_hash += ch
    # shorten
    short = ""
    i = 0
    while i < len(bmp_hash):
        j = i + 1
        while j < len(bmp_hash) and bmp_hash[j] == bmp_hash[i]:
            j += 1
        if j - i > 1:
            short += str(j - i)
        short += bmp_hash[i]
        i = j
    f7 = _hash_f7(short)
    motion_time_data = f"2;{lo:.2f};{hi:.2f};{f7};{short}"
    # MotionFirstSendData
    indices = random.sample(range(1, len(arr)), min(3, len(arr) - 1))
    mtdv    = ";".join(f"{idx},{int(arr[idx])}" for idx in indices)
    return motion_time_data, mtdv

_F7_TABLE = [
    3523407757,2768625435,1007455905,1259060791,3580832660,2724731650,996231864,1281784366,
    3705235391,2883475241,852952723,1171273221,3686048678,2897449776,901431946,1119744540,
    3484811241,3098726271,565944005,1455205971,3369614320,3219065702,651582172,1372678730,
    3245242331,3060352845,794826487,1483155041,3322131394,2969862996,671994606,1594548856,
    3916222277,2657877971,123907689,1885708031,3993045852,2567322570,1010288,1997036262,
    3887548279,2427484129,163128923,2126386893,3772416878,2547889144,248832578,2043925204,
    4108050209,2212294583,450215437,1842515611,4088798008,2226203566,498629140,1790921346,
    4194326291,2366072709,336475711,1661535913,4251816714,2322244508,325317158,1684325040,
]

def _hash_f7(s: str) -> int:
    j = 0
    for ch in s:
        c = ord(ch)
        idx = (255 & j) ^ c
        if idx < len(_F7_TABLE):
            j = (j >> 8) ^ _F7_TABLE[idx]
        else:
            j = j >> 8
    return j

def generate_sensor(app: str = "com.goethe.app", lang: str = "en_US") -> str:
    if not HAS_CRYPTO:
        raise RuntimeError("pip install cryptography")

    device    = random.choice(DEVICES)
    now       = _now_ms()
    boot_time = now - _rand_int(6600, 50000)
    start_ts  = now - _rand_int(4000, 8000)
    android_id = _gen_android_id()

    # System info
    battery = _rand_int(1, 100)
    sys_info = (
        f"-1,uaend,-1,{device['height']},{device['width']},1,{battery},1,"
        f"{_url_encode(lang)},{_url_encode(device['release'])},1,"
        f"{_url_encode(device['model'])},{_url_encode(device['bootloader'])},"
        f"{_url_encode(device['hardware'])},-1,{app},{android_id},-1,-1,"
        f"{_url_encode(device['codename'])},{_url_encode(device['incremental'])},"
        f"{device['sdk_int']},{_url_encode(device['manufacturer'])},"
        f"{_url_encode(device['product'])},{_url_encode(device['tags'])},"
        f"{_url_encode(device['type'])},{_url_encode(device['user'])},"
        f"{_url_encode(device['display'])},{_url_encode(device['board'])},"
        f"{_url_encode(device['brand'])},{_url_encode(device['device'])},"
        f"{_url_encode(device['fingerprint'])},{_url_encode(device['host'])},"
        f"{_url_encode(device['id'])}"
    )
    ab_val   = _ab(sys_info)
    neg_rand = _rand_int(0, 2**31) * (-1 if _rand_bool() else 1)
    sys_info_full = f"{sys_info},{ab_val},{neg_rand},{start_ts // 2}"

    # Touch events
    tact, touch_vel, touch_steps = _gen_touch_events()

    # Background events
    bg_events = _gen_background_events(start_ts)

    # Motion time data
    motion_count = 1 << (random.randint(5, 7))  # power of 2 between 32-128
    motion_time_data, motion_time_data_val = _gen_motion_time_data(motion_count)

    # Verify stats
    elapsed    = _now_ms() - start_ts
    long_val   = touch_vel
    r1         = _rand_int(4, 16) * 1000
    r2         = _rand_int(15, 53) * 1000
    feistel    = _feistel_encode(long_val, touch_steps, elapsed)
    verify     = f"0,{touch_vel},0,0,{long_val},{elapsed},0,{touch_steps},0,0,{r1},{r2},0,{feistel},{start_ts}"

    # Perf bench
    perf = device.get("perf_bench", "17,906,59,822,89000,898,46300,462,3269")

    # Assemble sensor pairs
    def pair(field_id, value):
        return f"-1,2,-94,{field_id},{value}"

    parts = [
        BMP_VERSION,
        pair("-70", ""),
        pair("-80", ""),
        pair("-121", ""),
        pair("-100", sys_info_full),
        pair("-101", "do_en,dm_en,t_en"),
        pair("-102", ""),
        pair("-103", bg_events),
        pair("-104", "-2,3,-50,-301,null"),
        pair("-108", ""),
        pair("-112", perf),
        pair("-115", verify),
        pair("-117", tact),
        pair("-120", ""),
        pair("-144", ""),
        pair("-160", ""),
        pair("-142", ""),
        pair("-145", motion_time_data),
        pair("-161", motion_time_data_val),
        pair("-143", ""),
        pair("-150", "1,0"),
    ]
    plaintext = "".join(parts)
    return encrypt_sensor(plaintext)

# ── AKAMAI SESSION ────────────────────────────────────────────────────────────

class AkamaiSession:
    """
    Manages a validated Akamai session for direct API calls.
    
    Usage:
        session = AkamaiSession()
        ok = await session.build()
        if ok:
            data = await session.fetch(api_url)
    """

    def __init__(self):
        self.cookies: dict = {}
        self._built_at: float = 0
        self._refresh_interval: float = 1200  # Akamai cookies last ~20 minutes

    @property
    def is_fresh(self) -> bool:
        return (time.time() - self._built_at) < self._refresh_interval

    async def build(self) -> bool:
        """
        Full Akamai cookie flow:
          1. Navigate to homepage — BM JS runs, _abck is set
          2. Navigate to exam page — session established
          3. Extract all cookies for use in direct API calls
        Returns True if session has _abck cookie.

        Priority order:
          1. Camoufox (stealth Firefox — best _abck success rate)
          2. SeleniumBase (real Chrome — proven working)
          3. Playwright (fallback)
          4. aiohttp + sensor (last resort)
        """
        print("  [AkamaiSession] Building session...")

        # Try Camoufox first — stealth Firefox, best Akamai bypass
        try:
            from camoufox.async_api import AsyncCamoufox
            print("  [AkamaiSession] Using Camoufox (stealth Firefox — best _abck success)")
            return await self._build_camoufox()
        except ImportError:
            print("  [AkamaiSession] Camoufox not installed — trying SeleniumBase")
            print("  [AkamaiSession] TIP: py -m pip install camoufox[geoip] && py -m camoufox fetch")

        try:
            from playwright.async_api import async_playwright
            return await self._build_playwright()
        except ImportError:
            print("  [AkamaiSession] Playwright not available — falling back to aiohttp+sensor")
            return await self._build_aiohttp()

    async def _build_camoufox(self) -> bool:
        """
        Use Camoufox (stealth Firefox) to get Akamai cookies.
        Camoufox injects fingerprints at C++ level — Akamai cannot detect it.
        This is the most reliable way to get _abck cookie.
        """
        from camoufox.async_api import AsyncCamoufox
        cookies = {}
        try:
            t0 = time.perf_counter()
            async with AsyncCamoufox(
                headless=False,
                humanize=True,
                block_webrtc=True,
                os="windows",
            ) as browser:
                ctx = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )
                page = await ctx.new_page()
                await page.goto(GOETHE_HOME, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(5)   # let Akamai JS run and set _abck
                await page.goto(GOETHE_EXAM_PAGE, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)
                raw = await ctx.cookies()
                for c in raw:
                    cookies[c["name"]] = c["value"]
                await ctx.close()
            elapsed = (time.perf_counter() - t0) * 1000
            akamai_keys = [k for k in cookies if any(x in k for x in ("_abck","ak_bmsc","bm_"))]
            print(f"  [AkamaiSession] Camoufox {elapsed:.0f}ms  akamai={akamai_keys}")
        except Exception as e:
            print(f"  [AkamaiSession] Camoufox failed: {e} — falling back to SeleniumBase")
            return await self._build_playwright()

        self.cookies   = cookies
        self._built_at = time.time()
        has_abck = "_abck" in cookies
        print(f"  [AkamaiSession] ready  _abck={'YES' if has_abck else 'NO'}  cookies={list(cookies.keys())}")
        return has_abck or bool(cookies.get("ak_bmsc"))

    async def _build_playwright(self) -> bool:
        """Use SeleniumBase (real browser) to get valid Akamai cookies once.
        Then all API calls use curl_cffi (fast, no browser) with these cookies.
        This is the PROVEN approach: curl_cffi + real cookies = 200 in ~250ms."""
        cookies = {}
        try:
            from seleniumbase import Driver as _SBDriver
            import threading, time as _time, tempfile, os as _os

            result_holder = {}

            def _get_cookies():
                # MUST change to temp dir — SeleniumBase creates 'downloaded_files'
                # in cwd and fails with WinError 5 if cwd is read-only
                original_cwd = _os.getcwd()
                temp_dir = tempfile.gettempdir()
                try:
                    _os.chdir(temp_dir)
                    drv = _SBDriver(uc=True, headless=False, block_images=True)
                finally:
                    _os.chdir(original_cwd)
                try:
                    # Disable cache — old cookies = 8 minute delay
                    try:
                        drv.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
                        drv.execute_cdp_cmd("Network.clearBrowserCache", {})
                        drv.delete_all_cookies()
                    except Exception:
                        pass
                    drv.get(GOETHE_HOME)
                    _time.sleep(4)
                    drv.get(GOETHE_EXAM_PAGE)
                    _time.sleep(2)
                    result_holder["cookies"] = {c["name"]: c["value"] for c in drv.get_cookies()}
                    drv.quit()
                except Exception as e:
                    result_holder["error"] = str(e)
                    try: drv.quit()
                    except Exception: pass

            t0 = time.perf_counter()
            print("  [AkamaiSession] Opening real browser to get Akamai cookies (one-time, ~8s)...")
            thread = threading.Thread(target=_get_cookies, daemon=True)
            thread.start()
            thread.join(timeout=30)
            elapsed = (time.perf_counter() - t0) * 1000

            if "cookies" in result_holder:
                cookies = result_holder["cookies"]
                akamai_keys = [k for k in cookies if any(x in k for x in ("_abck","ak_bmsc","bm_"))]
                print(f"  [AkamaiSession] Got {len(cookies)} cookies in {elapsed:.0f}ms  akamai={akamai_keys}")
            else:
                err = result_holder.get("error", "timeout")
                print(f"  [AkamaiSession] SeleniumBase failed: {err} — falling back to Playwright")
                return await self._build_playwright_fallback()

        except ImportError:
            print("  [AkamaiSession] SeleniumBase not installed — trying Playwright")
            return await self._build_playwright_fallback()
        except Exception as e:
            print(f"  [AkamaiSession] Cookie build failed: {e}")
            return await self._build_playwright_fallback()

        self.cookies   = cookies
        self._built_at = time.time()
        has_abck   = "_abck" in cookies
        has_akamai = any(k in cookies for k in ("ak_bmsc", "bm_sv", "bm_s"))
        print(f"  [AkamaiSession] ready  _abck={'YES' if has_abck else 'NO'}  cookies={list(cookies.keys())}")
        return has_abck or has_akamai

    async def _build_playwright_fallback(self) -> bool:
        """Playwright fallback for cookie collection."""
        from playwright.async_api import async_playwright
        cookies = {}
        try:
            async with async_playwright() as pw:
                for headless in [False, True]:
                    try:
                        browser = await pw.chromium.launch(
                            headless=headless,
                            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                                  "--disable-dev-shm-usage"] +
                                 (["--window-size=1,1", "--window-position=-10000,0"] if not headless else [])
                        )
                        ctx = await browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                            locale="en-IN", timezone_id="Asia/Kolkata",
                            viewport={"width": 1920, "height": 1080},
                        )
                        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});window.chrome={runtime:{}};")
                        page = await ctx.new_page()
                        t0 = time.perf_counter()
                        await page.goto(GOETHE_HOME, wait_until="domcontentloaded", timeout=15000)
                        # Wait longer — Akamai JS needs time to run and set _abck
                        await asyncio.sleep(5)
                        await page.goto(GOETHE_EXAM_PAGE, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(3)
                        raw = await ctx.cookies()
                        for c in raw:
                            cookies[c["name"]] = c["value"]
                        await browser.close()
                        elapsed = (time.perf_counter() - t0) * 1000
                        akamai_keys = [k for k in cookies if any(x in k for x in ("_abck","ak_bmsc","bm_"))]
                        print(f"  [AkamaiSession] Playwright(headless={headless}) {elapsed:.0f}ms  akamai={akamai_keys}")
                        # _abck is the key cookie — if we have it, we're done
                        if "_abck" in cookies:
                            break
                        if any(k in cookies for k in ("ak_bmsc", "bm_sv")):
                            break
                    except Exception as e2:
                        print(f"  [AkamaiSession] Playwright(headless={headless}) error: {e2}")
                        try: await browser.close()
                        except Exception: pass
        except Exception as e:
            print(f"  [AkamaiSession] Playwright fallback failed: {e}")
            return await self._build_aiohttp()

        self.cookies   = cookies
        self._built_at = time.time()
        has_abck = "_abck" in cookies
        print(f"  [AkamaiSession] ready  _abck={'YES' if has_abck else 'NO'}  cookies={list(cookies.keys())}")
        return has_abck or bool(cookies.get("ak_bmsc"))

    async def _build_aiohttp(self) -> bool:
        """Fallback: aiohttp + BMP sensor (gets ak_bmsc but not _abck)."""
        cookies = {}
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as sess:

            # Step 1: GET homepage — sets bm_s/bm_ss/bm_so initial cookies
            try:
                async with sess.get(
                    GOETHE_HOME,
                    headers={
                        "User-Agent": ua,
                        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                        "Accept-Language": "en-IN,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                    allow_redirects=True,
                ) as r:
                    for k, v in r.cookies.items():
                        cookies[k] = v.value
                    for hdr in r.headers.getall("Set-Cookie", []):
                        p = hdr.split(";")[0].strip()
                        if "=" in p:
                            k2, _, v2 = p.partition("=")
                            cookies[k2.strip()] = v2.strip()
                    akamai_keys = [k for k in cookies if any(x in k for x in ("_abck","ak_bmsc","bm_"))]
                    print(f"  [AkamaiSession] homepage {r.status}  akamai={akamai_keys}")
            except Exception as e:
                print(f"  [AkamaiSession] homepage failed: {e}")
                return False

            # Step 1b: GET the BM script — triggers _abck cookie generation
            try:
                async with sess.get(
                    f"https://www.goethe.de{BM_SCRIPT_PATH}",
                    headers={
                        "User-Agent": ua,
                        "Accept": "*/*",
                        "Referer": GOETHE_HOME,
                        "Accept-Language": "en-IN,en;q=0.9",
                    },
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as r:
                    for k, v in r.cookies.items():
                        cookies[k] = v.value
                    for hdr in r.headers.getall("Set-Cookie", []):
                        p = hdr.split(";")[0].strip()
                        if "=" in p:
                            k2, _, v2 = p.partition("=")
                            cookies[k2.strip()] = v2.strip()
                    akamai_keys = [k for k in cookies if any(x in k for x in ("_abck","ak_bmsc","bm_"))]
                    print(f"  [AkamaiSession] BM script {r.status}  akamai={akamai_keys}")
            except Exception as e:
                print(f"  [AkamaiSession] BM script failed: {e}")

            # Step 2: Generate sensor
            try:
                sensor = generate_sensor()
                print(f"  [AkamaiSession] sensor generated ({len(sensor)} chars)")
            except Exception as e:
                print(f"  [AkamaiSession] sensor generation failed: {e}")
                print("  [AkamaiSession] Install: pip install cryptography")
                # Continue without sensor - might still work with just homepage cookies
                sensor = None

            # Step 3: POST sensor
            if sensor:
                try:
                    # The BM script POSTs to its own path with these exact headers
                    async with sess.post(
                        SENSOR_URL,
                        data=sensor,
                        headers={
                            "User-Agent":   ua,
                            "Content-Type": "text/plain;charset=UTF-8",
                            "Origin":       "https://www.goethe.de",
                            "Referer":      GOETHE_HOME,
                            "Accept":       "*/*",
                            "Accept-Language": "en-IN,en;q=0.9",
                            "Accept-Encoding": "gzip, deflate, br",
                            "Connection":   "keep-alive",
                        },
                        cookies=cookies,
                        timeout=aiohttp.ClientTimeout(total=8),
                        allow_redirects=True,
                    ) as r:
                        for k, v in r.cookies.items():
                            cookies[k] = v.value
                        akamai_keys = [k for k in cookies if k in ("_abck","ak_bmsc","bm_sz","bm_sv","bm_s","bm_ss")]
                        body_preview = ""
                        try:
                            body_preview = (await r.text())[:80]
                        except Exception:
                            pass
                        print(f"  [AkamaiSession] sensor POST {r.status}  akamai={akamai_keys}  body={body_preview}")
                except Exception as e:
                    print(f"  [AkamaiSession] sensor POST failed: {e}")

            # Step 4: GET exam page
            try:
                async with sess.get(
                    GOETHE_EXAM_PAGE,
                    headers={
                        "User-Agent":  ua,
                        "Accept":      "text/html,application/xhtml+xml,*/*;q=0.8",
                        "Referer":     GOETHE_HOME,
                        "Accept-Language": "en-IN,en;q=0.9",
                    },
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as r:
                    for k, v in r.cookies.items():
                        cookies[k] = v.value
                    print(f"  [AkamaiSession] exam page {r.status}  total cookies={len(cookies)}")
            except Exception as e:
                print(f"  [AkamaiSession] exam page failed: {e}")

        self.cookies    = cookies
        self._built_at  = time.time()
        has_akamai = any(k in cookies for k in ("_abck", "bm_sv", "ak_bmsc"))
        print(f"  [AkamaiSession] ready  has_akamai={has_akamai}  cookies={list(cookies.keys())}")
        return has_akamai

    async def fetch(self, url: str, timeout: int = 8) -> tuple:
        """
        Fetch URL using validated Akamai session.
        Returns (status, data_or_None, latency_ms).
        Auto-rebuilds session if stale.
        """
        if not self.is_fresh:
            await self.build()

        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")

        t0 = time.perf_counter()
        try:
            if HAS_CURL:
                # Use curl_cffi for correct TLS fingerprint
                async with CurlSession(impersonate="chrome124") as s:
                    r = await s.get(
                        url,
                        headers={
                            "User-Agent":    ua,
                            "Accept":        "application/json, text/plain, */*",
                            "Accept-Language": "en-IN,en;q=0.9",
                            "Referer":       "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm",
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma":        "no-cache",
                        },
                        cookies=self.cookies,
                        timeout=timeout,
                    )
                    lat = (time.perf_counter() - t0) * 1000
                    if r.status_code == 200:
                        try:    return 200, r.json(), lat
                        except: return 200, None, lat
                    # Update cookies from response
                    for k, v in r.cookies.items():
                        self.cookies[k] = v
                    return r.status_code, None, lat
            else:
                # Fallback to aiohttp
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as s:
                    async with s.get(
                        url,
                        headers={
                            "User-Agent":    ua,
                            "Accept":        "application/json, text/plain, */*",
                            "Referer":       "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm",
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                        },
                        cookies=self.cookies,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as r:
                        lat = (time.perf_counter() - t0) * 1000
                        for k, v in r.cookies.items():
                            self.cookies[k] = v.value
                        if r.status == 200:
                            try:    return 200, await r.json(content_type=None), lat
                            except: return 200, None, lat
                        return r.status, None, lat
        except Exception as e:
            lat = (time.perf_counter() - t0) * 1000
            return 0, None, lat

    async def goethe_login(self, email: str, password: str) -> bool:
        """
        Log into goethe.de via CAS (Central Authentication Service).
        After login, self.cookies will contain the authenticated session cookies.
        Returns True if login was successful.

        Flow:
          1. GET login page → extract execution token (hidden form field)
          2. POST credentials + execution token → follow redirect back to goethe.de
          3. Verify login by checking for username/profile in response
        """
        login_url = (
            "https://login.goethe.de/cas/login"
            "?service=https%3A%2F%2Fwww.goethe.de%2Fservices%2Fcas%2Fservice%2Fgoethe%2F"
        )
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

        print(f"  [GoetheLogin] Logging in as {email}...")

        try:
            if HAS_CURL:
                async with CurlSession(impersonate="chrome124") as s:
                    # Step 1: GET login page — extract execution token
                    r1 = await s.get(
                        login_url,
                        headers={
                            "User-Agent":      ua,
                            "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
                            "Accept-Language": "en-IN,en;q=0.9",
                            "Referer":         "https://www.goethe.de/",
                        },
                        cookies=self.cookies,
                        timeout=15,
                    )
                    # Merge cookies from login page
                    for k, v in r1.cookies.items():
                        self.cookies[k] = v

                    html1 = r1.text
                    # Extract execution token
                    m = re.search(r'<input[^>]+name=["\']execution["\'][^>]+value=["\']([^"\']+)["\']', html1)
                    if not m:
                        # Try alternate attribute order
                        m = re.search(r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']execution["\']', html1)
                    if not m:
                        print(f"  [GoetheLogin] Could not find execution token in login page")
                        return False
                    execution = m.group(1)
                    print(f"  [GoetheLogin] Got execution token ({len(execution)} chars)")

                    # Step 2: POST credentials
                    post_data = {
                        "username":   email,
                        "password":   password,
                        "execution":  execution,
                        "_eventId":   "submit",
                        "geolocation": "",
                    }
                    r2 = await s.post(
                        login_url,
                        data=post_data,
                        headers={
                            "User-Agent":      ua,
                            "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
                            "Accept-Language": "en-IN,en;q=0.9",
                            "Content-Type":    "application/x-www-form-urlencoded",
                            "Referer":         login_url,
                            "Origin":          "https://login.goethe.de",
                        },
                        cookies=self.cookies,
                        timeout=15,
                        allow_redirects=True,
                    )
                    # Merge all cookies from login response + redirects
                    for k, v in r2.cookies.items():
                        self.cookies[k] = v

                    final_url = str(r2.url) if hasattr(r2, 'url') else ""
                    html2 = r2.text

                    # Step 3: Verify login — check for username or profile indicators
                    logged_in = (
                        "goethe.de" in final_url and "login.goethe.de" not in final_url
                        or "logout" in html2.lower()
                        or "my account" in html2.lower()
                        or "mein konto" in html2.lower()
                        or email.split("@")[0].lower() in html2.lower()
                    )

                    if logged_in:
                        print(f"  [GoetheLogin] ✅ Login successful for {email}  final_url={final_url[:60]}")
                        print(f"  [GoetheLogin] Cookies after login: {list(self.cookies.keys())[:8]}")
                        return True
                    else:
                        # Check for error message
                        err_m = re.search(r'<div[^>]+class=["\'][^"\']*error[^"\']*["\'][^>]*>(.*?)</div>', html2, re.DOTALL)
                        err_text = err_m.group(1).strip() if err_m else "unknown error"
                        print(f"  [GoetheLogin] ❌ Login failed for {email}: {err_text[:100]}")
                        return False
            else:
                # aiohttp fallback
                import aiohttp as _aiohttp
                connector = _aiohttp.TCPConnector(ssl=False)
                async with _aiohttp.ClientSession(connector=connector) as s:
                    # Step 1: GET login page
                    async with s.get(
                        login_url,
                        headers={"User-Agent": ua, "Accept": "text/html,*/*;q=0.8"},
                        cookies=self.cookies,
                        timeout=_aiohttp.ClientTimeout(total=15),
                        allow_redirects=True,
                    ) as r1:
                        for k, v in r1.cookies.items():
                            self.cookies[k] = v.value
                        html1 = await r1.text()

                    m = re.search(r'<input[^>]+name=["\']execution["\'][^>]+value=["\']([^"\']+)["\']', html1)
                    if not m:
                        m = re.search(r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']execution["\']', html1)
                    if not m:
                        print(f"  [GoetheLogin] Could not find execution token")
                        return False
                    execution = m.group(1)

                    # Step 2: POST credentials
                    post_data = {
                        "username":    email,
                        "password":    password,
                        "execution":   execution,
                        "_eventId":    "submit",
                        "geolocation": "",
                    }
                    async with s.post(
                        login_url,
                        data=post_data,
                        headers={
                            "User-Agent":   ua,
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Referer":      login_url,
                            "Origin":       "https://login.goethe.de",
                        },
                        cookies=self.cookies,
                        timeout=_aiohttp.ClientTimeout(total=15),
                        allow_redirects=True,
                    ) as r2:
                        for k, v in r2.cookies.items():
                            self.cookies[k] = v.value
                        html2 = await r2.text()
                        final_url = str(r2.url)

                    logged_in = (
                        "goethe.de" in final_url and "login.goethe.de" not in final_url
                        or "logout" in html2.lower()
                        or email.split("@")[0].lower() in html2.lower()
                    )
                    if logged_in:
                        print(f"  [GoetheLogin] ✅ Login successful for {email}")
                        return True
                    else:
                        print(f"  [GoetheLogin] ❌ Login failed for {email}")
                        return False

        except Exception as e:
            print(f"  [GoetheLogin] Exception during login for {email}: {e}")
            return False

    async def fetch_html(self, url: str, timeout: int = 8) -> tuple:
        """
        Fetch HTML page using validated Akamai session.
        Used for polling the exam detail page where the Book button appears instantly.
        Returns (status, html_text_or_None, latency_ms).
        """
        if not self.is_fresh:
            await self.build()

        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")

        t0 = time.perf_counter()
        try:
            if HAS_CURL:
                async with CurlSession(impersonate="chrome124") as s:
                    r = await s.get(
                        url,
                        headers={
                            "User-Agent":    ua,
                            "Accept":        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "en-IN,en;q=0.9",
                            "Referer":       "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm",
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma":        "no-cache",
                        },
                        cookies=self.cookies,
                        timeout=timeout,
                    )
                    lat = (time.perf_counter() - t0) * 1000
                    for k, v in r.cookies.items():
                        self.cookies[k] = v
                    if r.status_code == 200:
                        return 200, r.text, lat
                    return r.status_code, None, lat
            else:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as s:
                    async with s.get(
                        url,
                        headers={
                            "User-Agent":    ua,
                            "Accept":        "text/html,application/xhtml+xml,*/*;q=0.8",
                            "Referer":       "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm",
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                        },
                        cookies=self.cookies,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as r:
                        lat = (time.perf_counter() - t0) * 1000
                        for k, v in r.cookies.items():
                            self.cookies[k] = v.value
                        if r.status == 200:
                            return 200, await r.text(), lat
                        return r.status, None, lat
        except Exception as e:
            lat = (time.perf_counter() - t0) * 1000
            return 0, None, lat


# ── TEST 2 WORKERS ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import random

    async def test_2_workers():
        print("=" * 60)
        print("  TEST: 2 WORKERS @ 5 req/s each = 10 req/s TOTAL")
        print("=" * 60)

        if not HAS_CRYPTO:
            print("  ERROR: pip install cryptography")
            sys.exit(1)

        print(f"  curl_cffi: {'YES' if HAS_CURL else 'NO'}")

        # Build ONE session (shared between workers)
        print("\n  Building Akamai session (one-time)...")
        session = AkamaiSession()
        ok = await session.build()
        
        if not ok:
            print("  ❌ Session build failed!")
            return
        
        print(f"  ✅ Session ready!\n")

        # Prepare URL
        eid = "O%201000353"
        base_url = (f"https://www.goethe.de/rest/examfinderv3/exams/institute/{eid}"
                    f"?sortField=startDate&sortOrder=ASC&hasJUGroup=true&dataMode=0"
                    f"&langId=1&langIsoCodes=en&countryIsoCode=in&count=50&start=1"
                    f"&isODP=0&category=E007&type=ER")

        # Worker function
        async def worker(worker_id, num_requests=25):
            success = 0
            fail = 0
            latencies = []
            
            for i in range(num_requests):
                ts = int(time.time() * 1000) + worker_id * 1000 + i
                url = f"{base_url}&_={ts}&r={random.randint(0, 999999)}"
                
                t0 = time.perf_counter()
                status, data, lat = await session.fetch(url, timeout=8)
                latencies.append(lat)
                
                if status == 200 and data and "DATA" in data:
                    success += 1
                else:
                    fail += 1
                
                # Each worker waits 0.2s between requests (5 req/s)
                await asyncio.sleep(0.2)
            
            avg_lat = sum(latencies) / len(latencies) if latencies else 0
            return success, fail, avg_lat

        # Run 2 workers in parallel
        print("  Running 2 workers × 50 requests = 100 total @ 5 req/s each...\n")
        
        start_time = time.perf_counter()
        results = await asyncio.gather(
            worker(1, 50),
            worker(2, 50)
        )
        total_time = time.perf_counter() - start_time
        
        total_success = results[0][0] + results[1][0]
        total_fail = results[0][1] + results[1][1]
        total_requests = total_success + total_fail
        avg_lat_1 = results[0][2]
        avg_lat_2 = results[1][2]
        
        print("\n" + "=" * 60)
        print("  RESULTS - 2 WORKERS")
        print("=" * 60)
        print(f"  Worker 1: {results[0][0]} success, {results[0][1]} fail, avg {avg_lat_1:.0f}ms")
        print(f"  Worker 2: {results[1][0]} success, {results[1][1]} fail, avg {avg_lat_2:.0f}ms")
        print(f"  TOTAL:     {total_success} success, {total_fail} fail")
        print(f"  Success rate: {total_success/total_requests*100:.1f}%")
        print(f"  Total time: {total_time:.1f}s")
        print(f"  Actual rate: {total_requests/total_time:.1f} req/s")
        
        if total_fail == 0:
            print("\n  ✅ VERDICT: 2 workers at 5 req/s = 10 req/s TOTAL - PERFECT!")
            print("  → You can use 2-3 workers in your main script safely.")

    asyncio.run(test_2_workers())
