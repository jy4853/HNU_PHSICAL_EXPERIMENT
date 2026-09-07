# -*- coding: utf-8 -*-
"""命令行入口 —— 与最初的单文件脚本等价。

用法（三选一）：
  1. 文件方式（推荐）：把浏览器复制的请求存到 request.txt（项目根目录），运行
         python -m app.cli
  2. 指定文件：python -m app.cli my_request.txt
  3. 交互方式：直接运行，按提示粘贴请求内容，单独一行输入 END 结束
  4. 都没有：使用 config.py 里的「默认配置」（默认课程 + 当前 Cookie）
"""
import json
import sys

from . import core


def load_raw():
    # 1. 命令行文件参数
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            return f.read()
    # 2. 项目根目录的 request.txt
    try:
        with open(core.REQUEST_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        if content.strip():
            return content
    except OSError:
        pass
    # 3. 交互粘贴
    print("请粘贴浏览器复制的请求（标头 + 负载），完成后单独一行输入 END 并回车：")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def main():
    raw = load_raw().strip()

    if raw:
        try:
            url, headers, cookies, data = core.parse_request(raw)
        except ValueError as e:
            print(f"解析失败：{e}")
            return
    else:
        built = core.build_default_data()
        if not built:
            print("没有可用的请求或默认配置，请提供 request.txt 或 config.py。")
            return
        url, headers, cookies, data = built

    try:
        course = json.loads(data["ObjectIDs"])[0].get("LabName")
    except Exception:
        course = "(未知)"

    print(f"目标课程：{course}")
    print(f"学号：{data['stuids']}")
    print(f"URL：{url}")
    print(f"开始选课（间隔 {core.INTERVAL}s，Ctrl+C 停止）...\n")

    selector = core.Selector(url, headers, cookies, data)

    def on_result(idx, code, ok, msg):
        mark = "[成功]" if ok else ""
        print(f"[{idx:>4}] HTTP {code} {mark} -> {msg}")

    try:
        selector.run(on_result)
    except KeyboardInterrupt:
        print("\n已手动停止。")


if __name__ == "__main__":
    main()
