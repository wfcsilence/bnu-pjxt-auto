#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDP 引擎 —— 纯标准库实现，零第三方依赖。
只暴露两个原语：evaluate(js) 和 navigate(url)。
通过 Chrome DevTools Protocol 连接已启动的浏览器，在页面上下文执行 JS。
"""
import base64
import json
import os
import socket
import struct
import time
import urllib.request
from urllib.parse import urlparse


class CDPError(Exception):
    pass


class CDP:
    def __init__(self, port=9222, url_key=None, timeout=10):
        self.port = port
        self.timeout = timeout
        self._id = 0
        self._buf = b""
        self._sock = None
        self._connect(url_key)

    def _connect(self, url_key):
        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:%d/json" % self.port, timeout=5
            ) as r:
                targets = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            raise CDPError(
                "无法连接浏览器调试端口 %d：%s\n"
                "请先关闭所有 Edge/Chrome 窗口，再用调试端口重新启动。" % (self.port, e)
            )

        pages = [t for t in targets if t.get("type") == "page"]
        if url_key:
            hit = [t for t in pages if url_key in t.get("url", "")]
            # 命中就用命中的；没命中但有其他标签时回退到第一个 http 页面，
            # 由调用方 navigate 到目标地址（避免“标签被关掉”就彻底报错）
            if hit:
                pages = hit
            else:
                http_pages = [t for t in pages if t.get("url", "").startswith("http")]
                pages = http_pages or pages
        if not pages:
            raise CDPError("浏览器里没有任何可用标签页，请重新启动调试浏览器")

        ws_url = pages[0].get("webSocketDebuggerUrl")
        if not ws_url:
            raise CDPError("页面缺少 webSocketDebuggerUrl")
        u = urlparse(ws_url)
        host = u.hostname or "127.0.0.1"
        port = u.port or self.port
        path = u.path or "/"

        self._sock = socket.create_connection((host, port), timeout=self.timeout)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            "GET %s HTTP/1.1\r\n"
            "Host: %s:%d\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
            % (path, host, port, key)
        )
        self._sock.sendall(req.encode("ascii"))
        self._read_http_response()

    def _read_http_response(self):
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise CDPError("WebSocket 握手失败：连接被关闭")
            data += chunk
        head, rest = data.split(b"\r\n\r\n", 1)
        if b"101" not in head.split(b"\r\n")[0]:
            raise CDPError("WebSocket 握手失败：\n" + head.decode("utf-8", "replace"))
        self._buf = rest

    def _recv_exact(self, n):
        while len(self._buf) < n:
            chunk = self._sock.recv(max(4096, n - len(self._buf)))
            if not chunk:
                raise CDPError("连接被关闭")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def _send_frame(self, text, opcode=0x1):
        data = text.encode("utf-8")
        mask = os.urandom(4)
        n = len(data)
        header = bytearray([0x80 | opcode])
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", n))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", n))
        header.extend(mask)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self._sock.sendall(bytes(header) + masked)

    def _recv_frame(self):
        h = self._recv_exact(2)
        opcode = h[0] & 0x0F
        length = h[1] & 0x7F
        masked = bool(h[1] & 0x80)
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else None
        data = self._recv_exact(length)
        if mask:
            data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        return opcode, data

    def _call(self, method, params=None, timeout=30):
        self._id += 1
        mid = self._id
        self._send_frame(json.dumps(
            {"id": mid, "method": method, "params": params or {}},
            ensure_ascii=False,
        ))
        deadline = time.time() + timeout
        self._sock.settimeout(min(self.timeout, max(0.1, deadline - time.time())))
        while time.time() < deadline:
            try:
                opcode, data = self._recv_frame()
            except socket.timeout:
                continue
            if opcode == 0x9:  # ping -> pong
                self._send_frame(data.decode("utf-8", "replace"), opcode=0xA)
                continue
            if opcode == 0x8:
                raise CDPError("浏览器关闭了调试连接")
            if opcode not in (0x1, 0x2):
                continue
            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            if msg.get("id") != mid:
                continue  # 事件消息
            if "error" in msg:
                raise CDPError(str(msg["error"]))
            return msg.get("result", {})
        raise CDPError("CDP 调用超时：%s" % method)

    def evaluate(self, expression, timeout=30):
        """在页面上下文执行 JS，返回其返回值（需 JSON 可序列化）"""
        result = self._call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            timeout,
        )
        if result.get("exceptionDetails"):
            d = result["exceptionDetails"]
            desc = d.get("exception", {}).get("description") or d.get("text", "")
            raise CDPError("JS 异常：%s" % desc)
        return result.get("result", {}).get("value")

    def navigate(self, url, wait=2.0):
        self._call("Page.navigate", {"url": url})
        time.sleep(wait)

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
