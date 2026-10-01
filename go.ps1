#requires -Version 7.0
[CmdletBinding(DefaultParameterSetName = 'Preview')]
param(
    [Parameter(ParameterSetName = 'Check')][switch]$Check,
    [Parameter(ParameterSetName = 'Manual')][switch]$Manual,
    [Parameter(Mandatory, ParameterSetName = 'Enterprise')][switch]$Enterprise,
    [Parameter(ParameterSetName = 'Enterprise')][string]$Ledger,
    [Parameter(ParameterSetName = 'Enterprise')][ValidateRange(1, 50)][int]$MaxNew,
    [Parameter(ParameterSetName = 'Enterprise')][switch]$StopNewWork,
    [Parameter(Mandatory, ParameterSetName = 'Live')][switch]$Live,
    [Parameter(ParameterSetName = 'Live')][switch]$AcceptLiveRun,
    [Parameter(Mandatory, ParameterSetName = 'Live')][string]$Repository,
    [Parameter(ParameterSetName = 'Live')]
    [Parameter(ParameterSetName = 'Enterprise')]
    [Parameter(ParameterSetName = 'Preview')][switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if ($Live -and -not $AcceptLiveRun) {
        throw 'Live issue creation requires -AcceptLiveRun. No cloud work was requested.'
    }
    if ($PSCmdlet.ParameterSetName -eq 'Enterprise' -and -not $Enterprise) {
        throw 'Enterprise ledger controls require -Enterprise.'
    }
    if ($Manual) {
        Write-Host 'Offline: .\go.ps1 -Check; .\go.ps1 -NoBrowser'
        Write-Host 'Enterprise rehearsal: .\go.ps1 -Enterprise -NoBrowser'
        Write-Host 'Durable replay: .\go.ps1 -Enterprise -Ledger out\enterprise-workshop.sqlite3'
        Write-Host 'Local limits: add -MaxNew 1 or -StopNewWork; no platform jobs are executed.'
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
    if ($Enterprise) {
        $arguments = @('-m', 'issue_agent', 'enterprise')
        if ($PSBoundParameters.ContainsKey('Ledger')) { $arguments += @('--ledger', $Ledger) }
        if ($PSBoundParameters.ContainsKey('MaxNew')) { $arguments += @('--max-new', $MaxNew.ToString()) }
        if ($StopNewWork) { $arguments += '--stop-new-work' }
        & python @arguments
        if ($LASTEXITCODE -ne 0) { throw 'Enterprise rehearsal failed; inspect its retained failure evidence.' }
        Write-Host 'Local rehearsal only: no GitHub API, agent, workflow, runner, or deployment was started.'
    } elseif ($Live) {
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
