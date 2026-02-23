# 📝 LaTeX环境配置指南 - Cursor版

## 🎯 目标

在Cursor中配置LaTeX环境，编写和编译学术论文。

---

## 📦 方法一：使用LaTeX Workshop扩展（推荐）

### 步骤1：安装LaTeX发行版

#### Windows系统：

**选项A：MiKTeX（推荐，轻量级）**
1. 下载：https://miktex.org/download
2. 安装时选择：
   - ✅ "Install missing packages on-the-fly: Yes"
   - ✅ "Add MiKTeX to PATH"
3. 安装完成后，重启Cursor

**选项B：TeX Live（完整版，体积大）**
1. 下载：https://www.tug.org/texlive/
2. 安装（需要较长时间，约4GB）
3. 安装完成后，重启Cursor

### 步骤2：在Cursor中安装LaTeX扩展

1. **打开扩展市场**：
   - 按 `Ctrl+Shift+X` 或点击左侧扩展图标

2. **搜索并安装**：
   - 搜索：`LaTeX Workshop`
   - 作者：James Yu
   - 点击"安装"

3. **安装其他推荐扩展**（可选）：
   - `LaTeX Utilities` - LaTeX工具
   - `LaTeX language support` - 语法高亮
   - `Better Comments` - 更好的注释

### 步骤3：配置LaTeX Workshop

1. **打开设置**：
   - 按 `Ctrl+,` 打开设置
   - 或：`File` → `Preferences` → `Settings`

2. **搜索LaTeX配置**：
   - 搜索：`latex-workshop`

3. **关键设置**（可选，有默认值）：
   ```json
   {
     "latex-workshop.latex.recipes": [
       {
         "name": "pdflatex ➞ bibtex ➞ pdflatex × 2",
         "tools": [
           "pdflatex",
           "bibtex",
           "pdflatex",
           "pdflatex"
         ]
       }
     ],
     "latex-workshop.latex.tools": [
       {
         "name": "pdflatex",
         "command": "pdflatex",
         "args": [
           "-synctex=1",
           "-interaction=nonstopmode",
           "-file-line-error",
           "%DOC%"
         ]
       },
       {
         "name": "bibtex",
         "command": "bibtex",
         "args": [
           "%DOCFILE%"
         ]
       }
     ],
     "latex-workshop.view.pdf.viewer": "tab",
     "latex-workshop.latex.autoClean.run": "onBuilt",
     "latex-workshop.latex.clean.fileTypes": [
       "*.aux",
       "*.bbl",
       "*.blg",
       "*.idx",
       "*.ind",
       "*.lof",
       "*.lot",
       "*.out",
       "*.toc",
       "*.acn",
       "*.acr",
       "*.alg",
       "*.glg",
       "*.glo",
       "*.gls",
       "*.fls",
       "*.log",
       "*.fdb_latexmk",
       "*.snm",
       "*.synctex.gz",
       "*.nav"
     ]
   }
   ```

### 步骤4：验证安装

1. **创建测试文件** `test.tex`：
   ```latex
   \documentclass{article}
   \begin{document}
   Hello, LaTeX!
   \end{document}
   ```

2. **编译**：
   - 按 `Ctrl+Alt+B` 编译
   - 或：右键 → `Build LaTeX project`

3. **查看PDF**：
   - 按 `Ctrl+Alt+V` 查看PDF
   - 或：点击右上角的"View LaTeX PDF"按钮

---

## 🔧 方法二：使用命令行编译（备用）

如果扩展不工作，可以使用命令行：

### Windows PowerShell：

```powershell
# 编译
pdflatex paper.tex

# 如果有参考文献
bibtex paper
pdflatex paper.tex
pdflatex paper.tex

# 查看PDF
start paper.pdf
```

### 在Cursor中集成：

1. **创建任务**：`.vscode/tasks.json`
   ```json
   {
     "version": "2.0.0",
     "tasks": [
       {
         "label": "Build LaTeX",
         "type": "shell",
         "command": "pdflatex",
         "args": [
           "-synctex=1",
           "-interaction=nonstopmode",
           "${file}"
         ],
         "group": {
           "kind": "build",
           "isDefault": true
         },
         "problemMatcher": []
       }
     ]
   }
   ```

2. **使用**：按 `Ctrl+Shift+B` 编译

---

## 📚 推荐LaTeX包

### 学术论文常用包：

```latex
\usepackage{amsmath}        % 数学公式
\usepackage{amssymb}        % 数学符号
\usepackage{graphicx}       % 插入图片
\usepackage{hyperref}       % 超链接
\usepackage{booktabs}      % 表格
\usepackage{algorithm}      % 算法
\usepackage{algorithmic}   % 算法伪代码
\usepackage{listings}      % 代码
\usepackage{xcolor}         % 颜色
\usepackage{geometry}       % 页面设置
\usepackage{fancyhdr}       % 页眉页脚
\usepackage{cite}           % 引用
\usepackage{url}            % URL
\usepackage{float}          % 浮动体控制
```

---

## 🎨 推荐主题和字体

### 中文字体支持：

```latex
\usepackage{ctex}           % 中文支持（推荐）
% 或
\usepackage{xeCJK}          % 另一种中文支持
```

### 代码高亮：

```latex
\usepackage{listings}
\usepackage{xcolor}

\lstset{
  language=Python,
  basicstyle=\ttfamily\small,
  keywordstyle=\color{blue},
  commentstyle=\color{green},
  stringstyle=\color{red}
}
```

---

## 🔍 常见问题解决

### 问题1：找不到pdflatex命令

**解决方案**：
1. 检查MiKTeX/TeX Live是否安装
2. 检查PATH环境变量
3. 重启Cursor

### 问题2：中文显示乱码

**解决方案**：
```latex
\usepackage[UTF8]{ctex}
% 或
\usepackage{xeCJK}
\setCJKmainfont{SimSun}  % 设置中文字体
```

### 问题3：图片无法显示

**解决方案**：
1. 使用 `\includegraphics[width=0.8\textwidth]{figures/xxx.png}`
2. 确保图片路径正确
3. 支持的格式：PDF, PNG, JPG

### 问题4：参考文献无法编译

**解决方案**：
1. 确保有 `.bib` 文件
2. 编译顺序：`pdflatex` → `bibtex` → `pdflatex` → `pdflatex`
3. 检查 `.bib` 文件格式

### 问题5：公式编号混乱

**解决方案**：
```latex
\numberwithin{equation}{section}  % 按章节编号
```

---

## 📖 学习资源

1. **LaTeX入门**：
   - Overleaf文档：https://www.overleaf.com/learn
   - LaTeX教程：https://www.latex-tutorial.com/

2. **中文LaTeX**：
   - CTEX文档：https://ctan.org/pkg/ctex
   - 中文LaTeX模板：https://github.com/CTeX-org/ctex-kit

3. **学术论文模板**：
   - IEEE模板：https://www.ieee.org/conferences/publishing/templates.html
   - ACM模板：https://www.acm.org/publications/proceedings-template

---

## ✅ 验证清单

- [ ] MiKTeX/TeX Live已安装
- [ ] LaTeX Workshop扩展已安装
- [ ] 测试文件可以编译
- [ ] PDF可以正常查看
- [ ] 中文显示正常（如果需要）
- [ ] 图片可以插入
- [ ] 公式可以正常显示

---

## 🚀 下一步

1. 使用提供的论文模板（`paper.tex`）
2. 开始编写论文
3. 使用 `Ctrl+Alt+B` 编译
4. 使用 `Ctrl+Alt+V` 查看PDF

**祝写作顺利！** 📝

