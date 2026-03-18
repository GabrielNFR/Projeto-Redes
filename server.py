import socket
import json
import sys

def main():
    if len(sys.argv) != 3:
        print("Uso correto: python src/server.py <IP> <PORTA>")
        sys.exit(1)
        
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP, PORT))
    
    print(f"Servidor escutando em {IP}:{PORT}")
    
    while True:
        data, addr = sock.recvfrom(1024)
        mensagem = json.loads(data.decode('utf-8'))
        
        if mensagem.get("tipo") == "HANDSHAKE":
            print(f"\nHandshake recebido de {addr}")
            print(f"Modo: {mensagem.get('modo')}")
            print(f"Tam_max: {mensagem.get('tam_max')}")
            
            resposta = {
                "tipo": "HANDSHAKE_ACK",
                "janela_inicial": 5,
                "status": "ACEITO"
            }
            
            sock.sendto(json.dumps(resposta).encode('utf-8'), addr)
            print("Resposta enviada.")
    
if __name__ == "__main__":
    main()