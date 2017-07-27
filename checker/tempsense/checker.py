# coding=utf-8
import random
import socket
import time

from .secure import *
from .choiceConstants import REGISTRATION, QUERY, SUBMISSION, SUPPORT
from .datatypes import DataEntry

from ctf_gameserver.checker import BaseChecker, OK, TIMEOUT, NOTWORKING, NOTFOUND


test_dict = {}


class TSRegisteringException(Exception):
    pass


class TSFlagNotFoundException(Exception):
    pass


class TSFlagNotDecryptedException(Exception):
    pass


class TSQueryNotWorkingException(Exception):
    pass


class TSSubmissionNotWorkingException(Exception):
    pass

class TSSupportNotWorkingException(Exception):
    pass


class TempSenseChecker(BaseChecker):
    def __init__(self, tick, team, service, ip):
        super().__init__(tick, team, service, ip)

        self.intros = ['Bots stole my flag! It looked like this: ',
                       'Have you seen the helpdesk supervisor? He is a master of disguise. Even in broad daylight he is impossible to be found! He something written on his back, something like ',
                       'Time to go mobile. The plate number of my car is ',
                       'Don\'t get into cars with strangers. Especially if their plate number is ',
                       'Our bots work part time at tinder and grindr. Or did you think those were real women? They always use the same password though, it\'s ',
                       'If you need to stock up on fiber eat strawberries. Strawberries are full of fiber.',
                       'Ironic! You can save other peoples flags but not your own. Here\'s mine: ']

        self.room_map = {
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

        self.sock = None
        self.host = self._ip
        self.port = 65533

        self.room_nr = None
        self.room = None
        self.mock_id = None

        self.buffer_size = 4096
        self.encoding = 'utf-8'

        self.registered = False

    """
    ##################
       MAIN METHODS
    ##################
    """

    def place_flag(self):
        # check connectivity
        try:
            self.connect()
            self.logger.info("[+] TS: Connectivity working place flag!")

            # register and pass flag to service
            self.register()
            self.logger.info("[+] TS: Registration during place flag worked!")
            self.pass_flag()
            self.logger.info("[+] TS: Passing a flag to the service works!")
            return OK
        except TSRegisteringException:
            return NOTWORKING
        except TSSubmissionNotWorkingException:
            return NOTWORKING
        except socket.timeout as e:
            self.logger.exception("timeout")
            raise e
        except IndexError:
            return NOTWORKING
        finally:
            self.close()

    def check_flag(self, tick):
        orig_flag = self.get_flag(tick)

        try:
            # check connectivity
            self.connect()
            self.logger.info("[+] TS: Connectivity working check flag!")

            list_id_keys_roomnr = self.load_data(tick)
            #self.logger.info("[+] TS: Loaded following list_id_keys_roomnr %s!", list_id_keys_roomnr)
            recovered_flag = self.query_flag(list_id_keys_roomnr)
            self.logger.info("[+] TS: Retrieving a flag from the service worked!")

            if recovered_flag is not None and recovered_flag.rstrip('\n') == orig_flag.rstrip('\n'):
                self.logger.info("[+] TS: Original flag and retrieved flag are the same string!")
                return OK
            else:
                self.logger.info("[-] TS: Retrieved flag did not match the original flag! orig was %s, retrieved was %s!", orig_flag, recovered_flag)
                return NOTFOUND
        except TSFlagNotFoundException:
            self.logger.exception('[-] TS: Flag was not found!')
            return NOTFOUND
        except TSFlagNotDecryptedException:
            self.logger.exception('[-] TS: Flag decryption failed!')
            return NOTWORKING
        except TSQueryNotWorkingException:
            self.logger.exception('[-] TS: Query failed!')
            return NOTWORKING
        except socket.timeout as e:
            self.logger.exception("timeout")
            raise e
        except IndexError:
            return NOTWORKING
        finally:
            self.close()

    def check_service(self):
        # check connectivity
        try:
            self.connect()
            self.logger.info("[+] TS: Connectivity working check service!")

            choice = random.choice(
                [self.check_registration, self.check_submission, self.check_query, self.check_support])
            # choice = self.check_support
            self.logger.info("[+] TS: Chose the following check: %s", choice.__name__)
            choice()
            self.logger.info("[+] TS: %s check working!", choice.__name__)

            return OK
        except TSRegisteringException:
            self.logger.exception("[-] TS: Registration check NOT working!")
            return NOTWORKING
        except TSSubmissionNotWorkingException:
            self.logger.exception("[-] TS: Submission check NOT working!")
            return NOTWORKING
        except TSQueryNotWorkingException:
            self.logger.exception("[-] TS: Query check NOT working!")
            return NOTWORKING
        except TSSupportNotWorkingException:
            self.logger.exception("[-] TS: Support check NOT working!")
            return NOTWORKING
        except socket.timeout as e:
            self.logger.exception("timeout")
            raise e
        except IndexError:
            return NOTWORKING
        finally:
            self.close()

    """
    ####################
       HELPER METHODS
    ####################
    """

    ### GENERAL HELPER ###

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.receive_til_menu()

    def close(self):
        assert isinstance(self.sock, socket.socket)
        # self.sock.shutdown(socket.SHUT_RDWR)
        self.registered = False
        self.sock.close()
        self.sock = None
        self.logger.debug("closed connection")

    def generate_room_data(self):
        self.room_nr = str(random.randint(1, 10))
        self.room = [room for room in self.room_map.keys() if self.room_map[room] == self.room_nr][0]

    def generate_data_entry_object(self):
        data_entry = DataEntry()
        data_entry.vinit(self.mock_id, self.room, str(random.randint(-10, 36)),
                         self.get_flag(self.tick))
        return data_entry

    def transmit(self, text):
        self.logger.debug("sending %s", repr(text))
        if isinstance(text, bytes):
            self.sock.sendall(text)
        else:
            self.sock.sendall(bytes(text, self.encoding))

    def receive_til_menu(self, expect_str="\n\n>"):
        data = ""
        while not data.endswith(expect_str):
            packet = self.receive()
            if not packet:
                return data
            data += packet
        return data
    def receive(self):
        data = self.sock.recv(self.buffer_size)
        self.logger.debug("received %s", repr(data))
        return data.decode(self.encoding)

    def store_data(self, sensor_id, priv, pub, room_nr):
        self.store_yaml(str(self.tick), [sensor_id, priv, pub, room_nr])
        #test_dict[str(self.tick)] = [sensor_id, priv, pub, room_nr]

    def load_data(self, tick):
        list_id_keys_roomnr = self.retrieve_yaml(str(tick))  # test_dict[str(tick)]
        if list_id_keys_roomnr is None:
            raise TSFlagNotFoundException('yaml was None!')
        return list_id_keys_roomnr

    ### HELPER PLACE FLAG ###

    def register(self, save_values=True):
        if self.registered:
            raise TSRegisteringException('Already registered!')

        self.generate_room_data()

        self.transmit(REGISTRATION)
        data = self.receive_til_menu()

        self.transmit('{}\n'.format(self.room_nr))
        # private key generation is super slow:
        try:
            data = self.receive_til_menu("PrivKey:")
        except socket.timeout:
            try:
                data = self.receive_til_menu("PrivKey:")
            except socket.timeout:
                data = self.receive_til_menu("PrivKey:")

        data = data.split('\n', maxsplit=2)
        sensor_id = data[0].lstrip('ID: ')
        pub = data[1].strip('PubKey: \n').rstrip('Provide ID for Priv')
        self.transmit(sensor_id)
        data = self.receive_til_menu().split('\n', maxsplit=1)
        priv = data[1].split("\n\n")[0]
        if save_values:
            self.store_data(sensor_id, priv, pub, self.room_nr)
        self.mock_id = sensor_id
        self.registered = True

    def pass_flag(self):
        if not self.registered:
            raise TSRegisteringException('Not registered yet!')

        data_entry = self.generate_data_entry_object()

        self.transmit(SUBMISSION)
        self.receive_til_menu("base64 encoded.\n")
        a = base64.b64encode(bytes(data_entry.export(), self.encoding))
        self.transmit(a)
        response = self.receive_til_menu()
        if 'Your data has been received and will be processed soon' not in response:
            raise TSSubmissionNotWorkingException('There was an error handling the passed data. {}'.format(response))

    ### HELPER CHECK FLAG ###

    def query_flag(self, list_id_keys):
        time.sleep(3)
        self.transmit(QUERY)
        data = self.receive_til_menu()
        if 'room' in data:
            self.transmit(list_id_keys[3])
            data = self.receive_til_menu()
            if 'No current data available' in data:
                raise TSFlagNotFoundException('Service did not have any data available! Probably deleted during service reset.')
            else:
                data = data.split('\n')
                for line in data:
                    if list_id_keys[0] in line:
                        enc_flag = line.split('\t', 1)[1].rstrip('\n')
                        if enc_flag.startswith('FAUST'):
                            self.logger.info('[*] TS: enc_flag was not encrypted, the team seems to have problems with their encryption routines or decided to gift flags to anyone!')
                            return enc_flag
                        self.logger.info('[*] TS: Got the following enc_flag: %s', enc_flag)
                        try:
                            plain = decrypt(list_id_keys[1], enc_flag)
                            if plain.startswith('FAUST'):
                                self.logger.info('[*] TS: Team uses standard RSA encryption with NO PADDING! enc_flag: %s; plain: %s', enc_flag, plain)
                                return plain
                            else:
                                raise Exception("[-] TS: decrypted flag was off {}".format(plain)) # TODO
                        except Exception:
                            self.logger.exception(
                                '[*] TS: Standard RSA encryption with NO PADDING raised exception')
                            try:
                                plain = dec_pkcs1_oaep(list_id_keys[1], enc_flag)
                                if plain.startswith('FAUST'):
                                    self.logger.info(
                                        '[*] TS: Team uses RSA PKCS1 OAEP encryption! enc_flag: %s; plain: %s', enc_flag, plain)
                                    return plain
                                else:
                                    raise Exception("[-] TS: decrypted flag was off {}".format(plain)) # TODO
                            except Exception:
                                self.logger.exception('[*] TS: RSA OAEP encryption raised exception')
                                try:
                                    plain = dec_pkcs1_1_5(list_id_keys[1], enc_flag)
                                    if plain.startswith('FAUST'):
                                        self.logger.info(
                                            '[*] TS: Team uses RSA PKCS1 v1.5 encryption! enc_flag: %s; plain: %s', enc_flag, plain)
                                        return plain
                                    else:
                                        raise Exception("[-] TS: decrypted flag was off {}".format(plain)) # TODO
                                except Exception:
                                    self.logger.exception(
                                        '[*] TS: Standard RSA PKCS v1.5 encryption raised exception')
                                    self.logger.info('[-] TS: Key was %s and cypther text was %s. Could not decrypt!', list_id_keys[1], enc_flag)
                                    raise TSFlagNotDecryptedException('The encryption scheme used by the Service is not supported. Supported are only: 1. Plain RSA w/o padding; 2. RSA PKCS1 v1.5; 3. RSA PKCS1 OAEP;!')
                return None
        else:
            raise TSQueryNotWorkingException('Querying for a room did not work! Service is broken!')

    ### HELPER CHECK SERVICE ###

    def check_registration(self):
        self.register(save_values=False)
        # try registering again
        self.transmit(REGISTRATION)
        data = self.receive_til_menu()
        if 'Your name is' not in data:
            self.logger.info('[-] TS: Second registration test failed!')
            raise TSRegisteringException('Second registration was possible! {}'.format(data))

    def check_submission(self):
        if not self.registered:
            self.register(save_values=False)

        self.transmit(SUBMISSION)
        self.receive_til_menu("base64 encoded.\n")

        if not self.registered:
            raise TSRegisteringException('Already registered!')

        self.generate_room_data()
        data_entry = self.generate_data_entry_object()
        a = base64.b64encode(bytes(data_entry.export(), self.encoding))
        self.transmit(a)
        response = self.receive_til_menu("\n")
        if 'Your data has been received and will be processed soon' in response:
            pass
        else:
            raise TSSubmissionNotWorkingException()

    def check_query(self):
        self.transmit(QUERY)
        data = self.receive_til_menu()
        if 'room' in data:
            self.transmit(str(random.randint(1, 10)) + '\n')
            data = self.receive_til_menu()
            if 'No current data available' not in data and ':' not in data:
                self.logger.warn("got unexpected data %s", repr(data))
                raise TSQueryNotWorkingException()
        else:
            raise TSQueryNotWorkingException()

    def check_support(self):
        self.transmit(SUPPORT)

        # crippled version:
        # if 'connected' in data:
        #     pass
        # else:
        #     raise Exception()

        # non crippled version:
        data = self.receive_til_menu("connected:\n")
        self.logger.info(data)
        self.logger.info('[*] TS: transmitting bad word')
        self.transmit('fuck you\n')
        data = self.receive_til_menu()
        self.logger.info("response: %s", data)
        if 'fancy' not in data:
            raise TSSupportNotWorkingException()
