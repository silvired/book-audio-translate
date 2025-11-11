# Script to install TTS with Visual Studio environment
Write-Host "Checking Python version..." -ForegroundColor Yellow
python --version

Write-Host "Activating Visual Studio environment..." -ForegroundColor Yellow

# Activate VS Developer Shell - correct syntax
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\Launch-VsDevShell.ps1" -Arch x64

Write-Host "Installing TTS..." -ForegroundColor Yellow
pip install -r audio_requirements.txt

Write-Host "Done!" -ForegroundColor Green
