# Script to organize documentation and reports into docs/ folder
# Run from project root: .\scripts\organize_docs.ps1

$ErrorActionPreference = "Continue"

Write-Host "Organizing PREMONITOR documentation..." -ForegroundColor Cyan

# Move markdown docs to docs/
$docs = @(
    "TRAINING_AND_DEPLOYMENT_GUIDE.md",
    "RESEARCH_SUMMARY.md",
    "REVIEW_SUMMARY.md",
    "README.md"
)

foreach ($doc in $docs) {
    if (Test-Path $doc) {
        Write-Host "Moving $doc to docs/" -ForegroundColor Green
        Move-Item -Path $doc -Destination "docs\" -Force
    }
}

# Move reports to docs/reports/
$reports = @(
    "VERIFICATION_REPORT.md",
    "VERIFICATION_REPORT_TRAINING_DEPLOYMENT.md",
    "TRAINING_EXECUTION_REPORT.md",
    "FINAL_VERIFICATION_SUMMARY.md",
    "CHANGELOG.md"
)

foreach ($report in $reports) {
    if (Test-Path $report) {
        Write-Host "Moving $report to docs/reports/" -ForegroundColor Green
        Move-Item -Path $report -Destination "docs\reports\" -Force
    }
}

Write-Host "`nDocumentation organized successfully!" -ForegroundColor Green
Write-Host "- Main docs: docs/" -ForegroundColor Yellow
Write-Host "- Reports: docs/reports/" -ForegroundColor Yellow
