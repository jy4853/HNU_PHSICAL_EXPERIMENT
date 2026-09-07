# -*- coding: utf-8 -*-
"""Tkinter 图形界面 —— 选课工具的桌面端。

选课循环在后台线程运行，通过线程安全的 queue 把日志传回主线程刷新界面。
"""
import json
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from . import core

DONE = object()  # 后台线程结束的哨兵


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("选课助手")
        self.root.geometry("840x660")

        self.parsed = None
        self.selector = None
        self.thread = None
        self.log_q = queue.Queue()

        self._build_ui()
        self._load_default_request()
        self._poll_log()

    # ---------- 界面 ----------
    def _build_ui(self):
        tk.Label(
            self.root,
            text="把浏览器 F12 复制的请求（标头 + 负载）粘贴到下面：",
        ).pack(anchor="w", padx=10, pady=(10, 0))

        self.request_text = scrolledtext.ScrolledText(self.root, height=14, wrap="none")
        self.request_text.pack(fill="x", padx=10, pady=6)

        btn_row = tk.Frame(self.root)
        btn_row.pack(fill="x", padx=10, pady=4)
        self.parse_btn = tk.Button(btn_row, text="解析请求", command=self.parse)
        self.parse_btn.pack(side="left")
        self.start_btn = tk.Button(btn_row, text="开始选课", command=self.start, state="disabled")
        self.start_btn.pack(side="left", padx=6)
        self.stop_btn = tk.Button(btn_row, text="停止", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left")

        self.info_var = tk.StringVar(value="尚未解析。")
        tk.Label(self.root, textvariable=self.info_var, fg="#333").pack(anchor="w", padx=10, pady=4)

        self.log_text = scrolledtext.ScrolledText(self.root, height=16, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_default_request(self):
        try:
            with open(core.REQUEST_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                self.request_text.insert("1.0", content)
        except OSError:
            pass

    def _log(self, line):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _poll_log(self):
        try:
            while True:
                item = self.log_q.get_nowait()
                if item is DONE:
                    self._log("[结束] 选课循环已停止。")
                    self.start_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                else:
                    self._log(item)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log)

    # ---------- 业务 ----------
    def parse(self):
        raw = self.request_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("提示", "请先粘贴请求内容。")
            return
        try:
            url, headers, cookies, data = core.parse_request(raw)
        except ValueError as e:
            messagebox.showerror("解析失败", str(e))
            return
        self.parsed = (url, headers, cookies, data)
        try:
            course = json.loads(data["ObjectIDs"])[0].get("LabName")
        except Exception:
            course = "(未知)"
        self.info_var.set(f"目标课程：{course} ｜ 学号：{data['stuids']} ｜ URL：{url}")
        self.start_btn.configure(state="normal")
        self._log(f"[解析] 已识别课程：{course}")

    def start(self):
        if not self.parsed:
            messagebox.showwarning("提示", "请先解析请求。")
            return
        url, headers, cookies, data = self.parsed
        self.selector = core.Selector(url, headers, cookies, data)
        self._log(f"[开始] 开始选课，间隔 {core.INTERVAL}s ...")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        def on_result(idx, code, ok, msg):
            mark = "[成功]" if ok else ""
            self.log_q.put(f"[{idx:>4}] HTTP {code} {mark} -> {msg}")
        try:
            self.selector.run(on_result)
        except Exception as e:
            self.log_q.put(f"[异常] {e}")
        finally:
            self.log_q.put(DONE)

    def stop(self):
        if self.selector:
            self.selector.stop()
            self.stop_btn.configure(state="disabled")
            self._log("[手动] 已请求停止，将在下一轮循环后停止...")


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    run()
