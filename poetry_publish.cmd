
@echo off
pushd %~dp0
rem call .venv\scripts\activate
set PYPI_REPO=test-pypi
set PYPI_REPO_FULL=repositories.%PYPI_REPO%

poetry config %PYPI_REPO_FULL% https://test.pypi.org/legacy/
poetry publish -r %PYPI_REPO% --build || echo Please auth in %PYPI_REPO_FULL% using poetry config poetry config http-basic.%PYPI_REPO% __token__ token
