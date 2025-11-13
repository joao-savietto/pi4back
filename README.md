# 🔬 Projeto Integrador 4 da Univesp (Universidade Virtual do Estado de São Paulo)
🚀 Um dashboard moderno para monitorar dados de sensores, como temperatura e umidade, com autenticação segura e visualizações em tempo real.

Este projeto é uma API RESTful desenvolvida com FastAPI e Tortoise ORM que permite a coleta de medições de temperatura e umidade provenientes de dispositivos IoT (ESP32). Os dados são armazenados em um banco de dados MySQL para posterior análise e visualização em um dashboard. O sistema inclui um avançado mecanismo de detecção de anomalias usando aprendizado de máquina.

## 💡 Funcionalidades Principais
- 📊 Coleta e armazenamento de medições de temperatura e umidade
- 🔐 Autenticação segura com JWT (JSON Web Tokens)
- 🔄 Sistema completo de refresh tokens
- 📱 Integração com dispositivos ESP32 via HTTP
- 🛢️ Armazenamento persistente em MySQL usando Tortoise ORM
- 🌐 API RESTful completa para acesso aos dados
- 🔍 **Detecção de Anomalias com Machine Learning** - Modelo LSTM Autoencoder treinado para identificar padrões anômalos nos sensores
- ⚙️ Migracões automáticas do banco de dados via Aerich
- 🐳 Configurações de deploy otimizadas (LocalDockerfile e docker-compose.yml)

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
    // Leitura dos sensores (substitua por código real)
    float temperatura = readTemperature();
    float umidade = readHumidity();
    
    // Envio para a API
    if (sensor.sendMeasurement(temperatura, umidade)) {
        Serial.println("Dados enviados com sucesso!");
    }
    
    delay(60000);  // Envia dados a cada minuto
}
```

### Configuração do ESP32:
1. Substitua os valores em `ESP32SensorExample.ino`:
   - `ssid` e `password`: Suas credenciais de WiFi
   - `serverUrl`: Endereço IP do servidor (ex: http://192.168.1.100:8000)
   - `username` e `password`: Credenciais do admin do sistema

## 🌟 Recursos Avançados

### 🔍 Detecção de Anomalias com Machine Learning
Este projeto implementa um sistema avançado de detecção de anomalias usando uma rede neural LSTM Autoencoder treinada em dados históricos dos sensores.

#### Funcionalidades:
- Modelo treinado com 72 passos temporais (6 horas)
- Cálculo automático do limiar de erro de reconstrução
- Métricas de desempenho detalhadas no console

#### Como usar:
```bash
# Treinar um novo modelo (ou reutilizar o existente)
python model_training/train_anomaly_detector.py
```

O script irá:
1. Buscar medições históricas da API
2. Preprocessar dados com MinMaxScaler
3. Treinar o modelo LSTM Autoencoder com early stopping
4. Salvar o modelo em `anomaly_detector_model.keras`
5. Calcular o limiar ótimo de erro de reconstrução

### ⚙️ Gerenciamento Automático do Banco de Dados
O sistema utiliza Aerich para gerenciar migrações automáticas do banco de dados:

```bash
# Aplicar migrações (executado automaticamente ao iniciar o serviço)
python -m aerich migrate
```

### 📦 Deploy Otimizado
Dois tipos de configuração disponíveis:
1. **Local Development**: `docker-compose.yml` com volume mounting para hot-reloading
2. **Production Build**: `LocalDockerfile` para imagens otimizadas

## 🧪 Desenvolvimento

### Estrutura de Desenvolvimento
- **Backend**: FastAPI + Tortoise ORM
- **Banco de Dados**: MySQL
- **Autenticação**: JWT (HS256)
- **Cliente ESP32**: C++ com biblioteca personalizada
- **Análise Predictiva**: LSTM Autoencoder com TensorFlow

### Comandos úteis para desenvolvimento:
```bash
# Rodar testes
python -m pytest tests/

# Verificar linting
flake8 .

# Formatar código
black .
isort .

# Treinar modelo de detecção de anomalias
python model_training/train_anomaly_detector.py

# Executar migracões do banco de dados
python -m aerich migrate
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

✅ Desenvolvido como parte do Projeto Integrador 4 da Univesp (Universidade Virtual do Estado de São Paulo)

🎓 Em parceria com a equipe acadêmica para aplicar conhecimentos em desenvolvimento full-stack e IoT.
