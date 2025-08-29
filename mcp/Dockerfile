FROM node:20-alpine
WORKDIR /src
COPY package.json package-lock.json* ./
RUN npm install --omit=dev --no-audit --no-fund || true
COPY . .
EXPOSE 9000
CMD ["node", "src/server.js"]