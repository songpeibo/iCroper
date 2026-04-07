# config/settings.py

from urllib.parse import quote

# QSettings 键：文件夹选择对话框起始路径（与 exe / 源码 cwd 无关）
SETTINGS_KEY_LAST_SOURCE_DIR = "last_source_dir"
SETTINGS_KEY_LAST_OUTPUT_DIR = "last_output_dir"

# 定义两套调色板
THEME_PALETTES = {
    "dark": {
        "bg_main": "#1e1e1e",       "bg_panel": "#2d2d2d",
        "bg_input": "#383838",      "bg_scroll": "#252526",     
        "bg_btn": "#3a3a3a",        "bg_btn_hover": "#454545",  
        "text_main": "#e0e0e0",     "text_sub": "#8a8a8a",      
        "accent": "#f48fb1",        "border": "#404040",
        "accent_soft": "#3d2f38",  "accent_muted": "#b87a90",
        "success": "#4caf50",       "success_hover": "#43a047",
        "btn_disabled": "#2b2b2b",  "text_disabled": "#555",
        "menu_bg": "#2d2d2d",       "menu_hover": "#3a3a3a", "menu_text": "#e0e0e0",
        "scrollbar": "#555",
        "title_glass_bg": "rgba(255, 255, 255, 0.10)",
        "title_glass_border": "rgba(255, 255, 255, 0.34)",
        "title_glass_hover": "rgba(255, 255, 255, 0.20)",
        "title_glass_border_hover": "rgba(255, 255, 255, 0.55)",
        "title_glass_icon": "rgba(230, 230, 230, 0.95)",
        "title_glass_close_hover_bg": "rgba(225, 29, 72, 0.88)",
        "title_glass_close_hover_border": "rgba(255, 182, 193, 0.65)",
        "title_glass_ctl_hover_bg": "rgba(255, 255, 255, 0.24)",
        "title_glass_ctl_hover_border": "rgba(255, 255, 255, 0.52)",
        "title_glass_ctl_pressed_bg": "rgba(255, 255, 255, 0.38)",
        "title_glass_ctl_pressed_border": "rgba(255, 255, 255, 0.68)",
        "glass_border": "rgba(255, 255, 255, 0.22)",
        "glass_btn_on_glass": "rgba(48, 48, 54, 0.82)",
        "glass_input_bg": "rgba(48, 48, 54, 0.68)",
        "glass_input_border": "rgba(255, 255, 255, 0.14)",
    },
    "light": {
        "bg_main": "#f5f7fa",       "bg_panel": "#ffffff",
        "bg_input": "#f5f7fa",      "bg_scroll": "#ffffff",
        "bg_btn": "#ffffff",        "bg_btn_hover": "#f0f2f7",
        "text_main": "#111827",     "text_sub": "#6b7280",
        # 日间强调色：蓝色系（路径设置 / 参数设置卡片、主按钮悬停、进度条等与 accent 联动）
        "accent": "#2563eb",        "border": "#e8ebf0",
        "accent_soft": "#dbeafe",   "accent_muted": "#60a5fa",
        "success": "#10b981",       "success_hover": "#059669",
        "cta_bg": "#111827",        "cta_hover": "#374151",
        "btn_disabled": "#f0f2f7",  "text_disabled": "#9ca3af",
        "menu_bg": "#ffffff",       "menu_hover": "#f5f7fa", "menu_text": "#111827",
        "scrollbar": "#d1d5db",
        "title_glass_bg": "rgba(255, 255, 255, 0.75)",
        "title_glass_border": "rgba(255, 255, 255, 0.95)",
        "title_glass_hover": "rgba(255, 255, 255, 0.92)",
        "title_glass_border_hover": "#ffffff",
        "title_glass_icon": "rgba(55, 65, 81, 0.88)",
        "title_glass_close_hover_bg": "rgba(220, 38, 38, 0.92)",
        "title_glass_close_hover_border": "rgba(254, 202, 202, 0.9)",
        "title_glass_ctl_hover_bg": "rgba(226, 232, 240, 0.98)",
        "title_glass_ctl_hover_border": "rgba(148, 163, 184, 0.65)",
        "title_glass_ctl_pressed_bg": "rgba(203, 213, 225, 1)",
        "title_glass_ctl_pressed_border": "rgba(100, 116, 139, 0.75)",
        "glass_border": "rgba(147, 197, 253, 0.55)",
        "glass_btn_on_glass": "rgba(255, 255, 255, 0.72)",
        "glass_input_bg": "rgba(255, 255, 255, 0.52)",
        "glass_input_border": "rgba(147, 197, 253, 0.45)",
    }
}

VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}

def get_style_sheet(theme_name="dark"):
    pal = THEME_PALETTES.get(theme_name, THEME_PALETTES["dark"])
    cta_bg = pal.get("cta_bg", pal["success"])
    cta_hover = pal.get("cta_hover", pal["success_hover"])
    combo_list_sel_bg = pal["accent_soft"] if theme_name == "light" else pal["accent"]
    combo_list_sel_fg = pal["accent"] if theme_name == "light" else "#ffffff"
    _svg_arrow = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'>"
        f"<path fill='{pal['text_sub']}' d='M0 1.5 L6 7 12 1.5 Z'/>"
        "</svg>"
    )
    combo_down_arrow_url = "url(data:image/svg+xml," + quote(_svg_arrow) + ")"

    # 半透明磨砂：纵向渐变（上亮下更透），比纯色更接近毛玻璃层次（仍无真 backdrop 模糊）
    if theme_name == "light":
        # 路径/参数卡片：浅蓝透明白渐变，与蓝色强调色呼应
        glass_panel_fill = (
            "qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, "
            "stop:0 rgba(255,255,255,0.58), stop:0.42 rgba(239,246,255,0.42), "
            "stop:1 rgba(219,234,254,0.26))"
        )
    else:
        glass_panel_fill = (
            "qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, "
            "stop:0 rgba(82,82,90,0.38), stop:0.45 rgba(48,48,54,0.52), "
            "stop:1 rgba(26,26,30,0.68))"
        )

    return f"""
    /* === 核心修复：去除焦点虚线框（Qt 样式表不支持 CSS text-shadow，写上只会刷屏告警） === */
    * {{ outline: none; }}

    /* === 主窗口（无边框圆角时由 paintEvent 绘制背景，此处透明） === */
    QWidget#BatchCropApp {{
        background-color: transparent;
    }}

    /* === 全局基础 === */
    QWidget {{
        background-color: {pal['bg_main']};
        color: {pal['text_main']};
        font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
        font-size: 14px;
    }}

    /* QLabel 默认透明底：否则会继承 QWidget 的壳背景色，在白卡片上形成灰块（如 X:/Y: 旁） */
    QLabel {{
        background-color: transparent;
    }}

    QLabel#unit_px {{
        color: {pal['text_sub']};
        font-size: 13px;
        padding-left: 2px;
        min-width: 22px;
    }}

    QLabel#status_bar {{
        color: {pal['text_sub']};
        font-size: 13px;
        background-color: transparent;
    }}

    /* 预览外框 ThemedPreviewFrame：背景与边框由 paintEvent 绘制，禁止全局 QWidget 底色盖住 */
    QFrame#themed_preview_frame {{
        background-color: transparent;
        border: none;
    }}

    /* === 自定义标题栏（圆角窗顶部） === */
    QFrame#app_title_bar {{
        background-color: transparent;
        border: none;
    }}
    QLabel#app_title_label {{
        background-color: transparent;
        color: {pal['accent']};
        font-weight: bold;
        font-size: 15px;
        letter-spacing: 0.3px;
    }}
    /* 标题栏窗口按钮：半透明玻璃感（Qt 无 backdrop-blur，用 rgba + 高光描边模拟） */
    QPushButton#title_ctl {{
        background-color: {pal['title_glass_bg']};
        border: 1px solid {pal['title_glass_border']};
        border-radius: 12px;
        min-width: 48px;
        max-width: 48px;
        min-height: 36px;
        max-height: 36px;
        padding: 0px;
        color: {pal['title_glass_icon']};
        font-size: 22px;
        font-weight: 500;
    }}
    QPushButton#title_ctl:hover {{
        background-color: {pal['title_glass_ctl_hover_bg']};
        border: 1px solid {pal['title_glass_ctl_hover_border']};
        color: {pal['text_main']};
    }}
    QPushButton#title_ctl:pressed {{
        background-color: {pal['title_glass_ctl_pressed_bg']};
        border: 1px solid {pal['title_glass_ctl_pressed_border']};
        color: {pal['text_main']};
    }}
    QPushButton#title_close {{
        background-color: {pal['title_glass_bg']};
        border: 1px solid {pal['title_glass_border']};
        border-radius: 12px;
        min-width: 48px;
        max-width: 48px;
        min-height: 36px;
        max-height: 36px;
        padding: 0px;
        color: {pal['title_glass_icon']};
        font-size: 24px;
        font-weight: 500;
    }}
    QPushButton#title_close:hover {{
        background-color: {pal['title_glass_close_hover_bg']};
        border: 1px solid {pal['title_glass_close_hover_border']};
        color: #ffffff;
    }}

    /* === 路径设置 / 参数设置：半透明磨砂玻璃（渐变 + 半透明内控件；Qt 无法实现背后实时模糊） === */
    QGroupBox#glass_panel {{
        border: 1px solid {pal['glass_border']};
        border-radius: 22px;
        margin-top: 22px;
        background: {glass_panel_fill};
        padding-top: 22px;
    }}
    QGroupBox#glass_panel::title {{
        subcontrol-origin: margin; left: 18px; padding: 0 8px;
        color: {pal['accent']};
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.6px;
    }}

    /*
     * 玻璃卡片内用 QWidget 做行/块容器时，仍会命中全局 QWidget 的 bg_main，在渐变底上出现条带状灰块（像阴影）。
     * 容器透明；输入框/下拉/带 objectName 的按钮由后面更具体的选择器单独铺色。
     */
    QGroupBox#glass_panel QWidget {{
        background-color: transparent;
    }}

    /* 路径区：主选源按钮（紫描边强调） */
    QPushButton#btn_source_pick {{
        background-color: {pal['glass_btn_on_glass']};
        border: 1px solid {pal['accent']};
        border-radius: 12px;
        padding: 8px 15px;
        color: {pal['accent']};
        font-weight: 600;
    }}
    QPushButton#btn_source_pick:hover {{
        background-color: {pal['accent_soft']};
        border-color: {pal['accent']};
        color: {pal['accent']};
    }}

    /* === 按钮通用 === */
    QPushButton {{
        background-color: {pal['bg_btn']};
        border: 1px solid {pal['border']};
        border-radius: 12px;
        padding: 9px 16px;
        color: {pal['text_main']};
    }}
    /* 鼠标悬停 或 获得焦点(键盘选中) 时，边框变色，代替虚线框 */
    QPushButton:hover {{
        background-color: {pal['bg_btn_hover']};
        border-color: {pal['accent']};
    }}
    
    /* === 工具栏小图标按钮 (Zoom) === */
    QPushButton#btn_icon_sm {{
        padding: 0px;
        border-radius: 10px;
        font-size: 16px;
        background-color: {pal['bg_panel']};
        border: 1px solid {pal['border']};
    }}
    QPushButton#btn_icon_sm:hover {{
        background-color: {pal['bg_btn_hover']};
        border-color: {pal['accent']};
    }}
    
    /* === 设置按钮 (圆形) === */
    QPushButton#btn_settings {{
        background-color: {pal['bg_panel']};
        border: 1px solid {pal['border']};
        border-radius: 20px; 
        font-size: 20px; 
        color: {pal['text_sub']};
        padding: 0px; margin: 0px; text-align: center;
    }}
    QPushButton#btn_settings:hover {{
        background-color: {pal['bg_btn_hover']}; color: {pal['text_main']};
        border-color: {pal['accent']};
    }}

    /* === 开始按钮 (深色主 CTA，参考 Swiftlet「Add」按钮) === */
    QPushButton#btn_start {{
        background-color: {cta_bg};
        border: none;
        color: #ffffff;
        font-weight: 600;
        font-size: 15px;
        border-radius: 14px;
        padding: 12px 24px;
    }}
    QPushButton#btn_start:hover {{
        background-color: {cta_hover};
    }}
    QPushButton#btn_start:disabled {{
        background-color: {pal['btn_disabled']}; color: {pal['text_disabled']};
    }}

    /* === 复选框美化 (去除虚线并微调间距) === */
    QCheckBox {{
        spacing: 8px; /* 文字和框的间距 */
    }}
    QCheckBox:focus {{
        outline: none; /* 再次确保去除虚线 */
        color: {pal['accent']}; /* 获得焦点时文字变色提示 */
    }}

    /* === 输入框（浅底 + 大圆角，接近搜索框风格） === */
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {pal['bg_input']};
        border: 1px solid {pal['border']};
        border-radius: 10px;
        padding: 8px 10px;
        color: {pal['text_main']};
        selection-background-color: {pal['accent']};
        selection-color: #ffffff;
    }}
    /* 输入框获得焦点时：高亮边框 */
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {pal['accent']};
    }}

    /* 磨砂玻璃块内的输入/下拉：须写在通用输入样式之后，否则会被覆盖 */
    QGroupBox#glass_panel QLineEdit,
    QGroupBox#glass_panel QSpinBox,
    QGroupBox#glass_panel QComboBox {{
        background-color: {pal['glass_input_bg']};
        border: 1px solid {pal['glass_input_border']};
    }}
    /* 玻璃面板内下拉：去掉过高 min-height，收紧垂直 padding，与 SpinBox 行高协调 */
    QGroupBox#glass_panel QComboBox {{
        min-height: 0px;
        padding: 3px 32px 3px 10px;
    }}
    QGroupBox#glass_panel QLineEdit:focus,
    QGroupBox#glass_panel QSpinBox:focus,
    QGroupBox#glass_panel QComboBox:focus {{
        border: 1px solid {pal['accent']};
    }}
    QGroupBox#glass_panel QComboBox:hover {{
        border-color: {pal['accent_muted']};
    }}

    /* QSpinBox：去掉上下调节钮占位与残影（与 NoButtons 配合） */
    QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
        width: 0px;
        height: 0px;
        border: none;
        margin: 0px;
        padding: 0px;
    }}
    QAbstractSpinBox::up-arrow, QAbstractSpinBox::down-arrow {{
        width: 0px;
        height: 0px;
        image: none;
        border: none;
    }}

    /* === QComboBox：紧凑高度 + 圆角矩形本体 + SVG 箭头 === */
    QComboBox {{
        padding: 5px 12px 5px 12px;
        min-height: 0px;
        border-radius: 12px;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 30px;
        border: none;
        border-top-right-radius: 9px;
        border-bottom-right-radius: 9px;
        background: transparent;
    }}
    QComboBox::down-arrow {{
        image: {combo_down_arrow_url};
        width: 12px;
        height: 8px;
        margin-right: 10px;
        border: none;
    }}
    QComboBox:hover {{
        border-color: {pal['accent_muted']};
    }}
    /* 弹出列表：明确的圆角矩形容器（列表 view 已在代码里去内框，这里只保留这一层圆角描边） */
    QComboBox QAbstractItemView {{
        background-color: {pal['bg_panel']};
        border: 1px solid {pal['border']};
        border-radius: 14px;
        padding: 6px;
        outline: none;
        selection-background-color: transparent;
        selection-color: {pal['text_main']};
    }}
    QComboBox QListView {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 24px;
        padding: 5px 12px;
        border-radius: 8px;
        color: {pal['text_main']};
    }}
    QComboBox QAbstractItemView::item:hover {{
        background-color: {pal['bg_btn_hover']};
    }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: {combo_list_sel_bg};
        color: {combo_list_sel_fg};
    }}

    /* === 图片预览区：外框为代码绘制；内层缩小+圆角（与 main_window PREVIEW_* 常量一致） === */
    QScrollArea#preview_scroll {{
        border: none;
        background-color: {pal['bg_scroll']};
        border-radius: 14px;
    }}
    QScrollArea#preview_scroll > QWidget {{
        background-color: {pal['bg_scroll']};
        border-radius: 12px;
    }}
    QScrollBar:vertical {{
        border: none; background: transparent; width: 8px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {pal['scrollbar']}; border-radius: 4px; min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QScrollBar:horizontal {{
        border: none; background: transparent; height: 8px; margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {pal['scrollbar']}; border-radius: 4px; min-width: 20px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* === 菜单 === */
    QMenu {{
        background-color: {pal['menu_bg']};
        border: 1px solid {pal['border']};
        border-radius: 10px; padding: 5px;
    }}
    QMenu::item {{
        padding: 8px 25px; border-radius: 6px; color: {pal['menu_text']};
    }}
    QMenu::item:selected {{ background-color: {pal['bg_btn_hover']}; }}
    
    QProgressBar {{
        border: none; background-color: {pal['bg_input']}; border-radius: 4px;
    }}
    QProgressBar::chunk {{
        background-color: {pal['accent']}; border-radius: 4px;
    }}

    /* 预览区标签：与白色画布底一致 */
    QLabel#preview_canvas {{
        background-color: transparent;
        color: {pal['text_sub']};
        border: none;
    }}
    """