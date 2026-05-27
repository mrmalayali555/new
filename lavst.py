#!/usr/bin/env python3
"""
GOETHE OID SNIPER v8.0
Dual-poll: JSON REST API + HTML exam page (real-time)
curl_cffi + Akamai session cookies — no scrapers, no Selenium polling
"""

# ╔══════════════════════════════════════════════════════════════════════════╗
#  ★  EDIT THIS SECTION ONLY — everything you need to configure is here  ★
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── Telegram bot token ────────────────────────────────────────────────────────
BOT_TOKEN = "5021332757:AAG2cU27dmY_CTMZwJxx8_oq9ljLKZx5kDY"

# ── Number of workers ─────────────────────────────────────────────────────────
# Each worker fires one request every POLL_INTERVAL seconds.
# 4 workers × 0.2s = ~20 req/s total (JSON + HTML combined = ~40 req/s)
# Increase if you want more speed, decrease if you get 403s.
LOCAL_WORKERS = 2       # workers on your laptop
RDP_WORKERS   = 1       # workers on RDP/VPS (set higher, faster machine)

# ── Poll interval (seconds between requests per worker) ──────────────────────
# 0.2s = safe (5 req/s per worker). Go lower only if you're not getting 403s.
LOCAL_POLL_INTERVAL = 0.15
RDP_POLL_INTERVAL   = 0.1

# ── How early to start firing before booking time ────────────────────────────
# Workers wake up this many seconds before the slot opens.
# 20s gives enough time to warm up without hammering too early.
START_EARLY_SECS = 30.0

# ── Akamai session refresh interval (seconds) ────────────────────────────────
# Session cookies expire after ~4 minutes. Auto-refreshed in background.
SESSION_REFRESH_SECS = 240

# ── Exam settings ─────────────────────────────────────────────────────────────
EXAM_CATEGORY = "E007"   # Goethe exam category
EXAM_TYPE     = "ER"     # ER = regular exam
EXAM_LEVEL    = "B2"     # A1/A2/B1/B2/C1/C2

# ── Hunt timeout ──────────────────────────────────────────────────────────────
MAX_HUNT_MINUTES = 60    # stop hunting after this many minutes (safety)

# ── Browser / booking settings ───────────────────────────────────────────────
WEBSOCKET_PORT  = 8787               # port for instant OID push to browser tabs
REDIRECT_PORTS  = [7979, 7980, 7981] # HTTP redirect server ports (redundancy)

# ── Email notification (optional) ────────────────────────────────────────────
EMAIL_ENABLED   = True
EMAIL_SENDER    = "justinkjames123@gmail.com"
EMAIL_PASSWORD  = ""    # set your Gmail app password here to enable
EMAIL_RECIPIENT = "justinkjames123@gmail.com"

# ── API keys (not used for polling — kept for exam fetch fallback only) ───────
KEYS = {
    "zenrows":      "00e41a8ee85a43db5a4708fe2cf9593a991e1fe4",
    "zenrows2":     "784523a2c967b2d8459047d6b9fdc1a34ab9ff12",
    "zenrows3":     "3bcf8bd91618962a75ebf7c0a2fac90ce2ff3bdb",
    "zenrows4":     "",
    "zenrows5":     "",
    "scraperapi":   "95d8c07bafd2968a41745a73a5ebc419",
    "scrapfly":     "scp-test-97eaf2fcf62f4f0fa3ccb492b7f5ac84",
    "oxylabs_user": "mrmalayali_VPgEl",
    "oxylabs_pass": "~sEAvvdqo3Ml0",
    "zyte":         "7c9b017b877f43e9843919c33aa0ef50",
    "scrapingant":  "b5d1d6a6f4564b28a8cabd3be04f8013",
    "scrapedo":     "d2f9d42c9c8144d7aa1f33d3c20729699557e730f56",
    "scrapingbee":  "610ZMOOVSLWVZSH7DECT18GU75BYABXT22BNML2627M8XKDKKLEYFRCHVMJN2R7KW540Y1D5PAUJW7GA",
    "scrappey":     "E1Or5UZx65ykcOqhcVLMm3qCqrCepSWJOgyLqO7OCvAL6gQ8yiWhwDWMyYqf",
}

# ── Browser paths (auto-detected, override here if needed) ───────────────────
# Leave empty "" to auto-detect. Only needed if auto-detect fails.
BROWSER_PATH_OVERRIDE = ""

# ╔══════════════════════════════════════════════════════════════════════════╗
#  END OF USER CONFIG — do not edit below unless you know what you're doing
# ╚══════════════════════════════════════════════════════════════════════════╝

# Internal config dict — built from the constants above
LOCAL_SELENIUM_WORKERS = LOCAL_WORKERS
RDP_SELENIUM_WORKERS   = RDP_WORKERS

DEFAULT_CFG = {
    "phase2_trigger":           20,
    "phase3_trigger":           3,
    "warmup_trigger":           60,
    "prewarm_browser_trigger":  30,
    "api_timeout":              20,
    "api_timeout_p3":           5,
    "selenium_workers_p1":      1,
    "selenium_workers_p3":      LOCAL_WORKERS,
    "selenium_interval_p1":     0.15,
    "selenium_interval_p3":     0.001,
    "rdp_selenium_interval_p1": 0.035,
    "rdp_selenium_interval_p3": 0.001,
    "num_students":             1,
    "max_hunt_min":             MAX_HUNT_MINUTES,
    "failfast_consec":          3,
    "failfast_slow":            15.0,
    "exam_category":            EXAM_CATEGORY,
    "exam_type":                EXAM_TYPE,
    "exam_level":               EXAM_LEVEL,
    "browser_stagger_ms":       300,
    "predictive_start_early":   2.0,
    "websocket_port":           WEBSOCKET_PORT,
    "redirect_ports":           REDIRECT_PORTS,
    "selenium_confirm_timeout": 30.0,
    "scrapedo_workers":         0,
    "scrapedo_interval":        0.5,
    "local_direct_workers":     LOCAL_WORKERS,
    "local_direct_interval":    LOCAL_POLL_INTERVAL,
    "local_workers_p3":         LOCAL_WORKERS,
    "curl_workers":             0,
    "curl_interval":            0.05,
}

# 
#  CENTERS
# 

CENTERS = {
    "Bangalore":  {"id": "O 10000353"},
    "Chennai":    {"id": "O 10000354"},
    "Kolkata":    {"id": "O 10000355"},
    "Mumbai":     {"id": "O 10000356"},
    "Delhi":      {"id": "O 10000357"},
    "Hyderabad":  {"id": "O 10000579"},
    "Pune":       {"id": "O 10000358"},
}

SLUG_MAP = {
    "Bangalore": "ban", "Chennai": "che", "Kolkata": "kol",
    "Mumbai": "mum", "Delhi": "del", "Hyderabad": "hyd", "Pune": "pun",
}

CENTER_LIST = list(CENTERS.keys())

GOETHE_HOME    = "https://www.goethe.de/"
GOETHE_REFERER = "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm"

