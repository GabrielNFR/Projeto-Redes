import hashlib

def calcular_checksum(payload):
    return hashlib.md5(payload.encode('utf-8')).hexdigest()

def fragmentar_e_montar(mensagem):
    pacotes = []
    seq_num = 0
    for i in range(0, len(mensagem), 4):
        payload = mensagem[i:i+4]
        pacote = {
            "tipo": "DATA",
            "seq_num": seq_num,
            "checksum": calcular_checksum(payload),
            "payload": payload
        }
        pacotes.append(pacote)
        seq_num += 1
    return pacotes