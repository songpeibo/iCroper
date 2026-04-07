# -*- coding: utf-8 -*-
"""应用界面文案：简体中文 / English。"""

from __future__ import annotations

LANG_ZH = "zh_CN"
LANG_EN = "en"
DEFAULT_LANG = LANG_ZH

SETTINGS_KEY_LANGUAGE = "language"

STRINGS: dict[str, dict[str, str]] = {
    LANG_ZH: {
        "path_section_title": "1. 路径设置",
        "btn_pick_source": "选择源文件夹",
        "ph_source_folder": "请选择包含图片的文件夹...",
        "btn_pick_output": "选择保存位置",
        "ph_output_folder": "默认保存在源目录下的 cropped_shapes 文件夹",
        "preview_empty": "请先加载图片目录...",
        "params_section_title": "2. 参数设置",
        "lbl_shape": "形状选择:",
        "shape_rect": "矩形",
        "shape_trap": "参数化梯形",
        "shape_tri": "三角形",
        "shape_circle": "圆形",
        "shape_star": "五角星",
        "shape_para": "平行四边形",
        "lbl_trap_align": "梯形对齐:",
        "align_center": "居中对齐（等腰）",
        "align_left": "左直角",
        "align_right": "右直角",
        "chk_lock_ratio": "锁定宽高比",
        "lbl_x": "X:",
        "lbl_y": "Y:",
        "lbl_w_short": "W:",
        "lbl_h": "H:",
        "lbl_trap_top": "上底宽:",
        "lbl_trap_bottom": "下底宽:",
        "lbl_para_border": "边框宽:",
        "lbl_para_skew": "倾斜偏移:",
        "btn_start": "开始批量处理",
        "btn_cancel": "停止处理",
        "status_ready": "就绪",
        "settings_tooltip": "设置",
        "menu_theme_to_light": "切换至日间模式 (Light)",
        "menu_theme_to_dark": "切换至夜间模式 (Dark)",
        "menu_switch_english": "Switch to English",
        "menu_switch_zh": "切换为简体中文",
        "menu_about": "关于 iCroper",
        "about_title": "关于 iCroper",
        "about_body": "iCroper v1.0\n轻量高效的批量图形裁剪工具。",
        "theme_switched_light": "已切换至日间模式",
        "theme_switched_dark": "已切换至夜间模式",
        "lang_switched_zh": "已切换为简体中文",
        "lang_switched_en": "Switched to English",
        "dlg_pick_source": "选择源文件夹",
        "dlg_pick_output": "选择保存文件夹",
        "status_source_picked": "已选择源目录: {path}",
        "status_output_set": "输出目录设置为: {path}",
        "err_no_images": "错误: 该目录下没有找到支持的图片",
        "title_no_images": "未找到图片",
        "msg_no_images": "请检查所选文件夹是否包含支持的图片格式。",
        "status_load_ok": "图片加载成功，共 {n} 张",
        "status_processing": "正在处理...",
        "status_canceling": "正在停止...",
        "status_cancelled": "已停止处理",
        "status_done": "处理完成",
        "title_task_done": "任务完成",
        "title_task_cancelled": "任务已停止",
        "task_done_body": "任务完成！\n成功: {success}\n失败: {failed}\n已处理: {processed}/{total}\n保存在: {path}",
        "task_cancelled_body": "任务已停止。\n成功: {success}\n失败: {failed}\n已处理: {processed}/{total}\n已保存到: {path}",
        "msg_ok": "好 的",
    },
    LANG_EN: {
        "path_section_title": "1. Paths",
        "btn_pick_source": "Source folder",
        "ph_source_folder": "Choose a folder with images...",
        "btn_pick_output": "Output folder",
        "ph_output_folder": "Default: cropped_shapes under the source folder",
        "preview_empty": "Load an image folder to preview...",
        "params_section_title": "2. Parameters",
        "lbl_shape": "Shape:",
        "shape_rect": "Rectangle",
        "shape_trap": "Parametric trapezoid",
        "shape_tri": "Triangle",
        "shape_circle": "Circle",
        "shape_star": "Star",
        "shape_para": "Parallelogram",
        "lbl_trap_align": "Trapezoid align:",
        "align_center": "Center (isosceles)",
        "align_left": "Left vertical",
        "align_right": "Right vertical",
        "chk_lock_ratio": "Lock aspect ratio",
        "lbl_x": "X:",
        "lbl_y": "Y:",
        "lbl_w_short": "W:",
        "lbl_h": "H:",
        "lbl_trap_top": "Top width:",
        "lbl_trap_bottom": "Bottom width:",
        "lbl_para_border": "Border width:",
        "lbl_para_skew": "Skew offset:",
        "btn_start": "Start batch crop",
        "btn_cancel": "Stop",
        "status_ready": "Ready",
        "settings_tooltip": "Settings",
        "menu_theme_to_light": "Switch to light mode",
        "menu_theme_to_dark": "Switch to dark mode",
        "menu_switch_english": "Switch to English",
        "menu_switch_zh": "切换为简体中文",
        "menu_about": "About iCroper",
        "about_title": "About iCroper",
        "about_body": "iCroper v1.0\nA lightweight tool for batch shape-based image cropping.",
        "theme_switched_light": "Switched to light mode",
        "theme_switched_dark": "Switched to dark mode",
        "lang_switched_zh": "已切换为简体中文",
        "lang_switched_en": "Switched to English",
        "dlg_pick_source": "Select source folder",
        "dlg_pick_output": "Select output folder",
        "status_source_picked": "Source folder: {path}",
        "status_output_set": "Output folder: {path}",
        "err_no_images": "Error: no supported images in this folder",
        "title_no_images": "No images found",
        "msg_no_images": "Please choose a folder that contains supported image formats.",
        "status_load_ok": "Loaded {n} image(s)",
        "status_processing": "Processing...",
        "status_canceling": "Stopping...",
        "status_cancelled": "Cancelled",
        "status_done": "Done",
        "title_task_done": "Finished",
        "title_task_cancelled": "Cancelled",
        "task_done_body": "Done.\nSuccess: {success}\nFailed: {failed}\nProcessed: {processed}/{total}\nSaved to: {path}",
        "task_cancelled_body": "Cancelled.\nSuccess: {success}\nFailed: {failed}\nProcessed: {processed}/{total}\nSaved to: {path}",
        "msg_ok": "OK",
    },
}


