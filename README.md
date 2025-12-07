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

如果使用第三方 OpenAI 兼容 API，可额外设置：

```bash
$env:OPENAI_BASE_URL="https://api.example.com/v1"
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
- 可选：勾选 **"启用元素验证"** 自动检查链接状态码和按钮可点击性
- 点击 **"开始扫描"** 按钮
- 等待扫描完成，日志区域会显示实时进度

### 3. 查看结果

- 点击左侧菜单 **"扫描结果"**
- 点击 **"刷新最近数据"** 加载最新扫描的元素
- 表格会显示：
  - **类型**：元素类型（链接、按钮等）
  - **文本**：元素文本（鼠标悬停查看完整内容）
  - **链接地址**：完整的URL地址
  - **验证状态**：是否已验证
  - **状态描述**：HTTP状态码及中文描述（如"200 - 成功"、"404 - 未找到"）
  - **响应时间**：请求响应时间
- 点击 **"AI 分析"** 按钮，可获取单个元素的智能测试建议（需配置 API Key）

### 4. 扫描历史

- 点击左侧菜单 **"扫描历史"**
- 查看最近50次扫描记录，包含：
  - 扫描时间（相对时间显示，如"2小时前"）
  - 目标URL
  - 扫描状态和持续时间
  - 检测到的元素数量
- 点击 **"查看详情"** 按钮查看会话的详细统计信息
- 点击 **"刷新列表"** 重新加载扫描历史

### 5. AI 批量分析

- 点击左侧菜单 **"AI 分析"**
- 从下拉列表中选择要分析的扫描会话
- 点击 **"开始分析"** 启动批量分析
- 查看生成的综合质量报告，包括：
  - **执行摘要**：整体质量评估
  - **关键问题**：需要立即修复的问题
  - **警告项**：中等优先级问题
  - **优化建议**：改进建议
  - **统计分析**：数据洞察
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

### StorageManager（存储管理器）

管理扫描会话、元素和 AI 报告的数据库操作。

```python
from data.storage import StorageManager

storage = StorageManager()
session = storage.create_session("https://example.com")
storage.save_elements(session.id, elements_data)
```

### AIClient（AI 客户端）

集成 OpenAI API，为元素生成分析报告。

```python
from ai.client import AIClient

client = AIClient()
report = client.analyze_element(element_data)
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

编辑 `ai/client.py` 中的 `_construct_element_prompt` 方法，修改分析问题和格式。

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

运行测试（示例）：

```bash
python test_core.py
```

## ⚠️ 注意事项

1. **API 费用**：使用 OpenAI API 会产生费用，请注意控制调用频率
2. **网站权限**：扫描网站前请确保您有权限访问和测试该网站
3. **浏览器资源**：Playwright 会启动真实浏览器，请确保系统资源充足
4. **数据隐私**：扫描数据存储在本地数据库，请妥善保管

## 🔄 未来计划

- [ ] 支持批量 URL 扫描
- [ ] 添加定时任务和自动化调度
- [ ] 集成更多 AI 模型（Claude、本地模型等）
- [ ] 元素截图功能完善
- [ ] 导出扫描报告（PDF/HTML）
- [ ] Web API 接口支持
- [ ] 业务流程测试能力

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发者**: AIChecker Team  
**最后更新**: 2025-12-04
# AIChecker
