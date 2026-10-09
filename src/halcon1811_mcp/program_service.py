"""Persist AI-authored HDevelop main programs and open them in HALCON 18.11."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import uuid

from .core import detect_executable, halcon_string, read_text, write_hdev


class PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "br", "li", "tr", "h1", "h2", "h3", "pre"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalized_code(code: str) -> str:
    code = code.replace("\r\n", "\n").strip()
    if code.startswith("```") or code.startswith("<"):
        raise ValueError("请提供 HDevelop main 的纯代码，不要传 Markdown 围栏或 XML。")
    if not code or len(code) > 200000 or "\x00" in code:
        raise ValueError("代码不能为空、包含 NUL 或超过 200000 字符。")
    if re.search(r"^\s*procedure\s+", code, re.MULTILINE | re.IGNORECASE):
        raise ValueError("当前工具接收 main 代码；外部过程可直接调用，本地过程定义需另行处理。")
    return code + "\n"


def program_name(name: str) -> str:
    name = name.strip()
    if name.lower().endswith(".hdev"):
        name = name[:-5]
    if not re.fullmatch(r"[\w\- ]{1,80}", name, flags=re.UNICODE):
        raise ValueError("程序名需要为 1–80 个文字、数字、下划线、空格或连字符，不能包含路径。")
    return name


class ProgramService:
    def __init__(self, root: Path, executable: str | None = None):
        self.root = root.resolve()
        self.executable = executable or os.environ.get("HALCON_HDEVELOP_EXE") or detect_executable()
        self.processes: dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()

    @property
    def docs(self) -> Path:
        if self.executable:
            return Path(self.executable).resolve().parents[2] / "doc" / "html" / "reference" / "operators"
        return Path(os.environ.get("HALCONROOT", "C:/Program Files/MVTec/HALCON-18.11-Steady")) / "doc" / "html" / "reference" / "operators"

    def environment(self) -> dict:
        return {"target_version": "18.11", "hdevelop": self.executable,
                "installed": bool(self.executable and Path(self.executable).is_file()),
                "save_directory": str(self.root), "operator_docs": str(self.docs),
                "operator_docs_available": self.docs.is_dir(),
                "workflow": "聊天输入需求 -> AI分析并写代码 -> MCP自动保存.hdev -> HDevelop加载"}

    def operator_help(self, name: str) -> dict:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,100}", name):
            raise ValueError("算子名只能包含小写英文、数字和下划线。")
        path = self.docs / f"{name}.html"
        if not path.is_file():
            return {"operator": name, "found": False, "target_version": "18.11"}
        parser = PlainHTML()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        text = re.sub(r"[ \t]+", " ", "".join(parser.parts))
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        return {"operator": name, "found": True, "path": str(path),
                "text": text[:24000], "truncated": len(text) > 24000}

    def _directory(self, identifier: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}", identifier):
            raise ValueError("程序或执行编号必须是工具返回的 32 位编号。")
        path = self.root / identifier
        if not (path / "program.json").is_file():
            raise ValueError("没有找到对应的已保存程序。")
        return path

    @staticmethod
    def _json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _launch(self, script: Path, run: bool = False) -> subprocess.Popen:
        exe = Path(self.executable) if self.executable else None
        if os.name != "nt" or exe is None or not exe.is_file():
            raise RuntimeError("没有找到 Windows HDevelop，请设置 HALCON_HDEVELOP_EXE。程序已保存。")
        command = [str(exe)] + (["-run"] if run else []) + [str(script)]
        return subprocess.Popen(command, cwd=exe.parent)

    def save(self, name: str, code: str, request: str = "", analysis: str = "", open_window: bool = True) -> dict:
        name, code = program_name(name), normalized_code(code)
        identifier = uuid.uuid4().hex
        directory = self.root / identifier
        directory.mkdir(parents=True, exist_ok=False)
        script = directory / f"{name}.hdev"
        write_hdev(code, script)
        source = directory / f"{name}.txt"
        source.write_text(code, encoding="utf-8")
        notes = directory / "analysis.md"
        notes.write_text(f"# 操作需求\n\n{request}\n\n# AI 分析\n\n{analysis}\n", encoding="utf-8")
        operators = sorted(set(re.findall(r"^\s*([a-z][a-z0-9_]*)\s*\(", code, flags=re.MULTILINE)))
        controls = {"if", "elseif", "while", "until", "catch", "switch"}
        missing = [operator for operator in operators if operator not in controls and not (self.docs / f"{operator}.html").is_file()]
        record = {"program_id": identifier, "name": name, "target_version": "18.11",
                  "saved": True, "script": str(script), "source": str(source), "analysis_file": str(notes),
                  "request": request, "created_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
                  "operators_without_local_reference": missing, "opened": False}
        self._write_json(directory / "program.json", record)
        if open_window:
            try:
                process = self._launch(script)
                self.processes[identifier] = process
                record.update(opened=True, pid=process.pid)
            except (OSError, RuntimeError) as error:
                record["open_error"] = str(error)
            self._write_json(directory / "program.json", record)
        return record

    def open(self, identifier: str) -> dict:
        directory = self._directory(identifier)
        record = self._json(directory / "program.json")
        process = self._launch(Path(record["script"]))
        self.processes[identifier] = process
        record.update(opened=True, pid=process.pid)
        record.pop("open_error", None)
        self._write_json(directory / "program.json", record)
        return record

    def list_programs(self, limit: int = 10) -> list[dict]:
        if not 1 <= limit <= 50:
            raise ValueError("数量需要在 1 到 50 之间。")
        if not self.root.exists():
            return []
        records = sorted(self.root.glob("*/program.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return [{key: value for key, value in self._json(path).items()
                 if key in ("program_id", "name", "script", "created_at", "opened")} for path in records[:limit]]

    def run(self, identifier: str) -> dict:
        directory = self._directory(identifier)
        record = self._json(directory / "program.json")
        # Use the HDevelop file as authority so manually saved edits are respected.
        import xml.etree.ElementTree as ET
        body = ET.parse(record["script"]).find("./procedure[@name='main']/body")
        if body is None:
            raise ValueError("已保存程序缺少 main。")
        source = "\n".join(element.text or "" for element in body)
        token = uuid.uuid4().hex
        execution = directory / "executions" / token
        execution.mkdir(parents=True, exist_ok=False)
        prefix = "MCP" + token[:8]
        complete, error_file = execution / "complete.txt", execution / "error.txt"
        wrapped = "\n".join([
            "* MCP execution copy; the saved source program is preserved.",
            "try", source,
            f"open_file ({halcon_string(complete)}, 'output', {prefix}Done)",
            f"fwrite_string ({prefix}Done, {halcon_string(token)})",
            f"close_file ({prefix}Done)",
            f"catch ({prefix}Exception)",
            f"open_file ({halcon_string(error_file)}, 'output', {prefix}Error)",
            f"fwrite_string ({prefix}Error, {prefix}Exception[0]$'d')",
            f"close_file ({prefix}Error)", "endtry", "",
        ])
        script = execution / f"run_{token}.hdev"
        write_hdev(wrapped, script)
        process = self._launch(script, run=True)
        with self.lock:
            self.processes[token] = process
        status = {"program_id": identifier, "execution_id": token, "pid": process.pid,
                  "execution_script": str(script), "saved_script": record["script"], "status": "running"}
        self._write_json(execution / "execution.json", status)
        return status

    def status(self, identifier: str, token: str) -> dict:
        directory = self._directory(identifier)
        if not re.fullmatch(r"[0-9a-f]{32}", token):
            raise ValueError("执行编号格式不正确。")
        execution = directory / "executions" / token
        path = execution / "execution.json"
        if not path.is_file():
            raise ValueError("没有找到对应执行。")
        result = self._json(path)
        error = read_text(execution / "error.txt")
        if error:
            result.update(status="failed", halcon_error_code=error)
        elif read_text(execution / "complete.txt") == token:
            result.update(status="completed")
        else:
            process = self.processes.get(token)
            if process is not None and process.poll() is not None:
                result.update(status="closed_without_completion", exit_code=process.returncode)
            else:
                result.update(status="running_or_waiting")
        self._write_json(path, result)
        return result
