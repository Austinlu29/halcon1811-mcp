"""Windows GUI and CLI entry point for the HALCON 18.11 prototype."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import queue
import sys
import threading

from .core import Controller, Parameters, detect_executable, prepare_job

from .paths import data_directory

ROOT = data_directory()


def gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    controller = Controller()
    events: queue.Queue = queue.Queue()
    root = tk.Tk()
    root.title("HALCON 18.11 自动算子原型")
    root.geometry("900x620")
    panel = ttk.Frame(root, padding=16)
    panel.pack(fill="both", expand=True)
    panel.columnconfigure(1, weight=1)
    panel.rowconfigure(9, weight=1)
    exe = tk.StringVar(value=detect_executable())
    image = tk.StringVar()
    mode = tk.StringVar(value="commandline")
    values = {"lower": tk.StringVar(value="128"), "upper": tk.StringVar(value="255"),
              "min_area": tk.StringVar(value="500"), "max_area": tk.StringVar(value="100000"),
              "mean_size": tk.StringVar(value="3")}

    def browse(variable, types):
        selected = filedialog.askopenfilename(filetypes=types)
        if selected:
            variable.set(selected)

    ttk.Label(panel, text="HALCON 18.11 hdevelop.exe").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(panel, textvariable=exe).grid(row=0, column=1, sticky="ew", padx=8)
    ttk.Button(panel, text="选择", command=lambda: browse(exe, [("HDevelop", "hdevelop.exe")])).grid(row=0, column=2)
    ttk.Label(panel, text="图片（留空使用演示图）").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(panel, textvariable=image).grid(row=1, column=1, sticky="ew", padx=8)
    ttk.Button(panel, text="选择", command=lambda: browse(image, [("图片", "*.png *.bmp *.jpg *.jpeg *.tif *.tiff"), ("所有文件", "*.*")])).grid(row=1, column=2)
    labels = [("lower", "灰度下限"), ("upper", "灰度上限"), ("min_area", "最小面积（像素）"),
              ("max_area", "最大面积（像素）"), ("mean_size", "均值滤波窗口（奇数）")]
    for row, (name, label) in enumerate(labels, start=2):
        ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(panel, textvariable=values[name]).grid(row=row, column=1, sticky="ew", padx=8)
    ttk.Label(panel, text="运行方式").grid(row=7, column=0, sticky="w")
    ttk.Combobox(panel, textvariable=mode, values=["commandline", "keyboard"], state="readonly").grid(row=7, column=1, sticky="ew", padx=8)
    buttons = ttk.Frame(panel)
    buttons.grid(row=8, column=0, columnspan=3, sticky="w", pady=12)
    log = tk.Text(panel, wrap="word", state="disabled")
    log.grid(row=9, column=0, columnspan=3, sticky="nsew")
    busy = False

    def params() -> Parameters:
        return Parameters(lower=int(values["lower"].get()), upper=int(values["upper"].get()),
                          min_area=float(values["min_area"].get()), max_area=float(values["max_area"].get()),
                          mean_size=int(values["mean_size"].get()))

    def append(text):
        log.configure(state="normal")
        log.insert("end", text + "\n")
        log.see("end")
        log.configure(state="disabled")

    def preview():
        try:
            job = prepare_job(image.get().strip() or None, ROOT / "runs", params())
            append(f"仅生成脚本：{job['script']}")
            append(Path(job["job_dir"], "source.txt").read_text(encoding="utf-8"))
        except Exception as error:
            messagebox.showerror("生成失败", str(error))

    def start():
        nonlocal busy
        if busy:
            return
        try:
            settings = params()
            settings.validate()
        except Exception as error:
            messagebox.showerror("参数错误", str(error))
            return
        captured_exe, captured_image, captured_mode = exe.get().strip(), image.get().strip() or None, mode.get()
        busy = True
        run_button.configure(state="disabled")
        preview_button.configure(state="disabled")
        cancel_button.configure(state="normal")

        def worker():
            try:
                result = controller.run(captured_exe, captured_image, ROOT / "runs", settings,
                                        mode=captured_mode, notify=lambda text: events.put(("log", text)))
                events.put(("log", json.dumps(result, ensure_ascii=False, indent=2)))
            except Exception as error:
                events.put(("log", str(error)))
            finally:
                events.put(("done", ""))

        threading.Thread(target=worker, daemon=True).start()

    preview_button = ttk.Button(buttons, text="生成并预览算子", command=preview)
    preview_button.pack(side="left", padx=4)
    run_button = ttk.Button(buttons, text="自动打开 HDevelop 并执行", command=start)
    run_button.pack(side="left", padx=4)
    cancel_button = ttk.Button(buttons, text="请求停止", command=controller.cancel, state="disabled")
    cancel_button.pack(side="left", padx=4)
    append("每次任务打开独立 HDevelop 窗口；完成后窗口保留。")
    append("commandline：通过 -run 加载执行；keyboard：定位本次任务窗口并发送 F5。")
    append("默认演示图预期检测到两个大目标，小噪点被面积筛选排除。")

    def poll():
        nonlocal busy
        while True:
            try:
                kind, text = events.get_nowait()
            except queue.Empty:
                break
            if kind == "done":
                busy = False
                run_button.configure(state="normal")
                preview_button.configure(state="normal")
                cancel_button.configure(state="disabled")
            else:
                append(text)
        root.after(100, poll)

    def close():
        if busy:
            append("任务运行中；请先请求停止并等待结束。")
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    poll()
    root.mainloop()


def main() -> None:
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="HALCON 18.11 HDevelop 可视化自动运行原型")
    parser.add_argument("action", choices=["gui", "generate", "run"], nargs="?", default="gui")
    parser.add_argument("--exe", default=detect_executable())
    parser.add_argument("--image", default=None)
    parser.add_argument("--output", type=Path, default=ROOT / "runs")
    parser.add_argument("--lower", type=int, default=128)
    parser.add_argument("--upper", type=int, default=255)
    parser.add_argument("--min-area", type=float, default=500)
    parser.add_argument("--max-area", type=float, default=100000)
    parser.add_argument("--mean-size", type=int, default=3)
    parser.add_argument("--mode", choices=["commandline", "keyboard"], default="commandline")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    if args.action == "gui":
        gui()
        return
    p = Parameters(args.lower, args.upper, args.min_area, args.max_area, args.mean_size)
    try:
        if args.action == "generate":
            result = prepare_job(args.image, args.output, p)
        else:
            result = Controller().run(args.exe, args.image, args.output, p, args.mode, args.timeout,
                                      notify=lambda text: print(text, flush=True))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError, TimeoutError, InterruptedError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
