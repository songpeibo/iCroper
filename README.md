# iCroper

iCroper 是一款基于 Python 的桌面批量图片裁剪工具，支持矩形与多种异形裁剪，适用于需要快速批处理图片的场景。

## 基础信息

- 开发语言：Python 3.10+
- GUI 框架：PySide6
- 图像处理：OpenCV
- 许可证：MIT License

## 功能

- 批量处理图片（源目录 -> 输出目录）
- 支持矩形、梯形、平行四边形、三角形、圆形、五角星裁剪
- 非矩形裁剪自动输出透明 PNG
- 预览区交互编辑（拖拽、缩放、参数同步）
- 处理中可取消任务
- 任务完成后显示处理统计（成功/失败/总数）
- 支持简体中文与 English 界面切换
- 记忆常用路径与语言设置

## 安装与运行

```bash
pip install PySide6 opencv-python numpy
python main.py
```

## 打包

```powershell
# 默认 onedir（推荐）
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1

# onefile 单文件
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1 -OneFile
```

## 使用方式

1. 选择源文件夹
2. 选择输出文件夹
3. 设置裁剪区域与形状参数
4. 点击开始批量处理

## 作者

SPB