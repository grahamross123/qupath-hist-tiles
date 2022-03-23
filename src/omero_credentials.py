import os
import rsa

def decrypt_credentials(pri_key_file, credentials_filename):
    with open(credentials_filename, 'rb') as cred_f, open(pri_key_file, 'rb') as key_file:
        keydata = key_file.read()
        pri_key = rsa.PrivateKey.load_pkcs1(keydata)
        cred = cred_f.read()
        dec_cred = rsa.decrypt(cred, pri_key).decode().split()
        usr = dec_cred[0]
        pwd = dec_cred[1]
    return usr, pwd

HOST = 'ssl://omero-prod.camp.thecrick.org'
PRI_KEY_FILE = os.path.expanduser('~/omero.pri.key')
CREDENTIALS_FILENAME = './src/.omero_credentials'
USERNAME, PASSWORD = decrypt_credentials(PRI_KEY_FILE, CREDENTIALS_FILENAME)
