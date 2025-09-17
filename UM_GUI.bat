@echo off
setlocal

rem Get the path of Uni_Mapper.py next to this .bat
set SCRIPT=%~dp0Uni_Mapper.py

python "%SCRIPT%"

endlocal
pause
