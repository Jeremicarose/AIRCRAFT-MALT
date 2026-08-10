FROM node:22.23.1-alpine3.24@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NODE_ENV=production

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
