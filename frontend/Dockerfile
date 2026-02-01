# frontend/Dockerfile

# --- Stage 1: Build the React App ---
FROM node:18-alpine as build
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
# We bake in the API URL for local docker usage
ENV VITE_API_BASE=http://localhost:8000
RUN npm run build

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine
# Copy build artifacts to Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]