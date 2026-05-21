import os
import subprocess
from config import get_browser_dir

def main():
    # 强行劫持下载路径
    target_dir = get_browser_dir()
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = target_dir

    print("==================================================")
    print(f"🚀 正在将 Chromium 内核独立下载至便携目录：")
    print(f"📁 {target_dir}")
    print("==================================================")

    # 调用系统命令执行下载
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("\n✅ 下载完成！Playwright 内核已彻底实现便携。")
        print("💡 以后打包分发时，只需确保 data 文件夹与 .exe 在同一目录即可！")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 下载失败: {e}")

if __name__ == "__main__":
    main()