# 将 `thesis_fixed.tex` 转为 Word（保持原排版：推荐方案）

> 目标：尽量保持你最初在 LaTeX（Cursor/Windows）里的版式（页边距、页眉页脚、字体、图表位置、编号规则）。
> 结论：**最稳的做法是：先编译 PDF，再用 Word/Acrobat“从 PDF 导出 Word”**。
> 直接 tex→docx（pandoc）通常会破坏排版，不推荐用于“保持原排版”。

---

## 方案 A（最推荐）：LaTeX → PDF → Word（保版式最强）

### Step 1：在 Windows / Cursor 里编译生成 PDF
- 打开 `thesis_fixed.tex`
- 用你原来的方式（XeLaTeX / latexmk -xelatex）编译
- 得到：`thesis_fixed.pdf`

> 这一步至关重要：你要保留的“原排版”，本质上就是 PDF 的版面。

### Step 2：把 PDF 转成 Word（按保真度从高到低推荐）

#### 2.1 Adobe Acrobat（最高保真，强烈推荐）
- 用 Acrobat 打开 `thesis_fixed.pdf`
- 选择：**导出 PDF** → **Microsoft Word** → `.docx`

优点：
- 页眉页脚、分页、图文相对位置保真度最好
- 公式会尽力转为可编辑对象（仍可能需要少量手工修复）

#### 2.2 Microsoft Word 自带“打开 PDF”转换（次推荐）
- Word → 打开 → 选择 `thesis_fixed.pdf`
- Word 会提示“将 PDF 转为可编辑文档” → 确认
- 另存为 `.docx`

优点：不需要额外软件；缺点：复杂公式/表格偶尔会错位。

#### 2.3 WPS / 在线工具（不推荐用于最终稿）
适合临时看，但对公式、页眉页脚、图表浮动体的保真度较差。

---

## 方案 B（备选）：Pandoc 直接 tex → docx（不保证排版）

仅在你愿意接受“Word 里需要重新排版”的情况下使用。

### 安装 Pandoc
- Windows：下载并安装 Pandoc： https://pandoc.org/installing.html

### 转换命令（在论文目录执行）
```bash
pandoc thesis_fixed.tex -o thesis_fixed.docx
```

如果有交叉引用/参考文献：
```bash
pandoc thesis_fixed.tex -o thesis_fixed.docx --citeproc
```

> 注意：此方案很容易破坏你在 LaTeX 里精细控制的页眉页脚、行距、缩进、浮动体位置。

---

## 最终建议（你要“保持原排版方式”时）

- **用方案 A**：先生成 PDF，再用 Acrobat/Word 转 docx。
- 转换完成后，只做最少的人工修复（尤其是公式与个别表格）。

---

## 你转完后如果发现问题（我可以继续帮你）
请把以下信息发我：
1) 你用的转换方式（Acrobat / Word / WPS / 在线）
2) 你遇到的具体问题截图（例如：公式变图片、表格错位、页眉页脚丢失）

我会给你针对性的“保版式修复策略”。
