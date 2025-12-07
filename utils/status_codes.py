"""
HTTP状态码工具模块
提供状态码描述和颜色编码功能
"""

from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# HTTP状态码中文描述映射
STATUS_CODES = {
    # 1xx 信息性状态码
    100: "继续",
    101: "切换协议",
    102: "处理中",
    103: "早期提示",
    
    # 2xx 成功状态码
    200: "成功",
    201: "已创建",
    202: "已接受",
    203: "非权威信息",
    204: "无内容",
    205: "重置内容",
    206: "部分内容",
    207: "多状态",
    208: "已报告",
    226: "IM使用",
    
    # 3xx 重定向状态码
    300: "多种选择",
    301: "永久重定向",
    302: "临时重定向",
    303: "查看其他",
    304: "未修改",
    305: "使用代理",
    307: "临时重定向",
    308: "永久重定向",
    
    # 4xx 客户端错误
    400: "错误的请求",
    401: "未授权",
    402: "需要付款",
    403: "禁止访问",
    404: "未找到",
    405: "方法不允许",
    406: "不可接受",
    407: "需要代理授权",
    408: "请求超时",
    409: "冲突",
    410: "已删除",
    411: "需要内容长度",
    412: "前提条件失败",
    413: "请求实体过大",
    414: "请求URI过长",
    415: "不支持的媒体类型",
    416: "请求范围不符",
    417: "期望失败",
    418: "我是茶壶",
    421: "错误的请求",
    422: "无法处理的实体",
    423: "已锁定",
    424: "失败的依赖",
    425: "太早",
    426: "需要升级",
    428: "需要前提条件",
    429: "请求过多",
    431: "请求头字段过大",
    451: "因法律原因不可用",
    
    # 5xx 服务器错误
    500: "服务器内部错误",
    501: "未实现",
    502: "网关错误",
    503: "服务不可用",
    504: "网关超时",
    505: "HTTP版本不支持",
    506: "变体协商",
    507: "存储空间不足",
    508: "检测到循环",
    510: "未扩展",
    511: "需要网络认证",
}


def get_status_description(status_code):
    """
    获取状态码的中文描述
    
    Args:
        status_code: HTTP状态码
        
    Returns:
        str: 格式化的状态码描述，如 "200 - 成功"
    """
    if status_code is None:
        return "-"
    
    description = STATUS_CODES.get(status_code, "未知状态")
    return f"{status_code} - {description}"


def get_status_color(status_code):
    """
    根据状态码获取对应的颜色
    
    Args:
        status_code: HTTP状态码
        
    Returns:
        QColor: 对应状态码范围的颜色
    """
    if status_code is None:
        return Qt.gray
    
    if 200 <= status_code < 300:
        # 2xx 成功 - 绿色
        return Qt.darkGreen
    elif 300 <= status_code < 400:
        # 3xx 重定向 - 蓝色
        return Qt.darkBlue
    elif 400 <= status_code < 500:
        # 4xx 客户端错误 - 橙色/深黄色
        return QColor(204, 102, 0)  # 深橙色
    elif 500 <= status_code < 600:
        # 5xx 服务器错误 - 红色
        return Qt.red
    else:
        # 其他 - 灰色
        return Qt.gray


def get_status_category(status_code):
    """
    获取状态码的类别
    
    Args:
        status_code: HTTP状态码
        
    Returns:
        str: 状态码类别描述
    """
    if status_code is None:
        return "未知"
    
    if 100 <= status_code < 200:
        return "信息性响应"
    elif 200 <= status_code < 300:
        return "成功"
    elif 300 <= status_code < 400:
        return "重定向"
    elif 400 <= status_code < 500:
        return "客户端错误"
    elif 500 <= status_code < 600:
        return "服务器错误"
    else:
        return "未知"
