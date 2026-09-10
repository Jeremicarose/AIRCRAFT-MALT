FROM node:22.23.1-alpine3.24@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS builder

WORKDIR /workspace/sdk/typescript
COPY sdk/typescript/package.json sdk/typescript/package-lock.json ./
RUN npm ci
COPY sdk/typescript/ ./
RUN npm run build

WORKDIR /workspace/reference/mlat/frontend
COPY reference/mlat/frontend/package.json reference/mlat/frontend/package-lock.json ./
RUN npm ci
COPY reference/mlat/frontend/ ./

ARG NEXT_PUBLIC_REGISTRY_CODE_HASH
ARG NEXT_PUBLIC_REGISTRY_CONTRACT_TX_HASH
ARG NEXT_PUBLIC_REGISTRY_CONTRACT_INDEX
ENV NEXT_PUBLIC_REGISTRY_CODE_HASH=$NEXT_PUBLIC_REGISTRY_CODE_HASH
ENV NEXT_PUBLIC_REGISTRY_CONTRACT_TX_HASH=$NEXT_PUBLIC_REGISTRY_CONTRACT_TX_HASH
ENV NEXT_PUBLIC_REGISTRY_CONTRACT_INDEX=$NEXT_PUBLIC_REGISTRY_CONTRACT_INDEX
ENV NODE_ENV=production
RUN npm run build

FROM node:22.23.1-alpine3.24@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS runner

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /workspace/reference/mlat/frontend/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /workspace/reference/mlat/frontend/.next/static ./reference/mlat/frontend/.next/static

USER nextjs
WORKDIR /app/reference/mlat/frontend
EXPOSE 3000

CMD ["node", "server.js"]
