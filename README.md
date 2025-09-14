# Projeto de Coleta de Dados IoT

Este projeto é uma API RESTful desenvolvida com FastAPI e Tortoise ORM que permite a coleta de medições de temperatura e umidade provenientes de dispositivos IoT (ESP32). Os dados são armazenados em um banco de dados MySQL para posterior análise e visualização em um dashboard.

## Funcionalidades Principais
- Recebimento de dados de sensores via HTTP POST requests
- Armazenamento persistente dos dados coletados
- API RESTful para acesso aos dados coletados
- Integração com banco de dados MySQL usando Tortoise ORM

## Estrutura do Projeto
```
pi3/
├── main.py          # Ponto de entrada da aplicação FastAPI
├── routes/          # Rotas da API (endpoints)
├── models/          # Modelos de dados para o banco de dados
└── utils/           # Funções utilitárias
```

## Executando o projeto

<p>Para executar o projeto, siga os seguintes passos:</p>

## 1. Criar virtualenv
```bash
python -m venv .venv
```

## 2. Ativar virtualenv
```bash 
source .venv/bin/activate
```

## 3. Instalar dependências
```bash
pip install -r requirements.txt
```

## 4. Executar o projeto no modo local
```bash
uvicorn pi3.main:app --host 0.0.0.0 --port 8000 --reload
```
