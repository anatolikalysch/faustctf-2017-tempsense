#!/usr/bin/env python3

import base64
import getopt
import sys

from Crypto import Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Cipher import PKCS1_OAEP

ENCODING = 'utf-8'


def usage():
    print('')
    print("Options: ")
    print('-k --key=     - the key you want to use in .pem format')
    print("-e --encrypt - encrypt file with given key")
    print("-d --decrypt - decrypt file with given key")
    print("-g --generate - generate key pair")
    print("-p --prepare= - prepare string for transmission")
    print("-r --recover= - recover string after recieving transmission")
    print(" ")
    print(" ")
    print("Copyright SecureBits - Trust is everything. All rights reserved 1997.\nThis software is provided as is and with no warranty whatsoever.\nYou should not assume this to work as you expect it to.\nMaybe it was coded by monkeys. Who knows?\n")
    sys.exit(0)


def generate_key_pair():
    new_key = RSA.generate(1024, e=3)
    public_key = new_key.publickey().exportKey("PEM")
    print(public_key.decode(ENCODING))
    private_key = new_key.exportKey("PEM")
    print(private_key.decode(ENCODING))
    # return private_key, public_key
    return 0


'''
Attention: this function performs the plain, primitive RSA encryption (textbook).
In real applications, you always need to use proper cryptographic padding, and you should not directly encrypt data with this method.
Failure to do so may lead to security vulnerabilities.
It is recommended to use modules Crypto.Cipher.PKCS1_OAEP or Crypto.Cipher.PKCS1_v1_5 instead.
'''


def encrypt(key, file):
    rsa_key = RSA.importKey(key)
    print(prepare_transmission(rsa_key.encrypt(file.encode(ENCODING), 9)[0], simple=True))
    return 0

'''
Better: This is PKCS1_v1_5.
'''


def enc_pkcs1_1_5(key, file):
    # file = file.encode(ENCODING)
    # rsa_key = RSA.importKey(key)
    # rsa_key = PKCS1_v1_5.new(rsa_key)
    # h = SHA.new(file)
    # print(prepare_transmission(rsa_key.encrypt(file + h.digest()), simple=True))
    print('To be implemented. By you that is. Or just use plain text. We don\'t judge.')
    return 0


'''
Better: This is PKCS1_OAEP.
'''


def enc_pkcs1_oaep(key, file):
    # rsa_key = RSA.importKey(key)
    # rsa_key = PKCS1_OAEP.new(rsa_key)
    # crypt = rsa_key.encrypt(file.encode(ENCODING))
    # print(prepare_transmission(crypt, simple=True))
    print('To be implemented. Wait eagerly for our next version.')
    return 0


'''
Attention: this function performs the plain, primitive RSA decryption (textbook).
For decryption this does not matter that much. Just some some interfaces I am offering.
'''
def decrypt(key, file):
    rsa_key = RSA.importKey(key)
    print(rsa_key.decrypt(recover_transmission(file, simple=True)).decode(ENCODING).rstrip('\n'))
    return 0


def dec_pkcs1_1_5(key, file):
    flag_size = 38
    rsa_key = RSA.importKey(key)
    rsa_key = PKCS1_v1_5.new(rsa_key)
    dsize = SHA.digest_size
    sentinel = Random.new().read(flag_size + dsize)
    message = rsa_key.decrypt(recover_transmission(file, simple=True), sentinel=sentinel)

    digest = SHA.new(message[:-dsize]).digest()
    if digest == message[-dsize:]:
        print(message[:-dsize].decode(ENCODING))
        return 0
    else:
        print('Could not decrypt!! Digest mismatch! Message was {}; Digest local: {}; Digest decrypted: {};'.format(message[:-dsize], digest, message[-dsize:]))
        return 1


def dec_pkcs1_oaep(key, file):
    rsa_key = RSA.importKey(key)
    rsa_key = PKCS1_OAEP.new(rsa_key)
    print(rsa_key.decrypt(recover_transmission(file, simple=True)).decode(ENCODING).rstrip('\n'))
    return 0



def prepare_transmission(string, simple=False):
    if not simple:
        return (base64.standard_b64encode(string.encode()) + reverse(str(base64.standard_b64encode(string.encode())))[
                                                             1:-2].encode()).decode(ENCODING)
    else:
        return base64.standard_b64encode(string).decode(ENCODING)

    return 0


def recover_transmission(string, simple=False):
    if not simple:
        return base64.standard_b64decode(string[:(len(string) // 2)].encode(ENCODING))
    else:
        return base64.standard_b64decode(string)


def reverse(text):
    if len(text) <= 1:
        return text
    return reverse(text[1:]) + text[0]


def main():
    if not len(sys.argv[1:]):
        usage()

    enc = False
    dec = False
    key = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hk:edgp:r:",
                                   ["help", "encrypt", "decrypt", "key=", "generate", "prepare=", "recover="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-e", "--encrypt"):
            enc = True
            dec = False
        elif o in ("-d", "--decrypt"):
            enc = False
            dec = True
        elif o in ("-k", "--key"):
            key = a
        elif o in ("-g", "--generate"):
            generate_key_pair()
        elif o in ("-p", "--prepare"):
            prepare_transmission(a)
        elif o in ("-r", "--recover"):
            recover_transmission(a)
        else:
            assert False, "Unhandled Option"

    if enc and not dec and key is not None:
        encrypt(key, sys.argv[-1])

    elif dec and not enc and key is not None:
        decrypt(key, sys.argv[-1])


if __name__ == "__main__":
    main()
