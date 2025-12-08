
FROM node:20-alpine AS build

WORKDIR /app

# Copia apenas ficheiros de dependências
COPY package*.json ./

# Instala dependências
RUN npm install
# Copia o resto do projeto
COPY . .


RUN chmod -R 755 /app/node_modules/.bin

# Faz o build de produção
RUN npm run build


FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
