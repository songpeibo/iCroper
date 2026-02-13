import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QSpinBox, QProgressBar, 
                               QMessageBox, QGroupBox, QScrollArea, QLineEdit, 
                               QComboBox, QCheckBox, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.utils import cv_imread_safe, cvimg_to_qpixmap
from core.processor import CropWorker
from config.settings import VALID_EXTENSIONS
from ui.custom_widgets import InteractableLabel 

class BatchCropApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("iCroper")
        self.resize(1200, 850)
        
        self.image_files = []
        self.source_dir = ""
        self.output_dir = ""
        self.worker = None 
        self.aspect_ratio = 1.0 

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- 1. 路径设置 ---
        path_group = QGroupBox("1. 路径设置")
        path_layout = QVBoxLayout(path_group)
        def create_path_row(btn_text, placeholder):
            layout = QHBoxLayout()
            btn = QPushButton(btn_text); btn.setFixedWidth(120)
            edit = QLineEdit(); edit.setPlaceholderText(placeholder); edit.setReadOnly(True)
            layout.addWidget(btn); layout.addWidget(edit)
            return btn, edit, layout
        self.btn_source, self.lbl_source, l1 = create_path_row("选择源文件夹", "...")
        self.btn_output, self.lbl_output, l2 = create_path_row("选择保存位置", "...")
        path_layout.addLayout(l1); path_layout.addLayout(l2)
        main_layout.addWidget(path_group)

        # --- 2. 预览与参数 ---
        content_layout = QHBoxLayout()
        
        # 左侧预览区
        preview_layout = QVBoxLayout()
        zoom_layout = QHBoxLayout()
        self.btn_zoom_in = QPushButton("放大 (+)")
        self.btn_zoom_out = QPushButton("缩小 (-)")
        self.btn_zoom_fit = QPushButton("自适应窗口")
        self.lbl_zoom_ratio = QLabel("100%")
        zoom_layout.addWidget(self.btn_zoom_in); zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_zoom_fit); zoom_layout.addWidget(self.lbl_zoom_ratio)
        zoom_layout.addStretch()
        preview_layout.addLayout(zoom_layout)

        self.scroll_area = QScrollArea()
        self.preview_label = InteractableLabel()
        self.preview_label.setText("请加载图片...")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.preview_label)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #505050;")
        preview_layout.addWidget(self.scroll_area)
        content_layout.addLayout(preview_layout, stretch=3)

        # === 右侧设置区 ===
        settings_group = QGroupBox("2. 参数设置")
        settings_layout = QVBoxLayout(settings_group)
        
        self.combo_shape = QComboBox()
        self.combo_shape.addItems(["矩形 (Rect)", "参数化梯形 (Trapezoid)", "三角形 (Tri)", "圆形 (Circle)", "五角星 (Star)", "平行四边形 (Parallelogram)"])
        settings_layout.addWidget(QLabel("形状选择:"))
        settings_layout.addWidget(self.combo_shape)

        # [新增] 梯形对齐方式 (默认隐藏)
        self.lbl_align = QLabel("梯形对齐:")
        self.combo_align = QComboBox()
        self.combo_align.addItems(["居中对齐 (等腰)", "左直角 (Left Vertical)", "右直角 (Right Vertical)"])
        self.container_align, _ = self.add_spin_row(settings_layout, self.lbl_align, self.combo_align)
        self.container_align.setVisible(False)

        # 创建数值输入框
        self.spin_x = self.create_spin(); self.spin_y = self.create_spin()
        self.spin_w = self.create_spin(); self.spin_h = self.create_spin()
        self.spin_w_bottom = self.create_spin()
        self.spin_w_bottom.setRange(-99999, 99999) # 允许偏移量为负数
        
        self.chk_lock_ratio = QCheckBox("锁定宽高比")
        settings_layout.addWidget(self.chk_lock_ratio)

        # X, Y
        self.add_spin_row(settings_layout, QLabel("X (起点):"), self.spin_x)
        self.add_spin_row(settings_layout, QLabel("Y (起点):"), self.spin_y)
        
        # W
        self.lbl_w = QLabel("宽度 W:")
        self.add_spin_row(settings_layout, self.lbl_w, self.spin_w)

        # W_Bottom (下底)
        self.lbl_w_bottom = QLabel("下底宽:")
        self.container_w_bottom, _ = self.add_spin_row(settings_layout, self.lbl_w_bottom, self.spin_w_bottom)
        self.container_w_bottom.setVisible(False)

        # H
        self.add_spin_row(settings_layout, QLabel("高度 H:"), self.spin_h)

        settings_layout.addStretch()
        content_layout.addWidget(settings_group, stretch=1)
        main_layout.addLayout(content_layout)

        # --- 3. 底部操作 ---
        self.progress_bar = QProgressBar()
        self.btn_start = QPushButton("开始执行")
        self.btn_start.setEnabled(False)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.btn_start)

        # --- 信号绑定 ---
        self.btn_source.clicked.connect(self.on_select_source)
        self.btn_output.clicked.connect(self.on_select_output)
        self.btn_start.clicked.connect(self.on_start)
        
        for w in [self.spin_x, self.spin_y, self.spin_w, self.spin_h, self.spin_w_bottom]:
            w.valueChanged.connect(self.sync_selection_to_preview)
        
        self.combo_shape.currentIndexChanged.connect(self.on_combo_changed)
        self.combo_align.currentIndexChanged.connect(self.sync_selection_to_preview) # [新增] 对齐改变刷新
        self.preview_label.selection_changed.connect(self.on_mouse_rect_selection)
        self.chk_lock_ratio.stateChanged.connect(self.on_lock_ratio_toggled)

        self.btn_zoom_in.clicked.connect(lambda: self.preview_label.set_scale(self.preview_label.scale_factor * 1.25))
        self.btn_zoom_out.clicked.connect(lambda: self.preview_label.set_scale(self.preview_label.scale_factor * 0.8))
        self.btn_zoom_fit.clicked.connect(self.action_zoom_fit)
        self.preview_label.zoom_changed.connect(self.on_zoom_changed)

    def create_spin(self):
        s = QSpinBox(); s.setRange(0, 99999); s.setSuffix(" px")
        return s

    def add_spin_row(self, layout, label_widget, spin_widget):
        h = QHBoxLayout()
        h.addWidget(label_widget)
        h.addWidget(spin_widget)
        w = QWidget(); w.setLayout(h)
        layout.addWidget(w)
        return w, label_widget

    def on_combo_changed(self):
        idx = self.combo_shape.currentIndex()
        if idx == 1: # 参数化梯形
            self.lbl_w.setText("上底宽:")
            self.lbl_w_bottom.setText("下底宽:")
            self.container_w_bottom.setVisible(True)
            self.container_align.setVisible(True) # 显示对齐选项
            self.chk_lock_ratio.setEnabled(False)
            self.preview_label.set_mode("rect")
            
            if self.spin_w_bottom.value() == 0:
                self.spin_w_bottom.setValue(self.spin_w.value())
                
        elif idx == 5: # 平行四边形
            self.lbl_w.setText("边框宽:")
            self.lbl_w_bottom.setText("倾斜偏移:")
            self.container_w_bottom.setVisible(True)
            self.container_align.setVisible(False)
            self.chk_lock_ratio.setEnabled(False)
            self.preview_label.set_mode("rect")
            
        else: # 其他模式
            self.lbl_w.setText("宽度 W:")
            self.lbl_w_bottom.setText("下底宽:")
            self.container_w_bottom.setVisible(False)
            self.container_align.setVisible(False)
            self.chk_lock_ratio.setEnabled(True)
            self.preview_label.set_mode("rect")

        self.sync_selection_to_preview()

    def sync_selection_to_preview(self):
        self.preview_label.set_shape_params(
            self.combo_shape.currentIndex(),
            self.spin_x.value(), self.spin_y.value(),
            self.spin_w.value(), self.spin_h.value(),
            self.spin_w_bottom.value(),
            self.combo_align.currentIndex() # 传入对齐方式
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

    def on_zoom_changed(self, scale):
        self.lbl_zoom_ratio.setText(f"{int(scale * 100)}%")

    def action_zoom_fit(self):
        vp = self.scroll_area.viewport()
        self.preview_label.zoom_to_fit(vp.width(), vp.height())

    def on_select_source(self):
        path = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if path:
            self.source_dir = path
            self.lbl_source.setText(path)
            self.load_first_image()

    def on_select_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if path:
            self.output_dir = path
            self.lbl_output.setText(path)

    def load_first_image(self):
        self.image_files = [os.path.join(self.source_dir, f) for f in os.listdir(self.source_dir) 
                            if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS]
        if not self.image_files: return QMessageBox.warning(self, "提示", "未找到图片")

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
            if not self.output_dir:
                self.output_dir = os.path.join(self.source_dir, "cropped_shapes")
                self.lbl_output.setText(self.output_dir)

    def on_start(self):
        idx = self.combo_shape.currentIndex()
        params = {
            'shape_type': idx,
            'x': self.spin_x.value(), 'y': self.spin_y.value(),
            'w': self.spin_w.value(), 'h': self.spin_h.value(),
            'w_bottom': self.spin_w_bottom.value(),
            'trap_align': self.combo_align.currentIndex() # 传入对齐方式
        }

        self.btn_start.setEnabled(False)
        self.progress_bar.setMaximum(len(self.image_files))
        
        self.worker = CropWorker(self.image_files, self.output_dir, params)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_task_finished)
        self.worker.start()

    def on_task_finished(self, msg):
        QMessageBox.information(self, "完成", msg)
        self.btn_start.setEnabled(True)
        self.progress_bar.setValue(0)