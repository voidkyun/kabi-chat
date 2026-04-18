FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
# Run install scripts in the foreground to avoid esbuild ETXTBSY failures
# observed on some Docker/overlayfs hosts during `npm ci`.
RUN npm ci --foreground-scripts

COPY frontend/ ./
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM caddy:2.10-alpine

COPY infra/deploy/prod/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend-build /frontend/dist /srv
