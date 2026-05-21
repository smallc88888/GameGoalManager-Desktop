<div align="center">
  
# 🎮 GameGoalManager
**游戏生涯记录程序**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated_Rendering-2EAD33.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## ✨ 核心特性 (Core Features)

* **🌐 数据检索引擎**：底层直连 RAWG API，提供精准的游戏信息拉取与封面抓取，内置异常分型诊断（精准拦截断网、Key 失效等异常并进行 UI 引导）。
* **💾 本地化持久层**：基于 `SQLAlchemy` 与 SQLite 构建实体关系模型。用户上传的通关截图将在后端通过 `Pillow` 进行非破坏性 `.webp` 极速压缩，实现数据与物理资产的双重隔离存储。
* **📸 自动化无头渲染长图引擎**：彻底摒弃前端截图组件的清晰度局限。后端内嵌 `Playwright` Chromium 无头浏览器，利用 Jinja2 与纯 CSS `Flexbox` 动态生成长图，并在服务端截取高清的数字成就海报。
* **🖥️ 桌面级应用构建**：采用 `pywebview` 将 B/S 架构无缝包装为原生桌面应用。通过跨界调用系统底层 API，实现长图“另存为”系统原生文件对话框，打破 Web 浏览器的下载交互沙盒限制。

---

## 🛠️ 技术栈与架构 (Tech Stack)

* **后端**: `Python 3` + `Flask` (MVC 路由层)
* **持久化**: `SQLAlchemy` (ORM) + `SQLite` (无状态本地数据库)
* **网关层**: `requests` + `python-dotenv` (动态密钥热更新)
* **自动化渲染**: `Playwright` (Headless Chromium 引擎)
* **媒体处理**: `Pillow` (WebP 流媒体实时转换)
* **前端视图**: 原生 `HTML5` + `CSS3` + 原生 `JavaScript` (Fetch API)
* **桌面外壳**: `pywebview`

---

## 💡 技术难点 (Technical Highlights)

> *“本项目并非简单的 CRUD 堆砌，在开发过程中重点攻克了以下工程痛点：”*

1. **解决“错误吞噬 (Error Swallowing)”与异常分流诊断**
   * **痛点**：传统的第三方 API 请求一旦失败，前端往往统一报错“未找到数据”，导致用户无法分辨是断网、鉴权失败还是真的查无此结果。
   * **解法**：在后端的 `RAWGClient` 中引入 `(success_bool, data_or_message)` 的元组返回规范。精准捕获 HTTP 401、`Timeout` 与 `ConnectionError`，并在前端使用 Early Return 进行三元分流诊断，提供精确的排障指导。
2. **纯 CSS 网格长图与 `aspect-ratio` 比例**
   * **痛点**：玩家上传的截图比例各异（16:9、4:3、甚至竖屏），若使用 Canvas 或强制宽高会导致图片严重拉伸变形，破坏“通关长图”的观感。
   * **解法**：摒弃笨重的 Echarts，在 Jinja2 模板中使用纯 HTML/CSS 构建陈列墙布局。通过 `aspect-ratio: 16/9` 锁定容器尺寸，并利用 `object-fit: contain` 结合底色填充，实现图片无损缩放。
3. **基于 `networkidle` 的无头浏览器时序控制**
   * **痛点**：由于图片素材存在网络加载延迟，Playwright 若单纯等待 DOM 解析完成即刻截图，会导致生成的长图出现大片空白死链。
   * **解法**：重构渲染时序，强制注入绝对路径（`request.host_url`），并监听 Chromium 的 `wait_until="networkidle"` 状态，将原本偶尔报错超时的 30 秒渲染优化至 1~2 秒内出图。

---

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
确保你的电脑已安装 **Python 3.10+**。将项目克隆到本地后，在根目录执行以下命令安装核心依赖：
```bash
pip install -r requirements.txt
```

### 2. 初始化无头渲染内核 (必填项)
为了让生成长图的功能正常运作，必须下载 Playwright 依赖的独立 Chromium 内核：
```bash
playwright install chromium
```

### 3. 配置 API 密钥
将根目录下的 .env.example 文件重命名为 .env。
前往 RAWG API 免费申请你的专属密钥，并填入 .env 文件中：
```bash
RAWG_API_KEY=your_api_key_here
```
(注：如果跳过此步，项目启动后会自动在界面弹出强制拦截网关，引导你进行可视化配置。)

### 4. 启动项目
```bash
python app.py
```
应用将以 pywebview 桌面窗体或默认浏览器窗口的形式启动！

-------------------------------------

<div align="center">
  
# 🎮 GameGoalManager
**A Video Game Career & Milestone Tracker**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated_Rendering-2EAD33.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## ✨ Core Features

