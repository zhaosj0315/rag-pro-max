@echo off
REM RAG Pro Max Windows 部署脚本

echo ============================================================
echo   RAG Pro Max Windows 部署
echo ============================================================

REM 检查 Python
echo.
echo 1. 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装
    echo 请从 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)
python --version
echo ✅ Python 已安装

REM 检查 pip
echo.
echo 2. 检查 pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip 未安装
    echo 请重新安装 Python 并勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo ✅ pip 已安装

REM 创建虚拟环境（可选）
echo.
echo 3. 创建虚拟环境（可选）...
set /p create_venv="是否创建虚拟环境？(y/n): "
if /i "%create_venv%"=="y" (
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ 虚拟环境已创建并激活
) else (
    echo ⏭️  跳过虚拟环境
)

REM 安装依赖
echo.
echo 4. 安装依赖...
pip install -r requirements.txt
echo ✅ 依赖安装完成

REM 创建必要目录
echo.
echo 5. 创建必要目录...
if not exist vector_db_storage mkdir vector_db_storage
if not exist chat_histories mkdir chat_histories
if not exist temp_uploads mkdir temp_uploads
if not exist hf_cache mkdir hf_cache
if not exist app_logs mkdir app_logs
if not exist suggestion_history mkdir suggestion_history
echo ✅ 目录创建完成

REM 检查端口
echo.
echo 6. 检查端口 8501...
netstat -ano | findstr :8501 >nul 2>&1
if errorlevel 1 (
    echo ✅ 端口 8501 可用
) else (
    echo ⚠️  端口 8501 已被占用
    echo 可以使用其他端口: streamlit run src/apppro.py --server.port 8502
)

REM 运行测试
echo.
echo 7. 运行出厂测试...
set /p run_test="是否运行测试？(y/n): "
if /i "%run_test%"=="y" (
    python tests/factory_test.py
) else (
    echo ⏭️  跳过测试
)

REM 完成
echo.
echo ============================================================
echo   部署完成！
echo ============================================================
echo.
echo 启动应用:
echo   streamlit run src/apppro.py
echo.
echo 或创建快捷方式:
echo   1. 右键 start_windows.bat
echo   2. 发送到 -^> 桌面快捷方式
echo.
pause
