# syntax=docker/dockerfile:1.5

FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_APP_NAME="Monorepo UI"
ARG VITE_API_BASE_URL="http://localhost:8000"

RUN VITE_APP_NAME="$VITE_APP_NAME" \
    VITE_API_BASE_URL="$VITE_API_BASE_URL" \
    npm run build

FROM nginx:1.27-alpine

COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
