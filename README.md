# Projeto-Redes

Projeto simples de comunicação UDP entre cliente e servidor, com troca inicial de mensagens via handshake em JSON.

## Pré-requisitos

- Python 3.8+ instalado
- VS Code (recomendado para usar terminal dividido)

## Como executar

### 1) Abra o projeto no VS Code

Abra a pasta do projeto no VS Code e confirme que você está na raiz (onde está este README).

### 2) Use terminal dividido (recomendado)

Para visualizar servidor e cliente ao mesmo tempo:

1. Abra o terminal integrado: `Terminal > New Terminal`
2. Crie um split no terminal: botão **Split Terminal** (ou atalho `Ctrl+Shift+5`)
3. Deixe um terminal para o servidor e o outro para o cliente

Isso facilita acompanhar logs e respostas em tempo real.

### 3) Inicie o servidor

No primeiro terminal:

```bash
python src/server.py 127.0.0.1 5000
```

Saída esperada:

```text
Servidor escutando em 127.0.0.1:5000
```

### 4) Inicie o cliente

No segundo terminal:

```bash
python src/client.py 127.0.0.1 5000
```

O cliente vai pedir:

- Modo de operação:
	- `1` para Go-Back-N
	- `2` para Repetição Seletiva
- Tamanho máximo por envio (mínimo 30)

Se tudo ocorrer bem, o cliente recebe `HANDSHAKE_ACK` e mostra status de conexão.

## Exemplo de fluxo rápido

1. Inicie o servidor.
2. Inicie o cliente apontando para o mesmo IP e porta.
3. Escolha o modo de operação no cliente.
4. Informe o tamanho máximo.
5. Verifique no terminal do servidor o recebimento do handshake e no cliente a confirmação da conexão.

## Recurso de IA Utilizado

Foi utilizado o Gemini como apoio em duas frentes:

- Estruturação e refinamento das instruções de uso no README.
- Ideação inicial da troca de mensagens entre cliente e servidor, com recomendação do uso de JSON.
