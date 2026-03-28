#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] проверка синтаксиса python-файлов"
python -m py_compile src/controller/guest_isolation.py src/topology/agrotex_topology.py

echo "[2/4] проверка форматирования shell-скриптов (bash -n)"
bash -n scripts/run_policy_checks.sh

echo "[3/4] проверка структуры репозитория"
test -f README.md && test -f WORK.md && test -f DESCRIPTION.md

echo "[4/4] проверка наличия ключевых директорий"
test -d src/controller && test -d src/topology

echo "[OK] базовые проверки пройдены успешно"