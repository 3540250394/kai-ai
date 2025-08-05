import sys
import signal
import os
try:
    import readline  # Unix
except ImportError:  # Windows fallback
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None  # minimal fallback; history features disabled
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
# --- 相对导入失败时退回本地目录导入 ---
try:
    from .agent import MorphAgent
    from .utils import print_with_prefix, load_config, save_config
except ImportError:
    from agent import MorphAgent  # type: ignore
    from utils import print_with_prefix, load_config, save_config  # type: ignore
import json
import yaml
from pathlib import Path
import pathlib as _pl
from utils import get_workspace_path
get_workspace_path()    # 不带参数仅创建目录
# --- 允许脚本直接运行 ---
if __package__ is None or __package__ == "":
    # 将上级目录加入 sys.path，支持相对导入
    sys.path.append(str(_pl.Path(__file__).resolve().parent))

DEFAULT_GLOBAL_PROMPT = """You are Morph, a cell-splitting AI assistant. Follow SOLID, KISS, be proactive, philosophically guided by Dialectics. Default language: English for code, Chinese for explanations."""

class MorphCLIController:
    """Morph CLI主控制室，负责用户交互与系统管理"""
    def __init__(self):
        self.agent = MorphAgent()
        self.config = load_config()
        self.command_history = []
        self.running = True
        # --- 增强：日志与持久化 ---
        self.log_file = Path(self.config.get("log_file", ".morph.log"))
        self.todo_file = Path(self.config.get("todo_file", ".todos.json"))
        self.todos: List[Dict[str, Any]] = self.load_todos()
        self.init_signal_handlers()
        self.init_readline()
        # 自动生成提示词目录与文件
        self.ensure_prompt_files()

    def init_signal_handlers(self):
        """初始化信号处理器"""
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_terminate)

    def init_readline(self):
        """初始化命令行历史记录"""
        if readline is not None:
            readline.set_history_length(1000)
            try:
                readline.read_history_file(self.config.get("history_file", ".morph_history"))
            except FileNotFoundError:
                pass

    def handle_interrupt(self, signum, frame):
        """处理Ctrl+C中断"""
        print_with_prefix("系统", "\n检测到中断信号，输入!exit完全退出", "system")

    def handle_terminate(self, signum, frame):
        """处理程序终止信号"""
        print_with_prefix("系统", "\n收到终止信号，正在退出...", "system")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """程序退出前的清理工作"""
        if readline is not None:
            try:
                readline.write_history_file(self.config.get("history_file", ".morph_history"))
            except Exception as e:
                print_with_prefix("警告", f"保存历史记录失败: {str(e)}", "warning")
        self.save_todos()
        print_with_prefix("系统", "资源已释放，感谢使用", "system")

    def print_welcome_message(self):
        """打印欢迎信息"""
        print(r"""
╔══════════════════════════════════════════════════════════╗
║                Morph 细胞分裂式AI助手                    ║
║                    CLI 控制中心                         ║
╚══════════════════════════════════════════════════════════╝
        """)
        print_with_prefix("系统", f"当前模型: {self.config['default_model']}", "system")
        print_with_prefix("系统", "输入!help查看命令列表，输入!exit退出", "system")

    def print_help(self):
        """打印帮助信息"""
        help_text = """
可用命令:
  !split N         - 分裂N个子agent执行并行任务（例如: !split 3）
  !config key=value - 修改系统配置（例如: !config max_history=20）
  !tools           - 显示可用工具列表
  !history         - 显示对话历史
  !clear           - 清空屏幕
  !stats           - 显示系统状态统计
  !help            - 显示本帮助信息
  !exit            - 退出程序
  !todos           - 管理待办事项
  !vfs             - 虚拟文件系统操作
  !agent           - 直接对子agent发送消息
  !graph           - 生成架构图
  !reload          - 配置热加载
  !prompt reload   - 查看全局提示词
  !workspace <action> - 工作区管理
  !prompt <action>   - 提示模板管理
"""
        print(help_text)

    def clear_screen(self):
        """清空终端屏幕"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_system_stats(self):
        """显示系统状态统计"""
        stats = {
            "对话历史长度": len(self.agent.conversation_history) - 1,  # 排除系统提示
            "当前模型": self.config["default_model"],
            "子agent模型": self.config["subagent_model"],
            "API基础地址": self.config["api_base"],
            "允许的工具": ", ".join(self.config["allowed_tools"]),
            "最大重试次数": self.config.get("max_retries", 3),
            "会话开始时间": datetime.fromtimestamp(self.config.get("session_start", time.time())).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print_with_prefix("系统", "=== 系统状态统计 ===", "system")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    # ---------- 日志 ----------
    def log_command(self, cmd: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {cmd}\n")

    # ---------- 待办事项 ----------
    def load_todos(self) -> List[Dict[str, Any]]:
        if self.todo_file.exists():
            try:
                return json.loads(self.todo_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def save_todos(self):
        try:
            self.todo_file.write_text(json.dumps(self.todos, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print_with_prefix("警告", f"保存TODO失败: {e}", "warning")

    def handle_todo_command(self, args: List[str]):
        if not args or args[0] == "list":
            if not self.todos:
                print_with_prefix("TODO", "暂无待办事项", "agent")
                return True
            print_with_prefix("TODO", "=== 待办事项 ===", "agent")
            for idx, item in enumerate(self.todos, 1):
                status = "✓" if item.get("done") else "✗"
                print(f"{idx}. [{status}] {item['text']}")
            return True
        if args[0] == "add":
            text = " ".join(args[1:])
            if not text:
                print_with_prefix("错误", "用法: !todos add <内容>", "error")
                return True
            self.todos.append({"text": text, "done": False})
            self.save_todos()
            print_with_prefix("TODO", "已添加", "agent")
            return True
        if args[0] == "done" and len(args) > 1 and args[1].isdigit():
            idx = int(args[1]) - 1
            if 0 <= idx < len(self.todos):
                self.todos[idx]["done"] = True
                self.save_todos()
                print_with_prefix("TODO", "已标记完成", "agent")
            else:
                print_with_prefix("错误", "索引超出范围", "error")
            return True
        print_with_prefix("错误", "未知 TODO 操作", "error")
        return True

    # ---------- 虚拟文件系统 ----------
    def handle_vfs_command(self, args: List[str]):
        if not args:
            print_with_prefix("错误", "用法: !vfs <ls|read|write> ...", "error")
            return True
        op, *rest = args
        try:
            if op == "ls":
                path = rest[0] if rest else "."
                files = os.listdir(path)
                for f in files:
                    print(f)
            elif op == "read":
                if not rest:
                    raise ValueError("缺少路径")
                print(Path(rest[0]).read_text(encoding="utf-8"))
            elif op == "write":
                if len(rest) < 2:
                    raise ValueError("用法: !vfs write <path> <内容>")
                Path(rest[0]).write_text(" ".join(rest[1:]), encoding="utf-8")
                print_with_prefix("VFS", "写入成功", "agent")
            else:
                print_with_prefix("错误", "未知 VFS 操作", "error")
        except Exception as e:
            print_with_prefix("错误", str(e), "error")
        return True

    # ---------- 直接对子 agent 发送消息 ----------
    def handle_agent_direct(self, msg: str):
        if not msg:
            print_with_prefix("错误", "用法: !agent <消息>", "error")
            return True
        self.agent.process_message(msg)
        return True

    # ---------- 自动分裂 ----------
    def handle_split_command(self, args: List[str]):
        if not args or not args[0].isdigit():
            print_with_prefix("错误", "用法: !split <N>", "error")
            return True
        n = int(args[0])
        pending = [t for t in self.todos if not t.get("done")][:n]
        if len(pending) < n:
            print_with_prefix("警告", "待办不足，自动填充空任务", "warning")
            pending += ["空任务"] * (n - len(pending))
        tasks = [item if isinstance(item, str) else item["text"] for item in pending]
        results = self.agent.split_subagents(n, tasks)
        # 标记完成
        for item in pending:
            if isinstance(item, dict):
                item["done"] = True
        self.save_todos()
        # 写结果到虚拟文件
        out = Path(self.config.get("split_output", "split_results.txt"))
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print_with_prefix("Split", f"结果已写入 {out}", "agent")
        return True

    # ---------- 生成架构图 ----------
    def handle_graph_command(self):
        mermaid = """graph TD\n    User-->MorphCLI\n    MorphCLI-->MorphAgent\n    MorphAgent-->SubAgent\n    MorphAgent-->VFS\n    MorphAgent-->TodoList\n    MorphCLI-->Config\n    MorphCLI-->Log"""
        out_file = Path(self.config.get("graph_file", "architecture.mmd"))
        out_file.write_text(mermaid, encoding="utf-8")
        print_with_prefix("Graph", f"Mermaid 图已写入 {out_file}", "agent")
        return True

    # ---------- 配置热加载 ----------
    def reload_config(self):
        cfg_path = Path(self.config.get("config_path", ".morph_config.json"))
        if not cfg_path.exists():
            print_with_prefix("错误", f"配置文件不存在: {cfg_path}", "error")
            return True
        try:
            if cfg_path.suffix in {".yml", ".yaml"}:
                self.config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            else:
                self.config = json.loads(cfg_path.read_text(encoding="utf-8"))
            print_with_prefix("系统", "配置已重新加载", "system")
        except Exception as e:
            print_with_prefix("错误", f"加载配置失败: {e}", "error")
        return True

    # ---------- 提示词文件生成 ----------
    def ensure_prompt_files(self):
        base = Path(self.config.get("prompt_dir", "prompts"))
        subdirs = {
            "development": "roadmap.md",
            "project": "analysis.md",
            "optimized": "prompts.md",
            "todo": "checklist.md"
        }
        try:
            base.mkdir(exist_ok=True)
            # 全局 prompt.txt
            global_prompt = base / "prompt.txt"
            if not global_prompt.exists():
                global_prompt.write_text(DEFAULT_GLOBAL_PROMPT, encoding="utf-8")
            # 子目录及文件
            for d, f in subdirs.items():
                folder = base / d
                folder.mkdir(exist_ok=True)
                file_path = folder / f
                if not file_path.exists():
                    file_path.write_text(f"# {f}\n\nTODO: Add content.", encoding="utf-8")
        except Exception as e:
            print_with_prefix("警告", f"初始化提示词目录失败: {e}", "warning")

    def handle_prompt_reload(self):
        base = Path(self.config.get("prompt_dir", "prompts"))
        global_prompt = base / "prompt.txt"
        if global_prompt.exists():
            print(global_prompt.read_text(encoding="utf-8"))
        else:
            print_with_prefix("错误", "全局提示词文件不存在", "error")
        return True

    def handle_workspace_command(self, args: List[str]):
        if not args:
            print_with_prefix("错误", "用法: !workspace <init|list|create>", "error")
            return True
        action = args[0].lower()
        if action == "init":
            result = self.init_workspace()
            print_with_prefix("工作区", result)
        elif action == "list":
            workspace_path = get_workspace_path()
            if workspace_path.exists():
                print_with_prefix("工作区", f"内容列表 ({workspace_path}):")
                for item in workspace_path.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(workspace_path)
                        print(f"  📄 {rel_path}")
                    elif item.is_dir() and item != workspace_path:
                        rel_path = item.relative_to(workspace_path)
                        print(f"  📁 {rel_path}/")
            else:
                print_with_prefix("工作区", "工作区不存在，请先运行 'kai workspace init'")
        elif action == "create":
            if len(args) < 2:
                print_with_prefix("错误", "请指定项目名称", "error")
                return True
            project_name = args[1]
            description = " ".join(args[2:]) if len(args) > 2 else ""
            result = self.create_project(project_name, description)
            print_with_prefix("工作区", result)
        else:
            print_with_prefix("错误", f"未知工作区操作: {action}", "error")
        return True

    def handle_prompt_command(self, args: List[str]):
        if not args:
            print_with_prefix("错误", "用法: !prompt <list|show|test>", "error")
            return True
        action = args[0].lower()
        if action == "list":
            prompt_path = Path(self.config.get("prompt_dir", "prompts"))
            if prompt_path.exists():
                print_with_prefix("提示", f"可用模板 ({prompt_path}):")
                for item in prompt_path.rglob("*.txt"):
                    rel_path = item.relative_to(prompt_path)
                    template_name = rel_path.stem
                    print(f"  📝 {template_name} ({rel_path})")
            else:
                print_with_prefix("提示", "提示目录不存在")
        elif action == "show":
            if len(args) < 2:
                print_with_prefix("错误", "请指定模板名称", "error")
                return True
            template_name = args[1]
            content = self.load_prompt(template_name)
            print_with_prefix("提示", f"模板 '{template_name}' 内容:")
            print("-" * 50)
            print(content)
            print("-" * 50)
        elif action == "test":
            if len(args) < 2:
                print_with_prefix("错误", "请指定模板名称", "error")
                return True
            template_name = args[1]
            content = self.load_prompt(template_name)
            print_with_prefix("提示", f"测试模板 '{template_name}':")
            print(f"长度: {len(content)} 字符")
            print(f"行数: {len(content.splitlines())} 行")
            if content.startswith("# Template"):
                print("⚠️  模板未找到")
            else:
                print("✅ 模板加载成功")
        else:
            print_with_prefix("错误", f"未知提示操作: {action}", "error")
        return True

    def init_workspace(self):
        workspace_path = get_workspace_path()
        try:
            workspace_path.mkdir(exist_ok=True)
            return "工作区初始化成功"
        except Exception as e:
            return f"工作区初始化失败: {e}"

    def create_project(self, project_name, description):
        workspace_path = get_workspace_path()
        if not workspace_path.exists():
            return "工作区不存在，请先运行 'kai workspace init'"
        project_path = workspace_path / project_name
        try:
            project_path.mkdir(exist_ok=True)
            (project_path / "README.md").write_text(f"# {project_name}\n\n{description}", encoding="utf-8")
            return f"项目 '{project_name}' 创建成功"
        except Exception as e:
            return f"项目创建失败: {e}"

    def load_prompt(self, template_name):
        prompt_path = Path(self.config.get("prompt_dir", "prompts"))
        template_path = prompt_path / f"{template_name}.txt"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        else:
            return "# Template not found"

    def process_user_input(self, user_input: str) -> bool:
        """处理用户输入"""
        if not user_input.strip():
            return True
        self.log_command(user_input)
        self.command_history.append(user_input)
        user_input = user_input.strip()

        # 处理特殊命令
        if user_input.startswith("!"):
            parts = user_input.split()
            cmd = parts[0]
            if cmd == "!help":
                self.print_help()
                return True
            elif cmd == "!clear":
                self.clear_screen()
                return True
            elif cmd == "!stats":
                self.show_system_stats()
                return True
            elif cmd == "!todos":
                return self.handle_todo_command(parts[1:])
            elif cmd == "!vfs":
                return self.handle_vfs_command(parts[1:])
            elif cmd == "!agent":
                return self.handle_agent_direct(" ".join(parts[1:]))
            elif cmd == "!split":
                return self.handle_split_command(parts[1:])
            elif cmd == "!graph":
                return self.handle_graph_command()
            elif cmd == "!reload":
                return self.reload_config()
            elif cmd == "!prompt" and len(parts) > 1 and parts[1] == "reload":
                return self.handle_prompt_reload()
            elif cmd == "!workspace":
                return self.handle_workspace_command(parts[1:])
            elif cmd == "!prompt":
                return self.handle_prompt_command(parts[1:])
            # 其他命令由agent处理
            return self.agent.handle_command(user_input)

        # 处理常规消息
        self.agent.process_message(user_input)
        return True

    def run(self):
        """启动CLI控制循环"""
        self.config["session_start"] = time.time()
        save_config(self.config)
        self.print_welcome_message()

        try:
            while self.running:
                try:
                    user_input = input("\n你> ")
                    self.process_user_input(user_input)
                except EOFError:
                    print_with_prefix("系统", "\n检测到EOF，退出程序", "system")
                    self.running = False
                except Exception as e:
                    print_with_prefix("错误", f"处理输入时出错: {str(e)}", "error")
        finally:
            self.cleanup()

def print_usage():
    """Print CLI usage information."""
    usage = """
