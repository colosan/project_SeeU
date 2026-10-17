@echo off
rem Records the autoplay scenario to build\autoplay\f########.png (30 fps).
rem Usage: tools\record_autoplay.cmd [path\to\godot.exe]
rem Without an argument it uses %GODOT% if set, else the first Godot it knows about on this PC or the others.
setlocal
set GODOT_EXE=%~1
if "%GODOT_EXE%"=="" set GODOT_EXE=%GODOT%
if "%GODOT_EXE%"=="" if exist "D:\MIDAS\godot\bin\godot.windows.editor.dev.x86_64.console.exe" set GODOT_EXE=D:\MIDAS\godot\bin\godot.windows.editor.dev.x86_64.console.exe
if "%GODOT_EXE%"=="" if exist "%USERPROFILE%\Downloads\Godot_v4.6.3-stable_win64.exe\Godot_v4.6.3-stable_win64_console.exe" set GODOT_EXE=%USERPROFILE%\Downloads\Godot_v4.6.3-stable_win64.exe\Godot_v4.6.3-stable_win64_console.exe
if "%GODOT_EXE%"=="" (
  echo No Godot found: pass its path or set GODOT.
  exit /b 1
)
cd /d "%~dp0.."
if not exist build\autoplay mkdir build\autoplay
del /q build\autoplay\* 2>nul
"%GODOT_EXE%" --path . --script res://tools/autoplay_record.gd --write-movie build\autoplay\f.png --fixed-fps 30 --disable-vsync
