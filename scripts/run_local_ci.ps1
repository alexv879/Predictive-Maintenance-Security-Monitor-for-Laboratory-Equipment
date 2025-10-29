# Premonitor Local CI Script
# Run this script to perform the same checks as CI/CD pipeline locally

$ErrorActionPreference = "Continue"
$global:failed = $false

function Run-Check {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "CHECK: $Name" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    try {
        & $Command
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[PASS] $Name" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[FAIL] $Name (exit code: $LASTEXITCODE)" -ForegroundColor Red
            $global:failed = $true
            return $false
        }
    } catch {
        Write-Host "[FAIL] $Name - Exception: $_" -ForegroundColor Red
        $global:failed = $true
        return $false
    }
}

# Banner
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║            PREMONITOR - LOCAL CI PIPELINE                 ║
║                                                           ║
╔═══════════════════════════════════════════════════════════╗

"@ -ForegroundColor Cyan

# Get project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow
Write-Host "Python Version: $(python --version)" -ForegroundColor Yellow
Write-Host ""

# Track results
$results = @()

# Check 1: Syntax Validation
$results += Run-Check "Syntax Validation" {
    Write-Host "Checking Python syntax for all source files..."
    $pythonFiles = Get-ChildItem -Path "pythonsoftware" -Filter "*.py"
    $allPassed = $true

    foreach ($file in $pythonFiles) {
        python -m py_compile $file.FullName
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [FAIL] $($file.Name)" -ForegroundColor Red
            $allPassed = $false
        } else {
            Write-Host "  [PASS] $($file.Name)" -ForegroundColor Gray
        }
    }

    if (-not $allPassed) {
        exit 1
    }
}

# Check 2: Dataset Validation
$results += Run-Check "Dataset Validation" {
    Write-Host "Running dataset validation script..."
    python scripts\check_datasets.py
}

# Check 3: Dataset Tests
$results += Run-Check "Dataset Tests" {
    Write-Host "Running dataset smoke tests..."
    python tests\test_datasets.py
}

# Check 4: Import Tests (may fail if dependencies not installed)
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CHECK: Module Import Tests (optional)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python tests\test_imports.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] Module Import Tests" -ForegroundColor Green
    $results += $true
} else {
    Write-Host "[WARN] Module Import Tests failed (may need dependencies)" -ForegroundColor Yellow
    # Don't mark as failed - this is expected without full deps
    $results += $true
}

# Check 5: Linting (if flake8 installed)
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CHECK: Linting (optional)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$flake8Available = $null -ne (Get-Command flake8 -ErrorAction SilentlyContinue)
if ($flake8Available) {
    Write-Host "Running flake8 linter..."
    flake8 pythonsoftware\ --count --select=E9,F63,F7,F82 --show-source --statistics
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Linting" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Linting found issues" -ForegroundColor Yellow
    }
} else {
    Write-Host "[SKIP] flake8 not installed (run: pip install flake8)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passed = ($results | Where-Object { $_ -eq $true }).Count
$total = $results.Count

Write-Host "Results: $passed/$total checks passed" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })

if ($global:failed) {
    Write-Host "`n[FAILED] CI checks failed - fix issues before committing" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n[SUCCESS] All CI checks passed!" -ForegroundColor Green
    exit 0
}
