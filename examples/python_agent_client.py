"""MCP bridge for an Agent's already-generated HDevelop source file."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def unpack(result) -> dict:
    if result.isError:
        detail = "\n".join(item.text for item in result.content if item.type == "text")
        raise RuntimeError(detail or "MCP tool returned an error")
    if result.structuredContent is not None:
        payload = result.structuredContent
        return payload.get("result", payload)
    for item in result.content:
        if item.type == "text":
            return json.loads(item.text)
    raise RuntimeError("MCP tool returned no JSON data")


async def connect_and_run(args) -> None:
    env = dict(os.environ)
    if args.hdevelop:
        env["HALCON_HDEVELOP_EXE"] = str(Path(args.hdevelop).expanduser().resolve())
    if args.data_dir:
        env["HALCON_MCP_DATA_DIR"] = str(Path(args.data_dir).expanduser().resolve())
        # Keep this example's outputs under the explicitly selected data directory.
        env["HALCON_PROGRAM_DIR"] = str(Path(args.data_dir).expanduser().resolve() / "programs")
    settings = StdioServerParameters(command=sys.executable, args=["-m", "halcon1811_mcp"], env=env)
    async with stdio_client(settings) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            environment = unpack(await session.call_tool("halcon_environment", {}))
            print(json.dumps({"tools": [tool.name for tool in tools.tools], "environment": environment},
                             ensure_ascii=False, indent=2))
            if args.inspect_only:
                return
            code = args.code_file.read_text(encoding="utf-8-sig")
            analysis = args.analysis_file.read_text(encoding="utf-8-sig") if args.analysis_file else ""
            saved = unpack(await session.call_tool("halcon_save_program", {
                "name": args.name, "code": code, "request": args.request, "analysis": analysis,
                "open_window": not args.save_only and not args.execute,
            }))
            print(json.dumps({"saved_program": saved}, ensure_ascii=False, indent=2))
            if saved.get("open_error"):
                raise RuntimeError(f"Program was saved, but HDevelop did not open: {saved['open_error']}")
            if not args.execute:
                return
            execution = unpack(await session.call_tool("halcon_run_program", {"program_id": saved["program_id"]}))
            deadline = time.monotonic() + args.timeout
            while True:
                status = unpack(await session.call_tool("halcon_execution_status", {
                    "program_id": saved["program_id"], "execution_id": execution["execution_id"],
                }))
                if status["status"] == "completed":
                    print(json.dumps({"execution": status}, ensure_ascii=False, indent=2))
                    return
                if status["status"] in ("failed", "closed_without_completion"):
                    raise RuntimeError(json.dumps(status, ensure_ascii=False))
                if time.monotonic() >= deadline:
                    raise TimeoutError("Execution is still running or waiting in HDevelop: " + json.dumps(status, ensure_ascii=False))
                await asyncio.sleep(1)


def main() -> None:
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hdevelop", help="Absolute path to hdevelop.exe; otherwise use the environment")
    parser.add_argument("--data-dir", type=Path, help="Root directory for generated output")
    parser.add_argument("--inspect-only", action="store_true", help="List tools and environment without saving or opening")
    parser.add_argument("--code-file", type=Path, help="UTF-8 plain HDevelop main source from your Agent")
    parser.add_argument("--name", default="agent_program")
    parser.add_argument("--request", default="")
    parser.add_argument("--analysis-file", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--save-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if not args.inspect_only and args.code_file is None:
        parser.error("--code-file is required unless --inspect-only is used")
    if not 1 <= args.timeout <= 600:
        parser.error("--timeout must be between 1 and 600 seconds")
    try:
        asyncio.run(connect_and_run(args))
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
