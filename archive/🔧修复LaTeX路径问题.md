# 🔧 修复LaTeX路径问题

## 问题

错误信息：`spawn pdflatex ENOENT` - 找不到pdflatex命令

这说明Cursor没有找到MiKTeX的路径。

---

## 解决方案

### 方法1：重启Cursor（最简单，先试这个）

1. **完全关闭Cursor**（所有窗口）
2. **重新打开Cursor**
3. **再次尝试编译**（`Ctrl+Alt+B`）

如果还不行，继续方法2。

---

### 方法2：手动配置路径

#### 步骤1：找到MiKTeX的安装路径

打开命令行（cmd），输入：
```bash
where pdflatex
```

这会显示pdflatex.exe的完整路径，例如：
- `D:\Mitex\miktex\bin\x64\pdflatex.exe`
- 或 `D:\Mitex\miktex\bin\pdflatex.exe`

#### 步骤2：修改配置文件

1. 打开 `.vscode/settings.json` 文件
2. 找到 `latex-workshop.latex.tools` 部分
3. 将 `command` 改为完整路径

**示例：**
```json
{
    "name": "pdflatex",
    "command": "D:\\Mitex\\miktex\\bin\\x64\\pdflatex.exe",
    "args": [
        "-synctex=1",
        "-interaction=nonstopmode",
        "-file-line-error",
        "%DOC%"
    ]
}
```

**注意：**
- 路径中的反斜杠要写成 `\\`（双反斜杠）
- 或者用正斜杠 `/`：`D:/Mitex/miktex/bin/x64/pdflatex.exe`

#### 步骤3：同样修改其他工具

需要修改：
- `pdflatex` → `pdflatex.exe` 的完整路径
- `bibtex` → `bibtex.exe` 的完整路径
- `xelatex` → `xelatex.exe` 的完整路径（如果需要）

---

### 方法3：添加到系统PATH（永久解决）

1. **找到MiKTeX的bin目录**（通过 `where pdflatex` 命令）
2. **添加到PATH环境变量**：
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"用户变量"中找到"Path"
   - 点击"编辑" → "新建"
   - 添加路径（例如：`D:\Mitex\miktex\bin\x64`）
   - 点击"确定"保存
3. **重启Cursor**

---

## 快速检查

运行以下命令找到路径：
```bash
where pdflatex
```

把结果告诉我，我帮你修改配置文件！

