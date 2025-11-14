# Archived Documentation

This directory contains documentation files that are no longer applicable to the current architecture but are preserved for historical reference.

## Traefik-Related Documentation (Archived November 2024)

The following files document the previous Traefik-based architecture that was used before the project migrated to a nginx-fronted design in November 2024:

- **TRAEFIK_FIX_README.md** - Documentation guide for Traefik routing configuration
- **TRAEFIK_FIX_NOTES.md** - Technical implementation details for Traefik fixes
- **TRAEFIK_HEALTH_CHECK_FIX.md** - Health check configuration for Traefik

### Why Archived?

In November 2024, ca-pdf underwent a major architectural refactor to simplify deployment:

- **Removed**: Traefik reverse proxy service (4th service container)
- **Simplified**: From 4-service to 3-service architecture (db, backend, frontend)
- **New Design**: Frontend nginx now acts as both static server and reverse proxy
- **Benefits**: Simplified configuration, no domain requirements, faster deployment

### Current Architecture

The current architecture uses:
- **3 services**: db, backend, frontend
- **nginx**: Frontend container on port 80 handles static assets and proxies `/api/*` to backend
- **Single network**: Default bridge network (no internal/edge separation)
- **Optional HTTPS**: Via cert/key file mounts to frontend

### Migration Information

For details on the architectural change, see:
- [CHANGES_SUMMARY.md](../../CHANGES_SUMMARY.md) - Complete refactor summary
- [CHANGELOG.md](../../CHANGELOG.md) - Version history entry
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Current architecture documentation
- [DEPLOYMENT.md](../../DEPLOYMENT.md) - Current deployment guide

---

**Archived Date**: 2024-11-14  
**Reason**: Architectural refactor to nginx-fronted design  
**Replacement**: Current documentation reflects 3-service nginx-based architecture
