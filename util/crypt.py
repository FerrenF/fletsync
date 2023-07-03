import bcrypt

from config import SECRET_KEY


def fl_hash_password(stri, salt=16):
    encoded_string = stri.encode('utf8', errors='strict')
    return bcrypt.hashpw(encoded_string, bcrypt.gensalt(salt))

