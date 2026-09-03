# `build` stage doubles as the local dev image (docker-compose targets it
# and overrides CMD with `npm run dev`) and as the base for the production
# build below. Railway builds this Dockerfile with no target override, so
# it gets the final `production` stage.
FROM node:20-slim AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# Vite inlines VITE_* vars at build time, not runtime — this has to be a
# build arg, set as a Railway build variable pointing at the backend
# service's public URL. See docs/DECISIONS.md #14 and README's Railway section.
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM node:20-slim AS production

WORKDIR /app
RUN npm install -g serve

COPY --from=build /app/dist ./dist

EXPOSE 3100

CMD ["sh", "-c", "serve -s dist -l ${PORT:-3100}"]
