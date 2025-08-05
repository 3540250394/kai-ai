import subprocess
import shlex
import re
from pathlib import Path
from typing import Any, Dict, Callable, List
from utils import get_workspace_path, load_prompt_template, save_to_workspace, initialize_workspace

class Toolkit:
    """A lightweight toolkit holding common coding-utility helpers.

    New tools can be registered dynamically; a small but useful default set is
    provided out-of-the-box for code-centric tasks. Usage:

    ```python
    tk = Toolkit()
    content = tk.call("read_file", "path/to/file.py")
    tk.call("write_file", "out.txt", "hello")
    ```
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._register_builtin_tools()

    # ---------------------------------------------------------------------
    # Registration helpers
    # ---------------------------------------------------------------------

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """Register a tool function by name. Overwrites if already present."""
        self._tools[name] = func

    def call(self, name: str, *args, **kwargs):
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name](*args, **kwargs)

    # ------------------------------------------------------------------
    # Built-in tools (file I/O, directory, search, shell)
    # ------------------------------------------------------------------

    def _register_builtin_tools(self) -> None:
        self.register("read_file", self._read_file)
        self.register("write_file", self._write_file)
        self.register("append_file", self._append_file)
        self.register("list_dir", self._list_dir)
        self.register("grep", self._grep)
        self.register("run_shell", self._run_shell)
        # New workspace and prompt tools
        self.register("save_workspace", self._save_workspace)
        self.register("load_prompt", self._load_prompt)
        self.register("init_workspace", self._init_workspace)
        self.register("create_project", self._create_project)

    # ---------- File helpers ----------
    @staticmethod
    def _read_file(path: str | Path, encoding: str = "utf-8") -> str:
        p = Path(path)
        return p.read_text(encoding=encoding)

    @staticmethod
    def _write_file(path: str | Path, content: str, encoding: str = "utf-8") -> None:
        p = Path(path)
        if not p.is_absolute():
            p = get_workspace_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)

    @staticmethod
    def _append_file(path: str | Path, content: str, encoding: str = "utf-8") -> None:
        p = Path(path)
        if not p.is_absolute():
            p = get_workspace_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding=encoding) as f:
            f.write(content)

    # ---------- Directory ----------
    @staticmethod
    def _list_dir(path: str | Path) -> List[str]:
        p = Path(path)
        return [str(child) for child in p.iterdir()]

    # ---------- Grep-like pattern search ----------
    @staticmethod
    def _grep(path: str | Path, pattern: str, ignore_case: bool = True) -> List[str]:
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(pattern, flags)
        matches: List[str] = []
        p = Path(path)
        if p.is_dir():
            files = p.rglob("*")
        else:
            files = [p]
        for file in files:
            if file.is_file():
                try:
                    for idx, line in enumerate(file.read_text(errors="ignore").splitlines(), 1):
                        if regex.search(line):
                            matches.append(f"{file}:{idx}:{line.strip()}")
                except Exception:
                    continue
        return matches

    # ---------- Shell ----------
    @staticmethod
    def _run_shell(cmd: str, cwd: str | Path | None = None, timeout: int | None = None) -> str:
        """Run a shell command and capture stdout/stderr."""
        proc = subprocess.run(
            shlex.split(cmd),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.stdout + proc.stderr

    # ---------- Workspace Management ----------
    @staticmethod
    def _save_workspace(filename: str, content: str, subdir: str = "drafts") -> str:
        """Save content to workspace with automatic organization."""
        filepath = save_to_workspace(filename, content, subdir)
        return f"文件已保存到工作区: {filepath}"

    @staticmethod
    def _load_prompt(template_name: str = "general") -> str:
        """Load a prompt template by name."""
        return load_prompt_template(template_name)

    @staticmethod
    def _init_workspace() -> str:
        """Initialize workspace structure."""
        initialize_workspace()
        return "工作区已初始化完成"

    @staticmethod
    def _create_project(project_name: str, description: str = "") -> str:
        """Create a new project structure in workspace."""
        project_path = get_workspace_path("projects", project_name)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create basic project structure
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "docs").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # Create README
        readme_content = f"""# {project_name}

{description}

## 项目结构

- `src/` - 源代码
- `docs/` - 文档
- `tests/` - 测试文件

## 开始使用

[项目使用说明]
"""
        (project_path / "README.md").write_text(readme_content, encoding="utf-8")
        
        return f"项目 '{project_name}' 已创建: {project_path}"
