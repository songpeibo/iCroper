import sys
import os
import traceback 
from pathlib import Path

# ========================================================
# 1. 环境修复 (开发 / PyInstaller)
# 目标：既保证能找到 platform 插件，也不丢失 imageformats/iconengines（SVG 依赖）
# ========================================================
def _set_qt_plugin_paths():
    def _valid_dir(p):
        return bool(p) and os.path.isdir(p)

    if hasattr(sys, "frozen"):
        # 打包：_MEIPASS 内通常是 PySide6/plugins
        plugins_root = os.path.join(sys._MEIPASS, "PySide6", "plugins")
        platforms_dir = os.path.join(plugins_root, "platforms")
        if _valid_dir(plugins_root):
            os.environ["QT_PLUGIN_PATH"] = os.path.normpath(plugins_root)
        if _valid_dir(platforms_dir):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.normpath(platforms_dir)
        print(f"[Debug] 打包环境 Qt plugins: {plugins_root}", flush=True)
        return

    # 开发环境：定位 site-packages/PySide6/plugins
    try:
        import importlib.util

        spec = importlib.util.find_spec("PySide6")
        if not spec or not spec.origin:
            return

        pyside6_dir = os.path.dirname(spec.origin)
        plugins_root = os.path.join(pyside6_dir, "plugins")
        platforms_dir = os.path.join(plugins_root, "platforms")

        # 仅在未设置或无效时补齐，避免覆盖用户自定义可用路径
        cur_plugin_root = os.environ.get("QT_PLUGIN_PATH", "")
        cur_platforms = os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH", "")
        if _valid_dir(plugins_root) and not _valid_dir(cur_plugin_root):
            os.environ["QT_PLUGIN_PATH"] = os.path.normpath(plugins_root)
        if _valid_dir(platforms_dir) and not _valid_dir(cur_platforms):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.normpath(platforms_dir)
    except Exception:
        pass


_set_qt_plugin_paths()
# ========================================================

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QIcon
from ui.main_window import BatchCropApp

# 引入新的样式生成函数
try:
    from config.settings import get_style_sheet
except ImportError:
    get_style_sheet = lambda x: "" # Fallback
    print("[Debug] 未找到配置文件，使用默认样式。")


def _resolve_app_icon_path() -> str:
    """兼容源码/打包场景的应用图标路径解析。"""
    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "logo.ico")
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidates.append(Path(meipass) / "logo.ico")
    else:
        project_root = Path(__file__).resolve().parent
        candidates.append(project_root / "logo.ico")

    for p in candidates:
        if p.exists() and p.is_file():
            return str(p)
    return ""

def main():
    print("--------------------------------------------------")
    print("程序正在初始化...", flush=True)
    
    try:
        app = QApplication(sys.argv)
        # Fusion + 样式表：避免 Windows 原生风格给文字加浮雕/投影感
        _fusion = QStyleFactory.create("Fusion")
        if _fusion is not None:
            app.setStyle(_fusion)
        
        # 默认启动使用 Dark Mode (深色模式)
        # 如果想默认白天模式，这里改成 "light" 即可
        app.setStyleSheet(get_style_sheet("light"))
        icon_path = _resolve_app_icon_path()
        if icon_path:
            app.setWindowIcon(QIcon(icon_path))
        
        print("正在加载主窗口...", flush=True)
        window = BatchCropApp()
        if icon_path:
            window.setWindowIcon(QIcon(icon_path))
        window.show()
        
        print("界面加载成功！进入事件循环。", flush=True)
        print("--------------------------------------------------")
        
        sys.exit(app.exec())

    except Exception:
        print("\n" + "!"*50)
        print("程序发生致命错误，无法启动！")
        print("请截图以下错误信息发送给开发者：")
        print("!"*50 + "\n")
        
        traceback.print_exc()
        
        print("\n" + "!"*50)
        input("请按回车键 (Enter) 退出程序...")

if __name__ == "__main__":
    main()