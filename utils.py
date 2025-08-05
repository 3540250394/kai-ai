import json
import uuid
import time
import os
from pathlib import Path
from typing import Any, Dict, List

__all__ = [
    "print_with_prefix",
    "generate_task_id",
    "truncate_history",
    "load_config",
    "save_config",
    "get_output_path",
    "get_workspace_path",
    "get_prompt_path",
    "load_prompt_template",
    "save_to_workspace",
    "initialize_workspace",
]

# ----------------- 打印辅助 -----------------

def _timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def print_with_prefix(prefix: str, message: str, tag: str = "info") -> None:
    """统一控制台输出格式。仅使用基本 print，兼容 Windows PowerShell。"""
    print(f"[{_timestamp()}] [{tag.upper()}] {prefix}: {message}")

# ----------------- ID & 历史 -----------------

def generate_task_id() -> str:
    """生成简短唯一任务 ID"""
    return uuid.uuid4().hex[:8]

def truncate_history(history: List[Dict[str, Any]], max_messages: int = 50) -> List[Dict[str, Any]]:
    """简单按条数裁剪对话历史，保留最新 max_messages 条。"""
    if len(history) <= max_messages:
        return history
    return history[-max_messages:]

# ----------------- 配置管理 -----------------

_DEFAULT_CONFIG = {
    "prompt_dir": "prompts",
    "history_file": ".morph_history",
    "log_file": ".morph.log",
    "todo_file": ".todos.json",
    "output_dir": "outputs",
    "workspace_dir": "workspace",
    "default_model": "ZhipuAI/GLM-4.5",
    "auto_save_workspace": True,
    "prompt_templates": {
        "coding": "coding_system.txt",
        "general": "prompt.txt"
    }
}

_CONFIG_FILE = Path(os.getenv("MORPH_CONFIG", ".morph_config.json"))


def load_config() -> Dict[str, Any]:
    """加载 JSON 配置文件，不存在则返回默认配置。"""
    if _CONFIG_FILE.exists():
        try:
            return {**_DEFAULT_CONFIG, **json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return _DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> None:
    """保存配置到 JSON 文件。"""
    try:
        _CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print_with_prefix("警告", f"保存配置失败: {e}", "warning")

# ----------------- 输出目录 -----------------

def get_output_path(*parts: str) -> Path:
    """Return absolute Path inside configured output_dir, ensuring directory exists."""
    cfg = load_config()
    base = Path(cfg.get("output_dir", "outputs"))
    base.mkdir(parents=True, exist_ok=True)
    p = base.joinpath(*parts)
    return p

# ----------------- 工作区目录 -----------------

def get_workspace_path(*parts: str) -> Path:
    """Return path inside configurable workspace_dir (source generation area)."""
    cfg = load_config()
    base = Path(cfg.get("workspace_dir", "workspace"))
    base.mkdir(parents=True, exist_ok=True)
    p = base.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

# ----------------- 提示管理 -----------------

def get_prompt_path(*parts: str) -> Path:
    """Return path inside configurable prompt_dir."""
    cfg = load_config()
    base = Path(cfg.get("prompt_dir", "prompts"))
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    p = base.joinpath(*parts)
    return p

def load_prompt_template(template_name: str = "general") -> str:
    """Load a prompt template by name."""
    cfg = load_config()
    templates = cfg.get("prompt_templates", {})
    
    if template_name in templates:
        prompt_file = templates[template_name]
        prompt_path = get_prompt_path(prompt_file)
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
    
    # Fallback to direct file lookup
    prompt_path = get_prompt_path(f"{template_name}.txt")
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    
    return f"# Template '{template_name}' not found"

def save_to_workspace(filename: str, content: str, subdir: str = "") -> Path:
    """Save content to workspace with automatic organization."""
    if subdir:
        filepath = get_workspace_path(subdir, filename)
    else:
        filepath = get_workspace_path(filename)
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    
    print_with_prefix("工作区", f"文件已保存: {filepath}", "success")
    return filepath

def initialize_workspace() -> None:
    """Initialize workspace structure with default directories."""
    cfg = load_config()
    workspace_base = Path(cfg.get("workspace_dir", "workspace"))
    
    # Create standard subdirectories
    subdirs = ["projects", "drafts", "outputs", "temp", "archive"]
    for subdir in subdirs:
        (workspace_base / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create a README if it doesn't exist
    readme_path = workspace_base / "README.md"
    if not readme_path.exists():
        readme_content = """# KAI 工作区

这是 KAI 的工作区目录，用于存储生成的代码、文档和项目文件。

## 目录结构

- `projects/` - 完整项目
- `drafts/` - 草稿和临时文件  
- `outputs/` - 输出文件
- `temp/` - 临时文件
- `archive/` - 归档文件

## 使用方式

所有通过 KAI 生成的文件都会自动保存到相应的子目录中。
"""
        readme_path.write_text(readme_content, encoding="utf-8")
