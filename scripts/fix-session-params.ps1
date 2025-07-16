#!/usr/bin/env powershell

# Script to fix Session import issues in all endpoint files

$files = @(
    "agents.py",
    "constraints.py", 
    "integration.py",
    "master_data.py",
    "observability.py",
    "prompts.py",
    "secrets.py",
    "skills.py",
    "system.py",
    "templates.py",
    "tools.py",
    "workflows.py"
)

$backendDir = "c:\Users\Srees\project\agent_mesh\backend"
$endpointsDir = "$backendDir\app\api\v1\endpoints"

foreach ($file in $files) {
    $filePath = "$endpointsDir\$file"
    Write-Host "Processing $file..."
    
    if (Test-Path $filePath) {
        # Read file content
        $content = Get-Content $filePath -Raw
        
        # Fix Session usage in function parameters
        $content = $content -replace "db: Session = Depends\(get_db\)", "db: AsyncSession = Depends(get_db)"
        
        # Write back to file
        Set-Content $filePath $content -NoNewline
        Write-Host "Fixed $file"
    } else {
        Write-Host "File $file not found"
    }
}

Write-Host "All files processed!"
