# -*- coding: utf-8 -*-
"""主窗口可复用 UI 组件（标题栏、预览外框、下拉与图标辅助函数）。"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPainterPath, QPen, QRegion
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea

from config.icons import icon_path
from config.settings import THEME_PALETTES

# 预览外框：内边距需大于描边，并给圆角内侧留空，避免内层方形视口盖住蓝色描边
PREVIEW_FRAME_BORDER = 2.0
# 内层 QScrollArea 圆角（略小于外框 22，与 margin 配套）
PREVIEW_SCROLL_CORNER_RADIUS = 14.0

# 预览工具栏 / 设置按钮 SVG 图标尺寸（与 QPushButton 固定边长配套）
TOOLBAR_ICON_SIZE = QSize(22, 22)
SETTINGS_ICON_SIZE = QSize(22, 22)
TITLE_ICON_SIZE = QSize(18, 18)
TITLE_BAR_CTL_ICON_SIZE = QSize(16, 16)


def svg_toolbar_button(
    btn: QPushButton, filename: str, size: QSize, fallback_text: str = ""
) -> None:
    p = icon_path(filename)
    icon = QIcon(p) if p else QIcon()
    pm = icon.pixmap(size)
    if (not icon.isNull()) and (not pm.isNull()):
        btn.setIcon(icon)
        btn.setIconSize(size)
        btn.setText("")
    else:
        # SVG/路径不可用时回退到字符，避免按钮空白
        btn.setIcon(QIcon())
        btn.setText(fallback_text)


def svg_title_button(
    btn: QPushButton, filename: str, size: QSize, fallback_text: str = ""
) -> None:
    """标题栏控制按钮：与工具栏图标同逻辑，但尺寸独立。"""
    svg_toolbar_button(btn, filename, size, fallback_text)


def menu_action_with_svg(
    action: QAction, filename: str, fallback_prefix: str = "", size: QSize = QSize(16, 16)
) -> None:
    p = icon_path(filename)
    icon = QIcon(p) if p else QIcon()
    pm = icon.pixmap(size)
    if (not icon.isNull()) and (not pm.isNull()):
        action.setIcon(icon)
        return
    if fallback_prefix:
        txt = action.text().strip()
        if not txt.startswith(fallback_prefix):
            action.setText(f"{fallback_prefix} {txt}")


def label_with_svg_or_text(
    label: QLabel, filename: str, size: QSize, fallback_text: str = ""
) -> None:
    p = icon_path(filename)
    icon = QIcon(p) if p else QIcon()
    pm = icon.pixmap(size)
    if (not icon.isNull()) and (not pm.isNull()):
        label.setPixmap(pm)
        label.setText("")
    else:
        label.setPixmap(QIcon().pixmap(size))
        label.setText(fallback_text)


class ThemedPreviewFrame(QFrame):
    """图片预览外框：用 paintEvent 绘制圆角与主题色描边（不依赖 QSS，避免 Fusion 下边框不显示）。"""

    CORNER_RADIUS = 22.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("themed_preview_frame")
        self._theme_name = "light"
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_theme(self, theme_name: str):
        self._theme_name = theme_name
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_inner_scroll_mask()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_inner_scroll_mask()

    def _sync_inner_scroll_mask(self):
        sa = self.findChild(QScrollArea)
        if sa is None or sa.width() <= 1 or sa.height() <= 1:
            return
        r = min(PREVIEW_SCROLL_CORNER_RADIUS, (min(sa.width(), sa.height()) - 1) * 0.5)
        if r < 1:
            sa.clearMask()
            return
        path = QPainterPath()
        path.addRoundedRect(QRectF(sa.rect()), r, r)
        sa.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pal = THEME_PALETTES.get(self._theme_name, THEME_PALETTES["light"])
        main_bg = QColor(pal["bg_main"])
        bg = QColor(pal["bg_scroll"])
        border_c = QColor(pal["accent"])
        wpen = PREVIEW_FRAME_BORDER
        inset = wpen * 0.5
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        rr = max(0.0, self.CORNER_RADIUS - inset)
        path = QPainterPath()
        path.addRoundedRect(rect, rr, rr)
        # 圆角外直角区先铺主背景，避免透明叠色异常
        painter.fillRect(self.rect(), main_bg)
        painter.fillPath(path, bg)
        pen = QPen(border_c)
        pen.setWidthF(wpen)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)


class StyledComboBox(QComboBox):
    """去掉下拉列表视图的 QFrame 边框；可选在展开前抬高 QListView，避免 Fusion+QSS 下列表高度被算短出现滚动条。"""

    def __init__(self, parent=None, *, popup_fit_all_items=False, anchor_popup_under_combo=None):
        super().__init__(parent)
        self._popup_fit_all_items = popup_fit_all_items
        # 默认同「铺满项」下拉一起：锚在组合框正下方，避免弹出层位置漂移
        self._anchor_popup_under_combo = (
            popup_fit_all_items if anchor_popup_under_combo is None else anchor_popup_under_combo
        )
        v = self.view()
        v.setFrameShape(QFrame.Shape.NoFrame)
        v.setLineWidth(0)

    def _popup_list_content_height(self):
        """与 QSS（列表项 min-height + padding、视图 padding）一致的列表内容高度，避免 minHeight 过大产生底部空白。"""
        v = self.view()
        n = self.count()
        if n <= 0:
            return 0
        fm = self.fontMetrics()
        fallback_rh = max(34, fm.height() + 12)
        # settings.py：QAbstractItemView padding:6px → 上下共 12
        total = 12
        for i in range(n):
            rh = v.sizeHintForRow(i)
            total += fallback_rh if rh < 1 else rh
        return total

    def _anchor_combo_popup_geometry(self):
        """将下拉层固定在组合框正下方、与组合框同宽，避免样式默认定位漂移或盖住下方控件的不稳定感。"""
        if not self._anchor_popup_under_combo:
            return
        view = self.view()
        if not view.isVisible():
            return
        popup = view.window()
        if popup is None or popup is self:
            return
        pos = self.mapToGlobal(QPoint(0, self.height()))
        w = max(self.width(), view.sizeHint().width())
        h = popup.height()
        popup.setGeometry(pos.x(), pos.y(), w, h)

    def showPopup(self):
        v = self.view()
        if self._popup_fit_all_items:
            n = self.count()
            if n > 0:
                h = self._popup_list_content_height()
                if h > 0:
                    v.setFixedHeight(h)
        super().showPopup()
        if self._anchor_popup_under_combo:
            QTimer.singleShot(0, self._anchor_combo_popup_geometry)

    def hidePopup(self):
        super().hidePopup()
        if self._popup_fit_all_items:
            w = self.view()
            w.setMinimumHeight(0)
            w.setMaximumHeight(16777215)


class TitleBar(QFrame):
    """无边框窗口顶栏：拖动、双击最大化、系统按钮。"""

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self._win = parent_window
        self._drag_pos = None
        self.setObjectName("app_title_bar")
        self.setFixedHeight(48)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 12, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_title_icon = QLabel("✂")
        self.lbl_title_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title_icon.setFixedSize(20, 20)
        label_with_svg_or_text(self.lbl_title_icon, "scissors.svg", TITLE_ICON_SIZE, "✂")
        lay.addWidget(self.lbl_title_icon)
        lay.addSpacing(6)

        title = QLabel("iCroper")
        title.setObjectName("app_title_label")
        lay.addWidget(title)
        lay.addStretch()

        self.btn_min = QPushButton()
        self.btn_min.setObjectName("title_ctl")
        self.btn_min.setFixedSize(48, 36)
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.clicked.connect(self._win.showMinimized)
        svg_title_button(self.btn_min, "minus-small.svg", TITLE_BAR_CTL_ICON_SIZE, "−")

        self.btn_max = QPushButton()
        self.btn_max.setObjectName("title_ctl")
        self.btn_max.setFixedSize(48, 36)
        self.btn_max.setCursor(Qt.PointingHandCursor)
        self.btn_max.clicked.connect(self._toggle_maximize)

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("title_close")
        self.btn_close.setFixedSize(48, 36)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self._win.close)
        svg_title_button(self.btn_close, "cross-small.svg", TITLE_BAR_CTL_ICON_SIZE, "×")

        ctl_row = QHBoxLayout()
        ctl_row.setSpacing(10)
        ctl_row.setContentsMargins(0, 0, 0, 0)
        ctl_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        ctl_row.addWidget(self.btn_min)
        ctl_row.addWidget(self.btn_max)
        ctl_row.addWidget(self.btn_close)
        lay.addLayout(ctl_row)
        self.sync_max_button()

    def sync_max_button(self):
        if self._win.isMaximized():
            svg_title_button(self.btn_max, "compress-alt.svg", TITLE_BAR_CTL_ICON_SIZE, "❐")
        else:
            svg_title_button(self.btn_max, "expand-arrows.svg", TITLE_BAR_CTL_ICON_SIZE, "□")

    def _toggle_maximize(self):
        if self._win.isMaximized():
            self._win.showNormal()
        else:
            self._win.showMaximized()
        self.sync_max_button()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._win.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self._win.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
