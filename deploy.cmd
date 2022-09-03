@echo off
set REGISTRY_IP=192.168.1.3
set REGISTRY_PORT=5001
set IMAGE_NAME=rozetka
set IMAGE_TAG=latest
set BUILD_TAG=%REGISTRY_IP%:%REGISTRY_PORT%/%IMAGE_NAME%:%IMAGE_TAG%
set BUILD_PATH=.

set "_DOCKER=docker"
@REM set "_DOCKER=C:\Program Files\Docker\Docker\resources\bin\docker.exe"

pushd %~dp0
@REM net start com.docker.service || exit /b
"%_DOCKER%" build -t %BUILD_TAG% %BUILD_PATH% || exit /b
"%_DOCKER%" push %REGISTRY_IP%:%REGISTRY_PORT%/%IMAGE_NAME% || exit /b
@REM net stop com.docker.service || exit /b
