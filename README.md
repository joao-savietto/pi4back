# 🚀 Projeto de Coleta de Dados IoT

Este projeto é uma API RESTful desenvolvida com FastAPI e Tortoise ORM que permite a coleta de medições de temperatura e umidade provenientes de dispositivos IoT (ESP32). Os dados são armazenados em um banco de dados MySQL para posterior análise e visualização em um dashboard.

## 💡 Funcionalidades Principais
- 📊 Coleta e armazenamento de medições de temperatura e umidade
- 🔐 Autenticação segura com JWT (JSON Web Tokens)
- 🔄 Sistema completo de refresh tokens
- 📱 Integração com dispositivos ESP32 via HTTP
- 🛢️ Armazenamento persistente em MySQL usando Tortoise ORM
- 🌐 API RESTful completa para acesso aos dados

## 📁 Estrutura do Projeto
```
pi4/
├── main.py                 # Ponto de entrada da aplicação FastAPI
├── routes/                 # Rotas da API (endpoints)
│   ├── auth.py             # Rotas de autenticação
│   ├── measurements.py     # Rotas para medições
│   └── users.py           # Rotas para usuários
├── models/                 # Modelos de dados para o banco de dados
│   ├── measurements.py     # Modelo de medições
│   └── users.py           # Modelo de usuários
├── auth/                   # Componentes de autenticação
│   ├── utils.py           # Utilitários JWT e hashing
│   └── dependencies.py    # Dependências de autenticação
└── utils/                  # Funções utilitárias
```

## ⚙️ Instalação e Execução

### 🐳 Com Docker Compose (Recomendado)
```bash
# Clone o repositório
git clone <seu-repositorio>
cd <nome-do-projeto>

# Crie o arquivo de ambiente com base no exemplo
cp .env_example .env

# Edite o .env para configurar suas credenciais
# Execute com Docker Compose
docker-compose up --build
```

### 🖥️ Execução Local (Modo Desenvolvimento)
```bash
# 1. Criar virtualenv
python -m venv .venv

# 2. Ativar virtualenv
source .venv/bin/activate  # Linux/MacOS
# ou
venv\Scripts\activate      # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente (copie .env_example para .env)
cp .env_example .env

# 5. Executar o projeto no modo local
uvicorn pi4.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🛠️ Configuração de Ambiente

O projeto utiliza variáveis de ambiente configuradas no arquivo `.env`. Veja as principais configurações:

```bash
# Configurações do MySQL
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=pi3back
MYSQL_USER=user
MYSQL_PASSWORD=password

# Configurações do Admin Padrão
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=password123

# Configurações de Segurança JWT
SECRET_KEY=seu-secret-key-aqui  # Altere esta chave em produção!
```

## 📡 Endpoints da API

### 🔐 Autenticação
- `POST /auth/login` - Login e obtenção de tokens
- `GET /auth/me` - Obtenção de informações do usuário logado
- `POST /auth/refresh` - Obtenção de novo access token com refresh token

### 📊 Medições
- `POST /measurements` - Criação de nova medição
- `GET /measurements` - Listagem das medições
- `GET /measurements/{id}` - Detalhes de uma medição específica

### 👤 Usuários
- `POST /users` - Criação de novo usuário
- `GET /users` - Listagem dos usuários
- `GET /users/{id}` - Detalhes de um usuário específico

## 🤖 Integração com ESP32

O projeto inclui uma biblioteca cliente para ESP32 que facilita a comunicação com a API:

### Exemplo de uso no ESP32:
```cpp
#include "ESP32SensorAPI.h"

void setup() {
    // Configuração do WiFi e inicialização da biblioteca
    sensor.initWiFi("SSID", "SENHA");
    sensor.begin();
}

void loop() {
    // Leitura dos sensores
    float temperatura = readTemperature();
    float umidade = readHumidity();
    
    // Envio para a API
    if (sensor.sendMeasurement(temperatura, umidade)) {
        Serial.println("Dados enviados com sucesso!");
    }
    
    delay(60000);  // Envia dados a cada minuto
}
```

## 🔧 Desenvolvimento

### Estrutura de Desenvolvimento
- **Backend**: FastAPI + Tortoise ORM
- **Banco de Dados**: MySQL
- **Autenticação**: JWT (HS256)
- **Cliente ESP32**: C++ com biblioteca personalizada

### Comandos úteis para desenvolvimento:
```bash
# Rodar testes
python -m pytest tests/

# Verificar linting
flake8 .

# Formatar código
black .
isort .

# Build Docker image
docker build -t pi4-api .
```

## 📋 Requisitos do Sistema

- Python 3.8+
- MySQL 5.7+
- Docker e Docker Compose (opcional, mas recomendado)
- ESP32 com módulo WiFi

## 🔒 Segurança

O sistema utiliza tokens JWT para autenticação:
- **Access Token**: Expira em 30 minutos
- **Refresh Token**: Expira em 7 dias
- **Hash de senhas**: Usando bcrypt

Para produção, certifique-se de configurar uma chave secreta segura no `.env`.

## 📖 Licença

Este projeto é licenciado sob a MIT License - veja o arquivo LICENSE para mais detalhes.
