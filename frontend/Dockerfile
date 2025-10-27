# syntax=docker/dockerfile:1.6

ARG NODE_VERSION=20.17.0
ARG NGINX_VERSION=1.27.2-alpine

FROM node:${NODE_VERSION}-alpine AS builder
ENV NODE_ENV=production
WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=secret,id=npm_token,required=false \
    sh -c 'set -e; \
        if [ -f /run/secrets/npm_token ]; then \
          echo "//registry.npmjs.org/:_authToken=$(cat /run/secrets/npm_token)" > ~/.npmrc; \
        fi; \
        npm ci; \
        rm -f ~/.npmrc'

ARG VITE_API_BASE_URL
ARG VITE_APP_NAME
ARG VITE_PUBLIC_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_PUBLIC_BASE_URL=${VITE_PUBLIC_BASE_URL}

COPY frontend/ ./
RUN npm run build

FROM nginx:${NGINX_VERSION} AS runtime
ARG COMMIT_SHA="unknown"
ARG BUILD_VERSION="dev"
ENV NGINX_PORT=8080 \
    COMMIT_SHA=${COMMIT_SHA} \
    BUILD_VERSION=${BUILD_VERSION}
LABEL org.opencontainers.image.title="frontend" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.revision="${COMMIT_SHA}"

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --start-period=20s --interval=30s --timeout=5s --retries=3 CMD wget --spider -q http://127.0.0.1:8080/healthz || exit 1
