import secrets

def generate_reference():
    return secrets.token_hex(8)