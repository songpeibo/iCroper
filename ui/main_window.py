import os
import sys
from pathlib import Path

# 直接运行本文件时，Python 默认把 ui/ 加入 path，找不到项目根的 core、config；补上项目根
_pkg_root = Path(__file__).resolve().parents[1]
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QSpinBox, QProgressBar, 
                               QGroupBox, QScrollArea, QLineEdit, 
                               QComboBox, QCheckBox, QApplication, QMenu, QFrame,
                               QAbstractSpinBox, QSizePolicy)
from PySide6.QtCore import Qt, QPoint, QEvent, QRectF, QSettings, QStandardPaths
from PySide6.QtGui import QAction, QCursor, QPainter, QPainterPath, QRegion, QColor, QPen, QFontMetrics, QGuiApplication

from core.utils import cv_imread_safe, cvimg_to_qpixmap
from core.processor import CropWorker
from config.settings import (
    VALID_EXTENSIONS,
    SETTINGS_KEY_LAST_OUTPUT_DIR,
    SETTINGS_KEY_LAST_SOURCE_DIR,
    get_style_sheet,
    THEME_PALETTES,
)
from config.i18n import (
    LANG_EN,
    LANG_ZH,
    SETTINGS_KEY_LANGUAGE,
    align_combo_labels,
    normalize_lang,
    shape_combo_labels,
    tr,
)
# 引入我们自定义的圆角弹窗
from ui.custom_widgets import InteractableLabel, ModernMessageBox 
from ui.window_components import (
    PREVIEW_FRAME_BORDER,
    SETTINGS_ICON_SIZE,
    TOOLBAR_ICON_SIZE,
    TitleBar,
    ThemedPreviewFrame,
    StyledComboBox,
    menu_action_with_svg,
    svg_toolbar_button,
)

WINDOW_CORNER_RADIUS = 14
# 参数面板最小高度：参数化梯形含「上底 / 下底」分两行，预留足够高度避免切换形状时跳动
SETTINGS_PANEL_MIN_HEIGHT = 478
# 参数面板固定宽度：切换形状、显隐行数时右侧卡片宽度不变（与预览区间 stretch 分配无关）
SETTINGS_PANEL_FIXED_WIDTH = 320
# 参数区内侧可用宽度（与 settings_layout 左右 ContentsMargins 一致）
SETTINGS_PANEL_INNER_WIDTH = SETTINGS_PANEL_FIXED_WIDTH - 40
# 梯形块再留余量，避免 QGroupBox 内边距与字体抗锯齿导致算宽略窄而重叠
TRAP_LAYOUT_INNER = SETTINGS_PANEL_INNER_WIDTH - 12
# 参数化梯形：X/Y 与上底/下底/H 之间及梯形区内各行间距（小于整块 settings_layout 的 15px）
TRAPEZOID_FORM_V_SPACING = 6
# 梯形单行宽数值框与右侧「px」标签的横向间隙（宽输入框易显得与 px 挤在一起）
TRAP_DIM_SPIN_PX_GAP = 10
# 梯形「标签 | 数值 | px」行内，标签与数值框之间的 QHBoxLayout spacing
TRAP_DIM_ROW_H_SPACING = 8

