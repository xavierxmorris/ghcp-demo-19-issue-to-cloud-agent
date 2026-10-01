#requires -Version 7.0
[CmdletBinding(DefaultParameterSetName = 'Preview')]
param(
    [Parameter(ParameterSetName = 'Check')][switch]$Check,
    [Parameter(ParameterSetName = 'Manual')][switch]$Manual,
    [Parameter(Mandatory, ParameterSetName = 'Live')][switch]$Live,
    [Parameter(ParameterSetName = 'Live')][switch]$AcceptLiveRun,
    [Parameter(Mandatory, ParameterSetName = 'Live')][string]$Repository,
    [Parameter(ParameterSetName = 'Live')]
    [Parameter(ParameterSetName = 'Preview')][switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if ($Live -and -not $AcceptLiveRun) {
        throw 'Live issue creation requires -AcceptLiveRun. No cloud work was requested.'
    }
    if ($Manual) {
        Write-Host 'Offline: .\go.ps1 -Check; .\go.ps1 -NoBrowser'
        Write-Host 'Live: read docs\LIVE-SETUP.md, configure the scoped secret and enable the trigger.'
        Write-Host '.\go.ps1 -Live -AcceptLiveRun -Repository OWNER/REPO'
        Write-Host 'The runner creates an UNASSIGNED issue. The issues:opened workflow starts Copilot.'
        Write-Host 'Observe: python -m issue_agent observe --repository OWNER/REPO --issue NUMBER'
        Write-Host 'Stop before merge. Assignment is not migration completion.'
        exit 0
    }
    & python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 2)"
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
    if ($Check) {
        & python -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw 'Offline unit tests failed.' }
        & python (Join-Path 'scripts' 'check_repo.py')
        if ($LASTEXITCODE -ne 0) { throw 'Repository checks failed.' }
        exit 0
    }
    if ($Live) {
        $result = & python -m issue_agent raise --repository $Repository --accept-live-run
        if ($LASTEXITCODE -ne 0) { throw 'Issue creation failed; inspect the retained evidence before retrying.' }
        $result | Write-Output
        $request = $result | ConvertFrom-Json
        if (-not $NoBrowser -and $request.issue_url) {
            Start-Process -FilePath $request.issue_url | Out-Null
        }
    } else {
        & python -m issue_agent preview
        if ($LASTEXITCODE -ne 0) { throw 'Offline preview failed.' }
        Write-Host 'Offline preview only: no issue, assignment, model, or PR was created.'
    }
} finally {
    Pop-Location
}
