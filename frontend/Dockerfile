# Build the React app, then serve the static files with nginx.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
# Not `npm ci`: package-lock.json was generated on Windows and omits the
# Linux-only optional deps of Vite's native bundler (@emnapi/*), so ci
# refuses to run. `npm install` keeps the locked versions and fills those in.
RUN npm install --no-audit --no-fund
COPY . .
# nginx (below) proxies /api to the backend, so the browser talks to one
# origin: no CORS, and no hard-coded backend host baked into the bundle.
ENV VITE_API_URL=/api
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
