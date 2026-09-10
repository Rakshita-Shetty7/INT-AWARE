# syntax=docker/dockerfile:1

# --- Build stage: compile the React/Vite SPA ---
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies from the lockfile for reproducible builds
COPY package.json package-lock.json ./
RUN npm ci

# Build the production bundle
COPY . .
RUN npm run build

# --- Serve stage: static files behind nginx with API/WS reverse proxy ---
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
