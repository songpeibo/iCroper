import cv2
import numpy as np
import os
from PySide6.QtCore import QThread, Signal
from .utils import cv_imread_safe, cv_imwrite_safe

def create_star_mask(w, h):
    """生成五角星 Mask"""
    mask = np.zeros((h, w), dtype=np.uint8)
    center = (w // 2, h // 2)
    radius_outer = min(w, h) // 2
    radius_inner = radius_outer * 0.382
    points = []
    angle = -np.pi / 2
    for i in range(10): 
        r = radius_outer if i % 2 == 0 else radius_inner
        x = center[0] + int(r * np.cos(angle))
        y = center[1] + int(r * np.sin(angle))
        points.append((x, y))
        angle += np.pi / 5
    pts = np.array([points], np.int32)
    cv2.fillPoly(mask, pts, 255)
    return mask

def safe_convert_to_bgra(img):
    """
    [新增] 安全地将图片转换为 BGRA 格式
    处理 灰度(2维)、BGR(3通道)、BGRA(4通道) 三种情况
    """
    if img is None: return None
    
    # 情况1: 灰度图 (只有高宽，没有通道维度)
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    
    # 情况2: 有通道维度
    if len(img.shape) == 3:
        channels = img.shape[2]
        if channels == 3: # BGR -> BGRA
            return cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        elif channels == 4: # 已经是 BGRA -> 直接返回
            return img
        elif channels == 1: # 单通道 -> BGRA
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
            
    # 其他情况 (如异常数据) 直接返回原图或抛错，这里选择返回原图尝试处理
    return img

def apply_crop(img, params):
    """
    params: {x, y, w, h, w_bottom, shape_type, trap_align}
    trap_align: 0=居中, 1=左直角, 2=右直角
    """
    shape_type = params.get('shape_type', 0)
    img_h, img_w = img.shape[:2]
    
    x, y, h = params['x'], params['y'], params['h']
    w_top = params['w']  
    w_bot = params.get('w_bottom', w_top)
    align = params.get('trap_align', 0)

    # === 1. 参数化梯形处理 ===
    if shape_type == 1:
        # 计算外接矩形的最大宽度
        max_w = max(w_top, w_bot)
        
        curr_w = min(max_w, img_w - x)
        curr_h = min(h, img_h - y)
        if curr_w <= 0 or curr_h <= 0: return None
        
        roi = img[y : y+curr_h, x : x+curr_w]
        
        # [修复] 使用安全转换函数
        roi = safe_convert_to_bgra(roi)
            
        mask = np.zeros((curr_h, curr_w), dtype=np.uint8)
        
        # 根据对齐方式计算顶点
        p1_x, p2_x, p3_x, p4_x = 0, w_top, w_bot, 0

        if align == 0: # 居中
            p1_x = (max_w - w_top) // 2
            p2_x = p1_x + w_top
            p3_x = (max_w - w_bot) // 2 + w_bot
            p4_x = (max_w - w_bot) // 2
            
        elif align == 2: # 右直角
            p1_x = max_w - w_top
            p2_x = max_w
            p3_x = max_w
            p4_x = max_w - w_bot

        # 生成坐标点
        pts = np.array([
            [p1_x, 0],       # 左上
            [p2_x, 0],       # 右上
            [p3_x, curr_h],  # 右下
            [p4_x, curr_h]   # 左下
        ], np.int32)
        
        cv2.fillPoly(mask, [pts], 255)
        roi[:, :, 3] = cv2.bitwise_and(roi[:, :, 3], mask)
        return roi

    # === 2. 其他常规形状 ===
    curr_w = min(w_top, img_w - x)
    curr_h = min(h, img_h - y)
    if curr_w <= 0 or curr_h <= 0: return None

    roi = img[y : y+curr_h, x : x+curr_w]
    if shape_type == 0: return roi

    # [修复] 使用安全转换函数
    roi = safe_convert_to_bgra(roi)

    mask = np.zeros((curr_h, curr_w), dtype=np.uint8)

    if shape_type == 2: # 三角形
        pts = np.array([[curr_w // 2, 0], [0, curr_h], [curr_w, curr_h]], np.int32)
        cv2.fillPoly(mask, [pts], 255)
    elif shape_type == 3: # 圆形
        cv2.ellipse(mask, (curr_w//2, curr_h//2), (curr_w//2, curr_h//2), 0, 0, 360, 255, -1)
    elif shape_type == 4: # 五角星
        mask = create_star_mask(curr_w, curr_h)
    elif shape_type == 5: # 平行四边形
        offset = params.get('w_bottom', 0)
        offset = max(-curr_w + 1, min(offset, curr_w - 1))
        
        if offset >= 0:
            pts = np.array([[0, 0], [curr_w - offset, 0], [curr_w, curr_h], [offset, curr_h]], np.int32)
        else:
            abs_offset = abs(offset)
            pts = np.array([[abs_offset, 0], [curr_w, 0], [curr_w - abs_offset, curr_h], [0, curr_h]], np.int32)
        cv2.fillPoly(mask, [pts], 255)

    roi[:, :, 3] = cv2.bitwise_and(roi[:, :, 3], mask)
    return roi

class CropWorker(QThread):
    progress_updated = Signal(int)
    finished_signal = Signal(str)

    def __init__(self, image_files, output_dir, params):
        super().__init__()
        self.image_files = image_files
        self.output_dir = output_dir
        self.params = params

    def run(self):
        if not os.path.exists(self.output_dir): 
            os.makedirs(self.output_dir)

        count = 0
        total = len(self.image_files)
        shape_type = self.params.get('shape_type', 0)
        
        prefixes = ["rect_", "trap_", "tri_", "circle_", "star_", "para_"]
        prefix = prefixes[shape_type] if shape_type < len(prefixes) else "crop_"

        for i, file_path in enumerate(self.image_files):
            img = cv_imread_safe(file_path)
            if img is not None:
                roi = apply_crop(img, self.params)
                if roi is not None:
                    filename = prefix + os.path.basename(file_path)
                    if shape_type != 0: 
                        name, _ = os.path.splitext(filename)
                        filename = name + ".png"
                    
                    save_path = os.path.join(self.output_dir, filename)
                    cv_imwrite_safe(save_path, roi)
            
            count += 1
            self.progress_updated.emit(count)

        self.finished_signal.emit(f"任务完成！\n成功处理 {count}/{total} 张。\n保存在: {self.output_dir}")