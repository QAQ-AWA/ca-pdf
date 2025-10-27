# syntax=docker/dockerfile:1.6

FROM node:20-alpine AS base
WORKDIR /app
ENV NODE_ENV=production

FROM base AS deps
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=secret,id=npm_token,required=false \
    sh -c 'set -e; \
        if [ -f /run/secrets/npm_token ]; then \
          echo "//registry.npmjs.org/:_authToken=$(cat /run/secrets/npm_token)" > ~/.npmrc; \
        fi; \
        npm ci; \
        rm -f ~/.npmrc'

FROM deps AS build
ARG VITE_API_BASE_URL
ARG VITE_APP_NAME
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_APP_NAME=${VITE_APP_NAME}
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
HEALTHCHECK --start-period=20s --interval=30s --timeout=5s --retries=3 CMD wget --spider -q http://localhost/healthz || exit 1
EXPOSE 80
