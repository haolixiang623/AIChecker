# AIChecker - 智能网页巡检工具

AIChecker 是一个基于 Python 和 Playwright 的智能网页巡检工具，能够自动检测网页上的交互元素（链接、按钮、输入框等），并提供 AI 驱动的元素分析和测试建议。

## ✨ 功能特性

- **🔍 自动化网页扫描**：使用 Playwright 自动化浏览器，扫描目标网页
- **🎯 元素检测**：自动识别并记录页面上的链接、按钮、表单元素等交互组件
- **✅ 智能验证**：自动验证链接状态码和按钮可点击性，支持HEAD/GET请求智能回退
- **🤖 AI 智能分析**：集成 OpenAI 兼容API，为检测到的元素生成测试用例和潜在问题分析
- **📊 批量AI分析**：对整个扫描会话进行综合质量分析，生成详细报告
- **💾 数据持久化**：使用 SQLite 数据库存储扫描会话、元素信息和分析报告
- **📜 扫描历史**：保存最近50次扫描记录，支持查看详细统计和元素列表
- **🖥️ 图形化界面**：基于 PySide6 的现代化桌面应用，提供友好的用户交互体验

## 📁 项目结构

```
aichecker/
├── ai/                      # AI 分析模块
│   ├── __init__.py
│   └── client.py           # OpenAI 客户端封装
├── core/                    # 核心功能模块
│   ├── __init__.py
│   ├── scanner.py          # 页面扫描器（Playwright）
│   ├── detector.py         # 元素检测器
│   └── validator.py        # 元素验证器（链接和按钮验证）
├── data/                    # 数据持久化模块
│   ├── __init__.py
│   ├── models.py           # 数据库模型（Peewee ORM）
│   └── storage.py          # 存储管理器
├── gui/                     # 图形界面模块
│   ├── __init__.py
│   ├── main_window.py      # 主窗口框架
│   └── views.py            # 业务视图（仪表盘、扫描、结果、历史、AI分析）
├── utils/                   # 工具模块
│   ├── __init__.py
│   └── status_codes.py     # HTTP状态码工具
├── main.py                  # 应用入口
├── requirements.txt         # 项目依赖
├── aichecker.db            # SQLite 数据库
└── test_*.py               # 测试文件
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows / macOS / Linux

### 安装步骤

1. **克隆或下载项目**

```bash
cd aichecker
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **安装 Playwright 浏览器**

```bash
playwright install chromium
```

4. **配置 OpenAI API（可选）**

如果需要使用 AI 分析功能，请设置环境变量：

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# macOS / Linux
export OPENAI_API_KEY="your-api-key-here"
```

如果使用第三方 OpenAI 兼容 API（如 SiliconFlow、DeepSeek 等），可额外设置：

```bash
$env:OPENAI_BASE_URL="https://api.siliconflow.cn/v1"
```

5. **运行应用**

```bash
python main.py
```

## 📖 使用指南

### 1. 仪表盘

启动应用后，默认显示仪表盘视图，可查看最近的扫描记录。

### 2. 新建扫描

- 点击左侧菜单 **"新建扫描"**
- 输入目标网址（例如：`https://example.com`）
- **可选**：勾选 **"启用元素验证"** 自动检查链接状态码和按钮可点击性
  - 链接验证：自动检测HTTP状态码（200、404、403等）
  - 按钮验证：检查按钮是否可点击、是否被禁用
  - 智能请求：HEAD请求失败时自动回退到GET请求
- 点击 **"开始扫描"** 按钮
- 等待扫描完成，日志区域会显示实时进度
- **扫描完成后自动跳转到扫描历史视图**

### 3. 扫描历史

- 点击左侧菜单 **"扫描历史"**
- 查看最近50次扫描记录，包含：
  - **扫描时间**：相对时间显示（如"2小时前"）
  - **目标URL**：扫描的网页地址
  - **扫描状态**：completed/pending/failed
  - **持续时间**：扫描耗时
  - **元素数量**：检测到的元素总数
