# Common Issues and Solutions

This document outlines common issues you might encounter when setting up Agent Mesh and how to resolve them.

## Issue 1: "Cannot find module '/app/server.js'"

**Problem**: The Node.js frontend container fails to start with this error.

**Solution**: 
1. This is now fixed with the improved Docker setup that separates development and production modes.
2. Use the development setup by default: `docker-compose up --build`
3. For production builds: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build`

## Issue 2: "role 'user' does not exist"

**Problem**: PostgreSQL container fails to start because the user role doesn't exist.

**Solution**:
1. The database initialization scripts now automatically create the user role
2. Ensure your `.env` file has the correct database configuration
3. If still having issues, run: `./quick-fix.ps1`

## Issue 3: "NoReferencedTableError: Foreign key... could not find table 'master.model_configurations'"

**Problem**: SQLAlchemy can't find the model_configurations table.

**Solution**:
1. This is now fixed with the added `ModelConfiguration` and `LLMProvider` models
2. The database migration scripts will create these tables automatically
3. Restart the containers: `docker-compose down && docker-compose up --build`

## Issue 4: "ModuleNotFoundError: No module named 'deprecated'"

**Problem**: The observability service fails because the `deprecated` module is missing.

**Solution**:
1. The `deprecated` module has been added to requirements.txt
2. Rebuild the containers: `docker-compose build --no-cache`

## Quick Fix Script

Run the quick fix script to automatically resolve most common issues:

```powershell
# On Windows
.\quick-fix.ps1

# On Linux/Mac
./quick-fix.sh
```

## Development vs Production

### Development Mode (Default)
```bash
# Start in development mode with hot reloading
docker-compose up --build

# Or use the helper script
.\run-docker.ps1 dev
```

### Production Mode
```bash
# Start in production mode with optimized builds
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build

# Or use the helper script
.\run-docker.ps1 prod
```

## Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your actual values:
   ```env
   # Database
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   POSTGRES_DB=agentmesh
   
   # LLM API Keys (optional)
   AZURE_OPENAI_API_KEY=your-key-here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   ```

## Troubleshooting

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Clean Restart
```bash
# Stop and remove containers
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

### Database Issues

If you encounter database connection issues:

1. Check if PostgreSQL is running:
   ```bash
   docker-compose exec postgres pg_isready -U user -d agentmesh
   ```

2. Connect to the database:
   ```bash
   docker-compose exec postgres psql -U user -d agentmesh
   ```

3. Check table creation:
   ```sql
   \dt app.*
   \dt master.*
   ```

### Port Conflicts

If you get port conflicts:

1. Stop conflicting services:
   ```bash
   # Stop PostgreSQL if running locally
   sudo service postgresql stop
   
   # Stop Redis if running locally
   sudo service redis stop
   ```

2. Or change ports in `docker-compose.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Use different external port
   ```

## Getting Help

If you're still experiencing issues:

1. Check the logs for specific error messages
2. Ensure all environment variables are set correctly
3. Verify Docker has enough resources allocated
4. Check if your firewall is blocking the ports

For additional support, please check the main README.md file or create an issue in the repository.
