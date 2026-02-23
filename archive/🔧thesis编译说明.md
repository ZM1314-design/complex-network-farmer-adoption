# 🔧 thesis.tex 编译说明

## ⚠️ 重要：必须使用XeLaTeX编译

`thesis.tex` 使用了 `xeCJK` 包，**必须使用XeLaTeX编译**，不能使用pdfLaTeX。

---

## 🚀 编译方法

### 方法1：在Cursor中使用XeLaTeX（推荐）

1. **打开 `thesis.tex` 文件**

2. **选择编译方式**：
   - 按 `Ctrl+Shift+P`
   - 输入 "LaTeX: Build with recipe"
   - 选择 **"xelatex"**

3. **或者右键**：
   - 右键点击 `thesis.tex`
   - 选择 "Build LaTeX project"
   - 选择使用 **xelatex**

4. **编译**：
   - 按 `Ctrl+Alt+B` 编译
   - 或点击右上角的编译按钮

---

### 方法2：修改配置文件（永久设置）

如果你想默认使用XeLaTeX，可以修改 `.vscode/settings.json`：

```json
{
    "latex-workshop.latex.recipes": [
        {
            "name": "xelatex",
            "tools": ["xelatex"]
        }
    ],
    "latex-workshop.latex.tools": [
        {
            "name": "xelatex",
            "command": "D:\\Mitex\\miktex\\bin\\x64\\xelatex.exe",
            "args": [
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "%DOC%"
            ]
        }
    ]
}
```

---

## ✅ 验证编译成功

编译成功后，应该生成：
- `thesis.pdf` - PDF文件
- `thesis.aux` - 辅助文件
- `thesis.log` - 日志文件
- `thesis.toc` - 目录文件（如果有目录）

---

## 🔍 如果还有错误

### 错误1：找不到字体

**解决**：确保系统有SimSun（宋体）字体，如果没有，可以改为：
```latex
\setCJKmainfont{Microsoft YaHei}  % 使用微软雅黑
```

### 错误2：某些包找不到

**解决**：MiKTeX会自动提示安装，点击"安装"即可。

---

## 📝 编译顺序（如果有目录和引用）

1. 第一次编译：生成目录和引用信息
2. 第二次编译：更新目录和引用

**通常编译两次即可！**

---

**现在试试用XeLaTeX编译吧！** 🚀

