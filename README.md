# Introdução
Este é um projeto FastAPI com Tortoise ORM e MySQL.

# Executando o projeto

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