- 点击 **"查看详情"** 按钮查看会话详情：
  - **摘要信息**：会话统计、链接统计、按钮统计
  - **元素列表**：完整的元素表格，包含验证状态和结果
- 点击 **"刷新列表"** 重新加载扫描历史

### 4. 扫描结果（快速查看）

- 点击左侧菜单 **"扫描结果"**
- 点击 **"刷新最近数据"** 加载最新扫描的元素
- 表格会显示：
  - **类型**：元素类型（链接、按钮等）
  - **文本**：元素文本（鼠标悬停查看完整内容）
  - **链接地址**：完整的URL地址
  - **验证状态**：✅ 已验证 / ⚪ 未验证
  - **状态描述**：
    - 链接：HTTP状态码及中文描述（如"200 - 成功"、"404 - 未找到"、"403 - 禁止访问"）
    - 按钮：✅ 可点击 / ❌ 不可点击
  - **响应时间**：请求响应时间（秒）
- 点击 **"AI 分析"** 按钮，可获取单个元素的智能测试建议（需配置 API Key）

### 5. AI 批量分析

- 点击左侧菜单 **"AI 分析"**
- 从下拉列表中选择要分析的扫描会话
- 点击 **"开始分析"** 启动批量分析
- 查看生成的综合质量报告，包括：
  - **执行摘要**：整体质量评估和关键发现
  - **关键问题**：需要立即修复的高优先级问题（如404错误、500错误）
  - **警告项**：中等优先级问题（如重定向、响应慢的链接）
  - **优化建议**：可访问性、SEO、用户体验方面的改进建议
  - **统计分析**：基于数据的洞察和趋势
- 点击 **"导出报告"** 保存为Markdown或文本文件

## 🔧 核心模块说明

### PageScanner（页面扫描器）

负责使用 Playwright 启动浏览器并加载目标网页。

```python
from core.scanner import PageScanner

scanner = PageScanner()
await scanner.start()
page = await scanner.scan("https://example.com")
await scanner.stop()
```

### ElementDetector（元素检测器）

分析页面上的交互元素，支持检测：
- 链接 (`<a>` 标签)
- 按钮 (`<button>`, `input[type="button"]`, `[role="button"]`)
- 提交按钮 (`input[type="submit"]`)

```python
from core.detector import ElementDetector

detector = ElementDetector()
elements = await detector.detect(page)
```

### ElementValidator（元素验证器）

验证元素的可用性和交互性，包括：
- **链接验证**：检查HTTP状态码、响应时间
- **按钮验证**：检查可点击性、是否禁用
- **智能请求**：HEAD请求失败时自动回退到GET请求
- **真实浏览器模拟**：添加完整的浏览器请求头，避免403错误

```python
from core.validator import ElementValidator

async with ElementValidator() as validator:
    result = await validator.validate_link(url, base_url)
    # result: {'valid': True, 'status_code': 200, 'response_time': 0.5, 'error': None}
```

### StorageManager（存储管理器）

管理扫描会话、元素和 AI 报告的数据库操作。

```python
from data.storage import StorageManager

storage = StorageManager()
session = storage.create_session("https://example.com")
storage.save_elements(session.id, elements_data)
summary = storage.get_session_summary(session.id)
```

### AIClient（AI 客户端）

集成 OpenAI 兼容API，为元素生成分析报告。

```python
from ai.client import AIClient

client = AIClient()
# 单个元素分析
report = client.analyze_element(element_data)
# 批量会话分析
report = client.analyze_session(session_data, elements_data)
```

## 🗄️ 数据库结构

AIChecker 使用 SQLite 数据库（`aichecker.db`）存储数据，包含三个主要表：

### ScanSession（扫描会话）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| url | String | 扫描的目标 URL |
| start_time | DateTime | 扫描开始时间 |
| end_time | DateTime | 扫描结束时间 |
| status | String | 状态（pending/completed/failed） |

