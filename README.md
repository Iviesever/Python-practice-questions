以下 `README.md`绝大部分由 AI 生成（

***

# 📚 Python 刷题系统 (学习通专用版)

这是一个基于 Python (Tkinter) 开发的本地轻量级刷题软件。

**核心目的：** 专为复习 **学习通 (Chaoxing)** 上的测验、作业和考试题目而设计。无需联网，支持错题回顾，界面简洁，即点即用。

![screenshot](./.img/screenshot.png)

## ✨ 功能特点

*   **多题型支持**：完美解析 单选题、多选题、判断题、填空题。
*   **智能解析**：针对学习通网页端的复制格式进行了专门优化。
*   **刷题模式**：
    *   🔁 **顺序练习**：按文件顺序一题题刷。
    *   🔀 **随机练习**：打乱顺序，模拟考试。
    *   ❌ **错题复习**：自动记录错题，可针对错误 1 次、2 次... N 次的题目进行专项突击。
*   **即时反馈**：支持“即点即判”模式（秒判），做题效率翻倍。
*   **自定义设置**：可调节字体大小、切换题库文件夹。

## 🚀 快速开始

### 1. 环境要求

确保你的电脑上安装了 [Python 3.x](https://www.python.org/)。
本项目仅依赖 Python 标准库（`tkinter`, `json`, `re`, `os` 等），**无需安装任何第三方 pip 包**。

### 2. 📂 如何制作题库 (关键步骤)

本软件最核心的功能是能够直接解析学习通的网页文本。请按照以下步骤操作：

1.  在项目根目录下找到（或新建）`题库` 文件夹。
2.  在 `题库` 文件夹内新建一个子文件夹（例如：`近代史纲要`、`Python程序设计`），这将作为一个独立的题库分类。
3.  **获取题目文本**：
    *   在电脑浏览器打开学习通的 **作业**、**测验** 或 **考试查看试卷** 等页面。
    *   **全选页面内容**：使用快捷键 **`Ctrl + A`**
    *   **复制** (`Ctrl + C`) 选中的所有文字。
4.  **保存文件**：
    *   在刚才新建的子文件夹里，新建一个 `.txt` 文本文件。
    *   将复制的内容直接 **粘贴** 进去。
    *   保存并关闭，**编码格式建议使用 UTF-8**。

```text
Python 刷题/
├── PS.exe           # 主程序
├── config.json      # (自动生成) 用户配置文件
├── mistakes.json    # (自动生成) 错题记录数据库
├── favicon.ico      # 程序图标
└── 题库/             # 存放题目数据的文件夹
    ├── 马克思主义原理/
    │   ├── 第一章测验.txt
    │   └── 期末模拟.txt
    └── 计算机基础/
        └── 题库1.txt
```

> **💡 提示**：只要是从学习通网页上直接复制下来的文本，通常都能完美自动识别题目。

### 3. 运行软件

Windows端：下载 release 的 PS.exe，双击运行

Android端：下载 [pydroid3](https://blog.qaiu.top/archives/pydroid3v72)到手机上，下载项目文件中的 [PS.pyw](https://github.com/Iviesever/Python-practice-questions/blob/master/PS.pyw)，用 pydroid3 打开

## 🛠️ 目录结构说明


## 📝 License

本项目采用 **MIT License** 开源许可证。

这意味着你可以自由地使用、复制、修改、合并、出版发行、散布、再授权及贩售本软件的副本，只需包含原作者的版权声明和许可声明即可。

---

### The MIT License (MIT)

Copyright (c) 2025 Iviesever

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
