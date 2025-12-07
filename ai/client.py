"""
AI客户端模块 - 提供OpenAI兼容API集成（第三方API）

配置说明：
==========

方法1: 使用环境变量（推荐）
-----------------------
Windows (PowerShell):
    $env:OPENAI_API_KEY="your-api-key-here"
    $env:OPENAI_BASE_URL="https://api.provider.com/v1"

Windows (命令提示符):
    set OPENAI_API_KEY=your-api-key-here
    set OPENAI_BASE_URL=https://api.provider.com/v1

Linux/macOS:
    export OPENAI_API_KEY="your-api-key-here"
    export OPENAI_BASE_URL="https://api.provider.com/v1"


方法2: 代码中直接传递
--------------------
from ai.client import AIClient

client = AIClient(
    api_key="your-api-key",
    base_url="https://api.provider.com/v1"
)


常见第三方API配置示例：
======================

# SiliconFlow
client = AIClient(
    api_key="sk-your-siliconflow-key",
    base_url="https://api.siliconflow.cn/v1"
)

# DeepSeek
client = AIClient(
    api_key="your-deepseek-key",
    base_url="https://api.deepseek.com/v1"
)

# 智谱AI (GLM)
client = AIClient(
    api_key="your-zhipu-key",
    base_url="https://open.bigmodel.cn/api/paas/v4"
)

# 通义千问 (Qwen)
client = AIClient(
    api_key="your-qwen-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

注意事项：
- API密钥请妥善保管，不要上传到代码仓库
- 必须同时设置 api_key 和 base_url 两个参数
- 建议使用环境变量方式，更安全
"""

import os
from openai import OpenAI

class AIClient:
    def __init__(self, api_key=None, base_url=None, model="gpt-3.5-turbo"):
        """
        初始化AI客户端（第三方API）
        
        Args:
            api_key (str, optional): API密钥。如果不提供，将从环境变量OPENAI_API_KEY读取
            base_url (str, optional): API基础URL。如果不提供，将从环境变量OPENAI_BASE_URL读取
            model (str, optional): 使用的模型名称。默认为 "gpt-3.5-turbo"
        
        Examples:
            # 使用环境变量
            client = AIClient()
            
            # 直接传递参数
            client = AIClient(
                api_key="your-key",
                base_url="https://api.provider.com/v1",
                model="deepseek-chat"
            )

            api_key="sk-nucovdvctqdpxqtpuemaxhokijptofzlguljabqfpkumstdc",
                base_url="https://api.siliconflow.cn/v1",
                model="deepseek-ai/DeepSeek-V3"
        """
        # 从参数或环境变量获取配置
        self.api_key = "sk-nucovdvctqdpxqtpuemaxhokijptofzlguljabqfpkumstdc" or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.siliconflow.cn/v1" or os.getenv("OPENAI_BASE_URL")
        self.model = "deepseek-ai/DeepSeek-V3"
        
        if not self.api_key:
            print("Warning: No API Key provided for AIClient")
            print("请设置环境变量 OPENAI_API_KEY 或在初始化时传入 api_key 参数")
            self.client = None
        else:
            # 创建OpenAI客户端
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def analyze_element(self, element_data):
        """
        Generates an analysis report for a single element.
        """
        if not self.client:
            return "Error: AI Client not initialized (Missing API Key)."

        prompt = self._construct_element_prompt(element_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model, # Use configured model
                messages=[
                    {"role": "system", "content": "You are a QA automation expert. Analyze the provided page element and suggest test cases or potential issues."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling AI API: {e}"

    def _construct_element_prompt(self, el):
        return f"""
        Analyze this web element:
        Type: {el.get('type')}
        Text: "{el.get('text')}"
        HREF: {el.get('href')}
        Selector: {el.get('selector')}
        
        Please provide:
        1. A brief description of what this element likely does.
        2. 2-3 negative test cases.
        3. Accessibility concerns (if any).
        """
    
    def analyze_session(self, session_data, elements_data, progress_callback=None):
        """
        对整个扫描会话进行批量AI分析
        
        Args:
            session_data: 会话信息字典
            elements_data: 元素数据列表
            progress_callback: 可选的进度回调函数
            
        Returns:
            str: 综合分析报告
        """
        if not self.client:
            return "错误: AI客户端未初始化（缺少API Key）"
        
        # 构建批量分析提示词
        prompt = self._construct_session_prompt(session_data, elements_data)
        
        if progress_callback:
            progress_callback(10, "正在发送分析请求...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一位专业的QA自动化测试专家。分析提供的网页扫描结果，生成全面的质量分析报告。请用中文回答。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            if progress_callback:
                progress_callback(100, "分析完成")
            
            return response.choices[0].message.content
        except Exception as e:
            return f"调用AI API时出错: {e}"
    
    def _construct_session_prompt(self, session_data, elements_data):
        """构建会话批量分析的提示词"""
        
        # 统计信息
        total_elements = len(elements_data)
        links = [e for e in elements_data if e.get('type') == 'a']
        buttons = [e for e in elements_data if e.get('type') in ['button', 'input']]
        
        # 验证结果统计
        validated = [e for e in elements_data if e.get('validated')]
        link_errors = [e for e in links if e.get('status_code') and e.get('status_code') >= 400]
        link_redirects = [e for e in links if e.get('status_code') and 300 <= e.get('status_code') < 400]
        unclickable_buttons = [e for e in buttons if e.get('clickable') == False]
        
        # 构建详细的元素列表
        element_details = []
        for i, el in enumerate(elements_data[:50], 1):  # 限制前50个元素以控制token
            detail = f"{i}. 类型: {el.get('type', 'N/A')}"
            if el.get('text'):
                detail += f", 文本: {el.get('text')[:50]}"
            if el.get('href'):
                detail += f", 链接: {el.get('href')[:80]}"
            if el.get('status_code'):
                detail += f", 状态码: {el.get('status_code')}"
            if el.get('clickable') is not None:
                detail += f", 可点击: {'是' if el.get('clickable') else '否'}"
            if el.get('validation_error'):
                detail += f", 错误: {el.get('validation_error')[:50]}"
            element_details.append(detail)
        
        prompt = f"""
请分析以下网页扫描结果并生成综合质量报告：

## 扫描信息
- 目标URL: {session_data.get('url')}
- 扫描时间: {session_data.get('start_time')}
- 扫描状态: {session_data.get('status')}
- 扫描时长: {session_data.get('duration', 0):.2f}秒

## 统计概览
- 总元素数: {total_elements}
- 链接数: {len(links)}
- 按钮数: {len(buttons)}
- 已验证元素: {len(validated)}

## 验证结果
- 链接错误(4xx/5xx): {len(link_errors)}个
- 链接重定向(3xx): {len(link_redirects)}个
- 不可点击按钮: {len(unclickable_buttons)}个

## 元素详情 (前50个)
{chr(10).join(element_details)}

请提供以下内容的分析报告:

1. **执行摘要** - 整体质量评估和关键发现
2. **关键问题** - 需要立即修复的高优先级问题（如404错误、500错误、不可点击的关键按钮）
3. **警告项** - 中等优先级问题（如重定向、响应慢的链接）
4. **优化建议** - 可访问性、SEO、用户体验方面的改进建议
5. **统计分析** - 基于数据的洞察和趋势

请使用清晰的Markdown格式，包含适当的标题、列表和重点标记。
"""
        return prompt
