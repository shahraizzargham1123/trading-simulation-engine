# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app

# These get baked into the bundle, so they need to be set at build time.
ARG VITE_API_BASE=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000/ws
ENV VITE_API_BASE=${VITE_API_BASE} \
    VITE_WS_URL=${VITE_WS_URL}

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# --- serve stage ---
FROM nginx:1.27-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
