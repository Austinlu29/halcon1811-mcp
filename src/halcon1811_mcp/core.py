"""Generate visible HDevelop jobs; GUI automation is optional and Windows only."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from typing import Callable


@dataclass(frozen=True)
class Parameters:
    lower: int = 128
    upper: int = 255
    min_area: float = 500
    max_area: float = 100000
    mean_size: int = 3

    def validate(self) -> None:
        if not 0 <= self.lower <= self.upper <= 255:
            raise ValueError("灰度阈值需要满足 0 ≤ 下限 ≤ 上限 ≤ 255。")
        if not all(math.isfinite(x) for x in (self.min_area, self.max_area)):
            raise ValueError("面积必须为有限数值。")
        if not 0 <= self.min_area <= self.max_area:
            raise ValueError("面积需要满足 0 ≤ 最小面积 ≤ 最大面积。")
        if self.mean_size < 1 or self.mean_size > 99 or self.mean_size % 2 != 1:
            raise ValueError("均值滤波窗口需要为 1 到 99 之间的奇数。")


def halcon_string(value: str | Path) -> str:
    """Escape one HDevelop string literal, independently of XML escaping."""
    text = str(value).replace("\\", "/") if isinstance(value, Path) else value
    if any(ord(c) < 32 for c in text):
        raise ValueError("路径或字符串中不能包含控制字符。")
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def create_demo_image(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("L", (640, 480), 35)
    draw = ImageDraw.Draw(image)
    draw.ellipse((90, 100, 230, 240), fill=220)
    draw.ellipse((350, 220, 510, 380), fill=220)
    draw.rectangle((280, 60, 285, 65), fill=220)
    image.save(path)


def build_source(image: Path, job: Path, token: str, p: Parameters) -> str:
    p.validate()
    q = halcon_string
    return "\n".join([
        "* Generated for HALCON 18.11. Run in HDevelop to view the operators.",
        "dev_update_window ('off')",
        "try",
        "    get_system ('version', HalconVersion)",
        f"    read_image (Image, {q(image)})",
        "    count_channels (Image, Channels)",
        "    if (Channels = 3)",
        "        rgb1_to_gray (Image, GrayImage)",
        "    else",
        "        access_channel (Image, GrayImage, 1)",
        "    endif",
        f"    mean_image (GrayImage, FilteredImage, {p.mean_size}, {p.mean_size})",
        f"    threshold (FilteredImage, Region, {p.lower}, {p.upper})",
        "    connection (Region, ConnectedRegions)",
        f"    select_shape (ConnectedRegions, SelectedRegions, 'area', 'and', {p.min_area}, {p.max_area})",
        "    count_obj (SelectedRegions, Number)",
        "    area_center (SelectedRegions, Area, Row, Column)",
        "    get_image_size (Image, Width, Height)",
        "    dev_open_window (0, 0, 640, 480, 'black', WindowHandle)",
        "    dev_set_part (0, 0, Height - 1, Width - 1)",
        "    dev_display (Image)",
        "    dev_set_draw ('margin')",
        "    dev_set_color ('green')",
        "    dev_set_line_width (2)",
        "    dev_display (SelectedRegions)",
        "    dump_window_image (OverlayImage, WindowHandle)",
        f"    write_image (OverlayImage, 'png', 0, {q(job / 'overlay.png')})",
        f"    open_file ({q(job / 'metrics.csv')}, 'output', MetricsHandle)",
        "    fwrite_string (MetricsHandle, 'area,row,column')",
        "    fnew_line (MetricsHandle)",
        "    if (Number > 0)",
        "        for Index := 0 to Number - 1 by 1",
        "            MetricLine := (Area[Index]$'.6f') + ',' + (Row[Index]$'.6f') + ',' + (Column[Index]$'.6f')",
        "            fwrite_string (MetricsHandle, MetricLine)",
        "            fnew_line (MetricsHandle)",
        "        endfor",
        "    endif",
        "    close_file (MetricsHandle)",
        f"    open_file ({q(job / 'version.txt')}, 'output', VersionHandle)",
        "    fwrite_string (VersionHandle, HalconVersion)",
        "    close_file (VersionHandle)",
        "    dev_update_window ('on')",
        "    * Completion is signaled only after all result files are closed.",
        f"    open_file ({q(job / 'complete.txt')}, 'output', CompleteHandle)",
        f"    fwrite_string (CompleteHandle, {q(token)})",
        "    close_file (CompleteHandle)",
        "catch (Exception)",
        f"    open_file ({q(job / 'error.txt')}, 'output', ErrorHandle)",
        "    fwrite_string (ErrorHandle, Exception[0]$'d')",
        "    close_file (ErrorHandle)",
        "    dev_update_window ('on')",
        "endtry",
        "* Window remains open. Inspect Image, SelectedRegions, Area, Row, Column.",
        "",
    ])


def write_hdev(source: str, path: Path) -> None:
    root = ET.Element("hdevelop", file_version="1.1", halcon_version="18.11.0.0")
    procedure = ET.SubElement(root, "procedure", name="main")
    ET.SubElement(procedure, "interface")
    body = ET.SubElement(procedure, "body")
    for line in source.splitlines():
        ET.SubElement(body, "c" if line.lstrip().startswith("*") or not line.strip() else "l").text = line
    ET.SubElement(ET.SubElement(procedure, "docu", id="main"), "parameters")
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def prepare_job(image: str | None, output: Path, p: Parameters) -> dict:
    p.validate()
    input_path = Path(image).expanduser().resolve() if image else None
    if input_path is not None and not input_path.is_file():
        raise ValueError(f"图片不存在：{input_path}")
    token = uuid.uuid4().hex
    job = output.resolve() / token
    job.mkdir(parents=True, exist_ok=False)
    if input_path is None:
        input_path = job / "demo.png"
        create_demo_image(input_path)
    source = build_source(input_path, job, token, p)
    script = job / f"halcon_ui_{token}.hdev"
    write_hdev(source, script)
    (job / "source.txt").write_text(source, encoding="utf-8")
    info = {"token": token, "job_dir": str(job), "script": str(script),
            "image": str(input_path), "parameters": asdict(p),
            "expected_objects": 2 if image is None and p == Parameters() else None}
    (job / "job.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def detect_executable() -> str:
    roots = [os.environ.get("HALCONROOT", ""),
             r"C:\Program Files\MVTec\HALCON-18.11-Steady",
             r"C:\Program Files\MVTec\HALCON-18.11-Progress"]
    for root in roots:
        if root:
            for arch in ("x64-win64", "x86sse2-win32"):
                exe = Path(root) / "bin" / arch / "hdevelop.exe"
                if exe.is_file():
                    return str(exe)
    return ""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return ""


class Controller:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    @staticmethod
    def _window(pid: int, token: str, timeout: float = 20):
        from pywinauto import Desktop

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for window in Desktop(backend="win32").windows(process=pid, visible_only=True):
                if token in window.window_text() and window.is_enabled():
                    return window
            time.sleep(0.2)
        raise RuntimeError("未找到标题包含本次任务编号的程序窗口。检查 HDevelop 的加载错误或授权对话框；也可改用命令行自动运行模式。")

    @staticmethod
    def _send(window, key: str) -> None:
        import win32gui
        from pywinauto.keyboard import send_keys

        window.set_focus()
        if win32gui.GetForegroundWindow() != window.handle:
            raise RuntimeError("HDevelop 未获得前台焦点，已取消发送按键。")
        send_keys(key)

    def run(self, exe: str, image: str | None, output: Path, p: Parameters,
            mode: str = "commandline", timeout: float = 60,
            notify: Callable[[str], None] = lambda text: None) -> dict:
        if os.name != "nt":
            raise RuntimeError("界面执行需要 Windows。")
        executable = Path(exe).expanduser().resolve()
        if not executable.is_file() or executable.name.lower() != "hdevelop.exe":
            raise ValueError("请选择 HALCON 18.11 的 hdevelop.exe。")
        if mode not in ("commandline", "keyboard"):
            raise ValueError("执行模式只能为 commandline 或 keyboard。")
        if not math.isfinite(timeout) or not 1 <= timeout <= 600:
            raise ValueError("超时需要在 1 到 600 秒之间。")
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("已有任务正在运行，请等待结束。")
        self._cancel.clear()
        process = None
        info = None
        try:
            info = prepare_job(image, output, p)
            job = Path(info["job_dir"])
            notify(f"已生成算子程序：{info['script']}")
            command = [str(executable)]
            if mode == "commandline":
                command.append("-run")
            command.append(info["script"])
            process = subprocess.Popen(command, cwd=executable.parent)
            info["pid"] = process.pid
            notify("已启动独立 HDevelop 窗口，等待算子执行。")
            deadline = time.monotonic() + timeout
            if mode == "keyboard":
                window = self._window(process.pid, info["token"], min(timeout, 20))
                if self._cancel.is_set():
                    raise InterruptedError("任务已取消。")
                # A fresh script starts at the first line, so F2 is unnecessary.
                self._send(window, "{F5}")
                notify("已向本次任务窗口发送 F5。")
            while True:
                if self._cancel.is_set():
                    raise InterruptedError("任务已取消。")
                if read_text(job / "error.txt"):
                    raise RuntimeError(f"HALCON 返回错误代码 {read_text(job / 'error.txt')}，请在 HDevelop 中查看失败行。")
                if read_text(job / "complete.txt") == info["token"]:
                    if not (job / "overlay.png").is_file() or not (job / "metrics.csv").is_file():
                        raise RuntimeError("发现完成标记，但结果文件缺失。")
                    break
                if process.poll() is not None:
                    raise RuntimeError("HDevelop 已退出且没有完成标记，请检查授权或加载错误。")
                if time.monotonic() >= deadline:
                    raise TimeoutError("等待执行超时，请查看 HDevelop 中是否有对话框、断点或授权错误。")
                time.sleep(0.2)
            import csv
            with (job / "metrics.csv").open(encoding="utf-8", newline="") as stream:
                objects = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]
            result = {**info, "status": "completed", "halcon_version": read_text(job / "version.txt"),
                      "object_count": len(objects), "objects": objects,
                      "overlay": str(job / "overlay.png"), "metrics": str(job / "metrics.csv")}
            if not result["halcon_version"].startswith("18.11"):
                result["warning"] = "实际运行版本并非 18.11，请重新选择可执行文件。"
            if info["expected_objects"] is not None and len(objects) != info["expected_objects"]:
                result["warning"] = "内置演示的默认参数预期检测到 2 个目标，请检查实际执行结果。"
            try:
                window = self._window(process.pid, info["token"], 1)
                window.capture_as_image().save(job / "hdevelop.png")
                result["window_screenshot"] = str(job / "hdevelop.png")
            except Exception as error:
                result["screenshot_warning"] = str(error)
            (job / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            notify(f"完成：检测到 {len(objects)} 个目标。HDevelop 窗口保留供查看。")
            return result
        except Exception as error:
            if info:
                failure = {**info, "status": "cancelled" if isinstance(error, InterruptedError) else "failed", "error": str(error)}
                if process and process.poll() is None:
                    try:
                        self._send(self._window(process.pid, info["token"], 1), "{F9}")
                        failure["stop_requested"] = True
                    except Exception as stop_error:
                        failure["stop_warning"] = str(stop_error)
                Path(info["job_dir"], "result.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding="utf-8")
                notify(f"失败信息保存在：{info['job_dir']}")
            raise
        finally:
            self._lock.release()
