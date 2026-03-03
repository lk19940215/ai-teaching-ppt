@echo off
setlocal enabledelayedexpansion

:: Claude Auto Loop - Windows unified entry point
::
:: Usage:
::   claude-auto-loop\loop.bat run "your requirement"
::   claude-auto-loop\loop.bat setup
::   claude-auto-loop\loop.bat update
::   claude-auto-loop\loop.bat validate

if "%~1"=="" (
    echo [ERROR] 请指定子命令
    echo.
    echo 用法:
    echo   claude-auto-loop\loop.bat run "你的需求"
    echo   claude-auto-loop\loop.bat setup
    echo   claude-auto-loop\loop.bat update
    echo   claude-auto-loop\loop.bat validate
    exit /b 1
)

set "CMD=%~1"
set "SCRIPT_DIR=%~dp0"
set "SH_FILE=%SCRIPT_DIR%%CMD%.sh"

:: Validate subcommand
if not exist "%SH_FILE%" (
    echo [ERROR] 未知子命令: %CMD%
    echo         找不到 %SH_FILE%
    echo.
    echo 可用子命令: run, setup, update, validate
    exit /b 1
)

:: Locate Git Bash via 'where git'
set "BASH_EXE="
for /f "delims=" %%G in ('where git 2^>nul') do (
    if not defined BASH_EXE (
        for %%P in ("%%~dpG..") do set "GIT_ROOT=%%~fP"
        if exist "!GIT_ROOT!\bin\bash.exe" (
            set "BASH_EXE=!GIT_ROOT!\bin\bash.exe"
        )
    )
)

:: Fallback: common install paths
if not defined BASH_EXE (
    for %%D in (
        "C:\Program Files\Git\bin\bash.exe"
        "C:\Program Files (x86)\Git\bin\bash.exe"
        "%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
    ) do (
        if exist %%D if not defined BASH_EXE set "BASH_EXE=%%~D"
    )
)

if not defined BASH_EXE (
    echo [ERROR] 未找到 Git Bash。
    echo         请安装 Git for Windows: https://git-scm.com/download/win
    exit /b 1
)

:: Strip the first argument (subcommand), pass the rest to .sh
shift
"%BASH_EXE%" "%SH_FILE%" %1 %2 %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%
