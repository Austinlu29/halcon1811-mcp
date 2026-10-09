"""Optional stdio MCP adapter using the official MCP SDK 1.x API."""
from pathlib import Path
import os

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from .core import Controller, Parameters, detect_executable, prepare_job
from .program_service import ProgramService
from .paths import data_directory

mcp = FastMCP("HALCON 18.11 HDevelop UI", instructions=(
    "用户在聊天中输入 HALCON 操作需求时，由聊天 AI 分析需求并编写兼容 18.11 的 HDevelop main 代码。"
    "先用 halcon_environment 和 halcon_operator_help 检查安装与关键算子参数，然后调用 halcon_save_program 自动保存并在 HDevelop 加载。"
    "工具接收纯代码，分析过程另存文件。仅生成并保存时不要运行；用户要求执行时再调用 halcon_run_program 并查询 halcon_execution_status。"
    "缺少必要图片路径或参数时澄清；每次保存保留独立版本，并在回复中给出绝对 .hdev 路径。"
))
controller = Controller()
output = data_directory() / "runs"
programs = ProgramService(Path(os.environ.get("HALCON_PROGRAM_DIR", str(data_directory() / "programs"))))
readonly = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
localwrite = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)


@mcp.tool(annotations=readonly)
def halcon_environment() -> dict:
    """Check the installed HDevelop, target version, local operator docs and save directory."""
    return programs.environment()


@mcp.tool(annotations=readonly)
def halcon_operator_help(operator: str) -> dict:
    """Read a local HALCON 18.11 operator reference before generating its code."""
    return programs.operator_help(operator)


@mcp.tool(annotations=localwrite)
def halcon_save_program(name: str, code: str, request: str = "", analysis: str = "", open_window: bool = True) -> dict:
    """Automatically save AI-authored HDevelop main code and optionally open it visibly.

    code must be plain HDevelop code, without Markdown fences or XML. Saves .hdev,
    plain code and the request/analysis in a new version directory. Does not run it.
    """
    return programs.save(name, code, request, analysis, open_window)


@mcp.tool(annotations=localwrite)
def halcon_open_program(program_id: str) -> dict:
    """Load a program previously saved by this MCP service in a visible HDevelop window."""
    return programs.open(program_id)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True))
def halcon_run_program(program_id: str) -> dict:
    """Execute a saved program in HDevelop when the user requests execution.

    Returns execution_id immediately. Query halcon_execution_status for completion
    or a HALCON error. stop/interactive operators may wait for input in HDevelop.
    """
    return programs.run(program_id)


@mcp.tool(annotations=readonly)
def halcon_execution_status(program_id: str, execution_id: str) -> dict:
    """Return completed, failed, running_or_waiting or closed_without_completion."""
    return programs.status(program_id, execution_id)


@mcp.tool(annotations=readonly)
def halcon_list_programs(limit: int = 10) -> list[dict]:
    """List recently saved program versions with their absolute .hdev paths."""
    return programs.list_programs(limit)


@mcp.tool()
def generate_threshold_program(image_path: str = "", lower: int = 128, upper: int = 255,
                               min_area: float = 500, max_area: float = 100000,
                               mean_size: int = 3) -> dict:
    """Generate a visible HDevelop program; empty image_path creates a demo image."""
    return prepare_job(image_path or None, output, Parameters(lower, upper, min_area, max_area, mean_size))


@mcp.tool()
def run_threshold_demo(image_path: str = "", lower: int = 128, upper: int = 255,
                       min_area: float = 500, max_area: float = 100000,
                       mean_size: int = 3, timeout_seconds: float = 60) -> dict:
    """Open a separate visible HDevelop window and run threshold/region operators.

    Uses HALCON_HDEVELOP_EXE or HALCONROOT. Requires a logged-in Windows desktop
    and a development license. Leaves HDevelop open for inspection.
    """
    executable = os.environ.get("HALCON_HDEVELOP_EXE") or detect_executable()
    if not executable:
        raise ValueError("请将 HALCON_HDEVELOP_EXE 设置为 HALCON 18.11 的 hdevelop.exe 路径。")
    return controller.run(executable, image_path or None, output,
                          Parameters(lower, upper, min_area, max_area, mean_size),
                          timeout=timeout_seconds)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
