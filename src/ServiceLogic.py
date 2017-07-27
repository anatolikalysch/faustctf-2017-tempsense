#!/usr/bin/env python3
# python imports
import random
import socket
import uuid
import base64
import os
import time
import zipfile
# specific imports
from BroBot import CTFBotBro
from JokerBot import CTFBotJoker
from LazyBot import CTFBotLazy
from SupervisorBot import CTFSupervisor
from datatypes import DataEntry
from tech_support import BadWordException
from queue import Queue
from threading import Thread
# own modules
import secWrap


# server values
IP = '0.0.0.0'
PORT = 65533
# thread env
THREADS = []
ENCODING = 'utf-8'
DATA_QUEUE = Queue()
REG_QUEUE = Queue()

# dirs
DATA_DIR = 'data/'
CONFIG_DIR = DATA_DIR + 'bot/'
REG_DIR = DATA_DIR + 'reg/'

# populate room mapping
room_map = {
    'Living room': '1',
    'Dining room': '2',
    'Sex dungeon': '3',
    'Flag room': '4',
    'Test room': '5',
    'Bed room': '6',
    'Computer room': '7',
    'Vestibule': '8',
    'Garage': '9',
    'Garden': '10'
}

TECH_SUPPORT_LOOP = [CTFBotBro, CTFBotBro, CTFBotBro, CTFBotBro, CTFBotBro, CTFBotLazy, CTFBotJoker]


class InvalidChoiceException(Exception):
    pass


def query_room_temp(room):
    with open(DATA_DIR + DATA_DIR + room_map[room], "r") as f:
        result = ''
        for line in f.readlines():
            try:
                addition = line.split('\t')
                room = addition[0].split(':')[0]
                ident = addition[0].split(':')[1].split(' - ')[0]
                cypher = secWrap.encrypt(get_pub_key(ident, room), addition[1])
                result += addition[0] + '\t' + cypher + '\n'
            except Exception as ex:
                result += line
        return result


def get_pub_key(ident, room):
    with open(REG_DIR + room + '/' + ident + '_pub.pem') as file:
        return file.read()

def get_priv_key(ident, room):
    with open(REG_DIR + room + '/' + ident + '_priv.pem') as file:
        return file.read()


class QueueWorker(Thread):
    def __init__(self):
        super().__init__()
        self.joined = False

    @staticmethod
    def append_values(value, file, directory):
        with open(directory + file, "a") as f:
            f.writelines(value)

    def run(self):
        while True:
            if not REG_QUEUE.empty():
                data = REG_QUEUE.get()
                self.append_values(data[2], '{}_priv.pem'.format(data[0]), REG_DIR + data[1] + '/')
                self.append_values(data[3], '{}_pub.pem'.format(data[0]), REG_DIR + data[1] + '/')

            elif not DATA_QUEUE.empty():
                data = DATA_QUEUE.get()
                line = data.cli_string()
                ident = line.split(':')[1].split(' - ')[0]
                room = line.split(':')[0]
                try:
                    self.append_values(line + get_pub_key(ident, room) + '\n\n', room_map[data.cli_string().split(':')[0]], DATA_DIR + DATA_DIR)
                    self.append_values(line, '9', CONFIG_DIR)
                except Exception as e:
                    pass

            else:
                if self.joined:
                    break
                else:
                    time.sleep(1)

    def join(self, timeout=None):
        self.joined = True


class Cleaner(Thread):
    def __init__(self):
        super().__init__()
        self.joined = False

    def run(self):
        while True:
            """
            Removes files from the passed in path that are older than an hour
            """
            time_in_secs = time.time() - (60 * 60)
            path = REG_DIR
            for root, dirs, files in os.walk(path, topdown=False):
                for file_ in files:
                    full_path = os.path.join(root, file_)
                    stat = os.stat(full_path)

                    if stat.st_mtime <= time_in_secs:
                        try:
                            if os.path.exists(full_path):
                                os.remove(full_path)
                        except OSError:
                            print("[*] TempSense: Unable to remove file: %s" % full_path)

            if self.joined:
                break
            else:
                time.sleep(60*15)

    def join(self, timeout=None):
        self.joined = True


