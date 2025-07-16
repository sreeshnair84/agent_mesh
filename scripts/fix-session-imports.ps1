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
    
    # Read file content
    $content = Get-Content $filePath -Raw
    
    # Fix imports - replace Session with AsyncSession
    $content = $content -replace "from sqlalchemy\.orm import Session", "from sqlalchemy.ext.asyncio import AsyncSession"
    $content = $content -replace "from sqlalchemy import.*Session.*", "from sqlalchemy.ext.asyncio import AsyncSession"
    
    # Fix Session usage in function parameters
    $content = $content -replace "db: Session = Depends\(get_db\)", "db: AsyncSession = Depends(get_db)"
    
    # Fix synchronous database operations to async
    $content = $content -replace "db\.query\(", "await db.execute(select("
    $content = $content -replace "\.first\(\)", ")).scalar_one_or_none()"
    $content = $content -replace "\.all\(\)", ")).scalars().all()"
    $content = $content -replace "db\.add\(", "db.add("
    $content = $content -replace "db\.commit\(\)", "await db.commit()"
    $content = $content -replace "db\.rollback\(\)", "await db.rollback()"
    $content = $content -replace "db\.refresh\(", "await db.refresh("
    $content = $content -replace "db\.delete\(", "await db.delete("
    
    # Write back to file
    Set-Content $filePath $content
    Write-Host "Fixed $file"
}

Write-Host "All files processed!"
