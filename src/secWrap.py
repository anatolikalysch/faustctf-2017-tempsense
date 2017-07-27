from subprocess import check_output

ENCODING = 'utf-8'

def generate_key_pair():
    output = check_output(['./secure', '-g']).decode(ENCODING)
    public_key = output.split('-----END PUBLIC KEY-----')[0] + '-----END PUBLIC KEY-----'
    private_key = output.split('-----END PUBLIC KEY-----')[1].lstrip('\n')
    return private_key, public_key


def encrypt(key, file):
    return check_output(['./secure -k "{}" -e "{}"'.format(key, file)], shell=True).decode(ENCODING)


def decrypt(key, file):
    return check_output(['./secure -k "{}" -d "{}"'.format(key, file)], shell=True).decode(ENCODING)