class ClientThread(Thread):
    def __init__(self, socket):
        super().__init__()
        self.conn = socket
        self.buffer_size = 2048

        self.room = None
        self.registered = False
        self.id = socket.getpeername()[0]
        self.transgressions = 0
        print("[+] New server socket thread started for " + IP + ":" + str(PORT))

    def run(self):
        while True:
            try:
                self.transmit(
                    'Welcome to the Temperature Sensor Station! What would you like to do?\n[1] Register\n[2] Query room\n[3] Submit temperature\n[4] Help\n\n>')
                data = self.recieve()
                if data == b'1\n':
                    try:
                        if not self.registered:
                            self.register_loop()
                        else:
                            self.transmit('Your name is {}.\n'.format(self.id))

                    except InvalidChoiceException:
                        break
                elif data == b'2\n':
                    data = self.generate_room_names()
                    self.transmit('Which room to query?\n' + data)
                    while True:
                        data = self.recieve().decode(ENCODING).rstrip('\n')
                        for room, number in room_map.items():
                            if data == number:
                                try:
                                    self.transmit(query_room_temp(room))
                                except FileNotFoundError:
                                    self.transmit('No current data available!\n')
                        break

                elif data == b'3\n':
                    self.transmit('%s' % 'Pass the data base64 encoded.\n')
                    self.submit_loop()
                elif data == b'4\n':
                    if self.transgressions == 3:
                        self.help_loop(supervisor=True)
                    elif self.transgressions > 3:
                        self.transmit(
                            'It seems you have been banned. Abusers will not be tolerated. Have a nice day!\n')
                        break
                    else:
                        self.transmit(
                            'Unfortunately we are very short on manpower... So let our electronic members help you with your question.\nFor QA reasons your conversation will be recorded. You are now connected:\n')
                        self.help_loop()
                elif data == b'':
                    self.finalize_connection()
            except Exception as ex:
                self.finalize_connection()
                break

    def register_loop(self):
        self.transmit('What room are you in?\n')
        self.transmit(self.generate_room_names())
        data = self.recieve().decode(ENCODING).rstrip('\n')
        if data in room_map.values():
            self.room = [room for room in room_map.keys() if room_map[room] == data][0]
            self.id = uuid.uuid4()
            self.registered = True
            priv, pub = secWrap.generate_key_pair()
            self.transmit('ID: {}\n'.format(self.id))
            self.transmit('PubKey: \n{}\n'.format(pub))
            self.transmit('Provide ID for PrivKey:')
            data = self.recieve()
            if str(self.id) in data.decode(ENCODING):
                self.transmit('PrivKey: \n{}\n'.format(priv))
                self.transmit('End of register phase.\n')
                REG_QUEUE.put([self.id, self.room, priv, pub])
        else:
            raise InvalidChoiceException()

    def submit_loop(self):
        data = self.recieve()
        try:
            data = base64.b64decode(data.decode(encoding=ENCODING))
            de = DataEntry()
            de.jinit(data)
            DATA_QUEUE.put(de)
            self.transmit('Your data has been received and will be processed soon.\n')
        except TypeError as er:
            self.transmit('\nThere was an error decoding your data.\n')
        except Exception as jde:
            self.transmit('\nYour JSON file seems corrupted.\n')

    def help_loop(self, supervisor=False):
        if supervisor:
            self.support = CTFSupervisor()
        else:
            self.support = random.choice(TECH_SUPPORT_LOOP)()
        self.transmit('TS:' + self.support.process_sentence('Hi') + '\n>')
        while True:
            try:
                data = self.recieve()
                self.transmit('TS:' + self.support.process_sentence(str(data, encoding=ENCODING)) + '\n>')
            except BadWordException as e:
                self.transmit(
                    'TS: ' + 'I do not fancy that tone. Come back when you\'ve learned to speak in a more civilized manner.' + '\n>')
                self.transgressions += 1
                break

    def transmit(self, text):
        print(text)
        text = text
        if isinstance(text, bytes):
            self.conn.sendall(text)
        else:
            self.conn.sendall(bytes(text, ENCODING))

    def recieve(self):
        data = self.conn.recv(self.buffer_size)
        print(data.decode(ENCODING))
        return data

    def finalize_connection(self):
        try:
            self.transmit('\nToo bad. Closing connestion.\n')
            self.conn.close()
        except:
            try:
                self.conn.close()
            except:
                pass


    def generate_room_names(self):
        data = ''
        for room in room_map.keys():
            data += '[{}] {}\n'.format(room_map[room], room)
        data += '[11] Back\n\n>'
        return data


def serv_start():
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((IP, PORT))
    if not os.path.exists(DATA_DIR) and not os.path.exists(CONFIG_DIR):
        os.makedirs(DATA_DIR)
        os.makedirs(DATA_DIR + DATA_DIR)
        os.makedirs(REG_DIR)
        os.makedirs(CONFIG_DIR)
        for room in room_map.keys():
            os.makedirs(REG_DIR + room)
        with zipfile.ZipFile('bot_speech.zip', 'r') as zip_arch:
            zip_arch.extractall(CONFIG_DIR)
    if not os.path.exists('nltk_data'):
        with zipfile.ZipFile('nltk_data.zip', 'r') as zip_arch:
            zip_arch.extractall()

    qworker = QueueWorker()
    qworker.name = 'qWorker'
    qworker.start()

    cleaner = Cleaner()
    cleaner.name = 'Cleaner'
    cleaner.start()

    tcp_server.listen(50)
    while True:
        try:
            print("[*] TempSense: Waiting for connections from TCP clients...")
            sock, addr = tcp_server.accept()
            newthread = ClientThread(sock)
            newthread.start()
            THREADS.append(newthread)
        except:
            for thread in THREADS:
                thread.finalize_connection()
                thread.join(timeout=10)
            break


if __name__ == "__main__":
    serv_start()
