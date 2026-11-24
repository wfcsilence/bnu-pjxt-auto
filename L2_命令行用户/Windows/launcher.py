#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评教自动化 · 启动器（L2 命令行版，Windows / macOS 通用）

职责：
  1) 把控制台切成 UTF-8，保证在任意系统语言下中文提示都不乱码
  2) 检测调试端口，未就绪则拉起「专用配置目录」的浏览器
  3) 逐项询问要填写的内容（选项 / 三个填空 / 是否自动提交），确认后执行
  4) 调用 run.py 完成批量填写

用法：python launcher.py      （Windows 由 一键评教.bat 调用）
      python3 launcher.py     （macOS 由 一键评教.command 调用）
退出码：0 正常 / 2 执行出错 / 3 未找到浏览器 / 4 启动失败 / 5 端口超时
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

D_PICK = "好"
D_OPTIONS = ["好", "较好", "一般", "较差", "差"]
D_FILLS = [("需要改进的地方？", "无"), ("突出优点是什么？", "无"),
           ("打多少分？（满分100分）", "90")]


def setup_console():
    """让中文在 cp936 / cp437 / UTF-8 任何控制台里都能正常显示。"""
    if os.name == "nt":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleOutputCP(65001)
            k.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def load_config():
    try:
        with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def answer_spec(cfg):
    """从 config.json 读默认值；缺字段就用内置默认。"""
    ans = cfg.get("answer") or {}
    pick = str(ans.get("pick") or D_PICK)
    options = [str(x) for x in (ans.get("pick_options") or D_OPTIONS)]
    meta = []
    for f in (ans.get("fills") or []):
        if isinstance(f, dict):
            meta.append((str(f.get("label") or "填空"), str(f.get("default", ""))))
        else:
            meta.append(("填空", str(f)))
    return pick, options, (meta or D_FILLS)


