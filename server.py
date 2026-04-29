import socket
import json
import sys
from utils import calcular_checksum


def main():
    if len(sys.argv) != 3:
        print("Uso correto: python src/server.py <IP> <PORTA>")
        sys.exit(1)

    IP = sys.argv[1]
    PORT = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP, PORT))

    print(f"Servidor escutando em {IP}:{PORT}")

    buffer_mensagens = {}
    cliente_ativo = None
    modo_operacao = None
    seq_esperado = 0

    while True:
        data, addr = sock.recvfrom(1024)
        mensagem = json.loads(data.decode('utf-8'))

        if mensagem.get("tipo") == "HANDSHAKE":
            print(f"\nHandshake recebido de {addr}")
            print(f"Modo: {mensagem.get('modo')}")
            print(f"Tam_max: {mensagem.get('tam_max')}")

            cliente_ativo = addr
            buffer_mensagens = {}
            
            modo_operacao = mensagem.get("modo")
            seq_esperado = 0
            
            resposta = {
                "tipo": "HANDSHAKE_ACK",
                "janela_inicial": 5,
                "status": "ACEITO"
            }

            sock.sendto(json.dumps(resposta).encode('utf-8'), addr)
            print("Resposta enviada.")

        elif mensagem.get("tipo") == "DATA":
            seq_num = mensagem.get('seq_num')
            payload = mensagem.get('payload')
            checksum = mensagem.get('checksum')

            print(f"\nRecebido pacote DATA #{seq_num}, payload: '{payload}'")

        if calcular_checksum(payload) != checksum:
            print(f"[ERRO] Checksum inválido no pacote #{seq_num}")
            continue
        
        if modo_operacao == "Go-Back-N":
            if seq_num == seq_esperado:
                buffer_mensagens[seq_num] = payload
                seq_esperado += 1

                ack = {
                    "tipo": "ACK",
                    "seq_num": seq_num
                }
            else:
                ack = {
                    "tipo": "ACK",
                    "seq_num": seq_esperado - 1
                }

        elif modo_operacao == "Repetição Seletiva":
            if seq_num not in buffer_mensagens:
                buffer_mensagens[seq_num] = payload

            ack = {
                "tipo": "ACK",
                "seq_num": seq_num
            }

            sock.sendto(json.dumps(ack).encode('utf-8'), addr)
            print(f"ACK enviado para o pacote #{seq_num}")

        elif mensagem.get("tipo") == "FIN":
            if buffer_mensagens:
                chaves_ordenadas = sorted(buffer_mensagens.keys())
                mensagem_completa = ''.join(buffer_mensagens[k] for k in chaves_ordenadas)
                print(f"\nMensagem completa recebida: '{mensagem_completa}'")
            
            buffer_mensagens = {}

if __name__ == "__main__":
    main()