# ✂️ iCroper - 批量图片形状裁剪工具

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![OpenCV](https://img.shields.io/badge/CV-OpenCV-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

**iCroper** 是一个基于 Python (PySide6 + OpenCV) 开发的高效桌面应用程序，专为批量处理图片裁剪需求设计。

它不仅支持常规的矩形裁剪，还专注于**异形裁剪**（梯形、圆形、五角星等），并支持生成透明背景的 PNG 图片，非常适合用于数据集制作、图像预处理或科研素材准备。

---

## ✨ 核心功能 (Features)

* **📂 批量自动化**：
    * 指定源文件夹和输出文件夹，一键处理成百上千张图片。
    * 支持多线程处理，界面不卡顿，实时显示进度条。
* **📐 丰富的形状支持**：
    * **矩形 (Rectangle)**：支持锁定宽高比。
    * **梯形 (Trapezoid)**：支持**居中对齐**、**左直角对齐**、**右直角对齐**，可自定义下底宽度。
    * **平行四边形 (Parallelogram)**：支持自定义倾斜偏移量。
    * **其他形状**：三角形、圆形、五角星。
* **👁️ 交互式预览 (Interactive UI)**：
    * **所见即所得**：在预览图上直接拖拽鼠标画框。
    * **双向同步**：拖拽画框会自动更新右侧参数，修改右侧参数也会实时更新预览框。
    * **缩放查看**：支持鼠标滚轮或按钮缩放图片，便于像素级微调。
* **🖼️ 透明通道输出**：
    * 裁剪非矩形形状（如圆形、星形）时，背景自动处理为**透明 (Alpha Channel)**。
* **🛠️ 鲁棒性设计**：
    * 支持中文路径读写。
    * 自动处理不同格式（灰度/RGB/RGBA）的图片源。

---

## 🛠️ 安装与运行 (Installation)

### 1. 环境要求
* Python 3.10 或更高版本

### 2. 克隆项目
```bash
git clone [https://github.com/你的用户名/iCroper.git](https://github.com/你的用户名/iCroper.git)
cd iCroper
```

### 3.安装依赖

建议使用虚拟环境:

```bash
# 创建虚拟环境 (可选)
python -m venv venv
# 激活虚拟环境 (Windows)
venv\Scripts\activate
# 激活虚拟环境 (Mac/Linux)
source venv/bin/activate
```

安装所需库：

```bash
pip install PySide6 opencv-python numpy
```

### 4.运行程序

```bash
python main.py
```

---

## 📖 使用指南 (Usage)

### 1.设置路径：

- 点击 “选择源文件夹” 加载需要处理的图片（支持 .jpg, .png, .bmp, .tif 等）。
- 点击 “选择保存位置” 设置输出目录（默认在源目录下创建 cropped_shapes）。

### 2.调整裁剪区域：

- 在左侧预览图中，按住鼠标左键拖拽以绘制裁剪框。
- 或者在右侧参数区直接输入 X, Y, W, H 数值。
- 使用鼠标滚轮放大/缩小预览图以查看细节。

### 3.选择形状与参数：

- 在右侧下拉框选择形状（如“参数化梯形”）。
- 梯形模式：设置“下底宽”并选择对齐方式（居中/左直角/右直角）。
- 平行四边形：设置“倾斜偏移”量。

### 4.开始处理：

- 点击底部的 “开始执行” 按钮。
- 等待进度条跑完，完成后会弹出提示框。

---

## 📦 打包为可执行文件 (Build EXE)

本项目已针对 PyInstaller 进行了路径优化，可以直接打包为独立的 .exe 文件分享给他人使用。

### 1.安装 PyInstaller：

```bash
pip install pyinstaller
```

### 2.执行打包命令（在项目根目录下）：

```bash
pyinstaller -F -w main.py --name iCroper --icon iCroper/logo.ico --add-data "iCroper/ui;ui" --add-data "iCroper/config;config"
```

(注意：请根据你的实际目录结构调整 --add-data 的源路径，如果 main.py 在 iCroper 文件夹内，可能需要调整为 --add-data "ui;ui")

---

### 📂 项目结构 (Project Structure)

```
iCroper/
├── main.py                 # 程序入口 (包含环境修复逻辑)
├── config/
│   └── settings.py         # 全局配置 (样式、支持的文件格式)
├── core/
│   ├── processor.py        # 图像处理核心算法 (Mask生成、裁剪)
│   └── utils.py            # 工具函数 (中文路径读写、QPixmap转换)
└── ui/
    ├── main_window.py      # 主窗口逻辑
    └── custom_widgets.py   # 自定义控件 (交互式预览Label、绘图逻辑)
```

---

## 📝 许可证 (License)

本项目采用 MIT License 开源。这意味着你可以自由地使用、修改和分发本项目，但请保留原作者的版权声明。

---

Developed with ❤️ by SPB