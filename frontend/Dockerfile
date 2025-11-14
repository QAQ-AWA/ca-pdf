# syntax=docker/dockerfile:1.6

ARG NODE_VERSION=20.17.0
ARG NGINX_VERSION=1.27.2-alpine

FROM node:${NODE_VERSION} AS builder
WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --include=dev

ARG VITE_API_BASE_URL
ARG VITE_APP_NAME
ARG VITE_PUBLIC_BASE_URL
ENV NODE_ENV=production \
    VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_PUBLIC_BASE_URL=${VITE_PUBLIC_BASE_URL}

COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig.json ./
COPY frontend/tsconfig.node.json ./
RUN npm run build

FROM nginx:${NGINX_VERSION} AS runtime
ARG COMMIT_SHA="unknown"
ARG BUILD_VERSION="dev"
ENV NGINX_PORT=80 \
    COMMIT_SHA=${COMMIT_SHA} \
    BUILD_VERSION=${BUILD_VERSION}
LABEL org.opencontainers.image.title="frontend" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.revision="${COMMIT_SHA}"

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --start-period=30s --interval=30s --timeout=10s --retries=3 CMD wget --spider -q http://127.0.0.1/healthz || exit 1
