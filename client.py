import socket
import json
import sys
import select, time
import os
from dotenv import load_dotenv
from utils import fragmentar_e_montar, calcular_checksum, criptografar_xor

def main():
    load_dotenv()

    if len(sys.argv) != 3:
        print("Uso correto: python client.py <IP> <PORTA>")
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
                mensagem_usuario = input("\nDigite a mensagem: ")

                if len(mensagem_usuario) > tam_max:
                    print("Erro: Mensagem muito grande.")
                    continue

                # Ajuste de segurança: usa a chave '42' se o .env não for encontrado
                chave = os.getenv("chave_privada") or "42"
                mensagem_usuario = criptografar_xor(mensagem_usuario, chave)

                lista_pdus = fragmentar_e_montar(mensagem_usuario)

                print(f"\n[FASE 1 OK] Foram gerados {len(lista_pdus)} pacotes:")

                for p in lista_pdus:
                    print(
                        f"  -> Pacote #{p['seq_num']} | "
                        f"Payload: '{p['payload']}' | "
                        f"Checksum: {p['checksum'][:10]}..."
                    )

                print("-" * 40)
                
                print("🛠️  [CONFIGURAÇÃO DE SIMULAÇÃO DE ERROS]")
                pkt_corromper = int(input("Qual número de pacote deseja CORROMPER? (Digite -1 para nenhum): "))
                pkt_perder = int(input("Qual número de pacote deseja PERDER/OMITIR? (Digite -1 para nenhum): "))
                print("-" * 40)

                base_janela = 0
                proximo_seq_num = 0
                total_pacotes = len(lista_pdus)

                timers = {}
                pacotes_ack_recebidos = set()

                while base_janela < total_pacotes:

                    tempo_atual = time.time()
                    limite_janela = min(base_janela + janela_atual, total_pacotes)

                    for i in range(base_janela, limite_janela):

                        if i == proximo_seq_num:
                            pacote = lista_pdus[i]
                            
                            pacote_enviar = pacote.copy()
                            deve_enviar = True

                            if i == pkt_corromper:
                                print(f"   💥 [SIMULAÇÃO] Forçando erro de Checksum no pacote #{i}!")
                                pacote_enviar["checksum"] = "checksum_totalmente_errado_via_simulacao"
                                pkt_corromper = -1

                            if i == pkt_perder:
                                print(f"   👻 [SIMULAÇÃO] Omitindo envio do pacote #{i} para simular perda em trânsito!")
                                deve_enviar = False
                                pkt_perder = -1

                            if deve_enviar:
                                sock.sendto(json.dumps(pacote_enviar).encode('utf-8'), (IP, PORT))
                                print(f"[>] Enviado pacote #{pacote_enviar['seq_num']}")
                            else:
                                print(f"[>] Pacote #{pacote_enviar['seq_num']} foi 'perdido' na simulação.")

                            timers[i] = time.time()
                            proximo_seq_num += 1

                        elif i < proximo_seq_num and i not in pacotes_ack_recebidos:

                            if (tempo_atual - timers.get(i, tempo_atual)) > 5.0:

                                if modo_escolhido == "Repetição Seletiva":
                                    print(
                                        f"    [TIMEOUT SR] Pacote avulso #{i} falhou. "
                                        f"Reenviando apenas o #{i}."
                                    )

                                    pacote = lista_pdus[i]
                                    sock.sendto(json.dumps(pacote).encode('utf-8'), (IP, PORT))
                                    timers[i] = time.time()

                                elif modo_escolhido == "Go-Back-N" and i == base_janela:
                                    print(
                                        f"    [TIMEOUT GBN] Base #{base_janela} falhou. "
                                        f"Retransmitindo janela inteira do começo."
                                    )

                                    proximo_seq_num = base_janela
                                    timers[base_janela] = time.time()
                                    break

                    pronto_para_ler, _, _ = select.select([sock], [], [], 0.1)

                    if pronto_para_ler:
                        data_ack, _ = sock.recvfrom(1024)
                        resposta_servidor = json.loads(data_ack.decode('utf-8'))

                        if resposta_servidor.get("tipo") == "ACK":
                            seq_ack = resposta_servidor.get("seq_num")

                            print(f"    [<] Recebido ACK para o pacote #{seq_ack}")

                            nova_janela = resposta_servidor.get("janela")

                            if nova_janela and nova_janela != janela_atual:
                                print(
                                    f"    [JANELA] Servidor ajustou janela: "
                                    f"{janela_atual} → {nova_janela}"
                                )
                                janela_atual = nova_janela

                            if modo_escolhido == "Go-Back-N":
                                if seq_ack >= base_janela:
                                    base_janela = seq_ack + 1

                            elif modo_escolhido == "Repetição Seletiva":
                                pacotes_ack_recebidos.add(seq_ack)

                                while base_janela in pacotes_ack_recebidos:
                                    base_janela += 1

                        elif resposta_servidor.get("tipo") == "NACK":
                            seq_nack = resposta_servidor.get("seq_num")

                            print(f"    [!] Recebido NACK para o pacote #{seq_nack}")

                            nova_janela = resposta_servidor.get("janela")

                            if nova_janela and nova_janela != janela_atual:
                                print(
                                    f"    [JANELA] Servidor ajustou janela: "
                                    f"{janela_atual} → {nova_janela}"
                                )
                                janela_atual = nova_janela

                            if seq_nack is not None and 0 <= seq_nack < total_pacotes:
                                pacote = lista_pdus[seq_nack]

                                sock.sendto(json.dumps(pacote).encode('utf-8'), (IP, PORT))

                                timers[seq_nack] = time.time()

                                print(
                                    f"    [RETRANSMISSÃO] Pacote #{seq_nack} "
                                    f"reenviado imediatamente por causa do NACK."
                                )

                                if modo_escolhido == "Go-Back-N":
                                    proximo_seq_num = seq_nack + 1

                            else:
                                print(f"    [ERRO] NACK recebido com seq_num inválido: {seq_nack}")

                        else:
                            print(f"    [ERRO] Resposta desconhecida do servidor: {resposta_servidor}")

                fin_msg = {
                    "tipo": "FIN"
                }

                sock.sendto(json.dumps(fin_msg).encode('utf-8'), (IP, PORT))

                print("Mensagem finalizada (FIN enviado).")

    except socket.timeout:
        print("TIMEOUT no handshake")

if __name__ == "__main__":
    main()