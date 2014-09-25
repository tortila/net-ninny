import socket

# establishing connection between proxy and actual server
class Connect:

    def __init__(self):
        # create new socker (TCP, IPv4)
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            # establish connection
            self.connection.connect((host, port))
            return self.connection
        except Exception, e:
            print e
            return False
