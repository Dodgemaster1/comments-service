set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

[doc("All command information")]
help:
    @just --list --unsorted

alias l := lint

[doc("Check and format code with autofix using ruff")]
[group("local")]
lint:
    uv run ruff format .
    uv run ruff check . --fix
    uv run ruff format .

alias tc := typecheck

[doc("Check types using pyrefly")]
[group("local")]
typecheck:
    uv run pyrefly check

alias m := manage
[doc("Run manage.py commands")]
[group("local")]
manage *args:
    uv run manage.py {{ args }}

alias t := test

[doc("Run tests (in tests/) using pytest")]
[group("local")]
test package:
    uv run --package {{ package }} pytest -v -s

alias c := check

[doc("Run all checks (lint, typecheck, test)")]
[group("local")]
check:
    just lint
    just typecheck
    just test

prod:
    uv run granian config.asgi:application --interface asgi --host 0.0.0.0 --port 8000
