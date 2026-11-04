"""Decrypt data.enc.json back to plain JSON (for the refresh's consistency check).

Usage: TODAY_PASS='...' python3 tools/decrypt.py data.enc.json out.json
"""
import base64, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT = base64.b64decode("OaGayBd3ylRhZIj9eEz2gw==")

env = json.load(open(sys.argv[1]))
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=200000).derive(os.environ["TODAY_PASS"].encode())
pt = AESGCM(key).decrypt(base64.b64decode(env["iv"]), base64.b64decode(env["ct"]), None)
open(sys.argv[2], "wb").write(pt)
print("decrypted", len(pt), "bytes")
