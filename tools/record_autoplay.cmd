@echo off
rem Records the autoplay scenario to build\autoplay\f########.png (30 fps).
rem Usage: tools\record_autoplay.cmd [path\to\godot.exe]
setlocal
set GODOT=%~1
if "%GODOT%"=="" set GODOT=D:\MIDAS\godot\bin\godot.windows.editor.dev.x86_64.console.exe
cd /d "%~dp0.."
if not exist build\autoplay mkdir build\autoplay
del /q build\autoplay\* 2>nul
"%GODOT%" --path . --script res://tools/autoplay_record.gd --write-movie build\autoplay\f.png --fixed-fps 30 --disable-vsync