### PageElement（页面元素）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| session_id | ForeignKey | 关联的扫描会话 |
| type | String | 元素类型（a/button等） |
| text | Text | 元素文本内容 |
| href | Text | 链接地址（仅链接） |
| element_id | String | 元素 ID 属性 |
| class_name | String | 元素 class 属性 |
| selector | String | CSS 选择器 |
| visible | Boolean | 是否可见 |
| validated | Boolean | 是否已验证 |
| validation_time | DateTime | 验证时间 |
| status_code | Integer | HTTP状态码（链接） |
| response_time | Float | 响应时间（秒） |
| clickable | Boolean | 是否可点击（按钮） |
| enabled | Boolean | 是否启用（按钮） |
| validation_error | Text | 验证错误信息 |
| screenshot_path | String | 截图路径（预留） |
| created_at | DateTime | 创建时间 |

### AIReport（AI 分析报告）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| session_id | ForeignKey | 关联的会话 |
| element_id | ForeignKey | 关联的元素 |
| content | Text | 报告内容 |
| created_at | DateTime | 创建时间 |

## 🔌 依赖项

- **playwright** - 浏览器自动化框架
- **PySide6** - Qt6 Python 绑定，用于 GUI
- **openai** - OpenAI API 客户端
- **peewee** - 轻量级 ORM 框架
- **aiohttp** - 异步HTTP客户端（用于链接验证）

## 🛠️ 开发与扩展

### 添加新的元素选择器

编辑 `core/detector.py`，在 `selectors` 列表中添加新的 CSS 选择器：

```python
selectors = [
    'a[href]',
    'button',
    'input[type="submit"]',
    'input[type="button"]',
    '[role="button"]',
    # 添加您的自定义选择器
    'input[type="text"]',
]
```

### 自定义 AI 分析提示词

编辑 `ai/client.py` 中的 `_construct_element_prompt` 或 `_construct_session_prompt` 方法，修改分析问题和格式。

### 扩展数据库模型

在 `data/models.py` 中添加新的表模型，然后运行：

```python
from data.models import db, YourNewModel
db.create_tables([YourNewModel])
```

## 📝 测试

项目包含测试文件：

- `test_core.py` - 核心模块测试
- `test_ai.py` - AI 客户端测试
- `test_data.py` - 数据存储测试
- `test_validator.py` - 验证器测试

运行测试（示例）：

```bash
python test_core.py
```

## ⚠️ 注意事项

1. **API 费用**：使用 OpenAI API 会产生费用，请注意控制调用频率
2. **网站权限**：扫描网站前请确保您有权限访问和测试该网站
3. **浏览器资源**：Playwright 会启动真实浏览器，请确保系统资源充足
4. **数据隐私**：扫描数据存储在本地数据库，请妥善保管
5. **验证性能**：启用元素验证会增加扫描时间，建议根据需要选择性启用

## 🎯 最新更新 (v1.1.0)

### ✅ 智能链接验证
- 添加完整的浏览器请求头，避免403 Forbidden错误
- HEAD请求失败时自动回退到GET请求
- 支持政府网站等严格的反爬虫机制

### 📊 扫描历史增强
- 扫描完成后自动跳转到历史视图
- 历史详情对话框支持Tab页显示
- 可查看完整的元素列表和验证结果

### 🎨 用户体验改进
- HTTP状态码中文描述和颜色编码
- 相对时间显示（如"2小时前"）
- 元素文本智能截断和悬停提示

## 🔄 未来计划

- [ ] 支持批量 URL 扫描
- [ ] 添加定时任务和自动化调度
- [ ] 集成更多 AI 模型（Claude、本地模型等）
- [ ] 元素截图功能完善
- [ ] 导出扫描报告（PDF/HTML）
- [ ] Web API 接口支持
- [ ] 业务流程测试能力
- [ ] 自定义请求头配置

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发者**: AIChecker Team  
**最后更新**: 2025-12-07
