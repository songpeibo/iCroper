import sys
import os
import traceback # 用于打印详细报错

# ========================================================
# 1. 环境修复 (针对 PyInstaller 打包)
# 这段代码必须放在 import PySide6 之前或 QApplication 启动之前
# ========================================================
if hasattr(sys, 'frozen'):
    # sys._MEIPASS 是 PyInstaller 打包后的临时解压目录
    # 我们强制告诉 Qt 去这里找 plugins/platforms 文件夹
    plugin_path = os.path.join(sys._MEIPASS, 'PySide6', 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    print(f"[Debug] 检测到打包环境，指定插件路径: {plugin_path}", flush=True)
# ========================================================

from PySide6.QtWidgets import QApplication

# 引入你的 UI 模块
# 请确保你的文件结构是：
# iCroper/
#   ├── main.py
#   ├── ui/
#   │   ├── __init__.py
#   │   ├── main_window.py
#   │   └── custom_widgets.py
#   ├── core/ ...
#   └── config/ ...
from ui.main_window import BatchCropApp

# 尝试导入样式，如果不存在则忽略
try:
    from config.settings import GLOBAL_STYLE
except ImportError:
    GLOBAL_STYLE = ""
    print("[Debug] 未找到配置文件，使用默认样式。")

def main():
    print("--------------------------------------------------")
    print("程序正在初始化...", flush=True)
    
    try:
        # 2. 启动应用
        app = QApplication(sys.argv)
        
        if GLOBAL_STYLE:
            app.setStyleSheet(GLOBAL_STYLE)
        
        print("正在加载主窗口...", flush=True)
        window = BatchCropApp()
        window.show()
        
        print("界面加载成功！进入事件循环。", flush=True)
        print("--------------------------------------------------")
        
        sys.exit(app.exec())

    except Exception:
        # 3. 致命错误捕获：防止黑框一闪而过
        # 如果出错，这里会捕获并打印，然后等待用户按回车
        print("\n" + "!"*50)
        print("程序发生致命错误，无法启动！")
        print("请截图以下错误信息发送给开发者：")
        print("!"*50 + "\n")
        
        traceback.print_exc() # 打印完整的红色报错信息
        
        print("\n" + "!"*50)
        input("请按回车键 (Enter) 退出程序...") # 关键：让窗口停住

if __name__ == "__main__":
    main()