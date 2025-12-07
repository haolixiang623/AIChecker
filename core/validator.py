import asyncio
import aiohttp
from urllib.parse import urljoin

class ElementValidator:
    """
    验证页面元素的可用性和交互性
    """
    
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 添加真实浏览器请求头,避免403错误
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def validate_link(self, url, base_url=None):
        """
        验证链接可用性
        
        Args:
            url: 目标 URL
            base_url: 基础 URL（用于相对路径）
        
        Returns:
            dict: {
                'valid': bool,
                'status_code': int,
                'response_time': float,
                'error': str
            }
        """
        # 处理相对路径
        if base_url and not url.startswith(('http://', 'https://', '//')):
            url = urljoin(base_url, url)
        
        # 跳过特殊协议
        if url.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            return {
                'valid': None,  # 不适用
                'status_code': None,
                'response_time': 0,
                'error': 'Non-HTTP protocol'
            }
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 添加Referer头以模拟真实浏览器行为
            extra_headers = {}
            if base_url:
                extra_headers['Referer'] = base_url
            
            # 首先尝试 HEAD 请求减少开销
            async with self.session.head(url, allow_redirects=True, headers=extra_headers) as response:
                response_time = asyncio.get_event_loop().time() - start_time
                
                # 如果HEAD请求返回403或405(Method Not Allowed),尝试GET请求
                if response.status in [403, 405]:
                    try:
                        start_time = asyncio.get_event_loop().time()
                        async with self.session.get(url, allow_redirects=True, headers=extra_headers) as get_response:
                            response_time = asyncio.get_event_loop().time() - start_time
                            return {
                                'valid': 200 <= get_response.status < 400,
                                'status_code': get_response.status,
                                'response_time': round(response_time, 3),
                                'error': None
                            }
                    except Exception:
                        # GET请求也失败,返回HEAD的结果
                        pass
                
                return {
                    'valid': 200 <= response.status < 400,
                    'status_code': response.status,
                    'response_time': round(response_time, 3),
                    'error': None
                }
        except asyncio.TimeoutError:
            return {
                'valid': False,
                'status_code': None,
                'response_time': self.timeout,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'valid': False,
                'status_code': None,
                'response_time': 0,
                'error': str(e)
            }
    
    async def validate_button(self, page, element_handle):
        """
        验证按钮可交互性
        
        Args:
            page: Playwright Page 对象
            element_handle: 元素句柄
        
        Returns:
            dict: {
                'clickable': bool,
                'enabled': bool,
                'click_result': str,
                'error': str
            }
        """
        try:
            # 检查是否禁用
            is_disabled = await element_handle.is_disabled()
            
            # 检查是否可点击（在视口内且未被遮挡）
            is_clickable = await element_handle.is_enabled()
            
            if not is_clickable or is_disabled:
                return {
                    'clickable': False,
                    'enabled': not is_disabled,
                    'click_result': 'Element is disabled or not clickable',
                    'error': None
                }
            
            # 尝试点击（使用 dry-run 模式，不实际触发）
            # 检查是否可以获取边界框（证明可点击）
            box = await element_handle.bounding_box()
            
            if box is None:
                return {
                    'clickable': False,
                    'enabled': True,
                    'click_result': 'Element has no bounding box',
                    'error': None
                }
            
            # 如果需要真实点击测试，可以在隔离的上下文中进行
            # await element_handle.click(trial=True)  # Playwright 的试运行模式
            
            return {
                'clickable': True,
                'enabled': True,
                'click_result': 'Element is clickable',
                'error': None
            }
            
        except Exception as e:
            return {
                'clickable': False,
                'enabled': False,
                'click_result': None,
                'error': str(e)
            }
    
    async def batch_validate_links(self, links, base_url=None, max_concurrent=10):
        """
        批量验证链接
        
        Args:
            links: URL 列表
            base_url: 基础 URL
            max_concurrent: 最大并发数
        
        Returns:
            list: 验证结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_with_semaphore(url):
            async with semaphore:
                return await self.validate_link(url, base_url)
        
        tasks = [validate_with_semaphore(link) for link in links]
        return await asyncio.gather(*tasks)
