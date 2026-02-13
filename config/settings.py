# 存放全局样式和默认配置，方便统一修改。

# 全局样式表
GLOBAL_STYLE = """
    QGroupBox { font-weight: bold; border: 1px solid #aaa; margin-top: 10px; border-radius: 4px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
    QPushButton { font-size: 14px; background-color: #eee; border: 1px solid #999; border-radius: 4px; padding: 5px; }
    QPushButton:hover { background-color: #ddd; }
    QPushButton:pressed { background-color: #ccc; }
"""

# 支持的图片扩展名
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}