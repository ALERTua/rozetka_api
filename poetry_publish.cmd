
@echo off
pushd %~dp0
rem call .venv\scripts\activate
poetry config repositories.test-pypi https://test.pypi.org/legacy/
poetry publish -r test-pypi --build
