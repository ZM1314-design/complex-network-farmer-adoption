"""build_full_model_tex.py

生成《模型最终版_全量.tex》：尽可能完整收录并解释
`📐完整数学模型公式集_详细版.md` 中的公式（以 $$...$$ 块为准），并为每个公式生成
“在做什么/为什么需要/有什么用处”的小白解释。

策略（更稳健）：
- 以 Markdown 中的每个 $$...$$ 数学块为“一个公式条目”
- 公式标题取该公式块之前最近的标题行：优先匹配“### 公式X：xxx”，否则使用最近的 '###/####' 标题
- 解释文本取公式块之后最近出现的三段：
  - '#### 📝 这一步在做什么？'
  - '#### 🤔 为什么需要这一步？'
  - '#### 💡 有什么用处？'
  若某段不存在则跳过。

这样能够覆盖原文中“公式编号体系 + 子公式(11.1/12.1...)”的全部 $$ 块，
避免只解析 12 个“公式X”标题导致遗漏。

编译：XeLaTeX
"""

from __future__ import annotations

import re
from pathlib import Path

MD_PATH = Path("📐完整数学模型公式集_详细版.md")
OUT_PATH = Path("模型最终版_全量.tex")


def _escape_tex(text: str) -> str:
    # 对解释文本做最小转义（公式本身不转义）
    return (
        text.replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
        .replace("&", "\\&")
    )


def _strip_md_noise(s: str) -> str:
    s = s.strip()
    if not s:
        return ""
    # 去掉粗体标记
    s = s.replace("**", "")
    # 代码块统一省略
    s = re.sub(r"```[\s\S]*?```", "（略：此处为代码示例）", s)
    # 去掉emoji对齐符号（保留文字）
    for ch in ["✅", "⭐", "📝", "🤔", "💡", "🎯", "📌", "📈", "📉", "📊", "📋", "🚀", "🔧", "🔍", "🎤", "🌟"]:
        s = s.replace(ch, "")
    return s.strip()


def extract_items(md: str):
    # 找出所有 $$...$$
    eq_re = re.compile(r"\$\$\s*(.*?)\s*\$\$", re.S)
    items = []

    # 预先记录每一行的起始 offset，便于定位“最近标题”
    line_starts = [0]
    for m in re.finditer(r"\n", md):
        line_starts.append(m.end())

    def find_prev_title(pos: int) -> str:
        # 向上找最近的标题行
        lines = md[:pos].splitlines()
        for line in reversed(lines):
            t = line.strip()
            if t.startswith("###") or t.startswith("####"):
                return t.lstrip("#").strip()
        return "（未命名公式）"

    def find_next_explain(pos: int, key: str) -> str:
        # 在 pos 之后找 '#### ... key'，取其后到下一个 ####/### 的文本
        m = re.search(r"^####\s+.*?" + re.escape(key) + r"\s*$", md[pos:], flags=re.M)
        if not m:
            return ""
        start = pos + m.end()
        nxt = re.search(r"^####\s+|^###\s+", md[start:], flags=re.M)
        end = start + nxt.start() if nxt else len(md)
        return md[start:end].strip()

    for idx, m in enumerate(eq_re.finditer(md), start=1):
        eq = m.group(1).strip()
        title = find_prev_title(m.start())
        what = _strip_md_noise(find_next_explain(m.end(), "这一步在做什么？"))
        why = _strip_md_noise(find_next_explain(m.end(), "为什么需要这一步？"))
        use = _strip_md_noise(find_next_explain(m.end(), "有什么用处？"))
        items.append({"idx": idx, "title": title, "eq": eq, "what": what, "why": why, "use": use})

    return items


def build_tex(items) -> str:
    preamble = r"""% ============================================
% 模型最终版_全量（公式+小白解释）
% 由 scripts/build_full_model_tex.py 从《📐完整数学模型公式集_详细版.md》自动生成
% 编译：XeLaTeX
% ============================================

\documentclass[12pt,a4paper]{article}

\usepackage{xeCJK}
\setCJKmainfont{SimSun}
\setCJKsansfont{SimHei}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\usepackage{hyperref}
\geometry{a4paper, left=2.4cm, right=2.4cm, top=2.8cm, bottom=2.8cm}

\title{模型最终版（全量）：公式与面向小白的解释}
\author{}
\date{}

\begin{document}
\maketitle
\tableofcontents
\newpage

\section{说明}
本文档基于《📐完整数学模型公式集\_详细版》自动整理而成。
为保证“一个都不漏”，本文档以原文中的每个 $$...$$ 数学块为单位进行收录，并为其补充小白可读的解释。

\section{公式汇总与解释}
"""

    body = []
    for it in items:
        title = _escape_tex(it["title"])
        body.append(f"\\subsection{{公式{it['idx']}：{title}}}\n")
        body.append("\\begin{equation*}\n")
        body.append(it["eq"] + "\n")
        body.append("\\end{equation*}\n")

        if it["what"]:
            body.append("\\paragraph{在做什么？}\n" + _escape_tex(it["what"]) + "\\par\n")
        if it["why"]:
            body.append("\\paragraph{为什么需要？}\n" + _escape_tex(it["why"]) + "\\par\n")
        if it["use"]:
            body.append("\\paragraph{有什么用处？}\n" + _escape_tex(it["use"]) + "\\par\n")

        body.append("\\vspace{0.6\\baselineskip}\n")

    return preamble + "\n".join(body) + "\\end{document}\n"


def main():
    md = MD_PATH.read_text(encoding="utf-8", errors="ignore")
    items = extract_items(md)
    tex = build_tex(items)
    OUT_PATH.write_text(tex, encoding="utf-8")
    print(f"[OK] Generated: {OUT_PATH} (equation blocks: {len(items)})")


if __name__ == "__main__":
    main()
