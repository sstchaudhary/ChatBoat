Param()
# Bootstraps the backend: create venv, install deps, run migrations
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $root

if (-not (Test-Path -Path .venv)) {
    python -m venv .venv
    Write-Host "Created .venv"
} else {
    Write-Host ".venv already exists"
}

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = 'python' }
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python manage.py makemigrations
& $python manage.py migrate
Write-Host "Bootstrap complete. To run server: .\.venv\Scripts\Activate.ps1; python manage.py runserver"

Pop-Location
