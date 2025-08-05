# KAI - 基于矛盾论的智能编程助手

> **Knowledge-Aware AI** - 将马克思主义矛盾论与现代AI技术完美结合的智能编程系统

## 🌟 核心理念

KAI基于马克思主义矛盾论的三大规律构建：

1. **对立统一规律** - 统一的协调机制 vs 独立的执行单元
2. **量变质变规律** - 消息积累触发系统状态转换  
3. **否定之否定规律** - 持续迭代推动螺旋上升

## 🚀 快速开始

### 安装和设置

```bash
# 1. 运行安装脚本（推荐）
python setup.py

# 2. 手动初始化工作环境
python init_workspace.py
```

### 启动方式

#### 方式一：使用Python脚本（推荐）
```bash
# 启动交互式对话
python kai.py chat

# 执行单次任务
python kai.py task "创建一个Python计算器"

# 查看配置
python kai.py config

# 显示帮助
python kai.py help
```

#### 方式二：使用批处理脚本（Windows）
```bash
# 启动交互式对话
kai.bat chat

# 工作区管理
kai.bat workspace list

# 提示模板管理
kai.bat prompt list
```

#### 方式三：添加到PATH（可选）
```bash
# 将KAI目录添加到系统PATH后，可直接使用：
kai chat
kai workspace list
kai prompt show coding
```

### 验证安装

```bash
# 检查工作区
python kai.py workspace list

# 检查提示模板
python kai.py prompt list

# 测试交互模式
python kai.py chat
```

## 📁 目录结构

```
kai/
├── CascadeProjects/windsurf-project/  # 核心系统
│   ├── cli.py                         # CLI控制器
│   ├── utils.py                       # 工具函数
│   └── tools.py                       # 工具集
├── prompts/                           # 提示模板
│   ├── coding_system.txt              # 编程系统提示
│   ├── prompt.txt                     # 通用提示
│   ├── debug.txt                      # 调试模板
│   ├── refactor.txt                   # 重构模板
│   └── architecture.txt               # 架构设计模板
├── workspace/                         # 工作区
│   ├── projects/                      # 完整项目
│   ├── drafts/                        # 草稿文件
│   ├── outputs/                       # 输出文件
│   ├── temp/                          # 临时文件
│   └── archive/                       # 归档文件
└── README.md                          # 本文档
```

## 🛠️ 命令参考

### 命令行模式

| 命令 | 说明 | 示例 |
|------|------|------|
| `kai chat` | 启动交互式对话 | `kai chat` |
| `kai task "描述"` | 执行单次任务 | `kai task "创建API接口"` |
| `kai config [key=value]` | 配置管理 | `kai config workspace_dir=my_workspace` |
| `kai workspace <action>` | 工作区管理 | `kai workspace init` |
| `kai prompt <action>` | 提示模板管理 | `kai prompt list` |

### 工作区管理

```bash
# 初始化工作区
kai workspace init

# 查看工作区内容
kai workspace list

# 创建新项目
kai workspace create my_project "项目描述"
```

### 提示模板管理

```bash
# 列出所有模板
kai prompt list

# 查看模板内容
kai prompt show coding

# 测试模板
kai prompt test debug
```

## 💬 交互式命令

在 `kai chat` 模式中可使用以下特殊命令：

| 命令 | 功能 | 示例 |
|------|------|------|
| `!help` | 显示帮助信息 | `!help` |
| `!clear` | 清屏 | `!clear` |
| `!workspace <action>` | 工作区操作 | `!workspace list` |
| `!prompt <action>` | 提示操作 | `!prompt show coding` |
| `!stats` | 显示系统统计 | `!stats` |
| `!config` | 查看配置 | `!config` |
| `!exit` | 退出程序 | `!exit` |

## 🔧 配置选项

KAI使用 `.morph_config.json` 文件存储配置：

```json
{
  "prompt_dir": "prompts",
  "workspace_dir": "workspace",
  "output_dir": "outputs",
  "default_model": "ZhipuAI/GLM-4.5",
  "auto_save_workspace": true,
  "prompt_templates": {
    "coding": "coding_system.txt",
    "general": "prompt.txt",
    "debug": "debug.txt",
    "refactor": "refactor.txt",
    "architecture": "architecture.txt"
  }
}
```

### 配置修改

```bash
# 查看当前配置
kai config

# 修改配置项
kai config workspace_dir=my_custom_workspace
kai config auto_save_workspace=false
```

## 📝 提示模板系统

### 内置模板

- **coding** - 编程系统提示，适用于代码生成和调试
- **general** - 通用提示，适用于一般对话
- **debug** - 调试专用模板，帮助分析和修复问题
- **refactor** - 重构模板，优化代码结构
- **architecture** - 架构设计模板，系统设计指导

### 使用模板

```bash
# 在交互模式中加载模板
!prompt show coding

# 在命令行中查看模板
kai prompt show debug
```

## 🏗️ 工作区系统

### 自动文件组织

KAI会自动将生成的文件保存到合适的目录：

- **projects/** - 完整的项目代码
- **drafts/** - 草稿和实验性代码
- **outputs/** - 生成的文档和报告
- **temp/** - 临时文件
- **archive/** - 归档的旧文件

### 项目创建

```bash
# 创建标准项目结构
kai workspace create my_app "我的应用程序"

# 生成的结构：
# workspace/projects/my_app/
# ├── README.md
# ├── src/
# ├── docs/
# └── tests/
```

## 🎯 使用场景

### 1. 代码开发

```bash
kai chat
你> 帮我创建一个Python Web API
!workspace create web_api "RESTful API项目"
```

### 2. 代码调试

```bash
kai chat
!prompt show debug
你> 我的代码出现了这个错误：[错误信息]
```

### 3. 架构设计

```bash
kai chat
!prompt show architecture
你> 设计一个微服务架构的电商系统
```

### 4. 代码重构

```bash
kai chat
!prompt show refactor
你> 重构这段代码，提高可读性
```

## 🔍 高级功能

### 工具集成

KAI内置了丰富的工具集：

- **文件操作** - 读取、写入、追加文件
- **目录管理** - 列出目录内容
- **模式搜索** - grep风格的文本搜索
- **Shell执行** - 运行系统命令
- **工作区管理** - 自动文件组织
- **提示加载** - 动态模板系统

### 自定义扩展

```python
# 注册自定义工具
toolkit = Toolkit()
toolkit.register("my_tool", my_function)
result = toolkit.call("my_tool", arg1, arg2)
```

## 🐛 故障排除

### 常见问题

1. **工作区未初始化**
   ```bash
   python init_workspace.py
   ```

2. **提示模板未找到**
   ```bash
   kai prompt list  # 查看可用模板
   ```

3. **配置文件损坏**
   ```bash
   rm .morph_config.json  # 删除配置文件
   kai config             # 重新生成默认配置
   ```

### 日志查看

```bash
# 查看系统日志
tail -f .morph.log
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源。

## 🙏 致谢

感谢所有为KAI项目做出贡献的开发者和用户！

---

**KAI** - 让哲学思想指导技术实现，让矛盾论推动编程进步！