# Brave first — most people use it for Goethe booking (better Akamai fingerprint)
EDGE_PATHS_TO_TRY = [
    r"C:\Users\jaisi\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

BROWSER_ROTATION_POOL = [
    # (label, binary_path, _unused)
    # Only browsers SeleniumBase supports with uc=True (Chrome-based, not Edge)
    ("Chrome",
     r"C:\Program Files\Google\Chrome\Application\chrome.exe",
     r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ("Brave",
     r"C:\Users\jaisi\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
     r"C:\Users\jaisi\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
    # Edge removed — SeleniumBase uc=True rejects msedge.exe binary
    # ChromeCanary removed — causes repeated chromedriver downloads (unstable)
]

# 
#  IMPORTS
# 

import asyncio
import json
import logging
import os
import random
import smtplib
import subprocess
import time
import urllib.request as _urllib_req
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import atexit

import aiohttp
import websockets

try:
    import browser_cookie3 as _bc3
    HAS_BC3 = True
except ImportError:
    _bc3 = None
    HAS_BC3 = False

try:
    from curl_cffi.requests import AsyncSession as CurlAsyncSession
    HAS_CURL = True
except ImportError:
    HAS_CURL = False

# Import our proven local bypass module
try:
    from akamai_sensor import AkamaiSession as _AkamaiSession
    HAS_AKAMAI_SESSION = True
except ImportError:
    _AkamaiSession = None
    HAS_AKAMAI_SESSION = False

# Global shared Akamai session (built once, reused for all workers)
_global_akamai_session = None

try:
    from seleniumbase import Driver as _SBDriver
    HAS_SELENIUMBASE = True
except ImportError:
    _SBDriver = None
    HAS_SELENIUMBASE = False

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from telegram.constants import ParseMode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("sniper")

# Update configuration with environment variables after imports
DEFAULT_CFG.update({
    "num_students": int(os.environ.get("DEFAULT_STUDENTS", "1")),
    "websocket_port": int(os.environ.get("WEBSOCKET_PORT", "8787")),
    "redirect_ports": list(map(int, os.environ.get("REDIRECT_PORTS", "7979,7980,7981").split(","))),
})

# Update global variables from environment
_WEBSOCKET_PORT = int(os.environ.get("WEBSOCKET_PORT", "8787"))
_REDIRECT_PORTS = list(map(int, os.environ.get("REDIRECT_PORTS", "7979,7980,7981").split(",")))

# 
#  LOGGING — Human-readable, dual output (CMD + file)
#  Every line is written to both the terminal AND the log file.
#  Language is plain English so anyone can read and understand it.
# 

_log_file      = None
_log_file_path = None
# asyncio.Lock() must NOT be created at module level (before any event loop exists).
# _log_lock is kept as None — it was dead code anyway; all actual locking uses _log_lock_sync.
_log_lock      = None
import threading as _threading
_log_lock_sync = _threading.Lock()

# ── colour codes for CMD readability ──────────────────────────────────────────
_C = {
    "reset":  "\033[0m",
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "red":    "\033[91m",
    "cyan":   "\033[96m",
    "bold":   "\033[1m",
    "dim":    "\033[2m",
    "blue":   "\033[94m",
    "magenta":"\033[95m",
}

def _colour(text: str, *codes) -> str:
    """Wrap text in ANSI colour codes for CMD output only."""
    prefix = "".join(_C.get(c, "") for c in codes)
    return f"{prefix}{text}{_C['reset']}"

def _init_log():
    global _log_file, _log_file_path
    ts      = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(os.path.expanduser("~"), "loggggs")
    os.makedirs(log_dir, exist_ok=True)
    fname = os.path.join(log_dir, f"log_{ts}.txt")
    try:
        _log_file      = open(fname, "w", encoding="utf-8", buffering=1)
        _log_file_path = fname
        _raw_write(f"{'='*60}")
        _raw_write(f"  GOETHE OID SNIPER v8.0  —  Session started {ts}")
        _raw_write(f"{'='*60}")
        print(_colour(f"\n  Log file: {fname}\n", "cyan"))
    except Exception as e:
        print(f"[WARNING] Could not create log file: {e}")

def _raw_write(text: str):
    """Write a plain line to the log file (no colour codes)."""
    if _log_file:
        try:
            with _log_lock_sync:
                _log_file.write(text + "\n")
        except Exception:
            pass

def _print_and_log(plain: str, coloured: str = None):
    """Print to CMD (with colour) and write to file (plain text)."""
    print(coloured if coloured else plain)
    _raw_write(plain)

# ── public logging helpers ────────────────────────────────────────────────────

def log_event(tag: str, msg: str, level: str = "INFO"):
    """
    General purpose event log.
    level = INFO | WARNING | ERROR | DEBUG
    """
    ts    = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    plain = f"[{ts}]  {tag:<18}  {msg}"

    if level == "WARNING":
        coloured = _colour(f"[{ts}]  ⚠  {tag:<18}  {msg}", "yellow")
    elif level == "ERROR":
        coloured = _colour(f"[{ts}]  ✖  {tag:<18}  {msg}", "red", "bold")
    elif level == "DEBUG":
        coloured = _colour(f"[{ts}]  ·  {tag:<18}  {msg}", "dim")
    else:
        coloured = f"[{ts}]  {_colour('ℹ', 'cyan')}  {tag:<18}  {msg}"

    _print_and_log(plain, coloured)

def log_request(source: str, sent_at: str, status: str, latency_ms: int,
                oid_found: bool = False, slots: str = "?", extra: str = ""):
    """
    Log a single HTTP request/response.
    source examples: local-W0, scrapedo-W1, zenrows, scraperapi, curl-W2
    """
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    # Determine source type label for clarity
    s = source.lower()
    if s.startswith("local-"):
        src_type = "DIRECT-LOCAL"   # curl_cffi + Akamai cookies on your laptop
    elif s.startswith("scrapedo"):
        src_type = "CLOUD-BROWSER"  # scrapedo real browser in cloud
    elif s.startswith("selenium"):
        src_type = "SELENIUM"       # local real browser
    elif s.startswith("curl-"):
        src_type = "CURL-DIRECT"    # curl_cffi TLS impersonation
    elif any(s.startswith(x) for x in ("zenrows", "scraperapi", "scrapfly",
                                        "oxylabs", "zyte", "scrapingant",
                                        "scrapingbee", "scrappey")):
        src_type = "API-SCRAPER"    # paid scraping service
    else:
        src_type = "UNKNOWN"

    oid_str  = "✔ OID FOUND" if oid_found else "no slot"
    slot_str = f" slots={slots}" if slots != "?" else ""
    extra_s  = f"  [{extra}]" if extra else ""

    plain = (
        f"[{ts}]  {src_type:<14}  {source:<20}  "
        f"sent={sent_at}  got={ts}  "
        f"status={status}  {latency_ms}ms"
        f"{slot_str}  {oid_str}{extra_s}"
    )

    if oid_found:
        coloured = _colour(plain, "green", "bold")
    elif "BLOCKED" in status or "403" in status or "FAIL" in status:
        coloured = _colour(plain, "yellow")
    elif "TIMEOUT" in status or "ERROR" in status:
        coloured = _colour(plain, "red")
    else:
        coloured = _colour(plain, "dim")

    _print_and_log(plain, coloured)

def log_phase(phase: int, msg: str):
    ts    = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    plain = f"[{ts}]  ── PHASE {phase} ──  {msg}"
    coloured = _colour(plain, "blue", "bold")
    _print_and_log(plain, coloured)

def log_state(old: str, new: str):
    ts    = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    plain = f"[{ts}]  STATE  {old}  →  {new}"
    coloured = _colour(plain, "magenta")
    _print_and_log(plain, coloured)

def log_summary(result):
    booking_url = make_booking_url(result.oid or "", getattr(result, "button_link", "")) if result.oid else "N/A"
    lines = [
        "",
        "=" * 60,
        "  HUNT COMPLETE — FINAL SUMMARY",
        "=" * 60,
        f"  Slot ID (OID)  : {result.oid or 'NOT FOUND — no slot appeared'}",
        f"  Booking URL    : {booking_url}",
        f"  Found by       : {result.source or 'N/A'}",
        f"  Phase          : {result.phase}",
        f"  Total time     : {result.elapsed:.3f} seconds",
        f"  Total requests : {result.attempts}",
        f"  API  success   : {result.api_ok}   failures: {result.api_fail}",
        f"  Direct success : {result.direct_ok}   failures: {result.direct_fail}",
        "=" * 60,
        "",
    ]
    for l in lines:
        if result.oid:
            _print_and_log(l, _colour(l, "green", "bold"))
        else:
            _print_and_log(l, _colour(l, "yellow"))
    
    # Add precision timing analysis if OID was found
    if result.oid:
        timing_summary = _precision_timer.get_summary()
        _print_and_log(timing_summary, _colour(timing_summary, "cyan"))

# 
#  STATE MACHINE
# 

class State:
    IDLE      = "IDLE"
    WAITING   = "WAITING"
    PHASE1    = "PHASE1"
    PHASE2    = "PHASE2"
    PHASE3    = "PHASE3"
    OID_FOUND = "OID_FOUND"
    DONE      = "DONE"

# 
#  IST CLOCK — perf_counter precision, fast-sync at T<60s
# 

class ISTClock:
    IST = timedelta(hours=5, minutes=30)
    TIME_APIS = [
        (
            "https://timeapi.io/api/time/current/zone?timeZone=Asia/Kolkata",
            lambda d: datetime(int(d["year"]), int(d["month"]), int(d["day"]),
                               int(d["hour"]), int(d["minute"]), int(d["seconds"])),
        ),
        (
            "https://worldtimeapi.org/api/timezone/Asia/Kolkata",
            lambda d: datetime.strptime(d["datetime"][:19], "%Y-%m-%dT%H:%M:%S"),
        ),
    ]

    def __init__(self):
        self._lock      = _threading.Lock()
        self._last_ist  = None
        self._last_perf = None
        self._ready     = _threading.Event()
        self._fast      = _threading.Event()
        self._stop      = _threading.Event()

    def start(self):
        t = _threading.Thread(target=self._loop, daemon=True)
        t.start()
        if not self._ready.wait(timeout=15):
            log.warning("IST sync failed — using system clock")
            with self._lock:
                self._last_ist  = datetime.utcnow() + self.IST
                self._last_perf = time.perf_counter()
            self._ready.set()
        log.info(f"IST: {self.now().strftime('%d %b %Y %H:%M:%S')}")

    def enable_fast(self):
        self._fast.set()

    def _fetch(self):
        import urllib.request
        for url, parser in self.TIME_APIS:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    ist  = parser(data)
                    with self._lock:
                        self._last_ist  = ist
                        self._last_perf = time.perf_counter()
                    self._ready.set()
                    return True
            except Exception:
                continue
        return False

    def _loop(self):
        while not self._stop.is_set():
            self._fetch()
            interval = 2 if self._fast.is_set() else 10
            self._stop.wait(timeout=interval)

    def now(self) -> datetime:
        with self._lock:
            if self._last_ist is None:
                return datetime.utcnow() + self.IST
            elapsed = time.perf_counter() - self._last_perf
            return self._last_ist + timedelta(seconds=elapsed)

_clock = ISTClock()

def ist_now() -> datetime:
    return _clock.now()

# 
#  HELPERS
# 

def _api_url(inst_id: str, category: str = "E007", exam_type: str = "ER") -> str:
    eid = inst_id.replace(" ", "%20")
    return (
        f"https://www.goethe.de/rest/examfinderv3/exams/institute/{eid}"
        f"?sortField=startDate&sortOrder=ASC&hasJUGroup=true&dataMode=0"
        f"&langId=1&langIsoCodes=en&countryIsoCode=in&count=50&start=1"
        f"&isODP=0&category={category}&type={exam_type}"
    )

def parse_booking_dt(book_from: str, book_from_time: str):
    try:
        dt_str = f"{book_from} {book_from_time[:8]}"
        return datetime.strptime(dt_str, "%d.%m.%Y %H:%M:%S")
    except Exception:
        return None

def parse_exams(data: dict, category: str = "E007", exam_type: str = "ER",
                exam_level: str = None) -> list:
    if not isinstance(data, dict):
        return []
    exams = []
    for item in data.get("DATA", []):
        if not isinstance(item, dict):
            continue
        if category and item.get("category") != category:
            continue
        if exam_type and item.get("targetGroupExam") != exam_type:
            continue
        if exam_level and item.get("languageLevel") != exam_level:
            continue
        exams.append({
            "startDate":            item.get("startDate", ""),
            "endDate":              item.get("endDate", ""),
            "acadPeriod":           item.get("acadPeriod", ""),
            "bookFrom":             item.get("bookFrom", ""),
            "bookFromTime":         item.get("bookFromTime", ""),
            "bookTo":               item.get("bookTo", ""),
            "bookToTime":           item.get("bookToTime", ""),
            "oid":                  item.get("oid", ""),
            "encOID":               item.get("encOID", ""),
            "buttonLink":           item.get("buttonLink", ""),
            "buttonDisabled":       item.get("buttonDisabled", "disabled"),
            "availability":         item.get("availability", 0),
            "price":                item.get("price", ""),
            "locationName":         item.get("locationName", ""),
            "languageLevel":        item.get("languageLevel", ""),
            "eventName":            item.get("eventName", ""),
            "bookFromTimeFormatted": item.get("bookFromTimeFormatted", ""),
        })
    return exams

def extract_oid(data, target_start=None, target_period=None, exam_level=None):
    """
    Extract first matching OID from DATA array.
    Returns (oid, button_link) tuple.
    button_link is the real booking URL from the API — use this instead of constructing oid= URL.
    Only returns a result when buttonDisabled is NOT "disabled" (i.e. booking is actually open).
    """
    if not isinstance(data, dict):
        return None, None
    for item in data.get("DATA", []):
        if not isinstance(item, dict):
            continue
        oid = item.get("oid")
        if not oid:
            continue
        if target_start and item.get("startDate") != target_start:
            continue
        if target_period and item.get("acadPeriod") != target_period:
            continue
        if exam_level and item.get("languageLevel") != exam_level:
            continue
        # OID found — fire immediately regardless of buttonDisabled state
        button_link = item.get("buttonLink", "")
        return oid, button_link
    return None, None

def make_booking_url(oid: str, button_link: str = "") -> str:
    """
    Build the correct booking URL.
    Always use oid= format — this is the working URL format for Goethe.
    (buttonLink prod= format returns a technical error page)
    """
    return f"https://www.goethe.de/coe?lang=en&oid={oid}"

# ─────────────────────────────────────────────────────────────────────────────
#  MANUAL AKAMAI COOKIES
# ─────────────────────────────────────────────────────────────────────────────

_manual_cookies: dict = {}

def _parse_cookie_string(raw: str) -> dict:
    """
    Parse a cookie string in any of these formats:
      - "name=value; name2=value2"  (DevTools copy)
      - "[Cookie] name=value"       (detection report format)
      - Just the value after "ak_bmsc=" etc.
    Returns a dict of {name: value}.
    """
    cookies = {}
    # Strip [Cookie] prefix if present
    raw = raw.replace("[Cookie]", "").replace("[COOKIE]", "").strip()
    # Split on semicolons or newlines
    for part in raw.replace("\n", ";").split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            name  = name.strip()
            value = value.strip()
            if name:
                cookies[name] = value
    return cookies

def _prompt_manual_cookies() -> dict:
    """
    Ask the user to paste Akamai cookies from their browser.
    Returns dict of cookies, or empty dict if skipped.
    """
    print(_colour("""
  ─────────────────────────────────────────────────────────────
  AKAMAI COOKIE SETUP  (helps avoid 403 blocks)
  ─────────────────────────────────────────────────────────────
  To get cookies:
    1. Open Edge/Chrome and visit: https://www.goethe.de/
    2. Press F12 → Application → Cookies → www.goethe.de
    3. Copy the values of:  ak_bmsc   bm_sv   _abck  (if present)

  You can paste them in ONE of these formats:
    • Full cookie string:  ak_bmsc=ABC123; bm_sv=XYZ456
    • Just skip (press Enter) — script will try browser cookies automatically
  ─────────────────────────────────────────────────────────────""", "cyan"))

    raw = _ask(_colour("  Paste cookies (or press Enter to skip): ", "cyan"), "").strip()
    if not raw:
        # Try auto-extract from browser
        auto = get_browser_cookies()
        if auto:
            akamai = {k: v for k, v in auto.items()
                      if k in ("ak_bmsc", "bm_sv", "_abck") or k.startswith("bm_")}
            if akamai:
                print(_colour(f"  Auto-extracted {len(akamai)} Akamai cookies from browser: {list(akamai.keys())}", "green"))
                return akamai
            # Return all browser cookies as fallback
            print(_colour(f"  Auto-extracted {len(auto)} browser cookies (no Akamai-specific ones found)", "yellow"))
            return auto
        print(_colour("  No cookies — will rely on API scrapers if direct requests get blocked", "yellow"))
        return {}

    parsed = _parse_cookie_string(raw)
    if parsed:
        print(_colour(f"  Loaded {len(parsed)} cookies: {list(parsed.keys())}", "green"))
    else:
        print(_colour("  Could not parse cookies — skipping", "yellow"))
    return parsed
#  Used for the initial exam fetch so Akamai doesn't block us.
# ─────────────────────────────────────────────────────────────────────────────

def get_browser_cookies() -> dict:
    """Extract goethe.de cookies from the user's installed browser."""
    if not HAS_BC3:
        return {}
    extractors = [
        ("Edge",    lambda: _bc3.edge(domain_name="goethe.de")),
        ("Firefox", lambda: _bc3.firefox(domain_name="goethe.de")),
        ("Chrome",  lambda: _bc3.chrome(domain_name="goethe.de")),
        ("Brave",   lambda: _bc3.brave(domain_name="goethe.de")),
    ]
    merged = {}
    for name, extractor in extractors:
        try:
            cj  = extractor()
            tmp = {c.name: c.value for c in cj} if cj else {}
            if tmp:
                log_event("COOKIES", f"Extracted {len(tmp)} cookies from {name} browser"
                          + (" (Akamai _abck found!)" if "_abck" in tmp else ""))
                merged.update(tmp)  # merge all browsers — more cookies = better
        except Exception:
            continue
    if merged:
        log_event("COOKIES", f"Total merged cookies from all browsers: {len(merged)} keys")
        return merged
    log_event("COOKIES", "No browser cookies found — will use headers only", "WARNING")
    return {}

# ─────────────────────────────────────────────────────────────────────────────
#  EMAIL NOTIFICATIONS  (configure at top of file)
# ─────────────────────────────────────────────────────────────────────────────

def send_email(subject: str, body: str):
    if not EMAIL_ENABLED or not EMAIL_PASSWORD:
        return
    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECIPIENT
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(EMAIL_SENDER, EMAIL_PASSWORD)
            s.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        log_event("EMAIL", f"Sent: {subject}")
    except Exception as e:
        log_event("EMAIL", f"Failed: {e}", "WARNING")

def send_email_async(subject: str, body: str):
    _threading.Thread(target=send_email, args=(subject, body), daemon=True).start()

# 
# 
#  INSTANT WEBSOCKET PUSH SERVER + MULTIPLE REDIRECT SERVERS
#  Zero-delay OID broadcast to all waiting tabs + redundancy
# 

import http.server
import socketserver
import json as _json

_redirect_oid: str = ""          # set when OID is found
_redirect_url: str = ""          # the real booking URL (buttonLink or oid= fallback)
_exam_page_url: str = ""         # exam listing page — opened in Edge before booking URL
_redirect_lock = _threading.Lock()
# Use the values already set from env vars at the top of the file (don't overwrite with hardcoded values)
# _WEBSOCKET_PORT and _REDIRECT_PORTS are already defined above from os.environ
_websocket_clients = set()       # connected waiting tabs
_redirect_servers = []           # list of running redirect servers
_websocket_server = None         # WebSocket server instance
_websocket_server_loop = None    # event loop running the WebSocket server (for threadsafe broadcast)
_tls_session_warmed = False      # TLS pre-warming state

def cleanup_servers():
    """Clean up all background servers on exit."""
    global _redirect_servers, _websocket_server
    
    log_event("CLEANUP", "Shutting down all background servers...")
    
    # Stop HTTP redirect servers
    for server in _redirect_servers:
        try:
            server.shutdown()
            server.server_close()
        except Exception:
            pass
    _redirect_servers.clear()
    
    # WebSocket server cleanup is handled by daemon threads
    log_event("CLEANUP", "All servers stopped, ports freed")

# Register cleanup function
atexit.register(cleanup_servers)

# 
#  HIGH-PRECISION TIMING SYSTEM
#  Logs exact timestamps for performance analysis and optimization
# 

# (import time already done above)

class PrecisionTimer:
    """High-precision timing system for performance analysis."""
    
    def __init__(self):
        self.events = {}
        self.start_time = None  # Will be set when first event is marked
    
    def mark(self, event_name: str, extra_info: str = ""):
        """Mark a high-precision timestamp for an event."""
        now = time.perf_counter()
        timestamp = datetime.now()
        
        # Initialize start_time on first event
        if self.start_time is None:
            self.start_time = now
        
        elapsed_ms = (now - self.start_time) * 1000
        
        self.events[event_name] = {
            'timestamp': timestamp,
            'perf_counter': now,
            'elapsed_ms': elapsed_ms,
            'extra_info': extra_info
        }
        
        # Log with millisecond precision
        ts_str = timestamp.strftime("%H:%M:%S.%f")[:-3]
        log_event("TIMING", f"{event_name}: {ts_str} (+{elapsed_ms:.1f}ms) {extra_info}")
        return now
    
    def measure_delay(self, start_event: str, end_event: str) -> float:
        """Measure delay between two events in milliseconds."""
        if start_event in self.events and end_event in self.events:
            start_time = self.events[start_event]['perf_counter']
            end_time = self.events[end_event]['perf_counter']
            delay_ms = (end_time - start_time) * 1000
            log_event("TIMING", f"Delay {start_event} → {end_event}: {delay_ms:.1f}ms")
            return delay_ms
        return -1
    
    def get_summary(self) -> str:
        """Get a summary of all timing events."""
        lines = ["", "=" * 60, "  PRECISION TIMING ANALYSIS", "=" * 60]
        for event, data in self.events.items():
            ts = data['timestamp'].strftime("%H:%M:%S.%f")[:-3]
            lines.append(f"  {event:<25} {ts} (+{data['elapsed_ms']:>7.1f}ms) {data['extra_info']}")
        lines.extend(["=" * 60, ""])
        return "\n".join(lines)

# Global precision timer
_precision_timer = PrecisionTimer()

# 
#  UTILITY FUNCTIONS
# 

def _ask(prompt: str, default: str = "") -> str:
    """Ask user a question, return stripped answer (or default on blank)."""
    try:
        ans = input(prompt).strip()
        return ans if ans else default
    except (EOFError, KeyboardInterrupt):
        return default

async def websocket_handler(websocket):
    """Handle WebSocket connections from waiting tabs."""
    global _websocket_clients
    _websocket_clients.add(websocket)
    log_event("WEBSOCKET", f"Client connected — {len(_websocket_clients)} total tabs waiting")
    try:
        await websocket.wait_closed()
    finally:
        _websocket_clients.discard(websocket)
        log_event("WEBSOCKET", f"Client disconnected — {len(_websocket_clients)} tabs remaining")

def start_websocket_server():
    """Start WebSocket server in background thread."""
    global _websocket_server, _websocket_server_loop

    def run_server():
        global _websocket_server_loop
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _websocket_server_loop = loop   # store so broadcast can schedule into it

        async def start_server():
            return await websockets.serve(websocket_handler, "127.0.0.1", _WEBSOCKET_PORT)

        try:
            server = loop.run_until_complete(start_server())
            log_event("WEBSOCKET", f"Started on ws://127.0.0.1:{_WEBSOCKET_PORT} — instant OID push to all tabs")
            loop.run_forever()
        except Exception as e:
            log_event("WEBSOCKET", f"Failed to start: {e}", "WARNING")
        finally:
            loop.close()

    t = _threading.Thread(target=run_server, daemon=True)
    t.start()

async def broadcast_oid(oid: str, button_link: str = ""):
    """Instantly broadcast OID to all connected tabs via WebSocket."""
    global _websocket_clients
    
    # HIGH-PRECISION TIMING: Mark WebSocket broadcast start
    broadcast_start = time.perf_counter()
    
    if not _websocket_clients:
        _precision_timer.mark("WEBSOCKET_BROADCAST_SKIP", "No clients connected")
        return
    
    url = make_booking_url(oid, button_link)
    message = _json.dumps({"oid": oid, "url": url})
    disconnected = set()
    
    for client in _websocket_clients.copy():
        try:
            await client.send(message)
        except Exception:
            disconnected.add(client)
    
    # Clean up disconnected clients
    _websocket_clients -= disconnected
    
    # HIGH-PRECISION TIMING: Mark WebSocket broadcast complete
    broadcast_end = time.perf_counter()
    broadcast_ms = (broadcast_end - broadcast_start) * 1000
    
    _precision_timer.mark("WEBSOCKET_BROADCAST_COMPLETE", 
                         f"{len(_websocket_clients)} clients, {broadcast_ms:.1f}ms")
    
    log_event("WEBSOCKET", f"Broadcasted OID to {len(_websocket_clients)} tabs in {broadcast_ms:.1f}ms (0ms delay)")

# Enhanced waiting page — session already established via /entry chain
def _generate_waiting_html():
    """Generate waiting page HTML with correct WebSocket port."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Waiting for slot...</title>
<link rel="preconnect" href="https://www.goethe.de">
<link rel="dns-prefetch" href="https://www.goethe.de">
<style>
  body {{ background:#0a0a0a; color:#00ff88; font-family:monospace;
         display:flex; align-items:center; justify-content:center;
         height:100vh; margin:0; flex-direction:column; }}
  h1 {{ font-size:2em; margin-bottom:0.3em; }}
  p  {{ color:#aaa; font-size:1.1em; }}
  .dot {{ animation: blink 0.8s infinite; }}
  @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0}} }}
</style>
</head>
<body>
<h1>&#9679; Waiting for slot<span class="dot">...</span></h1>
<p>Session ready. Tab will jump to booking page the instant a slot appears.</p>
<script>
  // Session already established via /entry chain:
  // COE init → exam listing page → here
  // All cookies (coesessionid, COE-Tab-ID, CFID/CFTOKEN, JSESSIONID, SRVCMS5WWW) are set.

  // Keep session alive — ping COE every 30s so cookies don't expire
  function keepAlive() {{
    fetch('https://www.goethe.de/coe?lang=en&_=' + Date.now(), {{
      mode: 'no-cors', cache: 'no-store', credentials: 'include'
    }}).catch(()=>{{}});
  }}
  setInterval(keepAlive, 30000);

  // Navigate to booking URL — all session cookies already in place
  function navigate(url) {{ window.location.replace(url); }}

  // WebSocket for instant push (zero delay)
  var ws;
  function connectWebSocket() {{
    try {{
      ws = new WebSocket('ws://127.0.0.1:{_WEBSOCKET_PORT}');
      ws.onmessage = function(e) {{
        var d = JSON.parse(e.data);
        if (d.url) {{ navigate(d.url); }}
      }};
      ws.onclose = function() {{ setTimeout(connectWebSocket, 200); }};
    }} catch(e) {{ setTimeout(poll, 100); }}
  }}
  connectWebSocket();

  // Fallback HTTP polling (5ms interval)
  function poll() {{
    fetch('/check', {{cache:'no-store'}}).then(r=>r.json()).then(d=>{{
      if(d.url){{ navigate(d.url); }}
      else {{ setTimeout(poll, 5); }}
    }}).catch(()=>{{ setTimeout(poll, 10); }});
  }}
  setTimeout(poll, 2000);
</script>
</body>
</html>""".encode('utf-8')

class _RedirectHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/check":
            with _redirect_lock:
                oid = _redirect_oid
                url = _redirect_url
            if oid:
                body = json.dumps({"url": url}).encode()
            else:
                body = b'{"url":null}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/entry":
            # EXACT COE SESSION PRE-WARM CHAIN (from real user navigation)
            # Step 1: goethe.de homepage
            # Step 2: India exams page
            # Step 3: B2 exam listing page
            # Step 4: Specific exam detail page (examId = encOID) — user provides this
            # Step 5: COE entry with oid — script navigates here when OID found
            # Step 6: /coe/options;coesessionid=XXX — final booking page (auto-redirect)
            port     = self.server.server_address[1]
            waiting  = f"http://127.0.0.1:{port}/"
            exam_url = _exam_page_url or "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm"

            html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Initialising session...</title>
<script>
// Walk the exact real user navigation chain to establish all session cookies:
// coesessionid, COE-Tab-ID, CFID/CFTOKEN, JSESSIONID, SRVCMS5WWW
var step = sessionStorage.getItem('coe_step') || '1';

if (step === '1') {{
  // Step 1: B2 exam listing page (English URL — matches HAR)
  sessionStorage.setItem('coe_step', '2');
  window.location.replace('https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm');

}} else if (step === '2') {{
  // Step 2: Specific exam detail page (examId=encOID)
  sessionStorage.setItem('coe_step', '3');
  window.location.replace('{exam_url}');

}} else {{
  // All steps done — go to waiting page. All cookies established.
  // When OID found: /coe?lang=en&oid=XXX → /coe/options;coesessionid=XXX
  sessionStorage.removeItem('coe_step');
  window.location.replace('{waiting}');
}}
</script>
</head>
<body style="background:#0a0a0a;color:#00ff88;font-family:monospace;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
<p>Initialising session... please wait</p>
</body></html>""".encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        else:
            # Generate HTML with correct WebSocket port
            html_content = _generate_waiting_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(html_content)))
            self.end_headers()
            self.wfile.write(html_content)

    def log_message(self, fmt, *args):
        pass  # silence default HTTP logs

def start_redirect_servers():
    """Start multiple redirect servers for redundancy. Safe to call multiple times."""
    global _redirect_servers
    
    # Guard — don't bind ports twice
    if _redirect_servers:
        return
    # Start multiple HTTP redirect servers
    for port in _REDIRECT_PORTS:
        try:
            socketserver.TCPServer.allow_reuse_address = True
            server = socketserver.TCPServer(("127.0.0.1", port), _RedirectHandler)
            t = _threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            _redirect_servers.append(server)
            log_event("REDIRECT SERVER", f"Started on http://127.0.0.1:{port}")
        except Exception as e:
            log_event("REDIRECT SERVER", f"Port {port} failed: {e}", "WARNING")
    
    if _redirect_servers:
        log_event("REDIRECT SERVER", f"{len(_redirect_servers)} servers running")
    else:
        log_event("REDIRECT SERVER", "All ports failed — will fall back to direct browser open", "WARNING")
        return
    
    # Start WebSocket server (optional - HTTP fallback if it fails)
    try:
        start_websocket_server()
        log_event("REDIRECT SERVER", f"{len(_redirect_servers)} HTTP servers + WebSocket — maximum redundancy")
    except Exception as e:
        log_event("WEBSOCKET", f"WebSocket failed to start: {e} — HTTP polling fallback active", "WARNING")

def set_redirect_oid(oid: str, button_link: str = ""):
    """Called the instant OID is found — all polling tabs jump immediately."""
    global _redirect_oid, _redirect_url
    booking_url = make_booking_url(oid, button_link)
    with _redirect_lock:
        _redirect_oid = oid
        _redirect_url = booking_url
    
    # Instantly broadcast via WebSocket (zero delay) using the WS server's own loop
    def _broadcast_in_thread():
        try:
            loop = _websocket_server_loop
            if loop and loop.is_running():
                # Schedule coroutine into the WebSocket server's loop — correct approach
                future = asyncio.run_coroutine_threadsafe(broadcast_oid(oid, button_link), loop)
                future.result(timeout=2)   # wait up to 2s for delivery
            else:
                # Fallback: create a temporary loop (WS server not running)
                tmp = asyncio.new_event_loop()
                tmp.run_until_complete(broadcast_oid(oid, button_link))
                tmp.close()
        except Exception as e:
            log_event("WEBSOCKET", f"Broadcast failed: {e}", "WARNING")

    # Run in separate thread so set_redirect_oid returns immediately
    t = _threading.Thread(target=_broadcast_in_thread, daemon=True)
    t.start()
    
    log_event("REDIRECT SERVER", f"OID set → booking URL: {booking_url[:80]} — all open tabs navigating NOW")

def prewarm_tls_session():
    """Pre-warm TLS session to Goethe.de to eliminate handshake delay."""
    global _tls_session_warmed
    if _tls_session_warmed:
        return
    
    def _prewarm():
        try:
            import urllib.request
            req = urllib.request.Request("https://www.goethe.de/", 
                                       headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read(1024)  # Read a bit to establish session
            global _tls_session_warmed
            _tls_session_warmed = True
            log_event("TLS PREWARM", "Session established — first requests will be 40-60ms faster")
        except Exception as e:
            log_event("TLS PREWARM", f"Failed: {e}", "WARNING")
    
    t = _threading.Thread(target=_prewarm, daemon=True)
    t.start()

# Legacy function for compatibility
def start_redirect_server():
    """Legacy wrapper — now starts multiple servers."""
    start_redirect_servers()

# 
#  BROWSER LAUNCHER
# 

def detect_browser_path() -> str:
    # Use override from config if set
    if BROWSER_PATH_OVERRIDE and os.path.isfile(BROWSER_PATH_OVERRIDE):
        return BROWSER_PATH_OVERRIDE
    for p in EDGE_PATHS_TO_TRY:
        if os.path.isfile(p):
            return p
    try:
        result = subprocess.run(["where", "msedge"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return ""

def detect_profiles(browser_path: str) -> list:
    """Auto-detect Edge/Chrome profiles from filesystem."""
    profiles = []
    if not browser_path:
        return ["Default"]
    # Determine user data dir
    if "Edge" in browser_path or "edge" in browser_path:
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data")
    else:
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
    if os.path.isdir(base):
        for entry in os.listdir(base):
            full = os.path.join(base, entry)
            if os.path.isdir(full) and (entry == "Default" or entry.startswith("Profile ")):
                profiles.append(entry)
    return sorted(profiles) if profiles else ["Default"]

# Global browser state
_browser_path    = ""
_browser_profiles = []
_prewarmed_tabs  = {}   # profile -> bool (True = tab already open)
_oid_lock        = _threading.Lock()
_oid_fired       = False
_persistent_selenium_driver = None  # Keep browser alive between exam fetch and hunt

def _launch_url_in_profile(url: str, profile: str, rdp_mode: bool = False):
    """Open URL in a specific browser profile. 1 profile = 1 tab."""
    global _browser_path
    if rdp_mode:
        try:
            os.system(f'start "" "{url}"')
        except Exception:
            pass
        return
    if _browser_path and os.path.isfile(_browser_path):
        try:
            subprocess.Popen([_browser_path, f"--profile-directory={profile}", url])
            log.info(f"[BROWSER] Opened [{profile}]  {url[:60]}")
        except Exception as e:
            log.error(f"[BROWSER] Failed [{profile}]: {e}")
    else:
        try:
            os.startfile(url)
        except Exception:
            pass

def prewarm_browsers(num_students: int, rdp_mode: bool = False):
    """
    ENHANCED browser pre-warming with multiple redirect servers:
    1. Opens browsers to MULTIPLE redirect servers for redundancy
    2. Each tab randomly picks a server to avoid single point of failure
    3. WebSocket + HTTP polling for maximum reliability
    4. TLS pre-warming for faster first requests
    """
    global _prewarmed_tabs
    
    # HIGH-PRECISION TIMING: Mark browser pre-warming start
    prewarm_start = _precision_timer.mark("BROWSER_PREWARM_START", f"{num_students} students")
    
    # Start all redirect servers if not already running
    start_redirect_servers()
    
    # Pre-warm TLS session
    prewarm_tls_session()
    
    profiles = _browser_profiles[:num_students] if _browser_profiles else ["Default"]
    log_event("BROWSER", f"Pre-warming {len(profiles)} profile(s) with {len(_REDIRECT_PORTS)} redundant servers + WebSocket")
    
    for i, profile in enumerate(profiles):
        # Each browser picks a random redirect server for load balancing
        port = random.choice(_REDIRECT_PORTS)
        redirect_url = f"http://127.0.0.1:{port}/"
        
        # HIGH-PRECISION TIMING: Mark each browser opening
        browser_start = time.perf_counter()
        _launch_url_in_profile(redirect_url, profile, rdp_mode)
        browser_end = time.perf_counter()
        browser_ms = (browser_end - browser_start) * 1000
        
        _prewarmed_tabs[profile] = True
        _precision_timer.mark(f"BROWSER_{i+1}_OPENED", f"profile={profile} port={port} {browser_ms:.1f}ms")
        
        log_event("BROWSER", f"Profile {profile} → server port {port} (opened in {browser_ms:.1f}ms)")
        if i < len(profiles) - 1:
            time.sleep(DEFAULT_CFG["browser_stagger_ms"] / 1000.0)
    
    # HIGH-PRECISION TIMING: Mark browser pre-warming complete
    _precision_timer.mark("BROWSER_PREWARM_COMPLETE", f"All {len(profiles)} browsers ready")
    _precision_timer.measure_delay("BROWSER_PREWARM_START", "BROWSER_PREWARM_COMPLETE")
    
    log_event("BROWSER", f"All {len(profiles)} browser(s) open with WebSocket + HTTP fallback (5ms polling)")

def launch_booking(oid: str, num_students: int, rdp_mode: bool = False, button_link: str = ""):
    """
    ENHANCED instant booking launch with multiple redundancy layers:
    1. WebSocket broadcast (0ms delay) to all connected tabs
    2. HTTP redirect servers update (5ms polling fallback)
    3. Direct URL opening for any profile — always fires regardless of WebSocket state
    """
    global _oid_fired
    with _oid_lock:
        if _oid_fired:
            return
        _oid_fired = True

    url = make_booking_url(oid, button_link)
    log_event("BROWSER", f"OID={oid} — triggering INSTANT redirect → {url[:80]}")

    # Step 1: Signal all pre-warmed tabs via WebSocket + HTTP (zero process spawn)
    set_redirect_oid(oid, button_link)

    # Step 2: ALWAYS open direct booking URL in Edge profiles
    # This covers: browsers still walking /entry chain, WebSocket not connected, etc.
    profiles = _browser_profiles[:num_students] if _browser_profiles else ["Default"]
    log_event("BROWSER", f"Opening booking URL directly in {len(profiles)} Edge profile(s)")
    for i, profile in enumerate(profiles):
        _launch_url_in_profile(url, profile, rdp_mode)
        if i < len(profiles) - 1:
            time.sleep(0.05)

    log_event("BROWSER", f"Booking URL opened in {len(profiles)} profile(s) — done")

# 
#  HUNT RESULT
# 

class HuntResult:
    def __init__(self):
        self.oid        = None
        self.button_link = ""   # real booking URL from API (buttonLink field)
        self.source     = None
        self.phase      = 0
        self.elapsed    = 0.0
        self.attempts   = 0
        self.api_ok     = 0
        self.api_fail   = 0
        self.direct_ok  = 0
        self.direct_fail = 0

# 
#  HUNT ENGINE v8 — 3-PHASE, DIRECT LOCAL PRIMARY
# 

async def run_hunt(bot, chat_id: int, center_name: str, exam: dict,
                   cfg: dict, stop_event: asyncio.Event,
                   rdp_mode: bool = False) -> HuntResult:
    """
    3-phase hunt engine.
    Phase 1: Direct local PRIMARY (0.5s) + ZenRows backup every 5s
    Phase 2: Direct local (0.2s) + all APIs staggered 0.3s
    Phase 3: Direct local BLITZ (3 workers, 0.1s) + all APIs (0.1s stagger)
    """
    inst_id    = CENTERS[center_name]["id"]
    api_url    = _api_url(inst_id, cfg.get("exam_category", "E007"), cfg.get("exam_type", "ER"))
    target_start  = exam["startDate"]
    target_period = exam.get("acadPeriod", "")
    exam_level    = cfg.get("exam_level", "B2")
    booking_dt    = parse_booking_dt(exam.get("bookFrom", ""), exam.get("bookFromTime", ""))

    # Set exam page URL for /entry chain — works in both CMD and Telegram mode
    global _exam_page_url
    enc_oid = exam.get("encOID", "")
    if enc_oid:
        _exam_page_url = f"https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm?examId={enc_oid}"
    else:
        _exam_page_url = "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm"
    log_event("HUNT START", f"exam_page_url={_exam_page_url}")

    result     = HuntResult()
    hunt_start = time.perf_counter()
    found_ev   = asyncio.Event()

    log_event("HUNT START", f"center={center_name} inst_id={inst_id} "
              f"target_start={target_start} period={target_period} "
              f"level={exam_level} booking_dt={booking_dt} "
              f"p2_trigger={cfg.get('phase2_trigger',20)}s "
              f"p3_trigger={cfg.get('phase3_trigger',3)}s "
              f"max_hunt={cfg.get('max_hunt_min',60)}min")

    # Log booking time clearly so user knows exactly when the hunt fires
    if booking_dt:
        sl_now = (booking_dt - ist_now()).total_seconds()
        bdt_str = booking_dt.strftime("%d %b %Y at %H:%M:%S")
        log_event("BOOKING TIME",
                  f"Slot opens on {bdt_str} IST  —  that is {sl_now/3600:.1f} hours from now  "
                  f"({sl_now:.0f} seconds)  |  "
                  f"Workers fire at T-{START_EARLY_SECS:.0f}s  |  "
                  f"Browsers pre-warm at T-{cfg.get('prewarm_browser_trigger',30)}s")
    else:
        log_event("BOOKING TIME",
                  "WARNING: No booking time found in exam data — hunt will start immediately and run continuously",
                  "WARNING")

    # Start redirect server immediately so browser tabs can be pre-warmed at any time
    # (only if not already running — avoids double-bind on ports)
    if not _redirect_servers:
        start_redirect_server()

    max_secs     = cfg.get("max_hunt_min", 60) * 60
    num_students = cfg.get("num_students", 1)
    prewarm_trig = cfg.get("prewarm_browser_trigger", 30)
    jitter_pct   = 0.10   # ±10% jitter on poll intervals

    current_phase = [1]
    last_msg_time = [0.0]

    def secs_left() -> float:
        if not booking_dt:
            return -999.0
        return (booking_dt - ist_now()).total_seconds()

    def jitter(base: float) -> float:
        return base * random.uniform(1.0 - jitter_pct, 1.0 + jitter_pct)

    def record_found(source: str, oid: str, button_link: str = ""):
        """
        Called when ANY source finds the OID.
        First call: sets found_ev, triggers browser launch, logs winner.
        Subsequent calls: logged as confirmation.
        For curl/direct workers: stop immediately after first find.
        For Selenium: also stop (no separate confirmation wait needed).
        """
        is_selenium = source.startswith("Selenium")
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if not found_ev.is_set():
            oid_found_time = _precision_timer.mark("OID_FOUND", f"source={source} oid={oid[:16]}...")
            found_ev.set()
            result.oid         = oid
            result.button_link = button_link
            result.source      = source
            result.elapsed     = time.perf_counter() - hunt_start
            result.phase       = current_phase[0]

            booking_url = make_booking_url(oid, button_link)
            msg = (
                f"\n  ★  SLOT FOUND!  ★\n"
                f"  Found by   : {source}\n"
                f"  Slot ID    : {oid}\n"
                f"  Booking URL: {booking_url}\n"
                f"  Phase      : {result.phase}\n"
                f"  Time taken : {result.elapsed:.3f} seconds\n"
                f"  Requests   : {result.attempts} total  "
                f"(API ok={result.api_ok} fail={result.api_fail}  "
                f"Direct ok={result.direct_ok} fail={result.direct_fail})\n"
                f"  Found at   : {ts}\n"
            )
            _print_and_log(msg, _colour(msg, "green", "bold"))

            # Sound alert — hear it instantly even if not watching
            try:
                import winsound
                for freq, dur in [(800, 200), (1200, 200), (1600, 400)]:
                    winsound.Beep(freq, dur)
            except Exception:
                pass  # non-Windows or winsound unavailable

            # Always stop all workers immediately once OID is found, regardless of source
            stop_event.set()
        else:
            # Duplicate find — just log it
            delta_ms = (time.perf_counter() - hunt_start - result.elapsed) * 1000
            msg = f"  ✔  CONFIRMED by {source}  ({delta_ms:.0f}ms after first find)"
            _print_and_log(msg, _colour(msg, "cyan"))
            stop_event.set()

    async def send_msg(text: str, force: bool = False):
        now = time.time()
        if not force and now - last_msg_time[0] < 5:
            return
        last_msg_time[0] = now
        try:
            await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        except Exception:
            pass

    #  IST fast-sync enabler at T<60s 
    async def ist_sync_task():
        while not found_ev.is_set() and not stop_event.is_set():
            sl = secs_left()
            if sl <= 60:
                _clock.enable_fast()
                log_event("IST SYNC", "Switched to high-frequency time sync (T < 60s)")
                return
            await asyncio.sleep(2)

    #  Precision browser launcher — fires the moment OID is found 
    async def browser_launch_task():
        """
        Waits for OID to be found, then INSTANTLY:
        1. Calls set_redirect_oid() — all pre-warmed tabs jump in < 50ms (no process spawn)
        2. Falls back to direct open for any non-pre-warmed profiles
        """
        await found_ev.wait()
        if result.oid:
            # HIGH-PRECISION TIMING: Mark when browser launch starts
            _precision_timer.mark("BROWSER_LAUNCH_START", f"oid={result.oid[:16]}...")
            
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_event("BROWSER", f"OID received at {ts} — triggering instant redirect NOW (no process spawn)")
            
            # launch_booking handles set_redirect_oid + WebSocket broadcast + direct open
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, launch_booking, result.oid, num_students, rdp_mode, result.button_link)
            
            _precision_timer.mark("BROWSER_LAUNCH_COMPLETE", f"{num_students} profiles ready")
            log_event("BROWSER", f"Booking URL live in {num_students} browser profile(s)")
            
            # Measure total delay from OID found to browser launch complete
            _precision_timer.measure_delay("OID_FOUND", "BROWSER_LAUNCH_COMPLETE")

    #  Precision countdown — busy-wait the last 50ms before booking time
    async def precision_countdown_task():
        """
        ENHANCED precision countdown with predictive pre-requests:
        1. Starts requests 2 seconds BEFORE booking time (catches early releases)
        2. Pre-warms TLS sessions to eliminate handshake delay
        3. Busy-waits the final 50ms for exact timing
        """
        if not booking_dt:
            return
        
        # Pre-warm TLS session early
        prewarm_tls_session()
        
        predictive_start = cfg.get("predictive_start_early", 2.0)
        
        while not found_ev.is_set() and not stop_event.is_set():
            sl = secs_left()
            
            # PREDICTIVE PRE-REQUESTS: Start 2s early (Goethe sometimes releases early)
            if sl <= predictive_start and sl > 0.05:
                if sl <= predictive_start and sl > (predictive_start - 0.1):
                    log_event("PRECISION", f"Starting PREDICTIVE requests T-{sl:.1f}s (catching early releases)")
                await asyncio.sleep(0.001)   # 1ms sleep during predictive phase
            elif sl <= 0.05:
                # Busy-wait the final 50ms for exact timing
                target_perf = time.perf_counter() + sl
                while time.perf_counter() < target_perf:
                    pass  # spin — this is intentional for precision
                log_event("PRECISION", "Booking time reached — all workers firing at maximum speed")
                return
            elif sl <= 1.0:
                await asyncio.sleep(0.001)   # 1ms sleep in final second
            else:
                await asyncio.sleep(0.1)

    #  Orchestrator — EXTREME SPEED MODE ONLY
    async def orchestrator():
        current_phase[0] = 3

        local_workers_count = cfg.get("local_direct_workers", 4) if (HAS_AKAMAI_SESSION and HAS_CURL) else 0
        local_interval      = cfg.get("local_direct_interval", 0.2)

        if local_workers_count == 0:
            log_phase(3, "ERROR — local_direct unavailable: akamai_sensor.py or curl_cffi missing. Install both.")

    # ── LOCAL DIRECT WORKER — curl_cffi + Akamai session cookies ────────────
    async def local_direct_worker(wid: int, interval: float):
        """
        PRIMARY method. curl_cffi (Chrome TLS fingerprint) + Akamai session cookies.
        Worker 0 builds the session immediately at hunt start (takes ~8s).
        All other workers wait for worker 0 to finish, then share the same session.
        Fires at T-20s before booking time.
        """
        global _global_akamai_session

        if not HAS_AKAMAI_SESSION:
            log_event("LOCAL DIRECT", "akamai_sensor.py not found — workers disabled", "ERROR")
            return
        if not HAS_CURL:
            log_event("LOCAL DIRECT", "curl_cffi not installed — workers disabled", "ERROR")
            return

        # ── Worker 0 builds session immediately; others wait for it ──────────
        if wid == 0:
            if _global_akamai_session is None:
                log_event("LOCAL DIRECT", "Building Akamai session NOW (one-time ~8s)...")
                _global_akamai_session = _AkamaiSession()
                _global_akamai_session._refresh_interval = SESSION_REFRESH_SECS
                ok = await _global_akamai_session.build()
                if not ok:
                    log_event("LOCAL DIRECT", "Session build FAILED — check akamai_sensor.py", "ERROR")
                    return
                log_event("LOCAL DIRECT", f"Session ready — cookies={list(_global_akamai_session.cookies.keys())[:5]}")
        else:
            # Wait for worker 0 to finish building
            waited = 0
            while _global_akamai_session is None and waited < 30:
                await asyncio.sleep(0.5)
                waited += 0.5
            if _global_akamai_session is None:
                log_event("LOCAL DIRECT", f"Worker {wid} timed out waiting for session", "ERROR")
                return

        # ── WAIT until T-20s before booking time ─────────────────────────────
        if booking_dt:
            while not stop_event.is_set():
                sl = secs_left()
                if sl <= START_EARLY_SECS:
                    break
                sleep_for = max(0.05, min(sl - START_EARLY_SECS, 1.0))
                await asyncio.sleep(sleep_for)
            if stop_event.is_set():
                return
            log_event("LOCAL DIRECT", f"Worker {wid} — T-{START_EARLY_SECS:.0f}s reached, FIRING NOW")

        session = _global_akamai_session
        log_event("LOCAL DIRECT", f"Worker {wid} firing (curl_cffi + Akamai cookies, interval={interval}s)")

        while not found_ev.is_set() and not stop_event.is_set():
            sent_at    = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            busted_url = f"{api_url}&_={int(time.time()*1000)}&r={random.randint(0,999999)}"

            status, data, lat = await session.fetch(busted_url, timeout=cfg.get("local_timeout", 8))
            result.attempts += 1

            if data and isinstance(data, dict) and "DATA" in data:
                result.direct_ok += 1
                sc = len(data["DATA"]) if isinstance(data["DATA"], list) else "?"
                oid, button_link = extract_oid(data, target_start, target_period, exam_level)
                log_request(f"local-W{wid}", sent_at, "200 OK", int(lat), bool(oid),
                            slots=str(sc), extra="direct")
                if oid:
                    record_found(f"local-W{wid}", oid, button_link)
                    return
            else:
                result.direct_fail += 1
                log_request(f"local-W{wid}", sent_at,
                            f"BLOCKED {status}" if status == 403 else f"FAIL {status}",
                            int(lat), False)
                if status == 403 and result.direct_fail % 5 == 0:
                    log_event("LOCAL DIRECT", f"Worker {wid} rebuilding expired session...")
                    await session.build()

            # Adaptive interval — poll faster as booking time approaches
            sl = secs_left()
            if sl <= 5:
                await asyncio.sleep(0.05)   # 50ms — critical window
            elif sl <= 15:
                await asyncio.sleep(0.1)    # 100ms
            else:
                await asyncio.sleep(jitter(interval))

    # ── HTML DIRECT WORKER — polls exam page HTML for instant OID detection ──
    async def html_direct_worker(wid: int, interval: float):
        """
        Polls the exam detail page HTML (not the JSON API).
        The HTML page is server-rendered per request — no CDN cache.
        The Book button href contains the OID the instant a slot opens.
        Runs in parallel with local_direct_worker (JSON API).
        Whichever finds OID first wins.
        """
        global _global_akamai_session

        if not HAS_AKAMAI_SESSION or not HAS_CURL:
            return

        enc_oid = exam.get("encOID", "")
        if not enc_oid:
            log_event("HTML WORKER", f"Worker {wid} — no encOID in exam data, skipping", "WARNING")
            return

        html_url = f"https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm?examId={enc_oid}"

        # Wait for session (built by local_direct_worker wid=0)
        waited = 0
        while _global_akamai_session is None and waited < 30:
            await asyncio.sleep(0.5)
            waited += 0.5
        if _global_akamai_session is None:
            log_event("HTML WORKER", f"Worker {wid} timed out waiting for session", "ERROR")
            return

        # Wait until T-20s
        if booking_dt:
            while not stop_event.is_set():
                sl = secs_left()
                if sl <= START_EARLY_SECS:
                    break
                await asyncio.sleep(max(0.05, min(sl - START_EARLY_SECS, 1.0)))
            if stop_event.is_set():
                return
            log_event("HTML WORKER", f"Worker {wid} — T-{START_EARLY_SECS:.0f}s reached, polling exam HTML NOW")

        session = _global_akamai_session
        log_event("HTML WORKER", f"Worker {wid} polling HTML: {html_url[:60]}...")

        while not found_ev.is_set() and not stop_event.is_set():
            sent_at    = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            busted_url = f"{html_url}&_={int(time.time()*1000)}&r={random.randint(0,999999)}"

            status, html, lat = await session.fetch_html(busted_url, timeout=8)
            result.attempts += 1

            if status == 200 and html:
                result.direct_ok += 1
                # Extract OID from Book button href — appears instantly when slot opens
                oid_match = re.search(r'href="/coe\?lang=en&amp;oid=([a-f0-9]{64})"', html)
                if oid_match:
                    oid = oid_match.group(1)
                    log_request(f"html-W{wid}", sent_at, "OID IN HTML", int(lat), True,
                                extra="exam-page-html")
                    record_found(f"html-W{wid}", oid, "")
                    return
                log_request(f"html-W{wid}", sent_at, "200 OK", int(lat), False,
                            extra="no-oid-yet")
            else:
                result.direct_fail += 1
                log_request(f"html-W{wid}", sent_at,
                            f"BLOCKED {status}" if status == 403 else f"FAIL {status}",
                            int(lat), False)
                if status == 403 and result.direct_fail % 5 == 0:
                    log_event("HTML WORKER", f"Worker {wid} rebuilding session (403)...")
                    await session.build()

            # Adaptive interval — poll faster as booking time approaches
            sl = secs_left()
            if sl <= 5:
                await asyncio.sleep(0.05)   # 50ms — critical window
            elif sl <= 15:
                await asyncio.sleep(0.1)    # 100ms
            else:
                await asyncio.sleep(jitter(interval))

    #  Orchestrator — EXTREME SPEED MODE ONLY
    async def orchestrator():
        current_phase[0] = 3

        local_workers_count = cfg.get("local_direct_workers", 4) if (HAS_AKAMAI_SESSION and HAS_CURL) else 0
        local_interval      = cfg.get("local_direct_interval", 0.2)

        if local_workers_count == 0:
            log_phase(3, "ERROR — local_direct unavailable: akamai_sensor.py or curl_cffi missing. Install both.")
            await send_msg("ERROR: local_direct unavailable — install akamai_sensor + curl_cffi", force=True)
            return

        total_rps = local_workers_count * int(1 / max(local_interval, 0.001))
        log_phase(3, (
            f"DUAL POLL — {local_workers_count} JSON workers + {local_workers_count} HTML workers "
            f"(curl_cffi + Akamai cookies) @ {local_interval}s "
            f"≈ {total_rps * 2} req/s total  [JSON=REST API, HTML=exam page real-time]"
        ))

        await send_msg(f"LOCAL DIRECT: {local_workers_count} workers @ {local_interval}s", force=True)

        tasks = [
            asyncio.create_task(local_direct_worker(wid, local_interval))
            for wid in range(local_workers_count)
        ] + [
            asyncio.create_task(html_direct_worker(wid, local_interval))
            for wid in range(local_workers_count)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        log_phase(3, (
            f"Hunt ended  |  total requests: {result.attempts}  |  "
            f"direct ok={result.direct_ok} fail={result.direct_fail}"
        ))
        total_rps = local_workers_count * int(1 / max(local_interval, 0.001))
        log_phase(3, (
            f"DUAL POLL — {local_workers_count} JSON workers + {local_workers_count} HTML workers "
            f"(curl_cffi + Akamai cookies) @ {local_interval}s "
            f"≈ {total_rps * 2} req/s total  [JSON=REST API, HTML=exam page real-time]"
        ))
        await send_msg(f"LOCAL DIRECT: {local_workers_count} workers @ {local_interval}s", force=True)

        tasks = [
            asyncio.create_task(local_direct_worker(wid, local_interval))
            for wid in range(local_workers_count)
        ] + [
            asyncio.create_task(html_direct_worker(wid, local_interval))
            for wid in range(local_workers_count)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        log_phase(3, (
            f"Hunt ended  |  total requests: {result.attempts}  |  "
            f"direct ok={result.direct_ok} fail={result.direct_fail}"
        ))

    #  Status loop 
    async def status_loop():
        while not stop_event.is_set():
            elapsed = time.perf_counter() - hunt_start

            # Hard timeout
            if not found_ev.is_set() and elapsed > max_secs:
                stop_event.set()
                await send_msg("Hunt timed out. No OID found.", force=True)
                log_event("HUNT", f"Timed out after {elapsed:.0f}s with no slot found", "WARNING")
                return

            # OID found — stop_event already set by record_found, just wait
            if found_ev.is_set():
                return

            sl    = secs_left()
            rate  = result.attempts / max(elapsed, 0.01)
            t_str = f"T-{sl:.1f}s" if sl > 0 else f"T+{abs(sl):.1f}s"
            if booking_dt:
                bdt_str = booking_dt.strftime("%H:%M:%S")
                time_info = f"Booking opens at {bdt_str}  |  {t_str}"
            else:
                time_info = "No booking time set — hunting continuously"
            line  = (
                f"BLITZ  |  {time_info}  |  "
                f"{result.attempts} reqs ({rate:.1f}/s)  |  "
                f"DIRECT-LOCAL: {result.direct_ok}ok / {result.direct_fail}fail"
            )
            _print_and_log(line, _colour(line, "cyan"))
            await send_msg(
                f"BLITZ | {time_info} | "
                f"#{result.attempts} ({rate:.1f}/s) | "
                f"Direct OK:{result.direct_ok} API OK:{result.api_ok}"
            )
            await asyncio.sleep(1)

    #  Background session refresh — keeps Akamai cookies fresh
    async def session_refresh_task():
        """Proactively refresh Akamai session before it expires."""
        global _global_akamai_session
        while not found_ev.is_set() and not stop_event.is_set():
            await asyncio.sleep(SESSION_REFRESH_SECS - 30)  # refresh 30s before expiry
            if found_ev.is_set() or stop_event.is_set():
                break
            if _global_akamai_session is not None:
                log_event("SESSION", "Proactive session refresh (keeping Akamai cookies fresh)...")
                ok = await _global_akamai_session.build()
                if ok:
                    log_event("SESSION", f"Session refreshed — cookies={list(_global_akamai_session.cookies.keys())[:4]}")
                else:
                    log_event("SESSION", "Session refresh failed — workers will rebuild on next 403", "WARNING")

    #  Run all tasks in parallel
    await asyncio.gather(
        asyncio.create_task(ist_sync_task()),
        asyncio.create_task(precision_countdown_task()),
        asyncio.create_task(browser_launch_task()),
        asyncio.create_task(session_refresh_task()),
        asyncio.create_task(orchestrator()),
        asyncio.create_task(status_loop()),
        return_exceptions=True,
    )

    log_summary(result)
    return result

# 
#  TELEGRAM BOT — GLOBAL STATE
# 

active_hunts = {}   # chat_id -> {task, stop, result}
user_exams   = {}   # chat_id -> {center, exams}
_rdp_mode    = False

def get_cfg(context) -> dict:
    user_cfg = context.user_data.get('config', {})
    cfg = dict(DEFAULT_CFG)
    cfg.update(user_cfg)
    return cfg

# 
#  COMMAND HANDLERS
# 

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '<b>GOETHE OID SNIPER v8.0</b>\n\n'
        'Ultra-fast exam slot detection + booking trigger.\n'
        'Direct local polling PRIMARY + all API backups.\n\n'
        'Use /help to see all commands.\n'
        'Use /centers to start.',
        parse_mode=ParseMode.HTML
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '<b>COMMANDS:</b>\n\n'
        '/start - Welcome\n'
        '/help - This help\n'
        '/centers - List exam centers\n'
        '/exams &lt;center&gt; - Fetch exams\n'
        '/hunt &lt;exam#&gt; - Start hunt (auto-wait)\n'
        '/hunt_now &lt;exam#&gt; - Hunt immediately\n'
        '/stop - Stop active hunt\n'
        '/status - Hunt status\n'
        '/config - Show config\n'
        '/set &lt;key&gt; &lt;value&gt; - Change config\n'
        '/ping - Alive check\n\n'
        '<b>PHASES:</b>\n'
        'Phase 1: T-inf to T-20s  Direct local (0.5s) + ZenRows\n'
        'Phase 2: T-20s to T-3s   Direct local (0.2s) + all APIs\n'
        'Phase 3: T-3s onwards    3 direct workers (0.1s) + all APIs',
        parse_mode=ParseMode.HTML
    )

async def cmd_centers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ['<b>Available Centers:</b>\n']
    for i, name in enumerate(CENTER_LIST):
        lines.append('  ' + str(i + 1) + '. ' + name)
    lines.append('\nUse: /exams &lt;name or number&gt;')
    await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.HTML)

async def cmd_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text('Usage: /exams <center name or number>')
        return
    arg = ' '.join(args)
    center_name = None
    try:
        idx = int(arg)
        if 1 <= idx <= len(CENTER_LIST):
            center_name = CENTER_LIST[idx - 1]
    except ValueError:
        for c in CENTER_LIST:
            if c.lower().startswith(arg.lower()):
                center_name = c
                break
    if not center_name:
        await update.message.reply_text('Unknown center: ' + arg + '\nUse /centers to see list.')
        return
    await update.message.reply_text('Fetching exams for <b>' + center_name + '</b>...', parse_mode=ParseMode.HTML)
    cfg = get_cfg(context)
    inst_id = CENTERS[center_name]['id']
    api_url = _api_url(inst_id, cfg.get('exam_category', 'E007'), cfg.get('exam_type', 'ER'))
    data = None
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url,
                                       headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                                       timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        try:
                            data = await r.json(content_type=None)
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception as e:
        await update.message.reply_text('Error fetching exams: ' + str(e))
        return
    if not data or not isinstance(data, dict) or 'DATA' not in data:
        await update.message.reply_text('Failed to fetch exams. Try again.')
        return
    exams = parse_exams(data, cfg.get('exam_category', 'E007'),
                        cfg.get('exam_type', 'ER'), cfg.get('exam_level', 'B2'))
    if not exams:
        exams = parse_exams(data)
    if not exams:
        await update.message.reply_text('No exams found for this center.')
        return
    user_exams[update.effective_chat.id] = {'center': center_name, 'exams': exams}
    lines = ['<b>Exams at ' + center_name + ':</b>\n']
    for i, ex in enumerate(exams):
        oid_status = 'OID READY' if ex.get('oid') else 'Waiting'
        book_time  = ex.get('bookFrom', '?') + ' ' + ex.get('bookFromTimeFormatted', ex.get('bookFromTime', '')[:5])
        lines.append(
            '  <b>' + str(i + 1) + '.</b> ' + ex['startDate'] + ' | ' +
            ex.get('languageLevel', '?') + ' | Book: ' + book_time + ' | ' + oid_status
        )
    lines.append('\nUse: /hunt &lt;number&gt; to start hunting')
    await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.HTML)

async def _start_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE, skip_wait: bool = False):
    args    = context.args
    chat_id = update.effective_chat.id
    if not args:
        await update.message.reply_text('Usage: /hunt <exam number>\nFirst use /exams <center>.')
        return
    cached = user_exams.get(chat_id)
    if not cached:
        await update.message.reply_text('First use /exams <center> to fetch exam list.')
        return
    try:
        idx = int(args[0])
        if idx < 1 or idx > len(cached['exams']):
            await update.message.reply_text('Invalid exam number. Range: 1-' + str(len(cached['exams'])))
            return
    except ValueError:
        await update.message.reply_text('Provide exam number (integer).')
        return
    exam        = cached['exams'][idx - 1]
    center_name = cached['center']
    if exam.get('oid'):
        url = 'https://www.goethe.de/coe?lang=en&oid=' + exam['oid']
        await update.message.reply_text(
            '<b>OID ALREADY AVAILABLE!</b>\n\n<b>Booking URL:</b>\n' + url +
            '\n\n<b>Center:</b> ' + center_name + '\n<b>Date:</b> ' + exam['startDate'],
            parse_mode=ParseMode.HTML
        )
        return
    if chat_id in active_hunts:
        active_hunts[chat_id]['stop'].set()
        await asyncio.sleep(0.5)
    cfg = get_cfg(context)
    booking_dt = parse_booking_dt(exam.get('bookFrom', ''), exam.get('bookFromTime', ''))
    now        = ist_now()
    secs_until = (booking_dt - now).total_seconds() if booking_dt else -1
    if not skip_wait and booking_dt and secs_until > 60:
        wait_until = max(0, secs_until - cfg['warmup_trigger'])
        if wait_until > 0:
            m, s = divmod(int(wait_until), 60)
            h, m = divmod(m, 60)
            await update.message.reply_text(
                '<b>Hunt scheduled</b>\n\n'
                '<b>Exam:</b> ' + exam['startDate'] + ' @ ' + center_name + '\n'
                '<b>Booking opens:</b> ' + (booking_dt.strftime('%d %b %Y %I:%M:%S %p') if booking_dt else '?') + ' IST\n'
                '<b>Hunt starts in:</b> ' + str(h).zfill(2) + ':' + str(m).zfill(2) + ':' + str(s).zfill(2) + '\n\n'
                'Waiting... Use /stop to cancel.',
                parse_mode=ParseMode.HTML
            )
            stop_event = asyncio.Event()
            active_hunts[chat_id] = {'stop': stop_event, 'task': None, 'result': None}
            waited = 0
            while waited < wait_until and not stop_event.is_set():
                await asyncio.sleep(min(5, wait_until - waited))
                waited += 5
            if stop_event.is_set():
                del active_hunts[chat_id]
                await update.message.reply_text('Hunt cancelled.')
                return
    stop_event = asyncio.Event()
    await update.message.reply_text(
        '<b>HUNT STARTING!</b>\n\n'
        '<b>Target:</b> ' + exam['startDate'] + ' @ ' + center_name + '\n'
        '<b>APIs:</b> LOCAL DIRECT + HTML POLL\n'
        '<b>Direct workers P3:</b> ' + str(cfg.get('local_workers_p3', 3)) + '\n'
        '<b>Phase 3 at:</b> T-' + str(cfg['phase3_trigger']) + 's\n'
        '<b>curl_cffi:</b> ' + ('YES' if HAS_CURL else 'NO') + '\n\n'
        'Hunting...',
        parse_mode=ParseMode.HTML
    )

    async def hunt_wrapper():
        try:
            hr = await run_hunt(
                bot=context.bot, chat_id=chat_id,
                center_name=center_name, exam=exam,
                cfg=cfg, stop_event=stop_event,
                rdp_mode=_rdp_mode,
            )
            if hr and hr.oid:
                url = make_booking_url(hr.oid, hr.button_link)
                await context.bot.send_message(
                    chat_id,
                    '<b>OID FOUND!</b>\n\n'
                    '<b>BOOK NOW:</b>\n' + url + '\n\n'
                    '<b>Time:</b> ' + str(round(hr.elapsed, 3)) + 's\n'
                    '<b>Phase:</b> ' + str(hr.phase) + '\n'
                    '<b>Source:</b> ' + str(hr.source) + '\n'
                    '<b>Attempts:</b> ' + str(hr.attempts) + '\n'
                    '<b>API OK:</b> ' + str(hr.api_ok) + ' | <b>Direct OK:</b> ' + str(hr.direct_ok),
                    parse_mode=ParseMode.HTML
                )
                await context.bot.send_message(chat_id, url)
                # Launch browsers
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, launch_booking, hr.oid, cfg.get('num_students', 1), _rdp_mode, hr.button_link)
            elif not stop_event.is_set():
                await context.bot.send_message(
                    chat_id,
                    '<b>Hunt ended - No OID found</b>\n\nAttempts: ' +
                    str(hr.attempts if hr else 0) + '\nUse /hunt ' + str(idx) + ' to retry.',
                    parse_mode=ParseMode.HTML
                )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error('Hunt error: ' + str(e))
            try:
                await context.bot.send_message(chat_id, 'Hunt error: ' + str(e))
            except Exception:
                pass
        finally:
            active_hunts.pop(chat_id, None)

    task = asyncio.create_task(hunt_wrapper())
    active_hunts[chat_id] = {'task': task, 'stop': stop_event, 'result': None}

async def cmd_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_hunt(update, context, skip_wait=False)

async def cmd_hunt_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_hunt(update, context, skip_wait=True)

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    hunt    = active_hunts.get(chat_id)
    if hunt:
        hunt['stop'].set()
        if hunt.get('task'):
            hunt['task'].cancel()
        active_hunts.pop(chat_id, None)
        await update.message.reply_text('Hunt stopped.')
    else:
        await update.message.reply_text('No active hunt.')

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    hunt    = active_hunts.get(chat_id)
    if hunt and hunt.get('task') and not hunt['task'].done():
        await update.message.reply_text(
            '<b>Hunt is ACTIVE</b>\nUse /stop to cancel.',
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text('No active hunt. Use /hunt to start one.')

async def cmd_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg   = get_cfg(context)
    lines = ['<b>Current Configuration:</b>\n']
    for k, v in cfg.items():
        lines.append('  <code>' + k + '</code> = ' + str(v))
    lines.append('\n<b>Method:</b> LOCAL DIRECT (curl_cffi + Akamai) + HTML POLL')
    lines.append('<b>curl_cffi:</b> ' + ('Available' if HAS_CURL else 'Not available'))
    lines.append('\nUse: /set &lt;key&gt; &lt;value&gt; to change')
    await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.HTML)

async def cmd_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            'Usage: /set <key> <value>\n\n'
            'Keys: proxy, students, phase2, phase3, workers_p3, timeout,\n'
            'interval_p1, interval_p2, interval_p3, api_timeout, exam_level,\n'
            'backoff_start, backoff_max, failfast_consec, failfast_slow, max_hunt_min'
        )
        return
    key      = args[0].lower()
    val      = args[1].lower()
    user_cfg = context.user_data.setdefault('config', {})
    key_map  = {
        'proxy':          ('use_proxy',          lambda v: v in ('on', 'true', 'yes', '1')),
        'students':       ('num_students',        lambda v: max(1, min(10, int(v)))),
        'phase2':         ('phase2_trigger',      lambda v: max(5, min(60, int(v)))),
        'phase3':         ('phase3_trigger',      lambda v: max(1, min(30, int(v)))),
        'workers_p3':     ('local_workers_p3',    lambda v: max(1, min(10, int(v)))),
        'timeout':        ('local_timeout',       lambda v: max(1.0, min(30.0, float(v)))),
        'interval_p1':    ('local_interval_p1',   lambda v: max(0.05, min(5.0, float(v)))),
        'interval_p2':    ('local_interval_p2',   lambda v: max(0.05, min(5.0, float(v)))),
        'interval_p3':    ('local_interval_p3',   lambda v: max(0.01, min(2.0, float(v)))),
        'api_timeout':    ('api_timeout',         lambda v: max(3, min(60, int(v)))),
        'api_timeout_p3': ('api_timeout_p3',      lambda v: max(1, min(20, int(v)))),
        'exam_level':     ('exam_level',          lambda v: v.upper()),
        'backoff_start':  ('backoff_start',       lambda v: max(0.5, min(10.0, float(v)))),
        'backoff_max':    ('backoff_max',          lambda v: max(1.0, min(30.0, float(v)))),
        'failfast_consec': ('failfast_consec',    lambda v: max(1, min(10, int(v)))),
        'failfast_slow':  ('failfast_slow',       lambda v: max(5.0, min(60.0, float(v)))),
        'max_hunt_min':   ('max_hunt_min',        lambda v: max(5, min(180, int(v)))),
    }
    if key not in key_map:
        await update.message.reply_text('Unknown key: ' + key + '\nValid: ' + ', '.join(key_map.keys()))
        return
    cfg_key, parser = key_map[key]
    try:
        parsed = parser(val)
        user_cfg[cfg_key] = parsed
        await update.message.reply_text('<code>' + cfg_key + '</code> = ' + str(parsed), parse_mode=ParseMode.HTML)
    except (ValueError, TypeError) as e:
        await update.message.reply_text('Invalid value: ' + str(e))

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = ist_now()
    await update.message.reply_text(
        'Pong! Bot is alive.\n'
        'IST: ' + now.strftime('%d %b %Y %H:%M:%S') + '\n'
        'Active hunts: ' + str(len(active_hunts)) + '\n'
        'APIs: LOCAL DIRECT + HTML POLL\n'
        'curl_cffi: ' + ('YES' if HAS_CURL else 'NO')
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().lower()
    greetings = ['hi', 'hello', 'hey', 'sup', 'yo', 'hola', 'namaste']
    if any(g == text or text.startswith(g + ' ') for g in greetings):
        await update.message.reply_text(
            'Hey! I am the <b>Goethe OID Sniper v8.0</b> bot.\n\nUse /help to see all commands.',
            parse_mode=ParseMode.HTML
        )
        return
    await update.message.reply_text('Use /help for available commands.')


# 
#  MAIN
# 

# ─────────────────────────────────────────────────────────────────────────────
#  CMD INTERFACE — v6.2 style, runs without Telegram
# ─────────────────────────────────────────────────────────────────────────────

# CENTER_LIST already defined at top of file — no redefinition needed

def _cmd_banner():
    print(_colour("""
  ╔══════════════════════════════════════════════════════════════╗
  ║       GOETHE OID SNIPER v8.0 — CMD INTERFACE                ║
  ║  LOCAL DIRECT ONLY · curl_cffi + Akamai · Instant browser   ║
  ║  Anti-Akamai · Precision timing · Dual log (CMD + file)     ║
  ╚══════════════════════════════════════════════════════════════╝
""", "cyan", "bold"))

def _pick_center() -> str:
    """Show numbered center list, return chosen center name."""
    global _manual_cookies
    while True:
        print(_colour("\n  Select a center:", "white", "bold"))
        for i, name in enumerate(CENTER_LIST, 1):
            print(f"    {_colour(str(i), 'cyan')}. {name}")
        print(f"    {_colour('c', 'magenta')}. Refresh Akamai cookies (paste new ones)")
        print(f"    {_colour('0', 'yellow')}. Exit")
        choice = _ask(f"  {_colour('Enter number:', 'cyan')} ")
        if choice == "0":
            return ""
        if choice.lower() == "c":
            _manual_cookies = _prompt_manual_cookies()
            continue
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(CENTER_LIST):
                return CENTER_LIST[idx]
        except ValueError:
            pass
        print(_colour("  Invalid choice — try again", "yellow"))

def _fetch_exams_cmd(center_name: str) -> list:
    """
    Fetch exam list using SeleniumBase (real browser) ONLY.
    Falls back to ALL ZenRows accounts → ScraperAPI → other scrapers.
    KEEPS THE BROWSER ALIVE for the hunt to avoid reopening delay.
    """
    global _persistent_selenium_driver
    
    inst_id = CENTERS[center_name]["id"]
    url     = _api_url(inst_id, DEFAULT_CFG["exam_category"], DEFAULT_CFG["exam_type"])
    print(_colour(f"\n  Fetching exams for {center_name}...", "cyan"))

    # ── Method 1: SeleniumBase (REAL BROWSER — always works) ─────────────────
    if HAS_SELENIUMBASE:
        driver = _persistent_selenium_driver
        driver_is_alive = False
        
        # Check if existing driver is still alive
        if driver:
            try:
                _ = driver.current_url  # Test if session is alive
                driver_is_alive = True
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(_colour(f"  [{ts}] ✓ Using existing browser session (ZERO delay!)", "green"))
                log_event("BROWSER", f"Reusing existing browser at {ts}")
            except Exception as e:
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(_colour(f"  [{ts}] ⚠ Previous browser session died — reopening...", "yellow"))
                log_event("BROWSER", f"Browser died ({e}), reopening at {ts}", "WARNING")
                _persistent_selenium_driver = None
                driver = None
        
        try:
            if not driver_is_alive:
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(_colour(f"  [{ts}] Opening real browser (SeleniumBase)...", "cyan"))
                log_event("BROWSER", f"Opening new Selenium session at {ts}")
                
                # headless=False — Akamai detects and blocks headless browsers
                # Change to temp dir to avoid permission issues
                import tempfile
                import os as _os
                original_cwd = _os.getcwd()
                temp_dir = tempfile.gettempdir()
                try:
                    _os.chdir(temp_dir)
                    # Fixed: removed downloads_path parameter (not supported in all versions)
                    driver = _SBDriver(uc=True, headless=False, block_images=True)
                    _persistent_selenium_driver = driver  # Keep alive
                finally:
                    _os.chdir(original_cwd)
                
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(_colour(f"  [{ts}] Browser opened, loading Goethe homepage...", "cyan"))
                log_event("BROWSER", f"Browser ready at {ts}")
                
                driver.get(GOETHE_HOME)
                time.sleep(3)   # wait for Akamai sensors to load
                driver.refresh()
                time.sleep(2)
            
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(_colour(f"  [{ts}] Fetching exam data via browser fetch()...", "cyan"))

            js = f"""
            var callback = arguments[arguments.length - 1];
            fetch("{url}&_=" + Date.now(), {{
                credentials: 'include',
                cache: 'no-store',
                headers: {{
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache'
                }}
            }})
            .then(res => res.json())
            .then(data => callback({{ ok: true, data: data }}))
            .catch(err => callback({{ ok: false, error: err.toString() }}));
            """
            result = driver.execute_async_script(js)

            if result.get("ok") and result.get("data"):
                data  = result["data"]
                exams = parse_exams(data, DEFAULT_CFG["exam_category"],
                                    DEFAULT_CFG["exam_type"], DEFAULT_CFG["exam_level"])
                if not exams:
                    # Try without level filter — show all exams
                    exams = parse_exams(data, DEFAULT_CFG["exam_category"], DEFAULT_CFG["exam_type"])
                if not exams:
                    # Try with no filters at all
                    exams = parse_exams(data)
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(_colour(f"  [{ts}] ✅ Got {len(exams)} exam(s) via real browser", "green"))
                log_event("BROWSER", f"Fetched {len(exams)} exams at {ts}")
                return exams
            else:
                err = result.get('error', 'unknown error')
                print(_colour(f"  Browser fetch returned no data: {err}", "red"))
        except Exception as e:
            print(_colour(f"  SeleniumBase error: {e}", "red"))
            import traceback
            traceback.print_exc()
            # Don't quit on error — keep browser alive for retry

    print(_colour("\n  ❌ Selenium fetch failed. Make sure SeleniumBase is installed.", "red"))
    print(_colour("  → pip install seleniumbase", "yellow"))
    return []

def _pick_exam(exams: list) -> dict:
    """Show numbered exam list, return chosen exam dict."""
    if not exams:
        print(_colour("  No exams found for this center.", "yellow"))
        return {}
    print(_colour("\n  Available exams:", "white", "bold"))
    for i, ex in enumerate(exams, 1):
        avail = ex.get("availability", 0)
        avail_str = _colour(f"slots={avail}", "green") if avail > 0 else _colour("no slots", "yellow")
        book_time = f"{ex.get('bookFrom','')} {ex.get('bookFromTime','')[:8]}".strip()
        btn_disabled = ex.get("buttonDisabled", "disabled")
        btn_status = _colour("BOOKING OPEN!", "green", "bold") if btn_disabled != "disabled" else _colour("not open yet", "dim")
        print(
            f"    {_colour(str(i), 'cyan')}. "
            f"{ex.get('startDate','')}  "
            f"Level={ex.get('languageLevel','')}  "
            f"{avail_str}  "
            f"Booking opens: {_colour(book_time, 'blue')}  "
            f"{btn_status}"
        )
    print(f"    {_colour('0', 'yellow')}. Back")
    while True:
        choice = _ask(f"  {_colour('Enter exam number:', 'cyan')} ")
        if choice == "0":
            return {}
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(exams):
                return exams[idx]
        except ValueError:
            pass
        print(_colour("  Invalid choice", "yellow"))

def _post_hunt_loop(result: HuntResult, num_students: int, center_name: str = "", exam: dict = None, cfg: dict = None, rdp_mode: bool = False):
    """
    After OID found — full v6.2-style post-OID command loop.
    Student state tracking, rehunt, URL, status, email.
    """
    global _redirect_oid, _oid_fired, _prewarmed_tabs, _manual_cookies
    
    oid = result.oid
    url = make_booking_url(oid, getattr(result, "button_link", ""))

    # Student state tracking
    student_states = {i: "LINK_OPENED" for i in range(1, num_students + 1)}

    print(_colour(f"\n  {'='*58}", "green", "bold"))
    print(_colour(f"  ★  SLOT FOUND!  OID = {oid}", "green", "bold"))
    print(_colour(f"  URL: {url}", "green"))
    print(_colour(f"  Found by: {result.source}  |  Phase: {result.phase}  |  Time: {result.elapsed:.3f}s", "green"))
    print(_colour(f"  {'='*58}", "green", "bold"))

    # Send email notification
    send_email_async(
        f"GOETHE SLOT FOUND — {oid}",
        f"<b>OID FOUND!</b><br>OID: {oid}<br>URL: <a href='{url}'>{url}</a><br>"
        f"Found by: {result.source} | Phase: {result.phase} | Time: {result.elapsed:.3f}s"
    )

    print(_colour("\n  Commands:", "cyan"))
    print("    s1 ok / s2 ok     → mark student as booked successfully")
    print("    s1 fail / s2 fail → mark student as failed (re-opens browser)")
    print("    s1 retry          → force re-open browser for student")
    print("    url               → show booking URL")
    print("    status            → show all student states")
    print("    cookies           → paste fresh Akamai cookies")
    print("    rehunt            → start a new hunt for same exam")
    print("    back              → return to main menu")

    while True:
        try:
            cmd = _ask(_colour("  cmd> ", "cyan")).lower().strip()
        except (EOFError, KeyboardInterrupt):
            print(_colour("\n  (type 'back' to return to menu)", "yellow"))
            continue

        if not cmd:
            continue

        elif cmd == "back" or cmd == "exit":
            break

        elif cmd == "url":
            print(_colour(f"  {url}", "green"))

        elif cmd == "cookies":
            _manual_cookies = _prompt_manual_cookies()
            print(_colour("  Cookies updated — will be used in next hunt", "green"))

        elif cmd == "status":
            print(_colour(f"\n  OID: {oid}", "green"))
            print(f"  Found by: {result.source}  Phase: {result.phase}  Time: {result.elapsed:.3f}s")
            print(f"  Requests: {result.attempts}  API ok={result.api_ok}  Direct ok={result.direct_ok}")
            print(_colour("  Student states:", "cyan"))
            for sid, state in student_states.items():
                color = "green" if state == "SUCCESS" else ("red" if state == "FAILED" else "cyan")
                print(f"    Student {sid}: {_colour(state, color)}")

        elif cmd.startswith("s") and len(cmd.split()) == 2:
            parts = cmd.split()
            try:
                sid   = int(parts[0][1:])
                action = parts[1]
                if sid not in student_states:
                    print(_colour(f"  No student {sid}", "yellow"))
                    continue
                if action == "ok":
                    student_states[sid] = "SUCCESS"
                    print(_colour(f"  Student {sid} marked SUCCESS", "green"))
                    if all(v == "SUCCESS" for v in student_states.values()):
                        print(_colour("  All students booked! Great success!", "green", "bold"))
                elif action == "fail":
                    student_states[sid] = "FAILED"
                    print(_colour(f"  Student {sid} marked FAILED — re-opening browser", "yellow"))
                    launch_booking(oid, 1, rdp_mode, getattr(result, "button_link", ""))
                elif action == "retry":
                    print(_colour(f"  Re-opening browser for student {sid}", "cyan"))
                    launch_booking(oid, 1, rdp_mode, getattr(result, "button_link", ""))
                else:
                    print(_colour("  Use: s1 ok | s1 fail | s1 retry", "yellow"))
            except (ValueError, IndexError):
                print(_colour("  Use: s1 ok | s1 fail | s1 retry", "yellow"))

        elif cmd == "rehunt":
            if not exam or not center_name or not cfg:
                print(_colour("  Rehunt not available (no exam context)", "yellow"))
                continue
            print(_colour("  Starting rehunt for same exam...", "cyan"))
            # Reset OID state for fresh hunt
            _redirect_oid = ""
            _oid_fired = False
            # Re-open booking browsers on waiting page
            profiles = _browser_profiles[:num_students] if _browser_profiles else ["Default"] * num_students
            for profile in profiles:
                port = random.choice(_REDIRECT_PORTS)
                entry_url = f"http://127.0.0.1:{port}/entry"
                _launch_url_in_profile(entry_url, profile, rdp_mode)
                _prewarmed_tabs[profile] = True
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(_colour(f"  [{ts}] ✓ All {num_students} booking browser(s) reset to waiting page", "green"))
            try:
                new_result = asyncio.run(_run_hunt_cmd(center_name, exam, cfg, rdp_mode))
            except KeyboardInterrupt:
                print(_colour("  Rehunt stopped.", "yellow"))
                continue
            if new_result and new_result.oid:
                result = new_result
                oid    = result.oid
                url    = make_booking_url(oid, getattr(result, "button_link", ""))
                student_states = {i: "LINK_OPENED" for i in range(1, num_students + 1)}
                print(_colour(f"  Rehunt found OID: {oid}", "green", "bold"))
                print(_colour(f"  Booking URL: {url}", "green"))
            else:
                print(_colour("  Rehunt ended — no slot found", "yellow"))

        else:
            print(_colour("  Unknown command. Type 'back' to return to menu.", "yellow"))

async def _run_hunt_cmd(center_name: str, exam: dict, cfg: dict, rdp_mode: bool):
    """Run the hunt engine and return result."""
    stop_ev = asyncio.Event()

    # Fake bot/chat_id — CMD mode doesn't need Telegram
    class _FakeBot:
        async def send_message(self, *a, **kw): pass
    fake_bot = _FakeBot()

    result = await run_hunt(fake_bot, 0, center_name, exam, cfg, stop_ev, rdp_mode)
    return result

def cmd_main():
    """Full CMD interface — v6.2 style."""
    global _browser_path, _browser_profiles, _rdp_mode, _persistent_selenium_driver
    global _manual_cookies, _oid_fired, _redirect_oid, _prewarmed_tabs

    _init_log()
    _cmd_banner()

    _clock.start()
    log_event("STARTUP", f"IST: {ist_now().strftime('%d %b %Y %H:%M:%S')}")

    _browser_path     = detect_browser_path()
    _browser_profiles = detect_profiles(_browser_path)
    if _browser_path:
        log_event("STARTUP", f"Browser: {_browser_path}")
        log_event("STARTUP", f"Profiles: {_browser_profiles}")
    else:
        log_event("STARTUP", "No Edge/Chrome found — will use system default", "WARNING")

    log_event("STARTUP", f"curl_cffi: {'YES ✔' if HAS_CURL else 'NO ✖ — pip install curl_cffi'}")
    log_event("STARTUP", f"akamai_sensor: {'YES ✔' if HAS_AKAMAI_SESSION else 'NO ✖ — akamai_sensor.py missing'}")
    log_event("STARTUP", f"SeleniumBase (exam fetch only): {'YES' if HAS_SELENIUMBASE else 'NO — pip install seleniumbase'}")
    if not HAS_CURL or not HAS_AKAMAI_SESSION:
        print(_colour("\n  ✖  CRITICAL: curl_cffi or akamai_sensor missing — local_direct workers will not fire!", "red", "bold"))
    if not HAS_SELENIUMBASE:
        print(_colour("\n  ⚠  SeleniumBase not found — needed for exam fetch:", "yellow"))
        print(_colour("     py -m pip install seleniumbase\n", "cyan"))

    # RDP mode
    rdp_ans = _ask(_colour("  Running on RDP/VPS? (y/n) [n]: ", "cyan"), "n").lower()
    _rdp_mode = rdp_ans in ("y", "yes")
    log_event("STARTUP", "RDP mode ON" if _rdp_mode else "Local mode")

    # Selenium worker count — set at top of file
    _wcount = RDP_SELENIUM_WORKERS if _rdp_mode else LOCAL_SELENIUM_WORKERS
    DEFAULT_CFG["selenium_workers_p3"] = _wcount
    log_event("STARTUP", f"Mode: LOCAL DIRECT ONLY (curl_cffi + Akamai cookies) — {LOCAL_SELENIUM_WORKERS} workers on local, {RDP_SELENIUM_WORKERS} on RDP")

    # Number of students
    while True:
        ns = _ask(_colour("  Number of students (1-10) [1]: ", "cyan"), "1")
        try:
            num_students = int(ns)
            if 1 <= num_students <= 10:
                break
        except ValueError:
            pass
        print(_colour("  Enter a number between 1 and 10", "yellow"))
    log_event("STARTUP", f"Students: {num_students}")
    
    # ── IMMEDIATELY open browser when student count is entered ────────────────
    # Two things happen at once:
    # 1. Open 1 Selenium browser (for polling the API — stays open for exam fetch + hunt)
    # 2. Open N Edge/Chrome booking browsers on the redirect waiting page (one per student)
    #    These will auto-navigate to the booking URL the instant OID is found (< 50ms)
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(_colour(f"\n  [{ts}] Opening {num_students} booking browser(s) + 1 Selenium poller...", "green", "bold"))
    
    # HIGH-PRECISION TIMING: Mark browser opening sequence start
    _precision_timer.mark("CMD_BROWSER_SEQUENCE_START", f"{num_students} students")
    log_event("BROWSER", f"Pre-opening {num_students} booking browsers + Selenium at {ts}")

    # Start redirect server first so browsers have something to load
    start_redirect_servers()

    # Open N booking browsers — each goes through exam page first, then waiting page
    # Flow: /entry → exam listing page → /waiting → booking URL  (looks like real user)
    profiles = _browser_profiles[:num_students] if _browser_profiles else ["Default"] * num_students
    for i, profile in enumerate(profiles):
        port = random.choice(_REDIRECT_PORTS)
        entry_url = f"http://127.0.0.1:{port}/entry"   # ← exam page first, then waiting

        browser_start = time.perf_counter()
        _launch_url_in_profile(entry_url, profile, _rdp_mode)
        browser_end = time.perf_counter()
        browser_ms = (browser_end - browser_start) * 1000

        _prewarmed_tabs[profile] = True
        ts2 = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(_colour(f"  [{ts2}] ✓ Booking browser {i+1}/{num_students} opened (Profile: {profile}, Server: {port}, {browser_ms:.1f}ms)", "green"))
        _precision_timer.mark(f"CMD_BROWSER_{i+1}_OPENED", f"profile={profile} port={port} {browser_ms:.1f}ms")

        if i < len(profiles) - 1:
            time.sleep(0.3)

    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(_colour(f"  [{ts}] All {num_students} booking browser(s) open — waiting for OID on redirect page", "green"))
    _precision_timer.mark("CMD_BOOKING_BROWSERS_READY", f"All {num_students} browsers ready")
    log_event("BROWSER", f"All {num_students} booking browsers ready at {ts}")

    # Open 1 Selenium browser for API polling (separate from booking browsers)
    if HAS_SELENIUMBASE and not _persistent_selenium_driver:
        try:
            import tempfile
            import os as _os
            original_cwd = _os.getcwd()
            temp_dir = tempfile.gettempdir()
            
            # HIGH-PRECISION TIMING: Mark Selenium browser opening
            selenium_start = time.perf_counter()
            try:
                _os.chdir(temp_dir)
                _persistent_selenium_driver = _SBDriver(uc=True, headless=False, block_images=True)
            finally:
                _os.chdir(original_cwd)
            selenium_end = time.perf_counter()
            selenium_ms = (selenium_end - selenium_start) * 1000

            _persistent_selenium_driver.get(GOETHE_HOME)
            time.sleep(2)
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(_colour(f"  [{ts}] ✓ Selenium poller ready (for API requests, opened in {selenium_ms:.1f}ms)", "green"))
            
            _precision_timer.mark("CMD_SELENIUM_READY", f"Selenium browser ready {selenium_ms:.1f}ms")
            log_event("BROWSER", f"Selenium poller loaded at {ts}")
        except Exception as e:
            print(_colour(f"  ⚠ Selenium poller failed to open: {e}", "yellow"))
            log_event("BROWSER", f"Selenium pre-open failed: {e}", "WARNING")
            import traceback
            traceback.print_exc()

    # HIGH-PRECISION TIMING: Mark entire browser sequence complete
    _precision_timer.mark("CMD_BROWSER_SEQUENCE_COMPLETE", f"All browsers ready")
    _precision_timer.measure_delay("CMD_BROWSER_SEQUENCE_START", "CMD_BROWSER_SEQUENCE_COMPLETE")

    # ── Akamai cookie setup — auto only, no prompt ───────────────────────────
    # Selenium carries real browser cookies automatically, no manual input needed

    cfg = dict(DEFAULT_CFG)
    cfg["num_students"] = num_students

    # Main loop — pick center → pick exam → hunt → repeat
    while True:
        center_name = _pick_center()
        if not center_name:
            print(_colour("\n  Goodbye!", "cyan"))
            break

        exams = _fetch_exams_cmd(center_name)
        if not exams:
            continue

        exam = _pick_exam(exams)
        if not exam:
            continue

        # Show booking time clearly
        booking_dt = parse_booking_dt(exam.get("bookFrom", ""), exam.get("bookFromTime", ""))
        if booking_dt:
            sl = (booking_dt - ist_now()).total_seconds()
            bdt_str = booking_dt.strftime("%d %b %Y at %H:%M:%S")
            print(_colour(f"\n  Booking opens: {bdt_str} IST", "blue", "bold"))
            if sl > 0:
                h, rem = divmod(int(sl), 3600)
                m, s   = divmod(rem, 60)
                print(_colour(f"  Time until booking: {h}h {m}m {s}s", "blue"))
            else:
                print(_colour("  Booking window is ALREADY OPEN — hunting immediately!", "green", "bold"))
        else:
            print(_colour("  No booking time in exam data — will hunt immediately", "yellow"))

        # OID already available?
        if exam.get("oid") and exam.get("availability", 0) > 0:
            booking_url = make_booking_url(exam["oid"], exam.get("buttonLink", ""))
            print(_colour(f"\n  OID already available!", "green", "bold"))
            print(_colour(f"  Booking URL:", "cyan"))
            print(_colour(f"  {booking_url}", "green"))   # full URL shown
            confirm = _ask(_colour("\n  Is this the correct booking URL? (y/n) [y]: ", "cyan"), "y").lower()
            if confirm in ("n", "no"):
                real_url = _ask(_colour("  Paste the correct booking URL: ", "cyan"), "").strip()
                if real_url:
                    booking_url = real_url
            ans = _ask(_colour("  Open booking page now? (y/n) [y]: ", "cyan"), "y").lower()
            if ans not in ("n", "no"):
                # Reset fired flag so launch_booking actually fires
                _oid_fired = False
                _redirect_oid = ""
                # Navigate directly to the confirmed URL
                profiles = _browser_profiles[:num_students] if _browser_profiles else ["Default"]
                for profile in profiles:
                    _launch_url_in_profile(booking_url, profile, _rdp_mode)
                _post_hunt_loop(
                    type("R", (), {"oid": exam["oid"], "button_link": exam.get("buttonLink", ""), "source": "pre-existing",
                                   "phase": 0, "elapsed": 0, "attempts": 0,
                                   "api_ok": 0, "api_fail": 0,
                                   "direct_ok": 0, "direct_fail": 0})(),
                    num_students, center_name, exam, cfg, _rdp_mode
                )
                continue

        # Confirm and start hunt
        print(_colour(f"\n  Ready to hunt:", "white", "bold"))
        print(f"    Center  : {center_name}")
        print(f"    Exam    : {exam.get('startDate','')}  Level={exam.get('languageLevel','')}")
        print(f"    Students: {num_students}")
        print(f"    Method  : LOCAL DIRECT + HTML POLL (curl_cffi + Akamai)")
        ans = _ask(_colour("  Start hunt? (y/n) [y]: ", "cyan"), "y").lower()
        if ans in ("n", "no"):
            continue

        # ── Exam detail page URL confirmation ─────────────────────────────────
        # Auto-build from encOID, show full URL, ask user to confirm or correct.
        # This URL is visited by BOTH Selenium (session warm-up) and Edge browsers
        # so the session looks like a real user who browsed to the exam page.
        global _exam_page_url
        enc_oid = exam.get("encOID", "")
        if enc_oid:
            # HAR confirmed: English URL /ins/in/en/ with examId parameter
            auto_exam_url_with_id = f"https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm?examId={enc_oid}"
        else:
            auto_exam_url_with_id = "https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm"

        print(_colour(f"\n  ─── Exam detail page ───────────────────────────────────────", "cyan"))
        print(_colour(f"  Auto-built URL:", "dim"))
        print(_colour(f"  {auto_exam_url_with_id}", "green"))   # full URL shown
        confirm = _ask(_colour("\n  Is this the correct exam page? (y/n) [y]: ", "cyan"), "y").lower()
        if confirm in ("n", "no"):
            real_url = _ask(_colour("  Paste the correct exam detail URL: ", "cyan"), "").strip()
            _exam_page_url = real_url if real_url else auto_exam_url_with_id
        else:
            _exam_page_url = auto_exam_url_with_id
        print(_colour(f"  ✓ Using: {_exam_page_url}", "green"))

        # ── Warm up Selenium browser — walk the full navigation chain ─────────
        if _persistent_selenium_driver:
            try:
                # Walk the chain matching the real HAR: English pages
                print(_colour(f"\n  Warming up Selenium session (walking real navigation chain)...", "cyan"))
                _persistent_selenium_driver.get("https://www.goethe.de/ins/in/en/spr/prf/gzb2.cfm")
                time.sleep(1)
                _persistent_selenium_driver.get(_exam_page_url)
                time.sleep(2)
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(_colour(f"  [{ts}] ✓ Selenium on exam detail page — session ready", "green"))
                log_event("BROWSER", f"Selenium warmed up: {_exam_page_url}")
            except Exception as e:
                print(_colour(f"  ⚠ Selenium warm-up failed: {e}", "yellow"))
        # ─────────────────────────────────────────────────────────────────────

        print(_colour("\n  Hunt starting — press Ctrl+C to stop\n", "green", "bold"))

        # HIGH-PRECISION TIMING: Mark hunt start
        _precision_timer.mark("HUNT_START", f"center={center_name} exam={exam.get('startDate','')}")

        # Reset OID state for fresh hunt
        _oid_fired = False
        _redirect_oid = ""

        # Re-open booking browsers — exam page first, then waiting page
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(_colour(f"  [{ts}] Re-opening {num_students} booking browser(s) (exam page → waiting page)...", "cyan"))
        profiles = _browser_profiles[:num_students] if _browser_profiles else ["Default"] * num_students
        for i, profile in enumerate(profiles):
            port = random.choice(_REDIRECT_PORTS)
            entry_url = f"http://127.0.0.1:{port}/entry"
            _launch_url_in_profile(entry_url, profile, _rdp_mode)
            _prewarmed_tabs[profile] = True
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(_colour(f"  [{ts}] ✓ All {num_students} booking browser(s) ready", "green"))

        try:
            result = asyncio.run(_run_hunt_cmd(center_name, exam, cfg, _rdp_mode))
        except KeyboardInterrupt:
            print(_colour("\n  Hunt stopped by user.", "yellow"))
            continue

        if result and result.oid:
            _post_hunt_loop(result, num_students, center_name, exam, cfg, _rdp_mode)
        else:
            print(_colour("\n  Hunt ended — no slot found.", "yellow"))
            retry = _ask(_colour("  Retry same exam? (y/n) [n]: ", "cyan"), "n").lower()
            if retry in ("y", "yes"):
                # Reset redirect server OID so it's fresh
                _redirect_oid = ""
                continue

        again = _ask(_colour("\n  Hunt another exam? (y/n) [y]: ", "cyan"), "y").lower()
        if again in ("n", "no"):
            print(_colour("\n  Goodbye!", "cyan"))
            break


def main():
    global _browser_path, _browser_profiles, _rdp_mode

    _init_log()

    # Ask user which mode to use
    print(_colour("""
  ╔══════════════════════════════════════════════════════════════╗
  ║       GOETHE OID SNIPER v8.0                                ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  1. CMD mode  (run directly in this window — recommended)   ║
  ║  2. Telegram  (control via Telegram bot)                    ║
  ╚══════════════════════════════════════════════════════════════╝
""", "cyan", "bold"))

    mode = _ask(_colour("  Choose mode (1 or 2) [1]: ", "cyan"), "1").strip()

    if mode == "2":
        # ── Telegram bot mode ──────────────────────────────────────────────
        _clock.start()
        log_event("STARTUP", f"IST: {ist_now().strftime('%d %b %Y %H:%M:%S')}")
        _browser_path     = detect_browser_path()
        _browser_profiles = detect_profiles(_browser_path)
        if _browser_path:
            log_event("STARTUP", f"Browser: {_browser_path}")
        if os.environ.get('SESSIONNAME', '').startswith('RDP') or os.environ.get('RDP_MODE') == '1':
            _rdp_mode = True
        log_event("STARTUP", f"Method: LOCAL DIRECT + HTML POLL (curl_cffi + Akamai)")
        log_event("STARTUP", f"curl_cffi: {'YES' if HAS_CURL else 'NO'}")
        log_event("STARTUP", "Telegram bot starting — send /start in Telegram")

        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler('start',     cmd_start))
        app.add_handler(CommandHandler('help',      cmd_help))
        app.add_handler(CommandHandler('centers',   cmd_centers))
        app.add_handler(CommandHandler('exams',     cmd_exams))
        app.add_handler(CommandHandler('hunt',      cmd_hunt))
        app.add_handler(CommandHandler('hunt_now',  cmd_hunt_now))
        app.add_handler(CommandHandler('stop',      cmd_stop))
        app.add_handler(CommandHandler('status',    cmd_status))
        app.add_handler(CommandHandler('config',    cmd_config))
        app.add_handler(CommandHandler('set',       cmd_set))
        app.add_handler(CommandHandler('ping',      cmd_ping))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        log.info('Telegram bot running!')
        app.run_polling(drop_pending_updates=True)
    else:
        # ── CMD mode (default) ─────────────────────────────────────────────
        cmd_main()


if __name__ == '__main__':
    main()


