import socket
import json
import sys
from utils import calcular_checksum,criptografar_xor
import os  
from dotenv import load_dotenv


def main():
    load_dotenv()
    if len(sys.argv) != 3:
        print("Uso correto: python server.py <IP> <PORTA>")
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
    janela_atual = 5

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
                "janela_inicial": janela_atual,
                "status": "ACEITO"
            }

            sock.sendto(json.dumps(resposta).encode('utf-8'), addr)
            print("Resposta enviada.")

        elif mensagem.get("tipo") == "DATA":
            seq_num = mensagem.get('seq_num')
            payload = mensagem.get('payload')
            checksum = mensagem.get('checksum')

            bytes_payload = len(payload.encode('utf-8'))
            checksum_calculado = calcular_checksum(payload)

            if checksum_calculado != checksum:
                print(f"\nRecebido pacote DATA #{seq_num} | Payload: '{payload}' | Bytes: {bytes_payload}")
                print(f"Checksum recebido: {checksum} | Checksum calculado: {checksum_calculado} → Status: CORROMPIDO")

                janela_atual = max(1, janela_atual - 1)
                print(f"[JANELA] Reduzida para {janela_atual}")

                nack = {
                    "tipo": "NACK",
                    "seq_num": seq_num,
                    "janela": janela_atual,
                    "checksum": calcular_checksum(f"NACK{seq_num}")
                }

                sock.sendto(json.dumps(nack).encode('utf-8'), addr)
                print(f"NACK enviado para o pacote #{seq_num}")

                continue

            print(f"\nRecebido pacote DATA #{seq_num} | Payload: '{payload}' | Bytes: {bytes_payload} | Checksum: {checksum} | Status: OK")
            
            if modo_operacao == "Go-Back-N":
                if seq_num == seq_esperado:
                    buffer_mensagens[seq_num] = payload
                    seq_esperado += 1

                    ack = {
                        "tipo": "ACK",
                        "seq_num": seq_num,
                        "janela": janela_atual
                    }

                    sock.sendto(json.dumps(ack).encode('utf-8'), addr)
                    print(f"ACK enviado para o pacote #{seq_num}")

                    janela_atual = min(5, janela_atual + 1)
                    print(f"[JANELA] Ajustada para {janela_atual}")
                else:
                    print(f"[GBN] Pacote #{seq_num} fora de ordem (esperado #{seq_esperado}). Descartado.")

            elif modo_operacao == "Repetição Seletiva":
                if seq_num not in buffer_mensagens:
                    buffer_mensagens[seq_num] = payload

                ack = {
                    "tipo": "ACK",
                    "seq_num": seq_num,
                    "janela": janela_atual
                }

                sock.sendto(json.dumps(ack).encode('utf-8'), addr)
                print(f"ACK enviado para o pacote #{seq_num}")

                janela_atual = min(5, janela_atual + 1)
                print(f"[JANELA] Ajustada para {janela_atual}")

        elif mensagem.get("tipo") == "FIN":
            if buffer_mensagens:
                chaves_ordenadas = sorted(buffer_mensagens.keys())
                mensagem_completa = ''.join(buffer_mensagens[k] for k in chaves_ordenadas)
                chave = os.getenv("chave_privada")
                mensagem_completa= criptografar_xor(mensagem_completa,chave)
                print(f"\nMensagem completa recebida: '{mensagem_completa}'")
            
            buffer_mensagens = {}

if __name__ == "__main__":
    main()