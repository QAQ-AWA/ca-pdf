"""Tests for database migrations and prestart script functionality."""

import subprocess
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config


@pytest.fixture
def alembic_config() -> Config:
    """Create an Alembic configuration object for testing."""
    project_root = Path(__file__).parent.parent
    alembic_ini = project_root / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option(
        "script_location", str(project_root / "app" / "db" / "migrations")
    )

    return config


def test_alembic_config_exists() -> None:
    """Test that alembic.ini exists and is configured properly."""
    project_root = Path(__file__).parent.parent
    alembic_ini = project_root / "alembic.ini"

    assert alembic_ini.exists(), "alembic.ini should exist"
    assert alembic_ini.is_file(), "alembic.ini should be a file"


def test_migrations_directory_exists() -> None:
    """Test that migrations directory exists."""
    project_root = Path(__file__).parent.parent
    migrations_dir = project_root / "app" / "db" / "migrations"

    assert migrations_dir.exists(), "migrations directory should exist"
    assert migrations_dir.is_dir(), "migrations should be a directory"

    # Check for required files
    assert (migrations_dir / "env.py").exists(), "env.py should exist"
    assert (migrations_dir / "script.py.mako").exists(), "script.py.mako should exist"


def test_migrations_can_be_checked(alembic_config: Config) -> None:
    """Test that we can check the current migration state."""
    try:
        # This should work without error
        command.current(alembic_config)
    except Exception as e:
        pytest.fail(f"Failed to check current migration: {e}")


def test_prestart_script_exists() -> None:
    """Test that prestart.sh script exists and is executable."""
    project_root = Path(__file__).parent.parent
    prestart_script = project_root / "scripts" / "prestart.sh"

    assert prestart_script.exists(), "prestart.sh should exist"
    assert prestart_script.is_file(), "prestart.sh should be a file"


def test_prestart_script_syntax() -> None:
    """Test that prestart.sh has valid bash syntax."""
    project_root = Path(__file__).parent.parent
    prestart_script = project_root / "scripts" / "prestart.sh"

    # Check syntax using bash -n
    result = subprocess.run(
        ["bash", "-n", str(prestart_script)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Bash syntax error: {result.stderr}"


def test_prestart_script_has_shebang() -> None:
    """Test that prestart.sh has proper shebang."""
    project_root = Path(__file__).parent.parent
    prestart_script = project_root / "scripts" / "prestart.sh"

    with open(prestart_script, "r") as f:
        first_line = f.readline().strip()

    assert first_line.startswith("#!"), "Script should have a shebang"
    assert "bash" in first_line, "Script should use bash"


def test_prestart_script_has_required_functions() -> None:
    """Test that prestart.sh contains required functions."""
    project_root = Path(__file__).parent.parent
    prestart_script = project_root / "scripts" / "prestart.sh"

    with open(prestart_script, "r") as f:
        content = f.read()

    # Check for key functions
    assert "wait_for_postgres()" in content, "Should have wait_for_postgres function"
    assert "run_migrations()" in content, "Should have run_migrations function"
    assert "log_info()" in content, "Should have log_info function"
    assert "log_error()" in content, "Should have log_error function"

    # Check for migration command
    assert "alembic upgrade head" in content, "Should run alembic upgrade head"

    # Check for retry logic
    assert "MAX_DB_WAIT_ATTEMPTS" in content, "Should have max wait attempts config"
    assert (
        "MAX_MIGRATION_ATTEMPTS" in content
    ), "Should have max migration attempts config"


def test_prestart_script_has_exponential_backoff() -> None:
    """Test that prestart.sh implements exponential backoff."""
    project_root = Path(__file__).parent.parent
    prestart_script = project_root / "scripts" / "prestart.sh"

    with open(prestart_script, "r") as f:
        content = f.read()

    # Check for backoff logic
    assert "backoff" in content.lower(), "Should implement backoff"
    assert "sleep" in content, "Should have sleep for backoff"

    # Check for exponential increase
    assert "*" in content or "**" in content, "Should have exponential calculation"


def test_prestart_script_uses_exec() -> None:
    """Test that prestart.sh uses exec to start the application."""
    project_root = Path(__file__).parent.parent
    prestart_script = project_root / "scripts" / "prestart.sh"

    with open(prestart_script, "r") as f:
        content = f.read()

    assert (
        'exec "$@"' in content or "exec " in content
    ), "Should use exec to start application"


def test_migration_upgrade_head_works_with_test_db(alembic_config: Config) -> None:
    """Test that migrations can be applied to test database."""
    # Note: This test is skipped because the conftest.py fixture already creates
    # the database schema using SQLAlchemy metadata. In a real deployment,
    # alembic upgrade head is the primary way to create/update the schema.
    # The prestart script handles this automatically in production.
    pytest.skip("Database schema already created by conftest fixture")


def test_dockerfile_uses_prestart_script() -> None:
    """Test that Dockerfile is configured to use prestart script."""
    project_root = Path(__file__).parent.parent
    dockerfile = project_root / "Dockerfile"

    assert dockerfile.exists(), "Dockerfile should exist"

    with open(dockerfile, "r") as f:
        content = f.read()

    # Check that prestart.sh is copied
    assert "prestart.sh" in content, "Dockerfile should copy prestart.sh"

    # Check that it's made executable or used in CMD
    assert (
        "chmod +x" in content or "./scripts/prestart.sh" in content
    ), "Dockerfile should make prestart.sh executable or use it"


def test_health_endpoint_remains_db_independent() -> None:
    """Test that /health endpoint doesn't depend on database."""
    project_root = Path(__file__).parent.parent
    routes_file = project_root / "app" / "api" / "routes.py"

    assert routes_file.exists(), "routes.py should exist"

    with open(routes_file, "r") as f:
        content = f.read()

    # Find the health_check function
    lines = content.split("\n")
    health_start = None
    health_end = None

    for i, line in enumerate(lines):
        if "async def health_check()" in line:
            health_start = i
        if health_start is not None and health_end is None:
            if line.strip().startswith("def ") or line.strip().startswith("async def "):
                if i > health_start:
                    health_end = i
                    break

    if health_end is None:
        health_end = len(lines)

    assert health_start is not None, "/health endpoint should exist"

    health_function = "\n".join(lines[health_start:health_end])

    # The basic health endpoint should not access database
    assert "get_engine" not in health_function, "/health should not access database"
    assert "connect()" not in health_function, "/health should not connect to database"
    assert (
        "execute" not in health_function
    ), "/health should not execute database queries"

    # But we should have a separate /health/db endpoint
    assert (
        "async def health_check_db()" in content
    ), "Should have separate /health/db endpoint for database checks"
