from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os

SECRET_KEY = b"4QZd2uv1guhXNl4x6cnla/pFOLAeojjl"


def encrypt_password(password: str) -> str:
    """Encrypts a password using AES encryption."""
    iv = os.urandom(16)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(password.encode(), AES.block_size))
    return base64.b64encode(iv + encrypted).decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypts a password using AES decryption."""
    encrypted_data = base64.b64decode(encrypted_password)
    iv = encrypted_data[:16]
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted_data[16:]), AES.block_size)
    return decrypted.decode()
