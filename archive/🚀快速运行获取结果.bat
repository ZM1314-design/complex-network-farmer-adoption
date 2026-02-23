@echo off
chcp 65001 >nul
echo ========================================
echo 快速实验运行 - 获取结果图表（RL > Baseline）
echo ========================================
echo.
echo 优化策略：只优化RL训练部分，其他部分保持原配置
echo.
echo 优化的部分（仅RL训练）：
echo   - RL训练轮数：80（原200，加速）
echo   - 批次大小：128（原64，加速）
echo   - 目标网络更新：每5轮（原10轮，加速）
echo.
echo 保持原配置的部分：
echo   - 农户数量：300（不变）
echo   - 时间步数：60（不变）
echo   - 相变扫描点数：20（不变）
echo.
echo 预计时间：15-20分钟（原2小时+）
echo.
echo 开始运行...
echo.

python run_quick_rl_only.py

echo.
echo ========================================
echo 运行完成！
echo ========================================
echo.
echo 生成的文件位置：
echo   - 图表：figures\ 目录
echo   - 数据：results\ 目录
echo.
pause

