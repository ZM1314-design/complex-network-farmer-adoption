# 🚀 LaTeX论文快速开始指南

## ✅ 已创建的文件

1. **`📝LaTeX环境配置指南.md`** - 详细的配置说明
2. **`paper.tex`** - 完整的论文模板
3. **`.vscode/settings.json`** - LaTeX Workshop配置
4. **`.vscode/tasks.json`** - 编译任务配置

---

## 🎯 快速开始（3步）

### 步骤1：安装LaTeX发行版

**Windows系统：**

1. 下载MiKTeX：https://miktex.org/download
2. 安装时勾选：
   - ✅ "Install missing packages on-the-fly: Yes"
   - ✅ "Add MiKTeX to PATH"
3. 重启Cursor

### 步骤2：安装LaTeX Workshop扩展

1. 在Cursor中按 `Ctrl+Shift+X` 打开扩展市场
2. 搜索：`LaTeX Workshop`
3. 点击"安装"

### 步骤3：开始编写

1. 打开 `paper.tex`
2. 修改标题、作者等信息
3. 按 `Ctrl+Alt+B` 编译
4. 按 `Ctrl+Alt+V` 查看PDF

---

## 📝 论文模板说明

### 已包含的内容：

✅ **完整的论文结构**：
- 摘要
- 引言
- 相关工作
- 模型与方法（包含所有公式）
- 实验设计
- 实验结果
- 讨论
- 结论
- 参考文献
- 附录

✅ **所有数学公式**：
- 双曲几何网络公式
- 三维质量动力学公式
- TPB决策模型公式
- 逾渗相变公式
- DQN强化学习公式

✅ **图表引用**：
- 自动引用项目生成的图表
- 表格模板
- 算法伪代码

✅ **中文支持**：
- 使用 `ctex` 包
- 支持中文输入和显示

---

## 🔧 常用操作

### 编译论文

**方法1：快捷键**
- `Ctrl+Alt+B` - 编译LaTeX

**方法2：命令面板**
- `Ctrl+Shift+P` → 输入 "LaTeX: Build LaTeX project"

**方法3：任务**
- `Ctrl+Shift+B` - 运行构建任务

### 查看PDF

- `Ctrl+Alt+V` - 在Cursor中查看PDF
- 或点击右上角的"View LaTeX PDF"按钮

### 插入图片

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/phase_transition.png}
    \caption{逾渗相变曲线}
    \label{fig:phase_transition}
\end{figure}
```

### 插入表格

```latex
\begin{table}[H]
    \centering
    \caption{表格标题}
    \label{tab:table1}
    \begin{tabular}{ccc}
        \toprule
        列1 & 列2 & 列3 \\
        \midrule
        数据1 & 数据2 & 数据3 \\
        \bottomrule
    \end{tabular}
\end{table}
```

### 引用公式

```latex
如公式\eqref{eq:hyperbolic_distance}所示
```

### 引用图表

```latex
如图\ref{fig:phase_transition}所示
如表\ref{tab:network_effect}所示
```

---

## 📊 使用项目生成的图表

论文模板已经配置好引用项目生成的图表：

- `figures/phase_transition.png` - 逾渗相变图
- `figures/diffusion_time.png` - 扩散时间图
- `figures/training_curves.png` - 训练曲线
- `figures/network_final_state.png` - 网络最终状态
- 等等...

**确保图表文件在 `figures/` 文件夹中！**

---

## 🔍 常见问题

### 问题1：编译失败 - 找不到包

**解决方案**：
1. MiKTeX会自动提示安装缺失的包
2. 点击"安装"即可
3. 或手动安装：`miktex install <包名>`

### 问题2：中文显示乱码

**解决方案**：
- 确保使用 `\usepackage[UTF8]{ctex}`
- 确保文件编码为UTF-8

### 问题3：图片无法显示

**解决方案**：
1. 检查图片路径是否正确
2. 确保图片格式为PDF、PNG或JPG
3. 使用绝对路径或相对路径

### 问题4：参考文献无法编译

**解决方案**：
1. 如果有 `.bib` 文件，编译顺序：
   - `pdflatex` → `bibtex` → `pdflatex` → `pdflatex`
2. LaTeX Workshop会自动处理

---

## 📚 下一步

1. **修改论文内容**：
   - 更新标题、作者、摘要
   - 根据实际结果修改数据
   - 添加更多分析

2. **添加参考文献**：
   - 创建 `references.bib` 文件
   - 使用BibTeX管理引用

3. **优化格式**：
   - 调整页面布局
   - 优化图表排版
   - 检查拼写和语法

4. **导出最终版本**：
   - 编译生成PDF
   - 检查所有图表和公式
   - 准备提交

---

## 🎉 完成！

现在你可以：
- ✅ 在Cursor中编写LaTeX论文
- ✅ 实时预览PDF
- ✅ 使用项目生成的图表
- ✅ 自动编译和错误检查

**祝写作顺利！** 📝

