# frontend/Dockerfile
FROM node:20-alpine
WORKDIR /src

# Install deps first (better layer caching)
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund || true

# Bring in source
COPY . .

EXPOSE 5173
# Bind to 0.0.0.0 so it’s reachable from host; port is fixed at 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]