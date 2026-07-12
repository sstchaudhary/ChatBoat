#!/usr/bin/env bash
python3 -m venv .venv
echo "Created .venv"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
echo "Virtualenv created and requirements installed. Activate with: source .venv/bin/activate"
