@echo off
REM RAG Pro Max Windows 启动脚本

echo ============================================================
echo   RAG Pro Max 启动
echo ============================================================
echo.

REM 激活虚拟环境（如果存在）
if exist venv\Scripts\activate.bat (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 启动应用
echo 启动应用...
streamlit run src/apppro.py

pause
