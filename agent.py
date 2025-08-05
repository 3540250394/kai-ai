from typing import List, Dict, Any, Optional
import os
import time
import json
import concurrent.futures
# --- 兼容脚本直接运行的导入兜底 ---
try:
    from .subagent import SubAgent  # type: ignore
    from .tools import Toolkit  # type: ignore
    from .utils import (
        print_with_prefix, generate_task_id,
        truncate_history, load_config
    )
except ImportError:  # 当没有父包时
    from subagent import SubAgent  # type: ignore
    from tools import Toolkit  # type: ignore
    from utils import (
        print_with_prefix, generate_task_id,
        truncate_history, load_config
    )
from pathlib import Path
from openai import OpenAI

DEFAULT_SYSTEM_PROMPT = "You are Morph, a cell-splitting AI assistant."

class MorphAgent:
    """通用 Morph Agent，负责基础消息处理与子-agent 调度。"""
    def __init__(self):
        # 工具箱（可由子类扩展注册）
        self.tools = Toolkit()
        # 系统配置
        self.config = load_config()
        # 加载系统提示词
        prompt_dir = Path(self.config.get("prompt_dir", "prompts"))
        prompt_file = prompt_dir / "prompt.txt"
        try:
            if prompt_file.exists():
                system_prompt = prompt_file.read_text(encoding="utf-8")
            else:
                system_prompt = DEFAULT_SYSTEM_PROMPT
        except Exception:
            system_prompt = DEFAULT_SYSTEM_PROMPT
        # 会话历史，首条为 system prompt
        self.conversation_history: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        # 初始化外部大模型客户端（硬编码 ModelScope）
        self.client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1',
            api_key='ms-e0e57607-fbcb-4be2-8d2e-6a4768907423',  # ModelScope Token (硬编码)
        )

    # ---------- 通用命令与消息处理 ----------
    def handle_command(self, user_input: str) -> bool:
        """占位：处理 MorphAgent 级别命令。返回 True 表示已处理。"""
        return False

    def _stream_chat(self) -> str:
        """调用外部模型，使用流式输出，返回完整助手回复文本"""
        response = self.client.chat.completions.create(
            model='ZhipuAI/GLM-4.5',
            messages=self.conversation_history,
            stream=True
        )
        collected = []
        for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
            collected.append(delta)
        print()  # 换行
        return "".join(collected)

    def process_message(self, user_input: str):
        """重写：发送到模型并流式打印回复"""
        self.conversation_history.append({"role": "user", "content": user_input})
        assistant_reply = self._stream_chat()
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})

    # ---------- 子 agent 分裂 ----------
    def split_subagents(self, num_agents: int, task_templates: List[str]) -> List[Dict[str, Any]]:
        """并行执行子 agent 任务，返回结果列表。"""
        results: List[Dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_agents) as executor:
            futures = [
                executor.submit(SubAgent(template).run)
                for template in task_templates
            ]
            for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
                try:
                    res = future.result()
                    results.append({"task_id": f"T{idx}", "status": "success", "result": res})
                except Exception as exc:
                    results.append({"task_id": f"T{idx}", "status": "error", "error": str(exc)})
        return results

