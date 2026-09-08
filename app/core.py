# -*- coding: utf-8 -*-
"""选课助手 —— 核心逻辑。

由最初的命令行脚本重构而来，把「解析请求」和「选课循环」拆成可复用组件，
供命令行（cli.py）和图形界面（gui.py）共同调用。本模块不含任何敏感信息。
"""
import json
import os
import re
import sys
import threading
import time
from urllib.parse import unquote

import requests

# ==================== 常量 ====================

INTERVAL = 0.15  # 每次请求间隔（秒）

DEFAULT_HEADERS = {
    "Accept": "application/json, text/javascript, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0"
    ),
    "X-Requested-With": "XMLHttpRequest",
}

# 数据目录：源码运行 = 项目根目录；打包成 exe 后 = exe 所在目录
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUEST_FILE = os.path.join(APP_DIR, "request.txt")


# ==================== 解析 ====================

def load_defaults():
    """从 config.py（gitignore）读取服务器地址、Cookie 和课程，用于兜底。"""
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    try:
        import config  # noqa: F401  （config.py 由用户自行维护，不提交）
        return (
            getattr(config, "HOST", ""),
            getattr(config, "PATH", ""),
            getattr(config, "DEFAULT_COOKIES", {}),
            getattr(config, "DEFAULT_OBJECT_IDS", []),
        )
    except Exception:
        return "", "", {}, []


def extract_json_array(text):
    """从任意文本中提取第一个合法 JSON 数组（自动兼容 URL 编码）。"""
    candidates = [text]
    try:
        candidates.append(unquote(text))
    except Exception:
        pass
    for cand in candidates:
        i = cand.find("[")
        while i != -1:
            try:
                obj, _ = json.JSONDecoder().raw_decode(cand[i:])
                if isinstance(obj, list):
                    return obj
            except (json.JSONDecodeError, ValueError):
                pass
            i = cand.find("[", i + 1)
    return None


def _referer(host, path):
    """由接口路径推导来源页（取路径的上级目录）。"""
    return f"http://{host}{os.path.dirname(path)}"


def split_request(content):
    """把浏览器复制的整段请求按「第一个空行」拆成 (标头, 负载)。

    标头 = 请求行 + Header；负载 = 请求体（ObjectIDs 的 JSON 数组）。
    没有空行时，整段都当作标头，负载为空。
    """
    content = (content or "").replace("\r\n", "\n")
    header, _, body = content.partition("\n\n")
    return header.strip(), body.strip()


def parse_request(raw, body=None):
    """解析浏览器复制的请求，返回 (url, headers, cookies, data)。

    body 为 None：raw 同时包含标头和负载（合并格式，命令行方式）。
    body 有值：raw 仅含标头（请求行 + Header），body 为负载（请求体）。
    """
    raw = (raw or "").strip()
    header_text = raw
    payload_text = body if body is not None else raw
    host_default, path_default, _, _ = load_defaults()

    # URL 路径：POST /path HTTP/1.1
    path = path_default
    m = re.search(r"^(?:POST|GET)\s+(\S+)\s+HTTP", header_text, re.MULTILINE | re.IGNORECASE)
    if m:
        path = m.group(1)

    # host
    host = host_default
    mh = re.search(r"^(?:[Hh]ost)\s*:\s*(\S+)", header_text, re.MULTILINE)
    if mh:
        host = mh.group(1).rstrip("/")

    # Cookie：找含 COOKIES_KEY_USERNAME= 的那一行
    cookies = {}
    for line in header_text.splitlines():
        if "COOKIES_KEY_USERNAME=" in line:
            line = re.sub(r"^[Cc]ookie\s*:\s*", "", line).strip()
            for pair in line.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    cookies[k.strip()] = v.strip()
            break

    # 课程信息（ObjectIDs 的 JSON 数组）
    obj_ids = extract_json_array(payload_text)
    if not obj_ids:
        raise ValueError("未找到课程信息的 JSON 数组（ObjectIDs），请确认已粘贴负载")

    student_id = obj_ids[0].get("StudentID", cookies.get("COOKIES_KEY_USERNAME", ""))

    data = {
        "ObjectIDs": json.dumps(obj_ids, ensure_ascii=False, separators=(",", ":")),
        "isBatch": "0",
        "stuids": student_id,
    }

    headers = dict(DEFAULT_HEADERS)
    headers["Origin"] = f"http://{host}"
    headers["Referer"] = _referer(host, path)

    return f"http://{host}{path}", headers, cookies, data


def build_default_data():
    """用 config.py 里的默认配置构造 (url, headers, cookies, data)；无配置返回 None。"""
    host, path, cookies, obj_ids = load_defaults()
    if not obj_ids:
        return None

    student_id = obj_ids[0].get("StudentID", cookies.get("COOKIES_KEY_USERNAME", ""))
    data = {
        "ObjectIDs": json.dumps(obj_ids, ensure_ascii=False, separators=(",", ":")),
        "isBatch": "0",
        "stuids": student_id,
    }
    headers = dict(DEFAULT_HEADERS)
    headers["Origin"] = f"http://{host}"
    headers["Referer"] = _referer(host, path)
    url = f"http://{host}{path}"
    return url, headers, cookies, data


# ==================== 选课 ====================

def parse_result(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return False, text.strip()[:120] or "(空响应)"
    if data.get("IsSuccess"):
        return True, ""
    return False, data.get("ErrorInfo") or data.get("DataInfo") or "(无错误信息)"


class Selector:
    """选课循环。应在独立线程中运行，通过回调上报进度，通过 stop() 停止。"""

    def __init__(self, url, headers, cookies, data, interval=INTERVAL):
        self.url = url
        self.headers = headers
        self.cookies = cookies
        self.data = data
        self.interval = interval
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self, on_result=None):
        """循环提交选课请求。on_result(index, http_code, ok, msg) 每轮回调一次；成功返回 True。"""
        session = requests.Session()
        session.cookies.update(self.cookies)

        i = 0
        while not self._stop.is_set():
            i += 1
            try:
                resp = session.post(self.url, data=self.data,
                                    headers=self.headers, timeout=30)
                code, text = resp.status_code, resp.text
            except requests.RequestException as e:
                if on_result:
                    on_result(i, None, False, f"请求异常：{e}")
                time.sleep(self.interval)
                continue

            ok, msg = parse_result(text)
            if on_result:
                on_result(i, code, ok, msg)

            if ok:
                if on_result:
                    on_result(i, code, True, "选课成功！")
                return True

            time.sleep(self.interval)

        return False
