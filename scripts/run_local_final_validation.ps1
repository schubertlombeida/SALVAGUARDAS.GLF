param(
    [Parameter(Mandatory=$true)][string]$CorpusZip,
    [Parameter(Mandatory=$true)][string]$GoldCsv,
    [string]$Model = "qwen2.5:7b",
    [int]$Samples = 40,
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CorpusZip)) { throw "No existe el corpus: $CorpusZip" }
if (-not (Test-Path $GoldCsv)) { throw "No existe el gold v2: $GoldCsv" }

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) { throw "Ollama no esta disponible en PATH." }

$models = ollama list 2>&1 | Out-String
if ($models -notmatch [regex]::Escape($Model)) {
    throw "El modelo $Model no aparece en ollama list. Ejecuta: ollama pull $Model"
}

$env:GLF_OLLAMA_URL = "http://127.0.0.1:11434"
$env:GLF_OLLAMA_MODEL = $Model
$env:GLF_CORPUS_ZIP = $CorpusZip

$output = Join-Path (Get-Location) "results\final_validation"
New-Item -ItemType Directory -Path $output -Force | Out-Null

$server = $null
try {
    $serverOut = Join-Path $output "server_stdout.log"\n    $serverErr = Join-Path $output "server_stderr.log"\n    $argLine = "-m app.server --archive `"$CorpusZip`" --port $Port"\n    $server = Start-Process python -ArgumentList $argLine -PassThru -WindowStyle Hidden -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr

    $ready = $false
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $status = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/status" -TimeoutSec 2
            if ($status.chunks -eq 585) { $ready = $true; break }
        } catch {}
    }
    if (-not $ready) {\n        Write-Host ""\n        Write-Host "El servidor no inicio. Diagnostico:" -ForegroundColor Red\n        if (Test-Path $serverErr) { Get-Content $serverErr | Write-Host }\n        if (Test-Path $serverOut) { Get-Content $serverOut | Write-Host }\n        throw "El servidor GLF no inicio correctamente."\n    }

    Write-Host ""
    Write-Host "Servidor listo: $($status.method), $($status.chunks) fragmentos"
    Write-Host "Recall@5 desarrollo registrado: $([math]::Round(100*$status.development_recall_at_5,1))%"
    Write-Host "Recall@5 validation registrado: $([math]::Round(100*$status.validation_recall_at_5,1))%"
    Write-Host ""

    python ".\scripts\benchmark_e2e.py" --gold $GoldCsv --base-url "http://127.0.0.1:$Port" --samples $Samples --warmup 3 --output (Join-Path $output "e2e_latency_v2.json")
    if ($LASTEXITCODE -ne 0) { throw "El benchmark de latencia fallo." }

    $report = Get-Content (Join-Path $output "e2e_latency_v2.json") -Raw | ConvertFrom-Json
    Write-Host ""
    Write-Host "VALIDACION FINAL LOCAL"
    Write-Host "Muestras: $($report.samples)"
    Write-Host "p50: $([math]::Round($report.p50_total_seconds,3)) s"
    Write-Host "p95: $([math]::Round($report.p95_total_seconds,3)) s"
    Write-Host "Meta p95 <= 7 s: $($report.target_met)"
    Write-Host "Reporte: $(Join-Path $output 'e2e_latency_v2.json')"
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
}
