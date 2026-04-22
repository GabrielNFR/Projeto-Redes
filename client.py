import socket
import json
import sys
from utils import fragmentar_e_montar, calcular_checksum

def main():
    if len(sys.argv) != 3:
        print("Uso correto: python src/client.py <IP> <PORTA>")
        sys.exit(1)

    IP = sys.argv[1]
    PORT = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)

    print("CONFIGURAÇÃO INICIAL")
    print("Escolha um modo de operação:")
    print("[1] Go-Back-N")
    print("[2] Repetição Seletiva")

    while True:
        modo = input("Escolha o modo (1 ou 2): ")
        if modo == "1":
            modo_escolhido = "Go-Back-N"
            break
        elif modo == "2":
            modo_escolhido = "Repetição Seletiva"
            break
        else:
            print("Opção inválida, escolha 1 ou 2.")

    tam_max = int(input("Digite o limite máximo de caracteres por envio (Mínimo de 30): "))
    if tam_max < 30:
        tam_max = 30

    handshake_msg = {
        "tipo": "HANDSHAKE",
        "modo": modo_escolhido,
        "tam_max": tam_max
    }

    print(f"Iniciado Handshake com o servidor {IP}:{PORT}...")
    sock.sendto(json.dumps(handshake_msg).encode('utf-8'), (IP, PORT))

    try:
        data, addr = sock.recvfrom(1024)
        resposta = json.loads(data.decode('utf-8'))

        if resposta.get("tipo") == "HANDSHAKE_ACK":
            janela_atual = resposta.get("janela_inicial")
            status = resposta.get("status")

            print("Conexão estabelecida com sucesso.")
            print(f"Servidor aceitou com janela: {janela_atual}")
            print(f"Status: {status}")

            while True:
                mensagem_usuario = input("Digite a mensagem: ")

                if len(mensagem_usuario) > tam_max:
                    print("Erro: Mensagem muito grande.")
                    continue

                lista_pdus = fragmentar_e_montar(mensagem_usuario)
                print(f"[FASE 1 OK] Lista gerada: {lista_pdus}")

                for pacote in lista_pdus:
                    try:
                        sock.sendto(json.dumps(pacote).encode('utf-8'), (IP, PORT))
                        print(f"Pacote de sequência #{pacote['seq_num']} enviado.")

                        data_ack, addr = sock.recvfrom(1024)
                        ack = json.loads(data_ack.decode('utf-8'))

                        if ack.get("tipo") == "ACK" and ack.get("seq_num") == pacote["seq_num"]:
                            print(f"Recebido ACK para o pacote de sequência #{pacote['seq_num']}")
                        else:
                            print(f"ACK inválido ou inesperado para o pacote #{pacote['seq_num']}")

                    except socket.timeout:
                        print(f"Timeout ao aguardar ACK do pacote #{pacote['seq_num']}")
                        break

                fin_msg = {
                    "tipo": "FIN"
                }
                sock.sendto(json.dumps(fin_msg).encode('utf-8'), (IP, PORT))
                print("Mensagem finalizada (FIN enviado).")

    except socket.timeout:
        print("TIMEOUT no handshake")

if __name__ == "__main__":
    main()