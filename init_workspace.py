#!/usr/bin/env python3
"""
KAI Workspace Initialization Script
初始化KAI工作区和提示模板系统
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent / "CascadeProjects" / "windsurf-project"
sys.path.insert(0, str(project_root))

from utils import initialize_workspace, get_workspace_path, get_prompt_path, print_with_prefix
from tools import Toolkit

def setup_workspace():
    """Setup workspace structure"""
    print_with_prefix("初始化", "正在设置工作区...")
    
    # Initialize workspace
    initialize_workspace()
    
    # Create sample files
    workspace_path = get_workspace_path()
    
    # Create sample project
    sample_project = workspace_path / "projects" / "sample"
    sample_project.mkdir(parents=True, exist_ok=True)
    
    sample_readme = sample_project / "README.md"
    sample_readme.write_text("""# 示例项目

这是一个示例项目，展示KAI工作区的使用方式。

## 功能特性

- 自动文件组织
- 项目模板生成
- 版本控制集成

## 开始使用

```bash
# 查看工作区内容
kai workspace list

# 创建新项目
kai workspace create my_project "我的新项目"
```
""", encoding="utf-8")
    
    # Create sample draft
    draft_file = workspace_path / "drafts" / "sample_code.py"
    draft_file.write_text("""#!/usr/bin/env python3
\"\"\"
示例代码文件
这个文件展示了如何在KAI工作区中组织代码
\"\"\"

def hello_kai():
    \"\"\"KAI问候函数\"\"\"
    print("Hello from KAI workspace!")
    return "矛盾论指导下的智能编程"

if __name__ == "__main__":
    result = hello_kai()
    print(f"结果: {result}")
""", encoding="utf-8")
    
    print_with_prefix("工作区", f"工作区已初始化: {workspace_path}")

def setup_prompts():
    """Setup prompt templates"""
    print_with_prefix("初始化", "正在设置提示模板...")
    
    prompt_path = get_prompt_path()
    
    # Ensure existing prompts are accessible
    existing_prompts = []
    if prompt_path.exists():
        for txt_file in prompt_path.rglob("*.txt"):
            existing_prompts.append(txt_file.relative_to(prompt_path))
    
    print_with_prefix("提示", f"发现 {len(existing_prompts)} 个现有模板:")
    for prompt in existing_prompts:
        print(f"  📝 {prompt.stem}")
    
    # Create additional useful templates
    templates_to_create = {
        "debug.txt": """# 调试模板

你是一个专业的调试助手。请帮助用户：

1. 分析错误信息和堆栈跟踪
2. 识别潜在的问题根源
3. 提供具体的修复建议
4. 推荐调试工具和方法

请始终保持：
- 逻辑清晰的分析过程
- 具体可行的解决方案
- 预防性的编程建议
""",
        "refactor.txt": """# 重构模板

你是一个代码重构专家。请帮助用户：

1. 识别代码异味和改进机会
2. 应用设计模式和最佳实践
3. 提高代码可读性和可维护性
4. 优化性能和资源使用

重构原则：
- 保持功能不变
- 逐步小步改进
- 充分测试验证
- 文档同步更新
""",
        "architecture.txt": """# 架构设计模板

你是一个系统架构师。请帮助用户：

1. 分析需求和约束条件
2. 设计系统架构和组件
3. 选择合适的技术栈
4. 考虑可扩展性和可维护性

设计原则：
- 单一职责原则
- 开闭原则  
- 依赖倒置原则
- 接口隔离原则
"""
    }
    
    for template_name, content in templates_to_create.items():
        template_file = prompt_path / template_name
        if not template_file.exists():
            template_file.write_text(content, encoding="utf-8")
            print_with_prefix("提示", f"创建模板: {template_name}")
    
    print_with_prefix("提示", f"提示系统已设置: {prompt_path}")

def main():
    """Main initialization function"""
    print_with_prefix("KAI", "开始初始化工作环境...")
    
    try:
        # Setup workspace
        setup_workspace()
        
        # Setup prompts  
        setup_prompts()
        
        # Test toolkit
        print_with_prefix("测试", "验证工具集...")
        toolkit = Toolkit()
        
        # Test workspace operations
        result = toolkit.call("init_workspace")
        print_with_prefix("测试", f"工具集测试: {result}")
        
        # Show final status
        print_with_prefix("完成", "KAI环境初始化完成!")
        print()
        print("🎉 现在你可以使用以下命令:")
        print("   kai chat                 # 启动交互模式")
        print("   kai workspace list       # 查看工作区")
        print("   kai prompt list          # 查看提示模板")
        print("   kai help                 # 查看帮助")
        
    except Exception as e:
        print_with_prefix("错误", f"初始化失败: {e}", "error")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
