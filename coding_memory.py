import ast
import pathlib
import json
import networkx as nx
from typing import List

class CodeMemory:
    """Maintain AST & import dependency graph for Python project."""

    def __init__(self, root: str | pathlib.Path = ".") -> None:
        self.root = pathlib.Path(root).resolve()
        self.graph = nx.DiGraph()
        self.reindex()

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def reindex(self) -> None:
        """(Re)build dependency graph for all *.py under root."""
        self.graph.clear()
        for py in self.root.rglob("*.py"):
            try:
                source = py.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py))
            except Exception:
                continue  # skip parse errors
            self.graph.add_node(py, type="file", ast=tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    rel = pathlib.Path(node.module.replace(".", "/") + ".py")
                    dep = (self.root / rel).resolve()
                    if dep.exists():
                        self.graph.add_edge(py, dep)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def who_depends_on(self, file: str | pathlib.Path) -> List[pathlib.Path]:
        file = pathlib.Path(file).resolve()
        return list(self.graph.predecessors(file))

    def to_json(self, out: str | pathlib.Path) -> None:
        data = {
            "edges": [(str(u), str(v)) for u, v in self.graph.edges()],
        }
        pathlib.Path(out).write_text(json.dumps(data, indent=2), encoding="utf-8")
