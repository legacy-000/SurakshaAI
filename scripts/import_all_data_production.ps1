Write-Host "Starting Suraksha AI Production Datastore Import..." -ForegroundColor Cyan

# Sequence to ensure foreign key integrity
$tables = @(
    @{ name = "District"; file = "catalyst_import_data\District.csv" },
    @{ name = "Unit"; file = "catalyst_import_data\Unit.csv" },
    @{ name = "CrimeHead"; file = "catalyst_import_data\CrimeHead.csv" },
    @{ name = "CrimeSubHead"; file = "catalyst_import_data\CrimeSubHead.csv" },
    @{ name = "CaseMaster"; file = "catalyst_import_data\CaseMaster.csv" },
    @{ name = "Accused"; file = "catalyst_import_data\Accused.csv" }
)

foreach ($table in $tables) {
    Write-Host "Importing table to Production: $($table.name)..." -ForegroundColor Yellow
    catalyst ds:import $table.file --table $table.name --production
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error importing $($table.name). Please check if the table exists in your Catalyst Production Datastore." -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Successfully imported $($table.name) to Production!" -ForegroundColor Green
}

Write-Host "All tables imported successfully to Production!" -ForegroundColor Green
