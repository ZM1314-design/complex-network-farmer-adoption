@echo off
chcp 65001 >nul
echo ========================================
echo 完整实验运行 - 生成所有结果图
echo ========================================
echo.
echo 运行模式：完整实验（基线 + RL训练 + 对比分析）
echo 预计时间：8-15分钟
echo.
echo 开始运行...
echo.

python run_complete_experiment.py

echo.
echo ========================================
echo 运行完成！
echo ========================================
echo.
echo 生成的文件位置：
echo   - 图表：figures\ 目录
echo   - 数据：results\ 目录
echo   - 模型：models\ 目录
echo.
pause

