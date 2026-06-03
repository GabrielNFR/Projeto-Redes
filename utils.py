def calcular_checksum(payload):
    soma = sum(ord(c) for c in payload)
    return str((~soma) & 0xFF)

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


def criptografar_xor(mensagem,chave_privada):
    chave_privada=int(chave_privada)    
    return "".join(chr(ord(c)^chave_privada) for c in mensagem)