from typing import Any, Dict

class SubAgent:
    """简化版 SubAgent，仅占位满足导入需求。后续可扩展实际逻辑。"""

    def __init__(self, task: str = "", context: Dict[str, Any] | None = None):
        self.task = task
        self.context = context or {}

    def run(self) -> str:
        """执行子任务，默认仅回显。"""
        return f"SubAgent completed task: {self.task}"
