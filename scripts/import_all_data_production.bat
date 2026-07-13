@echo off
echo Starting Suraksha AI Production Datastore Import...

echo Importing table: District...
catalyst ds:import catalyst_import_data\District.csv --table District --production
if %ERRORLEVEL% neq 0 goto error

echo Importing table: Unit...
catalyst ds:import catalyst_import_data\Unit.csv --table Unit --production
if %ERRORLEVEL% neq 0 goto error

echo Importing table: CrimeHead...
catalyst ds:import catalyst_import_data\CrimeHead.csv --table CrimeHead --production
if %ERRORLEVEL% neq 0 goto error

echo Importing table: CrimeSubHead...
catalyst ds:import catalyst_import_data\CrimeSubHead.csv --table CrimeSubHead --production
if %ERRORLEVEL% neq 0 goto error

echo Importing table: CaseMaster...
catalyst ds:import catalyst_import_data\CaseMaster.csv --table CaseMaster --production
if %ERRORLEVEL% neq 0 goto error

echo Importing table: Accused...
catalyst ds:import catalyst_import_data\Accused.csv --table Accused --production
if %ERRORLEVEL% neq 0 goto error

echo All tables imported successfully to Production!
pause
exit /b 0

:error
echo An error occurred during the Production import. Please check if the tables exist in your Catalyst Production Datastore.
pause
exit /b 1