def port_open(port):
    s = socket.socket()
    s.settimeout(1.0)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def find_browser():
    if os.name == "nt":
        cands = []
        for base in (os.environ.get("ProgramFiles(x86)"),
                     os.environ.get("ProgramFiles"),
                     os.environ.get("LOCALAPPDATA")):
            if not base:
                continue
            cands.append(os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"))
            cands.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
    else:
        home = os.path.expanduser("~")
        cands = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            home + "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def profile_dir():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "PJAuto", "EdgeProfile")
    return os.path.expanduser("~/Library/Application Support/PJAuto/ChromeProfile")


def launch(browser, port, profile, url):
    args = [browser,
            "--remote-debugging-port=%d" % port,
            "--user-data-dir=%s" % profile,
            "--no-first-run",
            "--no-default-browser-check",
            url or "about:blank"]
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = 0x00000008  # DETACHED_PROCESS，关掉本窗口也不影响浏览器
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(args, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, **kwargs)


# ---------- 交互 ----------

def norm(s):
    """全角数字/标点转半角，去掉首尾空白。"""
    try:
        s = unicodedata.normalize("NFKC", s)
    except Exception:
        pass
    return s.strip()


def ask_raw(prompt):
    """返回用户输入原文；EOF（非交互环境）返回 None。"""
    try:
        return input(prompt)
    except EOFError:
        print()
        return None
    except KeyboardInterrupt:
        print()
        raise


def ask_pick(options):
    print("      选择题（%s）" % "   ".join(
        "%d)%s" % (i + 1, o) for i, o in enumerate(options)))
    for _ in range(3):
        raw = ask_raw("      选哪一项？[1-%d，回车=1 %s]：" % (len(options), options[0]))
        if raw is None:
            print("      未输入，用默认「%s」。" % options[0])
            return options[0]
        v = norm(raw)
        if v == "":
            return options[0]
        if v.isdigit() and 1 <= int(v) <= len(options):
            return options[int(v) - 1]
        if v in options:
            return v
        print("      没有「%s」这一项。请输入编号 1-%d，或直接输入 %s。"
              % (v, len(options), " / ".join(options)))
    print("      多次输入无效，先用默认「%s」。" % options[0])
    return options[0]


def ask_fills(meta):
    vals = []
    print("      填空题共 %d 项（按页面上的顺序）：" % len(meta))
    for i, (label, dflt) in enumerate(meta):
        show = dflt if dflt != "" else "留空"
        raw = ask_raw("       %d. %s [回车=%s]：" % (i + 1, label, show))
        if raw is None:
            vals.append(dflt)
            continue
        v = norm(raw)
        if v == "":
            vals.append(dflt)
        elif v == "-":
            vals.append("")
        else:
            vals.append(v)
    return vals


def score_warn(vals, meta):
    """第 3 个空通常是分数，做一次温和校验（只提示，不阻止）。"""
    idx = None
    for i, (label, _d) in enumerate(meta):
        if "分" in label and ("100" in label or "成绩" in label):
            idx = i
            break
    if idx is None or idx >= len(vals):
        return ""
    v = vals[idx]
    if v == "":
        return "分数那个空是空的，确认页面上允许留空。"
    if not re.fullmatch(r"\d+(\.\d+)?", v):
        return "分数填的是「%s」，不是纯数字，确认这里确实填分数。" % v
    if not (0 <= float(v) <= 100):
        return "分数填的是「%s」，超出 0-100。" % v
    return ""


def ask_confirm():
    raw = ask_raw("      确认开始？输入 Y 回车开始，直接回车取消：")
    if raw is None:
        return False
    return norm(raw).lower() in ("y", "yes")


# ---------- 主流程 ----------

def main():
    setup_console()
    cfg = load_config()
    port = int(cfg.get("port", 9222))
    url = cfg.get("list_url", "")
    d_pick, options, meta = answer_spec(cfg)

    print("=" * 48)
    print("   评教自动化 · 一键批量填写（命令行版）")
    print("=" * 48)
    print()

    # --- 1/4 调试端口 ---
    if port_open(port):
        print("[1/4] 调试端口 %d 已就绪，复用现有浏览器窗口。" % port)
    else:
        browser = find_browser()
        if not browser:
            print("[错误] 没找到 Chrome / Edge 浏览器。")
            print("       macOS 请先安装 Google Chrome 或 Microsoft Edge，")
            print("       Windows 请确认已安装 Edge。")
            return 3
        prof = profile_dir()
        try:
            os.makedirs(prof, exist_ok=True)
        except Exception:
            pass
        print("[1/4] 调试端口未开启，需要先启动专用浏览器窗口。")
        print()
        print("      · 首次使用：在弹出的窗口里登录一次评教系统")
        print("      · 登录态保存在独立目录，以后不用再登录")
        print("      · 与你平时用的浏览器互不影响")
        print()
        ask_raw("      按回车键启动浏览器...")
        try:
            launch(browser, port, prof, url)
        except Exception as e:
            print("[错误] 启动浏览器失败：%s" % e)
            return 4

        print("      等待端口就绪（最多 30 秒）...")
        ready = False
        for i in range(30):
            time.sleep(1)
            if port_open(port):
                print("      端口已就绪（用时 %d 秒）。" % (i + 1))
                ready = True
                break
        if not ready:
            print()
            print("[错误] 30 秒内调试端口仍未就绪。常见原因：")
            print("       · 安全软件 / 终端安全策略拦截了本地调试端口")
            print("       · 浏览器企业策略禁用了远程调试")
            print("       排查：用浏览器打开 http://127.0.0.1:%d/json/version" % port)
            return 5

    # --- 2/4 设定内容 ---
    print()
    print("[2/4] 请设定要填写的内容（直接回车 = 用方括号里的默认值）")
    print()
    pick = ask_pick(options)
    print()
    fills = ask_fills(meta)
    warn = score_warn(fills, meta)

    # --- 3/4 确认 ---
    print()
    print("[3/4] 将要提交的内容")
    print()
    print("      选择题：每题都选「%s」" % pick)
    for (label, _d), v in zip(meta, fills):
        print("      %s %s" % (label, "（留空）" if v == "" else v))
    print()
    print("      评教一经提交无法修改，请再核对一遍。")
    if warn:
        print("      [提醒] %s" % warn)
    print()
    if not ask_confirm():
        print("      已取消，未做任何提交。")
        return 0

    # --- 4/4 执行 ---
    print()
    print("[4/4] 开始批量填写，期间请勿操作那个浏览器窗口...")
    print()
    sys.stdout.flush()
    cmd = [sys.executable, os.path.join(HERE, "run.py"),
           os.path.join(HERE, "config.json"), "--pick", pick]
    for v in fills:
        cmd += ["--fill", v]
    rc = subprocess.call(cmd, cwd=HERE)
    sys.stdout.flush()
    print()
    if rc == 0:
        print("      完成。请到浏览器「已评教」标签核对结果。")
    else:
        print("      [错误] 执行器退出码 %d，请查看上面的提示。" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
