#!/usr/bin/env bash
# Prestart script for backend container
# Waits for PostgreSQL, runs migrations, then starts the application

set -Eeuo pipefail

# Configuration
MAX_DB_WAIT_ATTEMPTS=30
MAX_MIGRATION_ATTEMPTS=3
INITIAL_BACKOFF=1

# Logging functions
log_info() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*"
}

log_warn() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $*" >&2
}

log_error() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

log_success() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $*"
}

# Wait for PostgreSQL to be ready with exponential backoff
wait_for_postgres() {
  log_info "Waiting for PostgreSQL to be ready..."
  
  local attempt=1
  local backoff=${INITIAL_BACKOFF}
  
  while [ ${attempt} -le ${MAX_DB_WAIT_ATTEMPTS} ]; do
    log_info "Checking database connection (attempt ${attempt}/${MAX_DB_WAIT_ATTEMPTS})..."
    
    # Try to connect using Python with SQLAlchemy
    if python3 -c "
import sys
import os
from sqlalchemy import create_engine, text

try:
    database_url = os.getenv('DATABASE_URL', '')
    # Convert asyncpg to psycopg for sync connection test
    test_url = database_url.replace('+asyncpg', '')
    if not test_url.startswith('postgresql'):
        print('DATABASE_URL not set or invalid', file=sys.stderr)
        sys.exit(1)
    
    engine = create_engine(test_url, connect_args={'connect_timeout': 5})
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    
    sys.exit(0)
except Exception as e:
    print(f'Connection failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1; then
      log_success "PostgreSQL is ready!"
      return 0
    fi
    
    log_warn "PostgreSQL not ready yet, waiting ${backoff}s before retry..."
    sleep ${backoff}
    
    # Exponential backoff with cap at 30 seconds
    backoff=$((backoff * 2))
    if [ ${backoff} -gt 30 ]; then
      backoff=30
    fi
    
    attempt=$((attempt + 1))
  done
  
  log_error "PostgreSQL did not become ready after ${MAX_DB_WAIT_ATTEMPTS} attempts"
  return 1
}

# Run database migrations with retry logic
run_migrations() {
  log_info "Running database migrations..."
  
  local attempt=1
  while [ ${attempt} -le ${MAX_MIGRATION_ATTEMPTS} ]; do
    log_info "Migration attempt ${attempt}/${MAX_MIGRATION_ATTEMPTS}..."
    
    if alembic upgrade head 2>&1; then
      log_success "Database migrations completed successfully"
      return 0
    fi
    
    log_warn "Migration attempt ${attempt} failed"
    
    if [ ${attempt} -lt ${MAX_MIGRATION_ATTEMPTS} ]; then
      local wait_time=$((attempt * 2))
      log_info "Waiting ${wait_time}s before retry..."
      sleep ${wait_time}
    fi
    
    attempt=$((attempt + 1))
  done
  
  log_error "Database migrations failed after ${MAX_MIGRATION_ATTEMPTS} attempts"
  return 1
}

# Main execution
main() {
  log_info "Starting backend prestart script..."
  
  # Check DATABASE_URL is set
  if [ -z "${DATABASE_URL:-}" ]; then
    log_error "DATABASE_URL environment variable is not set"
    exit 1
  fi
  
  # Wait for PostgreSQL
  if ! wait_for_postgres; then
    log_error "Database connection check failed"
    exit 1
  fi
  
  # Run migrations
  if ! run_migrations; then
    log_error "Migration execution failed"
    exit 1
  fi
  
  log_success "Prestart script completed successfully"
  
  if [ $# -eq 0 ] || { [ "$1" = "gunicorn" ] && [ $# -eq 1 ]; }; then
    local workers="${WEB_CONCURRENCY:-2}"
    local host="${APP_HOST:-0.0.0.0}"
    local port="${APP_PORT:-8000}"
    log_info "Starting application server with ${workers} worker(s) on ${host}:${port}"
    set -- gunicorn app.main:app \
      --worker-class uvicorn.workers.UvicornWorker \
      --workers "${workers}" \
      --bind "${host}:${port}"
  else
    log_info "Starting application server with custom command: $*"
  fi
  
  exec "$@"
}

# Run main function with all script arguments
main "$@"
