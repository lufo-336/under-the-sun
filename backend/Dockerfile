FROM node:22-alpine

WORKDIR /app
ENV NODE_ENV=production

# Prima solo le dipendenze: se cambia il codice ma non package.json,
# Docker riusa questo strato e la build è immediata.
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY src ./src
COPY scripts ./scripts

USER node
EXPOSE 3000
CMD ["node", "src/server.js"]
