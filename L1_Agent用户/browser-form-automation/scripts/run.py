#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用配方执行器：读一份 JSON 配方，循环完成批量表单提交。

用法：
  python run.py recipes/bnu-pjxt.json
  python run.py recipes/bnu-pjxt.json --pick 较好 --fill 无 --fill 无 --fill 95

--pick / --fill 会覆盖配方 answer 里的默认值；不传就用配方里的默认值。
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import CDP, CDPError


def load_recipe(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def answer_spec(recipe):
    """返回 (默认选项, 选项列表, [(填空标签, 填空默认值), ...])。"""
    ans = recipe.get("answer") or {}
    pick = str(ans.get("pick") or "好")
    options = ans.get("pick_options") or []
    fills = []
    for f in (ans.get("fills") or []):
        if isinstance(f, dict):
            fills.append((str(f.get("label") or "填空"), str(f.get("default", ""))))
        else:
            fills.append(("填空", str(f)))
    return pick, options, fills


def resolve_answer(recipe, pick=None, fills=None):
    """把「用户给的」和「配方默认的」合并成最终要填的内容。"""
    d_pick, _options, meta = answer_spec(recipe)
    defaults = [d for _l, d in meta]
    n = len(meta) if meta else 3

    final_pick = str(pick).strip() if pick is not None else d_pick
    if not final_pick:
        final_pick = d_pick

    vals = [str(x).strip() for x in (fills or [])]
    # 约定：单个 "-" 表示这个空留白，与 launcher 的输入规则一致
    vals = ["" if v == "-" else v for v in vals]
    if not vals:
        vals = defaults[:]
    for i in range(len(vals), n):
        vals.append(defaults[i] if i < len(defaults) else "")
    vals = vals[:n] if n else vals
    return final_pick, vals


def render_js(js, pick, fills):
    """把配方里的 __PICK__ / __FILLS__ 替换成安全的 JS 字面量。"""
    pick_lit = json.dumps(pick, ensure_ascii=False)
    fills_lit = json.dumps(list(fills), ensure_ascii=False)
    out = {}
    for k, v in js.items():
        if isinstance(v, str):
            v = v.replace("__PICK__", pick_lit).replace("__FILLS__", fills_lit)
        out[k] = v
    return out


def safe_eval(c, expr, tries=3, delay=1.2):
    """页面跳转瞬间执行上下文可能失效，重试几次。"""
    last = None
    for _ in range(tries):
        try:
            return c.evaluate(expr)
        except CDPError as e:
            last = e
            time.sleep(delay)
    raise last


def wait_ready(c, js, attempts=20, delay=1.5):
    """等待列表页可用，同时把「未登录」和「加载慢」区分开。"""
    expr = js.get("ready")
    if not expr:
        return True, {}
    info = {}
    for _ in range(attempts):
        try:
            info = safe_eval(c, expr, tries=2, delay=0.8) or {}
        except CDPError:
            info = {}
        if info.get("login"):
            raise CDPError(
                "调试浏览器里没有登录态。\n"
                "请在弹出的调试浏览器窗口里登录一次评教系统，"
                "确认能看到课程列表后重新运行本脚本。"
            )
        if info.get("hasList"):
            return True, info
        time.sleep(delay)
    return False, info


def run(recipe_path, pick=None, fills=None):
    recipe = load_recipe(recipe_path)
    final_pick, final_fills = resolve_answer(recipe, pick, fills)
    js = render_js(recipe["js"], final_pick, final_fills)

    # 先亮出要填什么，再动手（提交不可撤销，这一步不该藏着）
    print("填写方案：选择题「%s」；填空 %s" % (
        final_pick, " / ".join(("（空）" if v == "" else v) for v in final_fills)), flush=True)
    print(flush=True)

    c = CDP(port=recipe.get("port", 9222), url_key=recipe.get("site_key"))
    log = []
    done = 0
    skipped = set()
    max_iter = recipe.get("max_iterations", 30)
    wait_click = recipe.get("wait_after_click_sec", 2.5)
    wait_submit = recipe.get("wait_after_submit_sec", 3.0)
    nav_wait = recipe.get("wait_after_nav_sec", 2.0)
    list_url = recipe.get("list_url")

    try:
        if list_url:
            c.navigate(list_url, wait=nav_wait)

        ok, info = wait_ready(c, js)
        if not ok:
            raise CDPError(
                "列表页加载超时：%s\n请确认调试浏览器里已登录并能打开评教列表页。"
                % (info.get("url") or "未知地址")
            )

        for i in range(max_iter):
            info = safe_eval(c, js["list"])
            if not isinstance(info, dict) or "n" not in info:
                log.append("iter%d: 列表探测异常 %r" % (i, info))
                break
            cnt = info["n"]
            if cnt == 0:
                log.append("iter%d: 待办已清空" % i)
                break

            names = info.get("names", []) or []
            cand = [k for k, n in enumerate(names) if n not in skipped]
            if not cand:
                log.append("iter%d: 剩余项已全部跳过（可能都是已填写状态）" % i)
                break
            idx = cand[0]
            teacher = names[idx] if idx < len(names) else "?"

            safe_eval(c, js["click"].replace("__INDEX__", str(idx)))
            time.sleep(wait_click)

            chk = safe_eval(c, js["check"])
            if not isinstance(chk, dict) or chk.get("forms", 0) == 0:
                log.append("iter%d: %s 无可填表单（已填写？），跳过" % (i, teacher))
                skipped.add(teacher)
                if list_url:
                    c.navigate(list_url, wait=nav_wait)
                continue

            result = safe_eval(c, js["fill_submit"])
            log.append("iter%d: %s -> %s" % (i, teacher, str(result)[:120]))
            time.sleep(wait_submit)

            after = safe_eval(c, js["list"])
            if isinstance(after, dict) and after.get("n", cnt) < cnt:
                done += 1
            elif list_url:
                c.navigate(list_url, wait=nav_wait)
                after2 = safe_eval(c, js["list"])
                if isinstance(after2, dict) and after2.get("n", cnt) < cnt:
                    done += 1
                else:
                    log.append("iter%d: 数量未减少，疑似提交失败，停止" % i)
                    break
            else:
                log.append("iter%d: 数量未减少，疑似提交失败，停止" % i)
                break

            if list_url:
                c.navigate(list_url, wait=nav_wait)

        final = safe_eval(c, js["list"])
        log.append("完成提交=%d 跳过=%d 剩余待办=%s" % (
            done, len(skipped), final.get("n") if isinstance(final, dict) else "?"))
    finally:
        c.close()

    return log, done, final_pick, final_fills


def main():
    ap = argparse.ArgumentParser(
        description="按配方批量填写并提交表单（需要浏览器已用调试端口启动并登录）")
    ap.add_argument("recipe", help="配方 JSON 路径")
    ap.add_argument("--pick", help="选择题选哪一项（覆盖配方 answer.pick）")
    ap.add_argument("--fill", action="append", metavar="文本",
                    help="填空题内容，按顺序重复传；有几个空就传几次")
    args = ap.parse_args()

    try:
        log, done, _pick, _fills = run(args.recipe, args.pick, args.fill)
    except CDPError as e:
        print("\n错误：%s" % e)
        sys.exit(2)
    except FileNotFoundError as e:
        print("\n错误：找不到配方文件 %s" % e.filename)
        sys.exit(1)

    print()
    for line in log:
        print(line)
    print("\n共提交 %d 项" % done)


if __name__ == "__main__":
    main()
