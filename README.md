# 选课助手

一个基于python自动提交选课请求的小工具，提供命令行和图形界面两种使用方式，示例代码主要供学习参考。

> ⚠️ 免责声明：本项目仅供学习与研究使用。请遵守相关平台的服务条款和法律法规，勿将本工具用于违规用途；因使用本项目产生的一切后果由使用者自行承担。

> ⚠️ 隐私提醒：`request.txt` 和 `config.py` 包含你的 Cookie / 账号等敏感信息，
> 已被 `.gitignore` 忽略，**不要**把它们提交到公开仓库。

## 直接使用（exe）

无需安装 Python，适合普通使用者：

1. 下载 `物理实验选课平台.exe`（见 GitHub Releases），放到任意文件夹。
2. 双击运行，把「请求标头」和「负载」分别粘到两个框，点「解析请求」→「开始选课」。
3. 可选：把 `request.txt` 放到 exe 旁边，启动时会自动读取，免去每次粘贴。

> 如需自行打包（已安装 Python）：
> `python -m PyInstaller --onefile --windowed --icon icon.ico --name 物理实验选课平台 run.py`

## 源码运行

```bash
pip install requests
python run.py
```

1. 浏览器 `F12` → `Network` → 找到对应的选课请求 → 分别复制「请求标头」和「负载 / 表单数据」。
2. 粘贴到界面两个文本框：上方放**请求标头**，下方放**负载（请求体）**（首次启动会自动读取 `request.txt`）。
3. 点「解析请求」确认课程，再点「开始选课」。

### 命令行

```bash
python -m app.cli               # 读取项目根目录的 request.txt
python -m app.cli 我的请求.txt   # 指定请求文件
```

### 更新请求 / 换课

不用改代码，只需更新 `request.txt`（或重新粘贴），课程信息会自动解析。


再次提醒：确认 `config.py`、`request.txt` 已被 `.gitignore` 忽略，不要提交。
