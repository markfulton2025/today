"""Encrypt the Today page data for GitHub Pages.

Usage: TODAY_PASS='...' python3 tools/encrypt.py data.json data.enc.json
AES-256-GCM, key from PBKDF2-SHA256 (200k iterations) with the fixed salt
below. index.html uses the same salt, so changing it logs out every device.
"""
import base64, json, os, sys, time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT = base64.b64decode("OaGayBd3ylRhZIj9eEz2gw==")

def main(src, dst):
    pw = os.environ.get("TODAY_PASS")
    if not pw:
        sys.exit("TODAY_PASS is not set")
    raw = open(src, "rb").read()
    json.loads(raw)  # must be valid JSON
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=200000).derive(pw.encode())
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, raw, None)
    env = {"v": 1, "stamp": time.strftime("%Y%m%d%H%M%S"), "iv": base64.b64encode(iv).decode(), "ct": base64.b64encode(ct).decode()}
    with open(dst, "w") as f:
        json.dump(env, f, separators=(",", ":"))
    print("encrypted", len(raw), "bytes ->", dst)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