def normalize_lang(code: object | None) -> str:
    if code is None:
        return DEFAULT_LANG
    c = str(code).strip()
    if not c:
        return DEFAULT_LANG
    if c in (LANG_ZH, LANG_EN):
        return c
    if c.lower().startswith("zh"):
        return LANG_ZH
    if c.lower() == "en" or c.lower().startswith("en"):
        return LANG_EN
    return DEFAULT_LANG


def tr(lang: str, key: str, **kwargs) -> str:
    lang = normalize_lang(lang)
    table = STRINGS.get(lang) or STRINGS[LANG_ZH]
    s = table.get(key)
    if s is None:
        s = STRINGS[LANG_ZH].get(key, key)
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, ValueError):
            return s
    return s


def shape_combo_labels(lang: str) -> list[str]:
    lang = normalize_lang(lang)
    return [
        tr(lang, "shape_rect"),
        tr(lang, "shape_trap"),
        tr(lang, "shape_tri"),
        tr(lang, "shape_circle"),
        tr(lang, "shape_star"),
        tr(lang, "shape_para"),
    ]


def align_combo_labels(lang: str) -> list[str]:
    lang = normalize_lang(lang)
    return [
        tr(lang, "align_center"),
        tr(lang, "align_left"),
        tr(lang, "align_right"),
    ]
