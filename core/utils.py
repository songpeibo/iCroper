import cv2
import numpy as np
import os
from PySide6.QtGui import QPixmap, QImage

# 纯粹的工具函数，不涉及任何业务逻辑或 UI 状态。

def cv_imread_safe(file_path):
    try:
        raw_data = np.fromfile(file_path, dtype=np.uint8)
        return cv2.imdecode(raw_data, cv2.IMREAD_UNCHANGED)
    except Exception as e:
        print(f"Read Error: {e}")
        return None

def cv_imwrite_safe(file_path, img):
    try:
        ext = os.path.splitext(file_path)[1]
        success, img_buf = cv2.imencode(ext, img)
        if success:
            img_buf.tofile(file_path)
            return True
    except Exception as e:
        print(f"Write Error: {e}")
    return False

def cvimg_to_qpixmap(cv_img):
    if cv_img is None: return None
    
    # 归一化处理
    if cv_img.dtype == np.uint16 or cv_img.dtype == np.float32:
        cv_img = cv2.normalize(cv_img, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')

    if len(cv_img.shape) == 3:
        if cv_img.shape[2] == 4:
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
            fmt = QImage.Format_RGBA8888
        else:
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            fmt = QImage.Format_RGB888
        h, w, _ = img_rgb.shape
        qimg = QImage(img_rgb.data, w, h, w * img_rgb.shape[2], fmt)
    else:
        h, w = cv_img.shape
        qimg = QImage(cv_img.data, w, h, w, QImage.Format_Grayscale8)
    
    return QPixmap.fromImage(qimg.copy())