KAI - 基于矛盾论的智能编程助手

用法:
    kai chat                    # 启动交互式对话
    kai task "任务描述"          # 执行单次任务
    kai config [key=value]      # 查看或设置配置
    kai workspace <action>      # 工作区管理
    kai prompt <action>         # 提示模板管理
    kai help                    # 显示帮助信息

工作区命令:
    kai workspace init          # 初始化工作区
    kai workspace list          # 列出工作区内容
    kai workspace create <name> # 创建新项目

提示命令:
    kai prompt list             # 列出可用模板
    kai prompt show <name>      # 显示模板内容
    kai prompt test <name>      # 测试模板

交互式命令 (在chat模式中):
    !workspace <action>         # 工作区操作
    !prompt <action>           # 提示模板操作
    !help                      # 显示帮助
    !clear                     # 清屏
    !exit                      # 退出
"""
    print(usage.strip())

def handle_task():
    """Handle single task execution."""
    if len(sys.argv) < 3:
        print_with_prefix("错误", "请提供任务描述", "error")
        return
    
    task_description = " ".join(sys.argv[2:])
    print_with_prefix("任务", f"执行任务: {task_description}")
    
    # Initialize CLI controller for single task
    cli = MorphCLIController()
    cli.agent.process_message(task_description)

def handle_config():
    """Handle configuration management."""
    if len(sys.argv) < 3:
        # Show current config
        config = load_config()
        print_with_prefix("配置", "当前配置:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        return
    
    # Set config value
    config_str = sys.argv[2]
    if "=" not in config_str:
        print_with_prefix("错误", "配置格式: key=value", "error")
        return
    
    key, value = config_str.split("=", 1)
    config = load_config()
    
    # Try to parse as JSON for complex values
    try:
        import json
        value = json.loads(value)
    except:
        pass  # Keep as string
    
    config[key] = value
    save_config(config)
    print_with_prefix("配置", f"已设置 {key} = {value}")

def handle_workspace():
    """Handle workspace management."""
    if len(sys.argv) < 3:
        print_with_prefix("错误", "请指定工作区操作: init, list, create", "error")
        return
    
    action = sys.argv[2].lower()
    toolkit = Toolkit()
    
    if action == "init":
        result = toolkit.call("init_workspace")
        print_with_prefix("工作区", result)
    
    elif action == "list":
        workspace_path = get_workspace_path()
        if workspace_path.exists():
            print_with_prefix("工作区", f"内容列表 ({workspace_path}):")
            for item in workspace_path.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(workspace_path)
                    print(f"  📄 {rel_path}")
                elif item.is_dir() and item != workspace_path:
                    rel_path = item.relative_to(workspace_path)
                    print(f"  📁 {rel_path}/")
        else:
            print_with_prefix("工作区", "工作区不存在，请先运行 'kai workspace init'")
    
    elif action == "create":
        if len(sys.argv) < 4:
            print_with_prefix("错误", "请指定项目名称", "error")
            return
        project_name = sys.argv[3]
        description = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        result = toolkit.call("create_project", project_name, description)
        print_with_prefix("工作区", result)
    
    else:
        print_with_prefix("错误", f"未知工作区操作: {action}", "error")

def handle_prompt():
    """Handle prompt template management."""
    if len(sys.argv) < 3:
        print_with_prefix("错误", "请指定提示操作: list, show, test", "error")
        return
    
    action = sys.argv[2].lower()
    
    if action == "list":
        from utils import get_prompt_path
        prompt_path = get_prompt_path()
        if prompt_path.exists():
            print_with_prefix("提示", f"可用模板 ({prompt_path}):")
            for item in prompt_path.rglob("*.txt"):
                rel_path = item.relative_to(prompt_path)
                template_name = rel_path.stem
                print(f"  📝 {template_name} ({rel_path})")
        else:
            print_with_prefix("提示", "提示目录不存在")
    
    elif action == "show":
        if len(sys.argv) < 4:
            print_with_prefix("错误", "请指定模板名称", "error")
            return
        template_name = sys.argv[3]
        toolkit = Toolkit()
        content = toolkit.call("load_prompt", template_name)
        print_with_prefix("提示", f"模板 '{template_name}' 内容:")
        print("-" * 50)
        print(content)
        print("-" * 50)
    
    elif action == "test":
        if len(sys.argv) < 4:
            print_with_prefix("错误", "请指定模板名称", "error")
            return
        template_name = sys.argv[3]
        toolkit = Toolkit()
        content = toolkit.call("load_prompt", template_name)
        print_with_prefix("提示", f"测试模板 '{template_name}':")
        print(f"长度: {len(content)} 字符")
        print(f"行数: {len(content.splitlines())} 行")
        if content.startswith("# Template"):
            print("⚠️  模板未找到")
        else:
            print("✅ 模板加载成功")
    
    else:
        print_with_prefix("错误", f"未知提示操作: {action}", "error")

def main():
    """CLI入口函数"""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()
    
    if command == "chat":
        cli = MorphCLIController()
        cli.run()
    elif command == "task":
        handle_task()
    elif command == "config":
        handle_config()
    elif command == "workspace":
        handle_workspace()
    elif command == "prompt":
        handle_prompt()
    elif command in ["help", "-h", "--help"]:
        print_usage()
    else:
        print_with_prefix("错误", f"未知命令: {command}", "error")
        print_usage()

if __name__ == "__main__":
    main()