import hashlib
import uuid

class PasswordHasher:
    @staticmethod
    def hash_password(password):
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
        return hashed_password

    @staticmethod
    def verify_password(stored_password, provided_password):
        hashed_password, salt = stored_password.split(':')
        return hashed_password == hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()