* **🌐 Data Retrieval Engine**: Directly connects to the RAWG API to provide precise game information and cover art fetching. Built-in precise error diagnostic routing (accurately intercepts network disconnections, invalid API Keys, etc., and provides UI guidance).
* **💾 Localized Persistence Layer**: Builds an Entity-Relationship model based on `SQLAlchemy` and SQLite. User-uploaded completion screenshots are non-destructively and rapidly compressed into `.webp` format via `Pillow` on the backend, achieving dual isolated storage of data and physical assets.
* **📸 Automated Headless Rendering Engine**: Completely abandons the resolution limitations of frontend screenshot components. The backend embeds a `Playwright` Chromium headless browser, utilizes Jinja2 and pure CSS `Flexbox` to dynamically generate long milestone images, and captures high-definition digital achievement posters on the server side.
* **🖥️ Desktop-Level Sandbox Breakthrough**: Uses `pywebview` to seamlessly wrap the B/S architecture into a native desktop application. By cross-calling underlying OS APIs, it implements a native "Save As" file dialog for the exported images, breaking the download interaction sandbox limits of standard web browsers.
* **🕹️ Famicom Minimalist Aesthetics**: The entire site is hand-crafted with a lightweight Nintendo "Famicom" (红白机) UI framework, with zero dependencies on bloated frontend component libraries.

---

## 🛠️ Tech Stack & Architecture

* **Backend Foundation**: `Python 3` + `Flask` (MVC Routing)
* **Persistence**: `SQLAlchemy` (ORM) + `SQLite` (Stateless Local Database)
* **Gateway Layer**: `requests` + `python-dotenv` (Dynamic Key Hot-swapping)
* **Automated Rendering**: `Playwright` (Headless Chromium Engine)
* **Media Processing**: `Pillow` (Real-time WebP Conversion)
* **Frontend View**: Native `HTML5` + `CSS3` + Native `JavaScript` (Fetch API)
* **Desktop Shell**: `pywebview`

---

## 💡 Technical Highlights

> *"This project is not a simple CRUD stack. During development, the following core engineering pain points were conquered:"*

1. **Resolving "Error Swallowing" and Implementing Diagnostic Routing**
   * **Pain Point**: When traditional third-party API requests fail, the frontend often uniformly reports "Data not found", making it impossible for users to distinguish whether it's a network disconnection, authentication failure, or genuinely no results.
   * **Solution**: Introduced a `(success_bool, data_or_message)` tuple return standard in the backend `RAWGClient`. Precisely captures HTTP 401, `Timeout`, and `ConnectionError`, and uses Early Return in the frontend for a ternary diagnostic routing, providing precise troubleshooting guidance.
2. **Pure CSS Grid Long Image and `aspect-ratio` Magic**
   * **Pain Point**: User-uploaded screenshots vary in aspect ratio (16:9, 4:3, or even vertical). Using Canvas or forcing width/height would cause severe stretching and distortion, ruining the visual experience of the milestone image.
   * **Solution**: Abandoned heavy charting libraries like Echarts, using pure HTML/CSS within Jinja2 templates to build a gallery wall layout. Locked the container size with `aspect-ratio: 16/9` and utilized `object-fit: contain` combined with background color padding to achieve lossless image scaling with built-in whitespace, creating a premium "cartridge" visual effect.
3. **Headless Browser Timing Control Based on `networkidle`**
   * **Pain Point**: Due to network loading delays for image assets, if Playwright simply waits for DOM parsing to finish before taking a screenshot, it results in exported images with blank dead links.
   * **Solution**: Refactored the rendering timing, forcefully injected absolute network paths (`request.host_url`), and listened for Chromium's `wait_until="networkidle"` state. This optimized the original rendering process—which occasionally timed out at 30 seconds—down to rapid, second-level image generation.

---

## 🚀 Quick Start

### 1. Environment Preparation
Ensure your computer has **Python 3.10+** installed. After cloning the project to your local machine, execute the following command in the root directory to install core dependencies:
```bash
pip install -r requirements.txt
```

### 2. Initialize Headless Rendering Engine (Required)
For the milestone image generation feature to function properly, you must download the standalone Chromium engine required by Playwright:
```bash
playwright install chromium
```

### 3. Configure API Key
Rename the .env.example file in the root directory to .env.
Go to the RAWG API to apply for your free exclusive key, and fill it into the .env file:
```bash
RAWG_API_KEY=your_api_key_here
```
(Note: If you skip this step, the project will automatically pop up a mandatory interception gateway in the UI upon startup, guiding you through visual configuration.)

### 4. Run the Application
```bash
python app.py
```
The application will instantly launch as a pywebview desktop window or in your default web browser!