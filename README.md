# Esta aplicação é um servidor Flask que consome uma API externa e gera relatórios em formato CSV. A documentação interativa dos endpoints é gerada via Swagger.

## Rodando a Aplicação com Docker*

1. Certifique-se de que o [Docker](https://docs.docker.com/get-docker/) e o [Docker Compose](https://docs.docker.com/compose/install/) estão instalados em sua máquina.

2. No diretório raiz do projeto, execute o seguinte comando para construir a imagem e iniciar o contêiner:

```bash
docker-compose up --build
```

3. A aplicação estará disponível em [http://localhost:5000](http://localhost:5000).

## Documentação da API

A documentação interativa (Swagger UI) está disponível em:

[http://localhost:5000/apidocs](http://localhost:5000/apidocs)
