
@echo off
pushd %~dp0
    set DOCKER_HOST=tcp://docker:2375
    set DOCKER_REMOTE=1
    call deploy.cmd %*
    where nircmd >nul 2>nul && nircmd beep 500 500
popd