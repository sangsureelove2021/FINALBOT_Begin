@echo off
chdir /d "%~dp0"
if "%1"=="--headless" (
    set DS_QUIET=true && node src/index.js --headless %*
) else if "%1"=="--full" (
    set DS_QUIET=true && node src/index.js %*
) else if "%1"=="--help" (
    set DS_QUIET=true && node src/index.js --help
) else if "%1"=="" (
    set DS_QUIET=true && node src/index.js --headless
) else (
    set DS_QUIET=true && node src/index.js %*
)