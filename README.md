# Projeto-Redes

Projeto de comunicação UDP entre cliente e servidor construído para simular um transporte confiável de dados na camada de aplicação. Implementa segmentação de mensagens (carga útil de 4 bytes), checksum próprio (soma ASCII mod 256 com complemento), criptografia simétrica XOR, reconhecimento negativo (NACK), simulação determinística de erros e perdas, e protocolos de janela deslizante com controle de janela variável (1-5) ditado pelo servidor (Go-Back-N e Repetição Seletiva).

## Pré-requisitos

- Python 3.8+ instalado
- VS Code (recomendado para usar terminal dividido)
- Instalar dependência:
  ```bash
  pip install python-dotenv
  ```

## Como executar

### 1) Abra o projeto no VS Code

Abra a pasta do projeto no VS Code e confirme que você está na raiz (onde está este README).

### 2) Configure a chave de criptografia

Crie um arquivo `.env` na raiz do projeto com o conteúdo:

```
chave_privada=42
```

Este arquivo contém a chave simétrica usada para cifrar/decifrar as mensagens via XOR. **Não versione este arquivo** (já está no `.gitignore`). O valor `42` pode ser qualquer número inteiro, desde que seja o mesmo no servidor e no cliente.

### 3) Use terminal dividido (recomendado)

Para visualizar servidor e cliente ao mesmo tempo:

1. Abra o terminal integrado: `Terminal > New Terminal`
2. Crie um split no terminal: botão **Split Terminal** (ou atalho `Ctrl+Shift+5`)
3. Deixe um terminal para o servidor e o outro para o cliente

Isso facilita acompanhar logs e respostas em tempo real.

### 4) Inicie o servidor

No primeiro terminal:

```bash
python server.py 127.0.0.1 5000
```

Saída esperada:

```text
Servidor escutando em 127.0.0.1:5000
```

### 5) Inicie o cliente

No segundo terminal:

```bash
python client.py 127.0.0.1 5000
```

O cliente vai pedir:

- Modo de operação:
	- `1` para Go-Back-N
	- `2` para Repetição Seletiva
- Tamanho máximo por envio (mínimo 30)

Se tudo ocorrer bem, o cliente recebe `HANDSHAKE_ACK` e mostra status de conexão.

### 6) Inicialização da Conexão

Após informar o modo e o tamanho máximo, o cliente iniciará a comunicação (Handshake).
Saída esperada no cliente:
```bash
Iniciado Handshake com o servidor 127.0.0.1:5000...
Conexão estabelecida com sucesso.
Servidor aceitou com janela: 5
Status: ACEITO
```
No servidor, você verá o registro das preferências escolhidas e a confirmação de recebimento.

### 7) Transmissão de Mensagens

O cliente ficará aguardando entrada de texto:
```bash
Digite uma mensagem:
```
Digite uma mensagem (obedecendo ao limite de caracteres escolhido no passo 5) e pressione Enter.

### 8) Simulação de Erros e Perdas

Após digitar a mensagem, o cliente exibirá a fragmentação e perguntará:
```bash
[CONFIGURAÇÃO DE SIMULAÇÃO DE ERROS]
Qual número de pacote deseja CORROMPER? (Digite -1 para nenhum):
Qual número de pacote deseja PERDER/OMITIR? (Digite -1 para nenhum):
```

- **Corromper:** Substitui o checksum do pacote escolhido por um valor inválido. O servidor detectará a falha de integridade e enviará um **NACK** (reconhecimento negativo).
- **Perder:** Omite completamente o envio do pacote escolhido. O temporizador (timeout de 5s) no cliente detectará a ausência de ACK e acionará a retransmissão.
- Use `-1` em ambos para uma transmissão sem erros simulados.

### 9) Acompanhamento da Transmissão (Terminais)

Após pressionar Enter, observe o comportamento simultâneo nos dois terminais:

**No terminal do cliente (sem erros):**
Você verá a mensagem sendo dividida em pequenos pacotes, o log de envio automático e a chegada das confirmações do servidor, até a finalização:
```bash
[FASE 1 OK] Foram gerados X pacotes:
  -> Pacote #0 | Payload: '...' | Checksum: ...
[>] Enviado pacote #0
[<] Recebido ACK para o pacote #0
Mensagem finalizada (FIN enviado).
```

**No terminal do cliente (com erros simulados):**
```bash
    [SIMULAÇÃO] Forçando erro de Checksum no pacote #2!
[>] Enviado pacote #2
    [!] Recebido NACK para o pacote #2
    [RETRANSMISSÃO] Pacote #2 reenviado imediatamente por causa do NACK.
```

**No terminal do servidor:**
Você verá os dados (payloads) chegando fragmentados de um em um. Se houver erro de checksum, o NACK será enviado e a janela reduzida. Após o recebimento de todos os lotes, o servidor decifra e exibe a mensagem original:
```bash
Recebido pacote DATA #0, payload: '...'
ACK enviado para o pacote #0

[ERRO] Checksum inválido no pacote #2
[JANELA] Reduzida para 4
NACK enviado para o pacote #2

Mensagem completa recebida: 'Sua mensagem original'
```


## Exemplo de fluxo rápido 

1. Inicie o servidor em um terminal: `python server.py 127.0.0.1 5000`
2. Inicie o cliente no outro terminal: `python client.py 127.0.0.1 5000`
3. No cliente, escolha o modo de operação (1 para Go-Back-N ou 2 para Repetição Seletiva).
4. Informe o tamanho máximo da mensagem (mínimo de 30).
5. O _Handshake_ será realizado e a janela inicial (5) informada.
6. Digite um texto no terminal do cliente.
7. O cliente irá exibir a fragmentação (pacotes de 4 caracteres cifrados com XOR contendo um número de sequência e checksum próprio).
8. Escolha se deseja simular erros (corromper checksum ou perder pacotes) ou siga sem erros (`-1`).
9. O cliente enviará os metadados e aguardará/receberá os ACKs ou NACKs correspondentes com base no limite da janela.
10. Ao receber um sinal `FIN`, o servidor decifra e imprime a mensagem original perfeitamente.

## Recurso de IA Utilizado

Foi utilizado o Gemini como apoio em duas frentes:

- Estruturação e refinamento das instruções de uso no README.
- Ideação inicial da troca de mensagens entre cliente e servidor, com recomendação do uso de JSON.
