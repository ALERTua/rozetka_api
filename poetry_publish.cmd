
pushd %~dp0
call .venv\scripts\activate
poetry config repositories.test-pypi https://test.pypi.org/legacy/
poetry publish -r test-pypi --build
