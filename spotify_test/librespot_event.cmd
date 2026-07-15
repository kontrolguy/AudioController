@echo off

cd /d "%~dp0"

echo %date% %time% EVENT=%PLAYER_EVENT% >> librespot_events.log

python "%~dp0librespot_event.py" >> librespot_event_output.log 2>&1