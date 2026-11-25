param([switch]$RefreshArchive)

$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$build = Join-Path $project 'build'
$latex = Join-Path $project 'latex'
$finalPdf = Join-Path $project 'Mathematical_Exploration_Prototype.pdf'

if ($RefreshArchive -or -not (Test-Path -LiteralPath (Join-Path $project 'archive/normalized-path.jsonl'))) {
    python (Join-Path $project 'scripts/inspect_archive.py')
    if ($LASTEXITCODE -ne 0) { throw 'Archive inspection failed.' }
}

python (Join-Path $project 'scripts/build_excerpt.py')
if ($LASTEXITCODE -ne 0) { throw 'Excerpt conversion failed.' }

New-Item -ItemType Directory -Force -Path $build | Out-Null
Push-Location -LiteralPath $latex
try {
    latexmk "-outdir=$build" -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
    if ($LASTEXITCODE -ne 0) { throw 'XeLaTeX compilation failed.' }
} finally {
    Pop-Location
}

$compiled = Join-Path $build 'main.pdf'
python (Join-Path $project 'scripts/check_pdf.py') $compiled
if ($LASTEXITCODE -ne 0) { throw 'Prototype PDF verification failed.' }

Move-Item -Force -LiteralPath $compiled -Destination $finalPdf
Get-Item -LiteralPath $finalPdf
