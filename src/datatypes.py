import json

"""
{
'Sensor'      : 'ID',
'Roomname'    : 'Roomname',
'Temperature' : '0 C',
'Proof'       : 'Proof'
}
"""


class DataEntry(object):
    def __init__(self):
        self.sensor = None
        self.room = None
        self.temp = None
        self.proof = None

    def jinit(self, jsonobject):
        data = json.loads(str(jsonobject, encoding='ascii'))
        self.sensor = data['Sensor']
        self.room = data['Roomname'] # TODO: check consistency nr or name
        self.temp = data['Temperature']
        self.proof = data['Proof']

    def vinit(self, sensor, room, temp, proof):
        self.sensor = sensor
        self.room = room
        self.temp = temp
        self.proof = proof


    def export(self):
        try:
            return json.dumps({
                'Sensor': self.sensor,
                'Roomname': self.room,
                'Temperature': self.temp,
                'Proof': self.proof
            })
        except Exception as e:
            print(e.args)

    def cli_string(self):
        return ''.join('%s:%s - %s\t%s\n' % (self.room, self.sensor, self.temp, self.proof))

    """
         _    _.--.____.--._     _.--.____.--._
    ( )=.-":;:;:;;':;:;:;"-._=.-":;:;:;;':;:;:;"-\
     \\\:;:;:;:;:;;:;::;:;:;::;:;:;:;:;;:;::;:;:;:\
      \\\:;:;:;:;:;;:;:;:;:;:;:;:;:;:;:;;:;::;:;:;:\
       \\\:;::;:;:;:;:;::;:;:;::;:;:;:;:;;:;::;:;:;:\
        \\\FLG_{Z29vZCBsdWNrIGFuZCBoYXZlIGZ1bg==};:;:\
         \\\:;::;:;:;:;:;::;:;:;::;:;:;:;:;;:;::;:;:;:\
          \\\;;:;:_:--:_:_:--:_;:;:;:;:;:--:_:_:--:;:;:\
           \\\_.-"             "-.__.-"             "-._\
            \\
             \\
              \\
               \\
                \\
                 \\

    YOU HAVE BEEN VISITED BY THE FLAG OF FLAGS.
    MANY FLAGS AND LONG UPTIMES WILL COME TO YOU AND YOUR SERVICES BUT ONLY IF YOU POST
    'THANK YOU FLAG OF FLAGS' IN OUR IRC CHANNEL AND SUBMIT A FLAG SOON.
        """

    def verify_proof(self, proof):
        from secure import SuperSecretAlgorithm
        algo = SuperSecretAlgorithm()
        if proof == algo.digest(self.sensor):
            return True
        else:
            return False
