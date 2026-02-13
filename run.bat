@echo off
chcp 65001 >nul
cd /d "%~dp0"

 REM 结束占用 8501 端口的进程（已有 Streamlit 实例）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING 监听"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

.venv\Scripts\streamlit.exe run mix_tools/ui/app.py
pause
