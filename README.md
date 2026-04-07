# ✂️ iCroper - 批量图片形状裁剪工具

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![OpenCV](https://img.shields.io/badge/CV-OpenCV-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

**iCroper** 是一个基于 Python（PySide6 + OpenCV）开发的高效桌面应用程序，专为批量处理图片裁剪需求设计。

它不仅支持常规的矩形裁剪，还专注于**异形裁剪**（梯形、圆形、五角星等），并支持生成透明背景的 PNG 图片，非常适合用于数据集制作、图像预处理或科研素材准备。

---

## ✨ 核心功能 (Features)

* **📂 批量自动化**：
    * 指定源文件夹和输出文件夹，一键处理多张图片。
    * 后台线程处理，界面不卡顿，实时显示进度条。
    * 处理过程中可随时取消任务；结束后弹出统计（成功 / 失败 / 已处理数）。
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
* **🌐 国际化与体验**：
    * 内置**简体中文 / English**，运行时切换并记忆。
    * 文件夹选择对话框起始路径：**上次记忆路径** → 当前已选 → 系统「图片」目录 → 用户主目录（不依赖当前工作目录，源码与打包 exe 行为一致）。
* **🛠️ 鲁棒性设计**：
    * 支持中文路径读写。
    * 自动处理不同格式（灰度 / RGB / RGBA）的图片源。
* **🎨 界面**：
    * 无框圆角窗口、SVG 图标资源、主题样式可扩展（`config/settings.py`）。

---

## 🛠️ 安装与运行 (Installation)

### 1. 环境要求

* Python 3.10 或更高版本

### 2. 克隆项目

```bash
git clone https://github.com/songpeibo/iCroper.git
cd iCroper
```

### 3. 安装依赖

建议使用虚拟环境：

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
pip install -r requirements.txt
```

（等价于安装 `PySide6`、`opencv-python`、`numpy`。）

### 4. 运行程序

```bash
python main.py
```

---

## 📥 预编译版本下载 (GitHub Releases)

若不想安装 Python，可直接使用 Release 里附带的 Windows 可执行文件。

1. 打开本仓库的 **Releases** 页面：  
   [https://github.com/songpeibo/iCroper/releases](https://github.com/songpeibo/iCroper/releases)
2. 在列表中选择**最新的**一条 Release（或你需要的版本）。
3. 在 **Assets** 区域下载附件，常见有两种：
   * **文件夹版（onedir，推荐）**：文件名多为 `iCroper-vx.x.x-win64-onedir.zip` 或类似。  
     解压后进入文件夹，运行其中的 `iCroper.exe`。请**保留同目录下的 `_internal` 等文件**，不要只拷贝单个 exe。
   * **单文件版（onefile，可选）**：单个 `iCroper.exe`。拷贝该文件到任意位置即可运行；首次启动可能略慢。
4. 若浏览器或 Windows 安全中心提示「未知发布者」，请选择「仍要运行」（未签名应用较常见）。

**维护者发布 Release 时请注意：** 创建正式发布前需填写**合法标签名**（例如 `v1.0.0`），不能为空或含空格；可先本地执行 `git tag v1.0.0` 并 `git push origin v1.0.0`，再在网页上选择该标签并上传上述 zip / exe。

---

## 📖 使用指南 (Usage)

### 1. 设置路径

* 点击「选择源文件夹」加载需要处理的图片（支持 `.jpg`、`.png`、`.bmp`、`.tif`、`.webp` 等）。
* 点击「选择保存位置」设置输出目录；若未选择，默认在源目录下创建 `cropped_shapes`。

### 2. 调整裁剪区域

* 在左侧预览图中，按住鼠标左键拖拽以绘制裁剪框。
* 或在右侧参数区直接输入 X、Y、W、H 数值。
* 使用鼠标滚轮或工具栏按钮放大 / 缩小预览图以查看细节。

### 3. 选择形状与参数

* 在右侧下拉框选择形状（如「参数化梯形」）。
* 梯形模式：设置「下底宽」并选择对齐方式（居中 / 左直角 / 右直角）。
* 平行四边形：设置倾斜偏移量。

### 4. 开始处理

* 点击底部的「**开始批量处理**」按钮。
* 需要中途停止时，点击「**停止处理**」。
* 进度条跑完后会弹出结果统计提示框。

---

## 📦 打包为可执行文件 (Build EXE)

项目入口 `main.py` 已包含 Qt 插件路径处理；推荐使用仓库内脚本一键打包（自动安装依赖、嵌入 `logo.ico`、收集 OpenCV / QtSvg 等）。

### Windows（在项目根目录）

```powershell
# 默认 onedir（推荐，需整文件夹分发）
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1

# 可选：单文件 exe
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1 -OneFile
```

产物路径：

* **onedir**：`dist\iCroper\iCroper.exe`（请与 `dist\iCroper\_internal` 等文件一并复制）
* **onefile**：`dist\iCroper.exe`

---

## 📂 项目结构 (Project Structure)

```
iCroper/
├── main.py                  # 程序入口（Qt 插件路径、应用图标）
├── logo.ico                 # 应用 / 打包图标
├── requirements.txt
├── README.md
├── scripts/
│   └── build.ps1            # PyInstaller 打包脚本
├── config/
│   ├── settings.py          # 主题样式、扩展名、QSettings 键等
│   ├── i18n.py              # 中英文文案
│   └── icons.py             # SVG 图标路径解析（兼容打包）
├── core/
│   ├── processor.py         # 裁剪 Worker、批量与取消
│   └── utils.py             # 中文路径读写、QPixmap 转换等
├── resources/
│   └── icons/               # SVG 图标资源
└── ui/
    ├── main_window.py       # 主窗口逻辑
    ├── window_components.py # 标题栏、预览框、下拉等组件
    └── custom_widgets.py    # 交互式预览、消息框等
```

---

## 📝 许可证 (License)

本项目采用 **MIT License** 开源。你可以自由地使用、修改和分发本项目，但请保留原作者的版权声明。

---

Developed with ❤️ by SPB
