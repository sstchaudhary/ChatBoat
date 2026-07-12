Param()
python -m venv .venv
Write-Host "Created .venv"
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
Write-Host "Virtualenv created and requirements installed. Activate with: .\.venv\Scripts\Activate.ps1"
