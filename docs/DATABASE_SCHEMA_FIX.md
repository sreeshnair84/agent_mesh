# Database Schema Initialization Fix

## Issue Resolved
**Error**: `psql:/docker-entrypoint-initdb.d/00_create_user.sql:24: ERROR:  schema "app" does not exist`

## Root Cause
The database initialization scripts were running in the wrong order. The user creation script was trying to grant permissions on schemas that hadn't been created yet.

## Fix Applied

### 1. Script Execution Order Fixed
Renamed initialization scripts to ensure correct execution order:

**Before:**
```
00_create_user.sql      # ❌ Runs first, references non-existent schemas
01_create_extensions.sql
02_create_schemas.sql
03_grant_permissions.sql
```

**After:**
```
01_create_extensions.sql    # ✅ Install PostgreSQL extensions
02_create_schemas.sql       # ✅ Create schemas 
03_create_user.sql         # ✅ Create user (after schemas exist)
04_grant_permissions.sql   # ✅ Grant schema permissions
```

### 2. User Creation Script Simplified
Updated `03_create_user.sql` to:
- Only create the database user
- Grant basic permissions on existing schemas (public)
- Avoid referencing custom schemas that might not exist yet

### 3. Permissions Script Enhanced
Updated `04_grant_permissions.sql` to:
- Check if schemas exist before granting permissions
- Use conditional logic to avoid errors
- Grant comprehensive permissions on all custom schemas

## Files Modified
- `database/init/03_create_user.sql` (renamed from `00_create_user.sql`)
- `database/init/04_grant_permissions.sql` (renamed from `03_grant_permissions.sql`)
- `quick-fix.ps1` - Updated to recommend database recreation
- `quick-fix.sh` - Updated to recommend database recreation

## How to Apply This Fix

### Option 1: Run Quick Fix Script (Recommended)
```bash
# Windows
.\quick-fix.ps1

# Linux/Mac
./quick-fix.sh
```
The script will offer to recreate the database with the fixed initialization order.

### Option 2: Manual Database Recreation
```bash
# Stop all services and remove database volumes
docker-compose down -v --remove-orphans

# Remove old images to ensure fresh builds
docker-compose build --no-cache

# Start services (database will initialize with correct script order)
docker-compose up -d

# Check database initialization
docker-compose logs postgres
```

## Verification Steps

1. **Check database initialization logs**:
   ```bash
   docker-compose logs postgres | grep -E "(CREATE|GRANT|ERROR)"
   ```

2. **Verify user and schemas exist**:
   ```bash
   # Connect to database
   docker-compose exec postgres psql -U user -d agentmesh
   
   # Check schemas
   \dn
   
   # Check user permissions
   \du
   ```

3. **Test backend connection**:
   ```bash
   # Backend should start without database errors
   docker-compose logs backend
   ```

## Expected Results

✅ **Database initialization completes without errors**  
✅ **User 'user' created with proper permissions**  
✅ **All schemas (app, master, vectors, observability, audit) created**  
✅ **Backend connects to database successfully**  
✅ **No more "schema does not exist" errors**

## Script Execution Flow
1. `01_create_extensions.sql` - Extensions (pgvector, uuid-ossp, etc.)
2. `02_create_schemas.sql` - Custom schemas and types
3. `03_create_user.sql` - Database user with basic permissions
4. `04_grant_permissions.sql` - Schema-specific permissions

This ensures schemas exist before any script tries to reference them.
