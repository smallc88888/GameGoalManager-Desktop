<div align="center">
  
# 🎮 GameGoalManager (Desktop Portable Edition)
**开箱即用的便携式游戏生涯档案室**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated_Rendering-2EAD33.svg)](https://playwright.dev/)
[![PyInstaller](https://img.shields.io/badge/PyInstaller-Standalone-FF6A00.svg)](https://pyinstaller.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*此仓库为 GameGoalManager 的 Windows 原生桌面分支。采用纯绿色便携化（Portable）架构设计，无需安装 Python 环境，所有数据与内核物理隔离，实现真正的数据保险箱体验。*

</div>

---

## ✨ 核心特性 (Core Features)

* **🌐 数据检索引擎**：底层直连 RAWG API，提供精准的游戏信息拉取与封面抓取，内置异常分型诊断。
* **💾 绿色便携化持久层 (Portable Data)**：基于 `SQLAlchemy` 与 SQLite 构建。系统自动在程序根目录生成独立 `data/` 保险箱，所有数据库、配置与玩家 WebP 截图均实现目录级隔离，完美支持 U 盘随身携带。
* **📸 自动化无头渲染长图引擎**：后端内嵌 `Playwright` Chromium 无头浏览器，利用 Jinja2 与纯 CSS 动态生成长图。内置“自清理机制 (Self-Cleaning)”，杜绝磁盘空间无限制膨胀。
* **🖥️ 桌面级应用构建**：采用 `pywebview` 将 B/S 架构无缝包装为原生桌面应用，跨界调用系统底层 API 实现原生文件存盘交互。

---

## 🛠️ 技术栈与架构 (Tech Stack)

* **桌面与打包**: `pywebview` (原生视窗) + `PyInstaller` (二进制构建)
* **后端引擎**: `Python 3` + `Flask` (MVC 路由)
* **持久化**: `SQLAlchemy` + `SQLite` (本地外置数据库)
* **自动化渲染**: `Playwright` (旁路挂载的 Chromium 内核)
* **前端视图**: 原生 `HTML5` + `CSS3` + `JavaScript` (Fetch API)

---

## 💡 技术难点 (Technical Highlights)

> *“本项目在桌面化重构过程中，重点攻克了以下工程痛点：”*

1. **规避 PyInstaller `_MEIPASS` 陷阱与 Chromium 旁路挂载 (核心亮点)**
   * **痛点**：若将 Playwright 数百兆的内核强制打入单文件 `.exe`，不仅会导致跨设备找不到内核崩溃，还会使软件冷启动解压耗时飙升至数十秒。且默认打包会使 SQLite 数据库在程序关闭后随临时目录一同销毁。
   * **解法**：重构全局路径导航仪，实现环境自适应。开发 `download_kernel.py` 脚本将 Chromium 剥离并实施“旁路挂载 (Side-loading)”。将用户资产物理隔离至 `data/` 目录中，实现毫秒级启动与绝对的数据安全。
2. **解决“错误吞噬 (Error Swallowing)”与异常分流诊断**
   * **解法**：在后端引入 `(success_bool, data_or_message)` 元组返回规范。精准捕获 HTTP 401 与 `Timeout` 异常，在前端使用 Early Return 进行三元分流诊断，提供精确排障指导。
3. **纯 CSS 网格长图与 `aspect-ratio` 比例魔法**
   * **解法**：在 Jinja2 模板中使用纯 HTML/CSS 构建陈列墙布局。通过 `aspect-ratio: 16/9` 锁定容器尺寸，并利用 `object-fit: contain` 实现任何异形截图的无损缩放与优雅留白。
4. **基于 `networkidle` 的时序控制与自清理机制**
   * **解法**：重构 Playwright 渲染时序，强制注入绝对网络路径并监听 `networkidle` 状态实现秒级出图。同时在生成管线前置入自动化碎片清理逻辑，根除本地存储冗余。

---

## 🚀 极速运行 (How to Use)

本软件为纯绿色免安装版，无需配置任何代码环境。

1. 前往本仓库右侧的 **[Releases]** 页面。
2. 下载最新版本的 `GameGoalManager-Desktop-vX.X.X.zip` 压缩包。
3. 解压至电脑任意非系统敏感目录（由于数据隔离机制，强烈建议**不要**解压在 C 盘 `Program Files` 内）。
4. 双击 `GameGoalManager.exe` 即可启动！

-------------------------------------

<div align="center">
  
# 🎮 GameGoalManager (Desktop Portable Edition)
**An Out-of-the-Box Portable Video Game Archive**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated_Rendering-2EAD33.svg)](https://playwright.dev/)
[![PyInstaller](https://img.shields.io/badge/PyInstaller-Standalone-FF6A00.svg)](https://pyinstaller.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## ✨ Core Features

* **🌐 Data Retrieval Engine**: Directly connects to the RAWG API with built-in precise error diagnostic routing.
* **💾 Green Portable Persistence Layer**: Auto-generates an isolated `data/` vault in the root directory. All SQLite databases, configurations, and user WebP screenshots are physically isolated, making it perfectly portable via USB drives.
* **📸 Automated Headless Rendering Engine**: Embeds a `Playwright` headless browser to dynamically generate milestone posters. Features a "Self-Cleaning Mechanism" to prevent unlimited disk space consumption.
* **🖥️ Desktop-Level Sandbox Breakthrough**: Uses `pywebview` to seamlessly wrap the B/S architecture into a native desktop application, cross-calling OS APIs for native file saving.

---

## 🛠️ Tech Stack & Architecture

* **Desktop & Build**: `pywebview` + `PyInstaller`
* **Backend Foundation**: `Python 3` + `Flask`
* **Persistence**: `SQLAlchemy` + `SQLite` (Externalized)
* **Automated Rendering**: `Playwright` (Side-loaded Chromium)
* **Frontend View**: Native `HTML5` + `CSS3` + `JavaScript` (Fetch API)

---

## 💡 Technical Highlights

> *"During the desktop refactoring process, the following core engineering pain points were conquered:"*

1. **Bypassing the PyInstaller `_MEIPASS` Trap & Chromium Side-loading (Highlight)**
   * **Pain Point**: Forcing Playwright's massive engine into a single `.exe` causes missing-kernel crashes across devices and spikes cold boot times to dozens of seconds. Furthermore, default packing destroys SQLite databases upon closing due to temporary directory flushing.
   * **Solution**: Refactored the global path router for environment auto-adaptation. Developed a `download_kernel.py` script to strip Chromium and implement "Side-loading". Physically isolated user assets into a `data/` directory, achieving millisecond startup times and absolute data permanence.
2. **Resolving "Error Swallowing" & Diagnostic Routing**
   * **Solution**: Introduced a `(success_bool, data_or_message)` return standard. Precisely captures HTTP 401 and `Timeout` exceptions, using Early Return in the frontend for ternary diagnostic routing.
3. **Pure CSS Grid Image & `aspect-ratio` Magic**
   * **Solution**: Locked the container size with `aspect-ratio: 16/9` and utilized `object-fit: contain` combined with background color padding to achieve lossless scaling of irregularly proportioned screenshots.
4. **`networkidle` Timing Control & Self-Cleaning Mechanism**
   * **Solution**: Listened for Chromium's `wait_until="networkidle"` state for rapid image generation. Injected automated garbage collection logic upstream of the rendering pipeline to eradicate local storage bloat.

---

## 🚀 How to Use (Portable Version)

This software is fully portable and requires no environment configuration.

1. Navigate to the **[Releases]** section on the right side of this repository.
2. Download the latest `GameGoalManager-Desktop-vX.X.X.zip`.
3. Extract it to any non-sensitive directory (avoid `Program Files` to ensure the `data/` folder has proper write permissions).
4. Double-click `GameGoalManager.exe` to launch!