import asyncio
from core.scanner import PageScanner
from core.detector import ElementDetector
from core.validator import ElementValidator

async def test_validation():
    """测试验证功能"""
    
    # 初始化
    scanner = PageScanner()
    detector = ElementDetector()
    
    # 扫描页面
    await scanner.start()
    page = await scanner.scan("https://www.example.com")
    
    if not page:
        print("页面加载失败")
        await scanner.stop()
        return
    
    # 获取当前页面 URL（用于相对路径转换）
    current_url = page.url
    print(f"当前页面: {current_url}\n")
    
    # 检测元素
    elements = await detector.detect(page)
    print(f"检测到 {len(elements)} 个元素\n")
    
    # 使用验证器
    async with ElementValidator() as validator:
        # 1. 验证链接
        print("=" * 50)
        print("链接验证测试")
        print("=" * 50)
        
        links = [el for el in elements if el['type'] == 'a' and el['href']]
        print(f"找到 {len(links)} 个链接")
        
        # 取前 10 个链接进行测试
        test_links = links[:10]
        
        for i, link in enumerate(test_links, 1):
            href = link['href']
            result = await validator.validate_link(href, current_url)
            
            status_icon = "✅" if result['valid'] else "❌"
            status_code = result['status_code'] or 'N/A'
            response_time = result['response_time']
            
            print(f"{i}. {status_icon} [{status_code}] {href[:60]}... ({response_time}s)")
            
            if result['error']:
                print(f"   错误: {result['error']}")
        
        # 2. 验证按钮
        print("\n" + "=" * 50)
        print("按钮交互性测试")
        print("=" * 50)
        
        buttons = [el for el in elements if el['type'] in ['button', 'input']]
        print(f"找到 {len(buttons)} 个按钮/输入元素")
        
        # 重新获取页面元素以测试交互性
        button_selector = 'button, input[type="submit"], input[type="button"]'
        button_handles = await page.locator(button_selector).all()
        
        for i, btn_handle in enumerate(button_handles[:5], 1):  # 测试前 5 个按钮
            try:
                text = await btn_handle.inner_text() or await btn_handle.get_attribute('value') or 'N/A'
                result = await validator.validate_button(page, btn_handle)
                
                icon = "✅" if result['clickable'] else "❌"
                enabled = "启用" if result['enabled'] else "禁用"
                
                print(f"{i}. {icon} 按钮: '{text[:30]}' - {enabled}")
                print(f"   结果: {result['click_result']}")
                
                if result['error']:
                    print(f"   错误: {result['error']}")
            except Exception as e:
                print(f"{i}. ⚠️  检测失败: {e}")
    
    await scanner.stop()
    print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_validation())