PREVIEW_FRAME_MARGIN = 10
class BatchCropApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("BatchCropApp")
        self.setWindowTitle("iCroper")
        self.resize(1200, 850)

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.image_files = []
        self.source_dir = ""
        self.output_dir = ""
        self.worker = None 
        self.is_processing = False
        self.aspect_ratio = 1.0 
        self.current_theme = "light"
        _st = QSettings("iCroper", "iCroper")
        self.lang = normalize_lang(_st.value(SETTINGS_KEY_LANGUAGE))

        self.init_ui()
        self._update_rounded_mask()
        self._startup_positioned = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._startup_positioned:
            self._center_on_screen()
            self._startup_positioned = True

    def _center_on_screen(self):
        """首次显示时将窗口居中到当前屏幕可用区域。"""
        # 优先按鼠标所在屏幕居中，多屏场景体验更自然
        screen = QGuiApplication.screenAt(QCursor.pos())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pal = THEME_PALETTES.get(self.current_theme, THEME_PALETTES["light"])
        bg = QColor(pal["bg_main"])
        border_c = QColor(pal["border"])
        rect = self.rect()
        r = float(WINDOW_CORNER_RADIUS)
        if self.isMaximized():
            painter.fillRect(rect, bg)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(rect, r, r)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(border_c)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRoundedRect(rect, r, r)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_rounded_mask()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_rounded_mask()
            if hasattr(self, "title_bar"):
                self.title_bar.sync_max_button()
            self.update()

    def _update_rounded_mask(self):
        if self.isMaximized():
            self.clearMask()
            return
        path = QPainterPath()
        path.addRoundedRect(self.rect(), WINDOW_CORNER_RADIUS, WINDOW_CORNER_RADIUS)
        poly = path.toFillPolygon().toPolygon()
        self.setMask(QRegion(poly))

    def _t(self, key: str, **kwargs) -> str:
        return tr(self.lang, key, **kwargs)

    def _display_path(self, p: str) -> str:
        """仅用于界面展示：统一使用正斜杠，避免 Windows 反斜杠观感不一致。"""
        return (p or "").replace("\\", "/")

    def _settings_store(self) -> QSettings:
        return QSettings("iCroper", "iCroper")

    def _pick_dialog_start_dir(self, last_key: str, current: str) -> str:
        """选择文件夹对话框起始路径：上次记忆 > 当前已选 > 系统图片目录 > 用户主目录（不依赖 cwd，exe 与源码一致）。"""
        st = self._settings_store()
        for raw in (st.value(last_key), current):
            if not raw:
                continue
            s = str(raw).strip()
            if s and os.path.isdir(s):
                return os.path.normpath(s)
        pics = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
        if pics and os.path.isdir(pics):
            return os.path.normpath(pics)
        home = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
        if home and os.path.isdir(home):
            return os.path.normpath(home)
        return ""

    def _persist_language(self):
        QSettings("iCroper", "iCroper").setValue(SETTINGS_KEY_LANGUAGE, self.lang)

    def toggle_language(self):
        self.lang = LANG_EN if self.lang == LANG_ZH else LANG_ZH
        self._persist_language()
        self.apply_language()
        self.status_bar.setText(
            self._t("lang_switched_zh") if self.lang == LANG_ZH else self._t("lang_switched_en")
        )

    def apply_language(self):
        """切换界面文案（简中 / English）。"""
        self.path_group.setTitle(self._t("path_section_title"))
        self.settings_group.setTitle(self._t("params_section_title"))
        self.btn_source.setText(self._t("btn_pick_source"))
        self.lbl_source.setPlaceholderText(self._t("ph_source_folder"))
        self.btn_output.setText(self._t("btn_pick_output"))
        self.lbl_output.setPlaceholderText(self._t("ph_output_folder"))
        if not self.image_files:
            self.preview_label.setText(self._t("preview_empty"))
        self.lbl_shape.setText(self._t("lbl_shape"))
        self.lbl_align.setText(self._t("lbl_trap_align"))
        self.chk_lock_ratio.setText(self._t("chk_lock_ratio"))
        self.lbl_x.setText(self._t("lbl_x"))
        self.lbl_y.setText(self._t("lbl_y"))
        self.lbl_h.setText(self._t("lbl_h"))
        self.btn_start.setText(self._t("btn_start"))
        self.btn_cancel.setText(self._t("btn_cancel"))
        self.btn_settings.setToolTip(self._t("settings_tooltip"))

        ix = self.combo_shape.currentIndex()
        ia = self.combo_align.currentIndex()
        self.combo_shape.blockSignals(True)
        self.combo_shape.clear()
        self.combo_shape.addItems(shape_combo_labels(self.lang))
        self.combo_shape.setCurrentIndex(max(0, min(ix, self.combo_shape.count() - 1)))
        self.combo_shape.blockSignals(False)
        self.combo_align.blockSignals(True)
        self.combo_align.clear()
        self.combo_align.addItems(align_combo_labels(self.lang))
        self.combo_align.setCurrentIndex(max(0, min(ia, self.combo_align.count() - 1)))
        self.combo_align.blockSignals(False)

        self.on_combo_changed()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 10, 24, 28)

        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # --- 1. 路径设置（磨砂玻璃卡片） ---
        self.path_group = QGroupBox(self._t("path_section_title"))
        self.path_group.setObjectName("glass_panel")
        self.path_group.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        path_layout = QVBoxLayout(self.path_group)
        path_layout.setSpacing(15)
        path_layout.setContentsMargins(20, 25, 20, 20)
        
        def create_path_row(btn_text, placeholder, btn_object_name=None):
            layout = QHBoxLayout()
            btn = QPushButton(btn_text); btn.setFixedWidth(130)
            btn.setCursor(Qt.PointingHandCursor)
            if btn_object_name:
                btn.setObjectName(btn_object_name)
            edit = QLineEdit(); edit.setPlaceholderText(placeholder); edit.setReadOnly(True)
            layout.addWidget(btn); layout.addWidget(edit)
            return btn, edit, layout
            
        self.btn_source, self.lbl_source, l1 = create_path_row(
            self._t("btn_pick_source"), self._t("ph_source_folder"), "btn_source_pick"
        )
        self.btn_output, self.lbl_output, l2 = create_path_row(
            self._t("btn_pick_output"), self._t("ph_output_folder")
        )
        path_layout.addLayout(l1); path_layout.addLayout(l2)
        main_layout.addWidget(self.path_group)

        # --- 2. 预览与参数 (中间主体) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(28)
        
        # === 左侧预览区 ===
        preview_layout = QVBoxLayout()
        
        # 工具条 (Zoom)
        zoom_layout = QHBoxLayout()
        self.btn_zoom_in = QPushButton()
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_fit = QPushButton()
        svg_toolbar_button(self.btn_zoom_in, "zoom-in.svg", TOOLBAR_ICON_SIZE, "+")
        svg_toolbar_button(self.btn_zoom_out, "zoom-out.svg", TOOLBAR_ICON_SIZE, "−")
        svg_toolbar_button(self.btn_zoom_fit, "expand.svg", TOOLBAR_ICON_SIZE, "⛶")
        self.lbl_zoom_ratio = QLabel("100%")
        self.lbl_zoom_ratio.setStyleSheet("font-weight: bold; margin-left: 8px; border: none;")
        
        for btn in [self.btn_zoom_in, self.btn_zoom_out, self.btn_zoom_fit]:
            btn.setObjectName("btn_icon_sm") # <--- 【关键修复】应用 padding:0 样式，防止图标被挤没
            btn.setFixedSize(36, 36) 
            btn.setCursor(Qt.PointingHandCursor)
            
        zoom_layout.addWidget(self.btn_zoom_in); zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_zoom_fit); zoom_layout.addWidget(self.lbl_zoom_ratio)
        zoom_layout.addStretch()
        preview_layout.addLayout(zoom_layout)

        # 预览区：ThemedPreviewFrame 用 paintEvent 画圆角与主题描边（QSS 边框在此场景不可靠）
        self.preview_frame = ThemedPreviewFrame(self)
        self.preview_frame.set_theme(self.current_theme)
        _preview_wrap = QVBoxLayout(self.preview_frame)
        _preview_wrap.setContentsMargins(PREVIEW_FRAME_MARGIN, PREVIEW_FRAME_MARGIN, PREVIEW_FRAME_MARGIN, PREVIEW_FRAME_MARGIN)
        _preview_wrap.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("preview_scroll")
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scroll_area.viewport().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.preview_label = InteractableLabel()
        self.preview_label.setObjectName("preview_canvas")
        self.preview_label.setText(self._t("preview_empty"))
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.preview_label)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        _preview_wrap.addWidget(self.scroll_area)
        preview_layout.addWidget(self.preview_frame)
        content_layout.addLayout(preview_layout, stretch=3)

        # === 右侧设置区（磨砂玻璃卡片） ===
        self.settings_group = QGroupBox(self._t("params_section_title"))
        self.settings_group.setObjectName("glass_panel")
        self.settings_group.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        settings_layout = QVBoxLayout(self.settings_group)
        settings_layout.setSpacing(15)
        settings_layout.setContentsMargins(20, 25, 20, 20)
        self.settings_group.setMinimumHeight(SETTINGS_PANEL_MIN_HEIGHT)
        self.settings_group.setFixedWidth(SETTINGS_PANEL_FIXED_WIDTH)

        # 形状选择
        self.combo_shape = StyledComboBox(popup_fit_all_items=True)
        self.combo_shape.addItems(shape_combo_labels(self.lang))
        self.combo_shape.setMaxVisibleItems(6)
        self.combo_shape.setFixedHeight(36)
        self.combo_shape.setMinimumHeight(36)
        self.combo_shape.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lbl_shape = QLabel(self._t("lbl_shape"))
        settings_layout.addWidget(self.lbl_shape)
        settings_layout.addWidget(self.combo_shape)

        # 梯形对齐（与标签同一行时 QComboBox 必须占满剩余宽度，否则宽度过小会显示成乱线）
        self.lbl_align = QLabel(self._t("lbl_trap_align"))
        self.lbl_align.setMinimumWidth(76)
        self.lbl_align.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.combo_align = StyledComboBox(popup_fit_all_items=True)
        self.combo_align.addItems(align_combo_labels(self.lang))
        self.combo_align.setMaxVisibleItems(3)
        self.combo_align.setFixedHeight(36)
        self.combo_align.setMinimumHeight(36)
        self.combo_align.setMinimumWidth(120)
        self.combo_align.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.container_align, _ = self.add_spin_row(settings_layout, self.lbl_align, self.combo_align)
        self.container_align.setVisible(False)

        # 数值输入框
        self.spin_x = self.create_spin(); self.spin_y = self.create_spin()
        self.spin_w = self.create_spin(); self.spin_h = self.create_spin()
        self.spin_w_bottom = self.create_spin()
        self.spin_w_bottom.setRange(-99999, 99999) 
        
        self.chk_lock_ratio = QCheckBox(self._t("chk_lock_ratio"))
        settings_layout.addWidget(self.chk_lock_ratio)

        # 参数排版：第一行 X Y，第二行 W H；列宽统一使上下输入框竖直对齐
        self.lbl_x = QLabel(self._t("lbl_x"))
        self.lbl_y = QLabel(self._t("lbl_y"))
        self._px_x = self._make_unit_px_label()
        self._px_y = self._make_unit_px_label()
        self.row_xywh = QWidget()
        self.row_xywh_v_layout = QVBoxLayout(self.row_xywh)
        self.row_xywh_v_layout.setSpacing(8)
        self.row_xywh_v_layout.setContentsMargins(0, 0, 0, 0)
        self.row_xy_layout = QHBoxLayout()
        self.row_xy_layout.setSpacing(10)
        self.row_xy_layout.setContentsMargins(0, 0, 0, 0)
        self.row_wh_wrap = QWidget()
        self.row_wh_layout = QHBoxLayout(self.row_wh_wrap)
        self.row_wh_layout.setSpacing(10)
        self.row_wh_layout.setContentsMargins(0, 0, 0, 0)
        self.row_xywh_v_layout.addLayout(self.row_xy_layout)
        self.row_xywh_v_layout.addWidget(self.row_wh_wrap)
        self.row_xywh.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self._params_numeric_block = QWidget()
        _params_num_l = QVBoxLayout(self._params_numeric_block)
        _params_num_l.setContentsMargins(0, 0, 0, 0)
        _params_num_l.setSpacing(TRAPEZOID_FORM_V_SPACING)

        self._px_w = self._make_unit_px_label()
        self._px_h = self._make_unit_px_label()
        self._px_w_bottom = self._make_unit_px_label()

        self.lbl_w = QLabel(self._t("lbl_w_short"))
        self.lbl_h = QLabel(self._t("lbl_h"))

        self.wh_trap_widget = QWidget()
        _trap_v = QVBoxLayout(self.wh_trap_widget)
        _trap_v.setSpacing(TRAPEZOID_FORM_V_SPACING)
        _trap_v.setContentsMargins(0, 0, 0, 0)
        self.wh_trap_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        # 上底 / 下底各占一行，避免 320 宽内双列中文标签挤爆数值框
        self.wh_trap_widths_block = QWidget()
        self.wh_trap_widths_block.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        _trap_wv = QVBoxLayout(self.wh_trap_widths_block)
        _trap_wv.setSpacing(TRAPEZOID_FORM_V_SPACING)
        _trap_wv.setContentsMargins(0, 0, 0, 0)
        self.wh_trap_upper_row = QWidget()
        self.wh_trap_upper_layout = QHBoxLayout(self.wh_trap_upper_row)
        self.wh_trap_upper_layout.setSpacing(TRAP_DIM_ROW_H_SPACING)
        self.wh_trap_lower_row = QWidget()
        self.wh_trap_lower_layout = QHBoxLayout(self.wh_trap_lower_row)
        self.wh_trap_lower_layout.setSpacing(TRAP_DIM_ROW_H_SPACING)
        _trap_wv.addWidget(self.wh_trap_upper_row)
        _trap_wv.addWidget(self.wh_trap_lower_row)
        self.wh_trap_h_row = QWidget()
        self.wh_trap_h_layout = QHBoxLayout(self.wh_trap_h_row)
        self.wh_trap_h_layout.setSpacing(TRAP_DIM_ROW_H_SPACING)
        _trap_v.addWidget(self.wh_trap_widths_block)
        _trap_v.addWidget(self.wh_trap_h_row)
        self.wh_trap_widget.setVisible(False)
        _params_num_l.addWidget(self.row_xywh)
        _params_num_l.addWidget(self.wh_trap_widget)
        settings_layout.addWidget(self._params_numeric_block)

        self.lbl_w_bottom = QLabel(self._t("lbl_trap_bottom"))
        self.container_w_bottom = QWidget()
        self.container_w_bottom_layout = QHBoxLayout(self.container_w_bottom)
        self.container_w_bottom_layout.setSpacing(10)
        settings_layout.addWidget(self.container_w_bottom)
        self.container_w_bottom.setVisible(False)

        settings_layout.addStretch()
        # stretch=0：加宽窗口时仅拉伸预览区，参数区保持固定宽
        content_layout.addWidget(self.settings_group, stretch=0)
        main_layout.addLayout(content_layout)

        # --- 3. 底部操作区 ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6) 
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.btn_start = QPushButton(self._t("btn_start"))
        self.btn_start.setObjectName("btn_start")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setMinimumHeight(50) 
        self.btn_start.setEnabled(False)
        self.btn_cancel = QPushButton(self._t("btn_cancel"))
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setMinimumHeight(50)
        self.btn_cancel.setEnabled(False)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.btn_start, 2)
        action_row.addWidget(self.btn_cancel, 1)
        main_layout.addLayout(action_row)
        
        # === 底部状态栏与设置 ===
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(5, 10, 5, 0)
        
        self.status_bar = QLabel(self._t("status_ready"))
        self.status_bar.setObjectName("status_bar")
        bottom_layout.addWidget(self.status_bar)
        
        bottom_layout.addStretch()
        
        # 设置按钮 (完美圆形)
        self.btn_settings = QPushButton()
        svg_toolbar_button(self.btn_settings, "settings.svg", SETTINGS_ICON_SIZE, "⚙")
        self.btn_settings.setObjectName("btn_settings") # 应用圆形样式和 padding:0
        self.btn_settings.setFixedSize(40, 40) 
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setToolTip(self._t("settings_tooltip"))
        bottom_layout.addWidget(self.btn_settings)
        
        main_layout.addLayout(bottom_layout)

        # --- 信号绑定 ---
        self.btn_settings.clicked.connect(self.show_settings_menu)
        self.btn_source.clicked.connect(self.on_select_source)
        self.btn_output.clicked.connect(self.on_select_output)
        self.btn_start.clicked.connect(self.on_start)
        self.btn_cancel.clicked.connect(self.on_cancel)
        
        for w in [self.spin_x, self.spin_y, self.spin_w, self.spin_h, self.spin_w_bottom]:
            w.valueChanged.connect(self.sync_selection_to_preview)
            
        self.combo_shape.currentIndexChanged.connect(self.on_combo_changed)
        self.combo_align.currentIndexChanged.connect(self.sync_selection_to_preview)
        self.preview_label.selection_changed.connect(self.on_mouse_rect_selection)
        self.chk_lock_ratio.stateChanged.connect(self.on_lock_ratio_toggled)
        self.btn_zoom_in.clicked.connect(lambda: self.preview_label.set_scale(self.preview_label.scale_factor * 1.25))
        self.btn_zoom_out.clicked.connect(lambda: self.preview_label.set_scale(self.preview_label.scale_factor * 0.8))
        # 回到“适配窗口”基准（该基准定义为 100%）
        self.btn_zoom_fit.clicked.connect(self.action_zoom_fit)
        self.preview_label.zoom_changed.connect(self.on_zoom_changed)

        self._refresh_wh_layout(self.combo_shape.currentIndex())

    def _clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def _reset_flexible_numeric_widths(self):
        """退出参数化梯形时恢复数值框与梯形对齐标签的水平伸缩。"""
        for s in (self.spin_x, self.spin_y, self.spin_w, self.spin_h, self.spin_w_bottom):
            s.setMinimumWidth(0)
            s.setMaximumWidth(16777215)
        self.lbl_align.setMinimumWidth(76)
        self.lbl_align.setMaximumWidth(16777215)

    def _trap_text_width(self, fm: QFontMetrics, text: str) -> int:
        """中文标签用 boundingRect 比 horizontalAdvance 更贴近实际占位，防止画到相邻控件上。"""
        return fm.boundingRect(text).width()

    def _xy_spin_field_width(self) -> int:
        """矩形行 X/Y 数值框宽度：与未手工拉宽时 QSpinBox.sizeHint 一致；梯形模式复用此宽度。"""
        sx = self.spin_x
        sx.setMinimumWidth(0)
        sx.setMaximumWidth(16777215)
        return max(48, sx.sizeHint().width())

    def _apply_trap_mode_geometry(self):
        """320px 内：X/Y 行与矩形相同列宽算法；上底/下底/H 用中文标签列宽 + 单行宽输入。"""
        fm = QFontMetrics(self.lbl_x.font())
        pad_dim = 14
        # 与矩形模式一致：第一列 max(X:, W:)、第二列 max(Y:, H:)，避免 X/Y 与 px、Y: 挤在一起
        w_col_xy = max(
            fm.horizontalAdvance(self._t("lbl_x")),
            fm.horizontalAdvance(self._t("lbl_w_short")),
        ) + 8
        h_col_xy = max(
            fm.horizontalAdvance(self._t("lbl_y")),
            fm.horizontalAdvance(self._t("lbl_h")),
        ) + 8
        trap_dim = max(
            self._trap_text_width(fm, self._t("lbl_trap_align")),
            self._trap_text_width(fm, self._t("lbl_trap_top")),
            self._trap_text_width(fm, self._t("lbl_trap_bottom")),
            self._trap_text_width(fm, self._t("lbl_h")),
        ) + pad_dim
        inner = TRAP_LAYOUT_INNER
        px_reserve = max(
            self._px_w.sizeHint().width(),
            self._px_w_bottom.sizeHint().width(),
            self._px_h.sizeHint().width(),
            fm.horizontalAdvance("px") + 10,
        )
        w_xy = self._xy_spin_field_width()
        # 须扣掉：标签与 spin 的 layout spacing、spin 与 px 的 addSpacing、px 占位，否则会算得过宽与「px」重叠
        trap_spin_row_overhead = (
            TRAP_DIM_ROW_H_SPACING + TRAP_DIM_SPIN_PX_GAP + px_reserve + 6
        )
        spin_full = max(72, inner - trap_dim - trap_spin_row_overhead)

        self.lbl_align.setFixedWidth(trap_dim)
        self.lbl_x.setFixedWidth(w_col_xy)
        self.lbl_y.setFixedWidth(h_col_xy)
        self.lbl_x.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_y.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for lb in (self.lbl_w, self.lbl_w_bottom, self.lbl_h):
            lb.setFixedWidth(trap_dim)
            lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.spin_x.setFixedWidth(w_xy)
        self.spin_y.setFixedWidth(w_xy)
        self.spin_w.setFixedWidth(spin_full)
        self.spin_w_bottom.setFixedWidth(spin_full)
        self.spin_h.setFixedWidth(spin_full)

    def _style_wh_labels_for_shape(self, idx):
        """参数化梯形：按面板内宽计算标签列与数值框宽度；其余形状：X/W、Y/H 列对齐。"""
        if idx == 1:
            self._apply_trap_mode_geometry()
        else:
            self._reset_flexible_numeric_widths()
            fm = QFontMetrics(self.lbl_x.font())
            w_col = max(fm.horizontalAdvance("X:"), fm.horizontalAdvance(self.lbl_w.text())) + 8
            h_col = max(fm.horizontalAdvance("Y:"), fm.horizontalAdvance(self.lbl_h.text())) + 8
            self.lbl_x.setFixedWidth(w_col)
            self.lbl_w.setFixedWidth(w_col)
            self.lbl_y.setFixedWidth(h_col)
            self.lbl_h.setFixedWidth(h_col)
            w_xy = self._xy_spin_field_width()
            self.spin_x.setFixedWidth(w_xy)
            self.spin_y.setFixedWidth(w_xy)
            # 与 X/Y 同一套宽度；否则 W/H 仅吃 sizeHint，视觉上会比上一行窄
            self.spin_w.setFixedWidth(w_xy)
            self.spin_h.setFixedWidth(w_xy)
            for lb in (self.lbl_x, self.lbl_y, self.lbl_w, self.lbl_h):
                lb.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if idx == 5:
                self.lbl_w_bottom.setMinimumWidth(0)
                self.lbl_w_bottom.setMaximumWidth(16777215)
                self.lbl_w_bottom.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            else:
                self.lbl_w_bottom.setMinimumWidth(76)
                self.lbl_w_bottom.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _refresh_wh_layout(self, idx):
        """非梯形：第一行 X Y、第二行 W H；梯形：首行 X Y，下方梯形区；平行四边形多一行倾斜偏移。"""
        self._style_wh_labels_for_shape(idx)
        self._clear_layout(self.row_xy_layout)
        self._clear_layout(self.row_wh_layout)
        self._clear_layout(self.wh_trap_upper_layout)
        self._clear_layout(self.wh_trap_lower_layout)
        self._clear_layout(self.wh_trap_h_layout)
        self._clear_layout(self.container_w_bottom_layout)

        def _add_xy_group(layout):
            layout.addWidget(self.lbl_x, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(self.spin_x, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(4)
            layout.addWidget(self._px_x, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(10)
            layout.addWidget(self.lbl_y, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(self.spin_y, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(4)
            layout.addWidget(self._px_y, 0, Qt.AlignmentFlag.AlignVCenter)

        def _add_wh_group(layout):
            layout.addWidget(self.lbl_w, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(self.spin_w, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(4)
            layout.addWidget(self._px_w, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(10)
            layout.addWidget(self.lbl_h, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(self.spin_h, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(4)
            layout.addWidget(self._px_h, 0, Qt.AlignmentFlag.AlignVCenter)

        if idx == 1:
            _add_xy_group(self.row_xy_layout)
            self.row_xy_layout.addStretch(1)
            self.row_wh_wrap.setVisible(False)
            self.wh_trap_widget.setVisible(True)
            self.container_w_bottom.setVisible(False)
            self.wh_trap_upper_layout.addWidget(self.lbl_w, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_upper_layout.addWidget(self.spin_w, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_upper_layout.addSpacing(TRAP_DIM_SPIN_PX_GAP)
            self.wh_trap_upper_layout.addWidget(self._px_w, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_upper_layout.addStretch(1)
            self.wh_trap_lower_layout.addWidget(self.lbl_w_bottom, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_lower_layout.addWidget(self.spin_w_bottom, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_lower_layout.addSpacing(TRAP_DIM_SPIN_PX_GAP)
            self.wh_trap_lower_layout.addWidget(self._px_w_bottom, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_lower_layout.addStretch(1)
            self.wh_trap_h_layout.addWidget(self.lbl_h, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_h_layout.addWidget(self.spin_h, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_h_layout.addSpacing(TRAP_DIM_SPIN_PX_GAP)
            self.wh_trap_h_layout.addWidget(self._px_h, 0, Qt.AlignmentFlag.AlignVCenter)
            self.wh_trap_h_layout.addStretch(1)
        else:
            self.wh_trap_widget.setVisible(False)
            self.row_wh_wrap.setVisible(True)
            _add_xy_group(self.row_xy_layout)
            self.row_xy_layout.addStretch(1)
            _add_wh_group(self.row_wh_layout)
            self.row_wh_layout.addStretch(1)
            self.container_w_bottom.setVisible(idx == 5)
            if idx == 5:
                self.container_w_bottom_layout.addWidget(self.lbl_w_bottom, 0, Qt.AlignmentFlag.AlignVCenter)
                self.container_w_bottom_layout.addWidget(self.spin_w_bottom, 1, Qt.AlignmentFlag.AlignVCenter)
                self.container_w_bottom_layout.addSpacing(4)
                self.container_w_bottom_layout.addWidget(self._px_w_bottom, 0, Qt.AlignmentFlag.AlignVCenter)

    def show_settings_menu(self):
        menu = QMenu(self)
        
        theme_text = (
            self._t("menu_theme_to_light")
            if self.current_theme == "dark"
            else self._t("menu_theme_to_dark")
        )
        action_theme = QAction(theme_text, self)
        menu_action_with_svg(
            action_theme,
            "sun.svg" if self.current_theme == "dark" else "moon-stars.svg",
            "☀️" if self.current_theme == "dark" else "🌙",
        )
        action_theme.triggered.connect(self.toggle_theme)
        menu.addAction(action_theme)

        lang_text = self._t("menu_switch_english") if self.lang == LANG_ZH else self._t("menu_switch_zh")
        action_lang = QAction(lang_text, self)
        menu_action_with_svg(action_lang, "globe.svg", "🌐")
        action_lang.triggered.connect(self.toggle_language)
        menu.addAction(action_lang)
        
        menu.addSeparator()
        
        action_about = QAction(self._t("menu_about"), self)
        menu_action_with_svg(action_about, "interrogation.svg", "ℹ️")
        action_about.triggered.connect(
            lambda: ModernMessageBox(
                self,
                self._t("about_title"),
                self._t("about_body"),
                theme=self.current_theme,
                icon_type="info",
                ok_text=self._t("msg_ok"),
                icon_svg="scissors.svg",
            ).exec()
        )
        menu.addAction(action_about)

        # 固定锚点：总是从设置按钮左上方弹出（不跟随鼠标）
        menu.adjustSize()
        anchor_global = self.btn_settings.mapToGlobal(QPoint(0, 0))
        popup_pos = QPoint(
            anchor_global.x() - menu.sizeHint().width() + self.btn_settings.width(),
            anchor_global.y() - menu.sizeHint().height() - 6,
        )
        menu.exec(popup_pos)

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        app = QApplication.instance()
        app.setStyleSheet(get_style_sheet(self.current_theme))
        self.preview_frame.set_theme(self.current_theme)
        self.status_bar.setText(
            self._t("theme_switched_light")
            if self.current_theme == "light"
            else self._t("theme_switched_dark")
        )

    # --- 逻辑方法 ---
    def create_spin(self):
        s = QSpinBox()
        s.setRange(0, 99999)
        s.setFixedHeight(34)
        s.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        return s

    def _make_unit_px_label(self):
        lb = QLabel("px")
        lb.setObjectName("unit_px")
        return lb

    def add_spin_row(self, layout, label_widget, editor_widget, show_px_unit=False):
        h = QHBoxLayout()
        h.setSpacing(10)
        h.addWidget(label_widget, 0, Qt.AlignmentFlag.AlignVCenter)
        stretch = 1 if isinstance(editor_widget, QComboBox) else 0
        h.addWidget(editor_widget, stretch, Qt.AlignmentFlag.AlignVCenter)
        if show_px_unit:
            h.addWidget(self._make_unit_px_label(), 0, Qt.AlignmentFlag.AlignVCenter)
        w = QWidget()
        w.setLayout(h)
        layout.addWidget(w)
        return w, label_widget

    def on_combo_changed(self):
        idx = self.combo_shape.currentIndex()
        if idx == 1:
            self.lbl_w.setText(self._t("lbl_trap_top"))
            self.lbl_w_bottom.setText(self._t("lbl_trap_bottom"))
            self.container_align.setVisible(True)
            self.chk_lock_ratio.setEnabled(False)
            self.preview_label.set_mode("rect")
            if self.spin_w_bottom.value() == 0:
                self.spin_w_bottom.setValue(self.spin_w.value())
        elif idx == 5:
            self.lbl_w.setText(self._t("lbl_para_border"))
            self.lbl_w_bottom.setText(self._t("lbl_para_skew"))
            self.container_align.setVisible(False)
            self.chk_lock_ratio.setEnabled(False)
            self.preview_label.set_mode("rect")
        else:
            self.lbl_w.setText(self._t("lbl_w_short"))
            self.lbl_w_bottom.setText(self._t("lbl_trap_bottom"))
            self.container_align.setVisible(False)
            self.chk_lock_ratio.setEnabled(True)
            self.preview_label.set_mode("rect")
        self._refresh_wh_layout(idx)
        self.sync_selection_to_preview()

    def sync_selection_to_preview(self):
        self.preview_label.set_shape_params(
            self.combo_shape.currentIndex(),
            self.spin_x.value(), self.spin_y.value(),
            self.spin_w.value(), self.spin_h.value(),
            self.spin_w_bottom.value(),
            self.combo_align.currentIndex()
        )

    def on_mouse_rect_selection(self, x, y, w, h):
        self.block_spin_signals(True)
        self.spin_x.setValue(x); self.spin_y.setValue(y)
        self.spin_w.setValue(w); self.spin_h.setValue(h)
        if self.combo_shape.currentIndex() == 1 and self.spin_w_bottom.value() == 0:
            self.spin_w_bottom.setValue(w)
        if self.chk_lock_ratio.isChecked() and h > 0:
            self.aspect_ratio = w / h
        self.block_spin_signals(False)

    def block_spin_signals(self, block):
        for s in [self.spin_x, self.spin_y, self.spin_w, self.spin_h, self.spin_w_bottom]:
            s.blockSignals(block)

    def on_lock_ratio_toggled(self, state):
        if state == Qt.Checked and self.spin_h.value() > 0:
            self.aspect_ratio = self.spin_w.value() / self.spin_h.value()

    def _fit_scale_base(self) -> float:
        """计算当前视口下“完整显示图片”的缩放基准（定义为 100%）。"""
        pm = getattr(self.preview_label, "_original_pixmap", None)
        if pm is None:
            return 1.0
        vp = self.scroll_area.viewport()
        vw, vh = vp.width(), vp.height()
        if vw < 200 or vh < 200:
            return 1.0
        iw, ih = pm.width(), pm.height()
        if iw <= 0 or ih <= 0:
            return 1.0
        vw -= 10
        vh -= 10
        if vw <= 0 or vh <= 0:
            return 1.0
        base = min(vw / iw, vh / ih)
        return 1.0 if base < 0.05 else base

    def on_zoom_changed(self, scale):
        base = self._fit_scale_base()
        ratio = int(round((scale / base) * 100)) if base > 0 else 100
        self.lbl_zoom_ratio.setText(f"{ratio}%")

    def action_zoom_fit(self):
        vp = self.scroll_area.viewport()
        self.preview_label.zoom_to_fit(vp.width(), vp.height())

    def on_select_source(self):
        start = self._pick_dialog_start_dir(SETTINGS_KEY_LAST_SOURCE_DIR, self.source_dir)
        path = QFileDialog.getExistingDirectory(self, self._t("dlg_pick_source"), start)
        if path:
            self.source_dir = path
            self._settings_store().setValue(SETTINGS_KEY_LAST_SOURCE_DIR, path)
            self.lbl_source.setText(self._display_path(path))
            self.status_bar.setText(self._t("status_source_picked", path=self._display_path(path)))
            self.load_first_image()

    def on_select_output(self):
        start = self._pick_dialog_start_dir(SETTINGS_KEY_LAST_OUTPUT_DIR, self.output_dir)
        path = QFileDialog.getExistingDirectory(self, self._t("dlg_pick_output"), start)
        if path:
            self.output_dir = path
            self._settings_store().setValue(SETTINGS_KEY_LAST_OUTPUT_DIR, path)
            self.lbl_output.setText(self._display_path(path))
            self.status_bar.setText(self._t("status_output_set", path=self._display_path(path)))

    def load_first_image(self):
        self.image_files = [os.path.join(self.source_dir, f) for f in os.listdir(self.source_dir) 
                            if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS]
        if not self.image_files: 
            self.status_bar.setText(self._t("err_no_images"))
            ModernMessageBox(
                self,
                self._t("title_no_images"),
                self._t("msg_no_images"),
                theme=self.current_theme,
                icon_type="error",
                ok_text=self._t("msg_ok"),
            ).exec()
            return

        img = cv_imread_safe(self.image_files[0])
        if img is not None:
            h, w = img.shape[:2]
            self.spin_w.setValue(w//2); self.spin_h.setValue(h//2)
            self.spin_w_bottom.setValue(w//2)
            self.spin_x.setValue(0); self.spin_y.setValue(0)
            
            pixmap = cvimg_to_qpixmap(img)
            self.preview_label.set_original_image(pixmap)
            QApplication.processEvents()
            self.action_zoom_fit()
            self.sync_selection_to_preview()
            self.btn_start.setEnabled(True)
            self.btn_cancel.setEnabled(False)
            if not self.output_dir:
                self.output_dir = os.path.join(self.source_dir, "cropped_shapes")
                self.lbl_output.setText(self._display_path(self.output_dir))
            self.status_bar.setText(self._t("status_load_ok", n=len(self.image_files)))

    def on_start(self):
        if not self.image_files:
            return
        idx = self.combo_shape.currentIndex()
        params = {
            'shape_type': idx,
            'x': self.spin_x.value(), 'y': self.spin_y.value(),
            'w': self.spin_w.value(), 'h': self.spin_h.value(),
            'w_bottom': self.spin_w_bottom.value(),
            'trap_align': self.combo_align.currentIndex()
        }
        self.is_processing = True
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_source.setEnabled(False)
        self.btn_output.setEnabled(False)
        self.status_bar.setText(self._t("status_processing"))
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.image_files))
        
        self.worker = CropWorker(self.image_files, self.output_dir, params)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_task_finished)
        self.worker.start()

    def on_cancel(self):
        if self.worker is None or not self.is_processing:
            return
        self.worker.stop()
        self.btn_cancel.setEnabled(False)
        self.status_bar.setText(self._t("status_canceling"))

    def on_task_finished(self, success: int, processed: int, failed: int, output_dir: str, canceled: bool):
        self.is_processing = False
        self.status_bar.setText(self._t("status_cancelled") if canceled else self._t("status_done"))
        display_out = self._display_path(output_dir)
        msg = (
            self._t("task_cancelled_body", success=success, failed=failed, processed=processed, total=len(self.image_files), path=display_out)
            if canceled
            else self._t("task_done_body", success=success, failed=failed, processed=processed, total=len(self.image_files), path=display_out)
        )
        ModernMessageBox(
            self,
            self._t("title_task_cancelled") if canceled else self._t("title_task_done"),
            msg,
            theme=self.current_theme,
            icon_type="info" if canceled else "success",
            ok_text=self._t("msg_ok"),
        ).exec()
        
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_source.setEnabled(True)
        self.btn_output.setEnabled(True)
        self.progress_bar.setValue(0)