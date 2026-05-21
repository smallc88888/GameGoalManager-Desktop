import os
import sys

def get_data_dir():
    """
    获取便携化 (Portable) 的核心数据目录。
    能自动识别 PyInstaller 打包环境，确保数据绝对安全。
    """
    if getattr(sys, 'frozen', False):
        # 如果是被 PyInstaller 打包成了 .exe，使用 .exe 所在的物理目录
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是开发阶段的 python app.py，使用当前项目根目录
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 在可执行文件旁边建立一个名为 'data' 的保险箱文件夹
    data_dir = os.path.join(base_path, "data")

    # 初始化资产目录结构
    os.makedirs(os.path.join(data_dir, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "exports"), exist_ok=True)

    return data_dir

def get_browser_dir():
    """
    获取自带 Chromium 内核的物理路径。
    我们将内核强行关进 data/playwright_browsers 这个保险箱里。
    """
    browser_dir = os.path.join(get_data_dir(), "playwright_browsers")
    os.makedirs(browser_dir, exist_ok=True)
    return browser_dir