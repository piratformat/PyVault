import base64
import os
import pickle
import random
import string

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

VALID_PASSWORD_TYPES = ('alpha',
                        'alphanum',
                        'alphanumspecial',
                        'mobilealpha',
                        'mobilealphanum',
                        'mobilealphanumspecial')

class Vault():
    def __init__(self, password=None, data_file=None):
        self.password = password
        self.key = None
        if data_file:
            self.load_file(data_file)
        else:
            self.data = {'salt': os.urandom(16),
                         'iterations': 1000000,
                         'vault': []}

    def load_data(self, data):
        self.data = pickle.loads(data)

    def save_data(self):
        return pickle.dumps(self.data)
    
    def load_file(self, fh):
        self.data = pickle.load(fh)

    def save_file(self, fh):
        pickle.dump(self.data, fh)
        
    def lock(self, password=None):
        if password:
            self.password = password
            self.key = None
        data = pickle.dumps(self.data['vault'])
        key = self.key or self.create_key(self.data['salt'],
                                          self.data.get('iterations', 1000000))
        self.data['vault'] = Fernet(key).encrypt(data)

    def unlock(self, password=None):
        if password:
            self.password = password
            self.key = None
        key = self.key or self.create_key(self.data['salt'],
                                          self.data.get('iterations', 1000000))
        try:
            self.data['vault'] = pickle.loads(Fernet(key).decrypt(self.data['vault']))
        except InvalidToken:
            self.data['vault'] = []
        
    def create_key(self, salt, iterations=1000000):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
            )
        return base64.urlsafe_b64encode(
            kdf.derive(bytearray(self.password, 'utf-8')))

    def get_objects(self):
        return self.data['vault']

    def set_objects(self, objs):
        self.data['vault'] = objs
    
    def add(self, obj):
        self.data['vault'].append(obj)

    def remove_password(self, obj):
        self.data['vault'].remove(obj)
        
def generate_password(password_type='alpha', n=10):
    alphabets = {'alpha': (string.ascii_letters, 'isupper', 'islower'),
                 'alphanum': (string.ascii_letters + string.digits, 'isupper', 'islower','isdigit'),
                 'alphanumspecial': (string.ascii_letters + string.digits + '!"#¤%&/()=?', 'isupper', 'islower','isdigit'),
                 'mobilealpha': (string.ascii_lowercase, 'islower'),
                 'mobilealphanum': (string.ascii_lowercase, 'islower'),
                 'mobilealphanumspecial': (string.ascii_lowercase, 'islower'),}
    if not password_type in alphabets:
        raise KeyError(f'Password type has to be one of the following: {", ".join(alphabets.keys())} it is "{password_type}".')
    while True:
        alphabet = alphabets[password_type][0]
        password = random.choices(alphabet, k=n)
        if password_type.startswith('mobile'):
            password[0] = password[0].upper()
        if 'mobilealphanum' in password_type :
            password[-2] = random.choice(string.digits)
        if password_type == 'mobilealphanumspecial':
            password[-1] = random.choice('!"#¤%&/()=?')
            
        for test in alphabets[password_type][1:]:
            if not [c for c in password if getattr(c, test)()]:
                break
        else:
            if password_type == 'alphanumspecial':
                if not [c for c in password if not c.isalpha()]:
                    continue
            break
    return ''.join(password)