class CodingAgent(MorphAgent):
    """代码专用Agent调度室，负责代码相关任务处理"""
    def __init__(self):
        super().__init__()
        self.code_projects = {}  # 跟踪代码项目 {project_id: {name, path, tasks}}
        self.code_templates = self._load_code_templates()
        self.initialize_coding_tools()

    def _load_code_templates(self) -> Dict[str, str]:
        """加载代码生成模板"""
        return {
            "python_function": "def {name}({params}):\n    \"\"\"{docstring}\"\"\"\n    {body}",
            "unit_test": "import unittest\n\nclass Test{name}(unittest.TestCase):\n    {tests}",
            "api_doc": "# {name} API\n\n## 功能描述\n{description}\n\n## 请求参数\n{params}\n\n## 返回值\n{returns}"
        }

    def initialize_coding_tools(self):
        """初始化代码专用工具"""
        # 扩展工具集
        self.tools.register_tool("code_analyze", self._tool_code_analyze)
        self.tools.register_tool("code_generate", self._tool_code_generate)
        self.tools.register_tool("unit_test", self._tool_unit_test)
        self.tools.register_tool("project_init", self._tool_project_init)

    def _tool_code_analyze(self, params: Dict[str, Any]) -> str:
        """代码分析工具"""
        file_path = params.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return f"错误: 文件不存在 - {file_path}"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read(10000)  # 限制读取大小

            # 简单分析
            lines = len(code.splitlines())
            functions = len([l for l in code.splitlines() if l.strip().startswith("def ")])
            classes = len([l for l in code.splitlines() if l.strip().startswith("class ")])
            imports = len([l for l in code.splitlines() if l.strip().startswith("import ") or l.strip().startswith("from ")])

            return (f"代码分析结果:\n"
                    f"文件: {file_path}\n"
                    f"行数: {lines}\n"
                    f"函数数量: {functions}\n"
                    f"类数量: {classes}\n"
                    f"导入语句: {imports}")
        except Exception as e:
            return f"分析失败: {str(e)}"

    def _tool_code_generate(self, params: Dict[str, Any]) -> str:
        """代码生成工具"""
        template_type = params.get("type")
        if template_type not in self.code_templates:
            return f"错误: 不支持的模板类型 - {template_type}"

        try:
            template = self.code_templates[template_type]
            generated = template.format(**params)
            return f"生成的{template_type}:\n```python\n{generated}\n```"
        except KeyError as e:
            return f"模板参数缺失: {str(e)}"
        except Exception as e:
            return f"生成失败: {str(e)}"

    def _tool_unit_test(self, params: Dict[str, Any]) -> str:
        """单元测试生成工具"""
        function_name = params.get("function_name")
        if not function_name:
            return "错误: 必须提供函数名"

        tests = []
        for i, test_case in enumerate(params.get("test_cases", [])):
            input_data = test_case.get("input")
            expected = test_case.get("expected")
            tests.append(f"def test_case_{i+1}(self):\n    result = {function_name}({input_data})\n    self.assertEqual(result, {expected})")

        if not tests:
            return "错误: 未提供测试用例"

        return self._tool_code_generate({
            "type": "unit_test",
            "name": function_name.capitalize(),
            "tests": "\n    ".join(tests)
        })

    def _tool_project_init(self, params: Dict[str, Any]) -> str:
        """项目初始化工具"""
        project_name = params.get("name")
        project_path = params.get("path", project_name)
        
        if not project_name:
            return "错误: 必须提供项目名称"

        try:
            # 创建项目目录
            os.makedirs(project_path, exist_ok=True)
            
            # 创建基础结构
            structure = [
                f"{project_path}/__init__.py",
                f"{project_path}/main.py",
                f"{project_path}/utils.py",
                f"{project_path}/tests/",
                f"{project_path}/tests/__init__.py",
                f"{project_path}/requirements.txt",
                f"{project_path}/README.md"
            ]

            for item in structure:
                if item.endswith("/"):
                    os.makedirs(item, exist_ok=True)
                else:
                    with open(item, "w", encoding="utf-8") as f:
                        if "main.py" in item:
                            f.write("def main():\n    print(\"Hello, World!\")\n\nif __name__ == \"__main__\":\n    main()")
                        elif "requirements.txt" in item:
                            f.write("# Project dependencies\n")
                        elif "README.md" in item:
                            f.write(f"# {project_name}\n\nA new project created with Morph Coding Agent")

            project_id = generate_task_id()
            self.code_projects[project_id] = {
                "name": project_name,
                "path": project_path,
                "created": time.time(),
                "tasks": []
            }

            return f"项目初始化成功:\nID: {project_id}\n路径: {os.path.abspath(project_path)}"
        except Exception as e:
            return f"项目初始化失败: {str(e)}"

    def split_coding_subagents(self, task_type: str, num_agents: int, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """分裂代码专用子agent"""
        if project_id and project_id not in self.code_projects:
            raise ValueError(f"项目ID不存在: {project_id}")

        task_templates = self._generate_coding_tasks(task_type, num_agents, project_id)
        return super().split_subagents(num_agents, task_templates)

    def _generate_coding_tasks(self, task_type: str, num_agents: int, project_id: Optional[str]) -> List[str]:
        """生成代码任务模板"""
        task_generators = {
            "code_review": self._generate_review_tasks,
            "refactor": self._generate_refactor_tasks,
            "test": self._generate_test_tasks,
            "document": self._generate_document_tasks,
            "debug": self._generate_debug_tasks
        }

        if task_type not in task_generators:
            raise ValueError(f"不支持的任务类型: {task_type}")

        return task_generators[task_type](num_agents, project_id)

    def _generate_review_tasks(self, num_agents: int, project_id: Optional[str]) -> List[str]:
        """生成代码审查任务"""
        tasks = [
            f"审查代码规范与风格，检查PEP8合规性",
            f"分析代码性能瓶颈，提出优化建议",
            f"识别潜在安全漏洞与风险点",
            f"评估代码可读性与可维护性",
            f"检查错误处理与边界情况覆盖"
        ]
        return tasks[:num_agents]

    def _generate_refactor_tasks(self, num_agents: int, project_id: Optional[str]) -> List[str]:
        """生成重构任务"""
        tasks = [
            f"重构函数与类结构，提升代码复用性",
            f"优化变量与函数命名，提高可读性",
            f"简化复杂逻辑，拆分大型函数",
            f"消除代码重复，提取公共功能",
            f"优化导入结构，减少循环依赖"
        ]
        return tasks[:num_agents]

    def _generate_test_tasks(self, num_agents: int, project_id: Optional[str]) -> List[str]:
        """生成测试任务"""
        tasks = [
            f"编写单元测试，覆盖核心功能",
            f"设计集成测试，验证模块交互",
            f"创建边界条件与异常测试用例",
            f"实现性能测试，建立基准指标",
            f"生成测试报告与覆盖率分析"
        ]
        return tasks[:num_agents]

    def _generate_document_tasks(self, num_agents: int, project_id: Optional[str]) -> List[str]:
        """生成文档任务"""
        tasks = [
            f"编写API文档，说明函数与类用法",
            f"创建项目 README，介绍整体功能",
            f"生成开发指南，指导环境配置与开发流程",
            f"编写用户手册，说明系统使用方法",
            f"整理架构设计文档，描述系统结构"
        ]
        return tasks[:num_agents]

    def _generate_debug_tasks(self, num_agents: int, project_id: Optional[str]) -> List[str]:
        """生成调试任务"""
        tasks = [
            f"定位运行时错误，分析堆栈跟踪",
            f"排查逻辑错误，验证算法正确性",
            f"检查数据处理错误，验证输入输出",
            f"分析性能问题，识别瓶颈代码",
            f"验证并发场景下的线程安全问题"
        ]
        return tasks[:num_agents]

    def handle_coding_command(self, user_input: str) -> bool:
        """处理代码专用命令"""
        if user_input.startswith("!code"):
            parts = user_input.split()
            if len(parts) < 2:
                print_with_prefix("错误", "代码命令格式: !code <操作> [参数]", "error")
                return True

            operation = parts[1]
            if operation == "init":
                self._handle_code_init(parts[2:])
            elif operation == "review":
                self._handle_code_review(parts[2:])
            elif operation == "generate":
                self._handle_code_generate(parts[2:])
            elif operation == "test":
                self._handle_code_test(parts[2:])
            elif operation == "projects":
                self._list_projects()
            else:
                print_with_prefix("错误", f"未知代码操作: {operation}", "error")
            return True
        return False

    def _handle_code_init(self, args: List[str]):
        """处理项目初始化命令"""
        if not args:
            print_with_prefix("错误", "用法: !code init <项目名> [路径]", "error")
            return

        project_name = args[0]
        path = args[1] if len(args) > 1 else project_name
        
        result = self.tools.execute("project_init", {
            "name": project_name,
            "path": path
        })
        print_with_prefix("代码助手", result, "agent")

    def _handle_code_review(self, args: List[str]):
        """处理代码审查命令"""
        if not args or not args[0].isdigit():
            print_with_prefix("错误", "用法: !code review <子agent数量> [项目ID]", "error")
            return

        try:
            num_agents = int(args[0])
            project_id = args[1] if len(args) > 1 else None
            
            print_with_prefix("代码助手", f"开始代码审查，分裂 {num_agents} 个子agent...", "agent")
            results = self.split_coding_subagents("code_review", num_agents, project_id)
            
            print_with_prefix("代码助手", "=== 代码审查结果汇总 ===", "agent")
            for res in results:
                print(f"\n任务ID: {res['task_id']}")
                print(f"结果: {res['result'] if res['status'] == 'success' else res['error']}")
                
        except Exception as e:
            print_with_prefix("错误", f"代码审查失败: {str(e)}", "error")

    def _handle_code_generate(self, args: List[str]):
        """处理代码生成命令"""
        if len(args) < 2:
            print_with_prefix("错误", "用法: !code generate <类型> <参数json>", "error")
            print_with_prefix("提示", "支持类型: python_function, unit_test, api_doc", "system")
            return

        try:
            template_type = args[0]
            params = json.loads(" ".join(args[1:]))
            
            result = self.tools.execute("code_generate", {
                "type": template_type,
                **params
            })
            print_with_prefix("代码助手", result, "agent")
            
        except json.JSONDecodeError:
            print_with_prefix("错误", "参数必须是有效的JSON", "error")
        except Exception as e:
            print_with_prefix("错误", f"代码生成失败: {str(e)}", "error")

    def _handle_code_test(self, args: List[str]):
        """处理测试生成命令"""
        if len(args) < 1:
            print_with_prefix("错误", "用法: !code test <函数名> <测试用例json>", "error")
            return

        try:
            function_name = args[0]
            test_cases = json.loads(" ".join(args[1:]))
            
            result = self.tools.execute("unit_test", {
                "function_name": function_name,
                "test_cases": test_cases
            })
            print_with_prefix("代码助手", result, "agent")
            
        except json.JSONDecodeError:
            print_with_prefix("错误", "测试用例必须是有效的JSON数组", "error")
        except Exception as e:
            print_with_prefix("错误", f"测试生成失败: {str(e)}", "error")

    def _list_projects(self):
        """列出所有项目"""
        if not self.code_projects:
            print_with_prefix("代码助手", "没有已创建的项目", "agent")
            return

        print_with_prefix("代码助手", "=== 项目列表 ===", "agent")
        for project_id, info in self.code_projects.items():
            print(f"ID: {project_id}")
            print(f"名称: {info['name']}")
            print(f"路径: {info['path']}")
            print(f"创建时间: {time.strftime('%Y-%m-%d %H:%M', time.localtime(info['created']))}")
            print(f"任务数: {len(info['tasks'])}")
            print("---")

    def process_message(self, user_input: str):
        """重写消息处理，优先处理代码命令"""
        if self.handle_coding_command(user_input):
            return
        super().process_message(user_input)