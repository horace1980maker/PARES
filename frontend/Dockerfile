# Build Stage
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Inyectar variable de entorno durante el build
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production Stage
FROM nginx:alpine

# Copiar configuración de nginx (la crearemos más adelante, o usaremos la default pero necesitamos soporte SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
