FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM caddy:2.10-alpine

COPY infra/deploy/prod/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend-build /frontend/dist /srv
