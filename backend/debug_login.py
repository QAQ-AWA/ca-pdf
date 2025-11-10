#!/usr/bin/env python3
"""Debug script to test login endpoint."""

import asyncio
import os
from httpx import AsyncClient

# Set up environment
os.environ.setdefault("APP_NAME", "Test API")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_app.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "2")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_MINUTES", "10")
os.environ.setdefault("BACKEND_CORS_ORIGINS", '["http://testclient"]')
os.environ.setdefault("AUTH_RATE_LIMIT_REQUESTS", "5")
os.environ.setdefault("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass123!")
os.environ.setdefault("ADMIN_ROLE", "admin")
os.environ.setdefault("ENCRYPTED_STORAGE_ALGORITHM", "fernet")
os.environ.setdefault("ENCRYPTED_STORAGE_MASTER_KEY", "L9oZbBY7bRHt9aCJloPAV9ooa-QKdfYU0uf5KIKGJ28=")

from app.main import create_application

async def main():
    app = create_application()
    
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # Try with query parameter
        response = await client.post(
            "/api/v1/auth/login?request=test",
            json={"email": "admin@example.com", "password": "AdminPass123!"},
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {response.text}")
        
        if response.status_code == 422:
            print("\nTrying without query parameter...")
            response2 = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "AdminPass123!"},
            )
            print(f"Status: {response2.status_code}")
            print(f"Content: {response2.text}")

if __name__ == "__main__":
    asyncio.run(main())