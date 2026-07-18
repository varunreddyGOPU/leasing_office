# Build context is the repo root (see docker-compose.yml) so the image can
# include packages/shared-types, which tsconfig paths reference.
FROM node:20-alpine

WORKDIR /repo/apps/web

COPY apps/web/package.json ./
RUN npm install

COPY packages /repo/packages
COPY apps/web ./

EXPOSE 3000
CMD ["npm", "run", "dev"]
