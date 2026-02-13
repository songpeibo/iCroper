from PySide6.QtWidgets import QLabel, QApplication
from PySide6.QtCore import Signal, Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QPolygon, QPixmap

class InteractableLabel(QLabel):
    selection_changed = Signal(int, int, int, int)
    polygon_changed = Signal(list)
    zoom_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignCenter)
        
        self._original_pixmap = None
        self.scale_factor = 1.0
        
        self.mode = "rect" 
        self.is_drawing = False
        self.start_pos = None
        
        self.rect_selection = QRect(0, 0, 0, 0)
        self.poly_points = []
        self.shape_type = 0
        self.w_bottom = 0 
        self.trap_align = 0 # [新增] 对齐方式: 0=居中, 1=左直角, 2=右直角

    def set_original_image(self, pixmap):
        self._original_pixmap = pixmap
        self.rect_selection = QRect(0, 0, 0, 0)
        self.poly_points = []
        self._update_display()

    def set_mode(self, mode):
        self.mode = mode
        self.poly_points = [] 
        self.update() 

    # [新增] trap_align 参数
    def set_shape_params(self, shape_type, x, y, w, h, w_bottom=0, trap_align=0):
        self.shape_type = shape_type
        self.rect_selection = QRect(x, y, w, h)
        self.w_bottom = w_bottom
        self.trap_align = trap_align
        self.update()

    def zoom_to_fit(self, view_width, view_height):
        if self._original_pixmap is None: return
        if view_width < 200 or view_height < 200: self.set_scale(1.0); return
        img_w = self._original_pixmap.width(); img_h = self._original_pixmap.height()
        view_width -= 10; view_height -= 10
        if view_width <= 0 or view_height <= 0: return
        new_scale = min(view_width / img_w, view_height / img_h)
        if new_scale < 0.05: new_scale = 1.0
        self.set_scale(new_scale)

    def set_scale(self, factor):
        self.scale_factor = max(0.01, min(factor, 50.0))
        self._update_display()
        self.zoom_changed.emit(self.scale_factor)

    def _update_display(self):
        if self._original_pixmap is None: return
        orig_sz = self._original_pixmap.size()
        new_w = int(orig_sz.width() * self.scale_factor)
        new_h = int(orig_sz.height() * self.scale_factor)
        scaled_pix = self._original_pixmap.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.FastTransformation)
        super().setPixmap(scaled_pix)
        self.adjustSize() 

    def map_to_real(self, pos):
        return QPoint(int(pos.x() / self.scale_factor), int(pos.y() / self.scale_factor))

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if event.angleDelta().y() > 0: self.set_scale(self.scale_factor * 1.1)
            else: self.set_scale(self.scale_factor * 0.9)
            event.accept()
        else: super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self._original_pixmap is None: return
        real_pos = self.map_to_real(event.pos())
        if event.button() == Qt.LeftButton:
            if self.mode == "rect":
                self.start_pos = real_pos
                self.is_drawing = True
            elif self.mode == "poly":
                if len(self.poly_points) < 4:
                    self.poly_points.append(real_pos)
                    self.update(); pts = [(p.x(), p.y()) for p in self.poly_points]; self.polygon_changed.emit(pts)
        elif event.button() == Qt.RightButton:
            if self.mode == "poly": self.poly_points = []; self.update(); self.polygon_changed.emit([])

    def mouseMoveEvent(self, event):
        if self._original_pixmap is None: return
        real_pos = self.map_to_real(event.pos())
        if self.mode == "rect" and self.is_drawing and self.start_pos:
            rect = QRect(self.start_pos, real_pos).normalized()
            self.rect_selection = rect
            self.selection_changed.emit(rect.x(), rect.y(), rect.width(), rect.height())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.mode == "rect" and event.button() == Qt.LeftButton:
            self.is_drawing = False
            if self.start_pos:
                real_pos = self.map_to_real(event.pos())
                rect = QRect(self.start_pos, real_pos).normalized()
                self.selection_changed.emit(rect.x(), rect.y(), max(1, rect.width()), max(1, rect.height()))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._original_pixmap is None: return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.scale_factor, self.scale_factor)
        line_w = max(1.0, 2.0 / self.scale_factor)
        point_r = max(2.0, 4.0 / self.scale_factor)

        x, y, w_box, h = self.rect_selection.getRect()
        pen = QPen(QColor(0, 255, 0), line_w)
        painter.setPen(pen)

        if self.mode == "rect":
            if self.shape_type == 0: # Rect
                painter.drawRect(x, y, w_box, h)
            
            elif self.shape_type == 1: # Trapezoid
                w_top = w_box
                w_bot = self.w_bottom
                max_w = max(w_top, w_bot)
                
                # === 核心修改：根据对齐方式计算绘图顶点 ===
                
                # 默认：左直角 (align=1)
                x1, x2 = x, x + w_top
                x3, x4 = x + w_bot, x
                
                if self.trap_align == 0: # 居中
                    x1 = x + (max_w - w_top) // 2
                    x2 = x1 + w_top
                    x3 = x + (max_w - w_bot) // 2 + w_bot
                    x4 = x + (max_w - w_bot) // 2
                    
                elif self.trap_align == 2: # 右直角
                    # 右边是直的，靠右对齐
                    x2 = x + max_w
                    x1 = x2 - w_top
                    x3 = x + max_w
                    x4 = x3 - w_bot

                y1, y2 = y, y
                y3, y4 = y + h, y + h

                # 绘制外接矩形 (虚线)
                pen_dash = QPen(QColor(255, 255, 0, 150), line_w, Qt.DashLine)
                painter.setPen(pen_dash)
                painter.drawRect(x, y, max_w, h)

                # 绘制梯形实体
                painter.setPen(QPen(QColor(0, 255, 0), line_w))
                painter.drawPolygon(QPolygon([QPoint(x1, y1), QPoint(x2, y2), QPoint(x3, y3), QPoint(x4, y4)]))

            elif self.shape_type == 2: # Tri
                painter.drawPolygon(QPolygon([QPoint(x, y), QPoint(x+w_box, y), QPoint(x+w_box//2, y+h)]))
            elif self.shape_type == 3: # Circle
                painter.drawEllipse(x, y, w_box, h)
            elif self.shape_type == 4: # Star
                painter.drawRect(x, y, w_box, h)
                painter.drawText(x, y-5, "★ Star")
                
            elif self.shape_type == 5: # Parallelogram
                offset = self.w_bottom
                offset = max(-w_box + 1, min(offset, w_box - 1)) # 限制偏移量绝对值不超过外框总宽
                
                if offset >= 0:
                    x1, y1 = x, y
                    x2, y2 = x + w_box - offset, y
                    x3, y3 = x + w_box, y + h
                    x4, y4 = x + offset, y + h
                else:
                    abs_offset = abs(offset)
                    x1, y1 = x + abs_offset, y
                    x2, y2 = x + w_box, y
                    x3, y3 = x + w_box - abs_offset, y + h
                    x4, y4 = x, y + h
                
                # 绘制外接矩形 (虚线)
                pen_dash = QPen(QColor(255, 255, 0, 150), line_w, Qt.DashLine)
                painter.setPen(pen_dash)
                painter.drawRect(x, y, w_box, h)
                
                # 绘制平行四边形实体
                painter.setPen(QPen(QColor(0, 255, 0), line_w))
                painter.drawPolygon(QPolygon([QPoint(x1, y1), QPoint(x2, y2), QPoint(x3, y3), QPoint(x4, y4)]))

        elif self.mode == "poly" and self.poly_points:
            painter.setPen(QPen(QColor(0, 255, 255), point_r * 2))
            for pt in self.poly_points: painter.drawPoint(pt)
            painter.setPen(QPen(QColor(0, 255, 255), line_w))
            if len(self.poly_points) > 1: painter.drawPolyline(self.poly_points)
            if len(self.poly_points) == 4:
                painter.drawLine(self.poly_points[-1], self.poly_points[0])
                painter.setBrush(QColor(0, 255, 255, 50))
                painter.drawPolygon(QPolygon(self.poly_points))