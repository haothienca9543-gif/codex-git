#!/usr/bin/env python3
"""Lấy thời gian đăng tải video TikTok từ URL video công khai.

Ví dụ:
    python check_tiktok_upload_time.py "https://www.tiktok.com/@user/video/7481234567890123456"
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="ignore")


def extract_create_time(html: str) -> int:
    patterns = [
        r'"createTime":"(\d{9,12})"',
        r'"createTime":(\d{9,12})',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return int(match.group(1))

    next_data_match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if next_data_match:
        payload = json.loads(next_data_match.group(1))
        candidate = _find_key(payload, "createTime")
        if isinstance(candidate, str) and candidate.isdigit():
            return int(candidate)
        if isinstance(candidate, int):
            return candidate

    raise ValueError("Không tìm thấy createTime trong trang TikTok.")


def _find_key(obj: object, key: str) -> object | None:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = _find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_key(item, key)
            if found is not None:
                return found
    return None


def format_timestamp(ts: int, timezone: str) -> str:
    tz = ZoneInfo(timezone)
    dt_obj = dt.datetime.fromtimestamp(ts, tz=tz)
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S %Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Kiểm tra thời gian đăng tải video TikTok từ URL công khai."
    )
    parser.add_argument("url", help="URL video TikTok")
    parser.add_argument(
        "--timezone",
        default="Asia/Ho_Chi_Minh",
        help="Múi giờ để hiển thị thời gian (mặc định: Asia/Ho_Chi_Minh)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        html = fetch_html(args.url)
        create_time = extract_create_time(html)
        pretty_time = format_timestamp(create_time, args.timezone)
    except urllib.error.HTTPError as exc:
        print(f"Lỗi HTTP khi gọi TikTok: {exc}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Không thể kết nối TikTok: {exc}", file=sys.stderr)
        return 1
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Không đọc được thời gian đăng video: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # fallback để CLI không crash thô
        print(f"Lỗi không xác định: {exc}", file=sys.stderr)
        return 1

    print(f"UNIX createTime: {create_time}")
    print(f"Thời gian đăng: {pretty_time}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
