"""
https://www.ida.liu.se/~TDTS06/labs/2014/NetNinny/default.html

TODO:
* parsing
    - handle only GET interactions
    - block requests for undesirable URLs and redirect to appropriate webpage
    - detect undesirable web content and redirect to appropriate webpage
* problems to resolve:
    - HTTP 1.0 and 1.1 support
    - HTTP data containing null characters
    - multithreading (instead of sequential listening in while loop)
    - connection: close / keep-alive
    - parsing should be case-insensitive to be compatible with popular browsers
    - GET requests look different with and without proxy
    - pages like WIKIPEDIA or YOUTUBE respond differently whith and without proxy
* extra features
    - look for forbidden keywords only in certain places (i.e. don't look at imagews)
    - extra extra: file upload using POST method
* in the end:
    - heavy testing with wireshark / tcpdump
"""
import socket
import sys  # for exit
import select
from Connect import Connect

HTTP_PORT = 80
HOST = ""  # default; any address
arbitrary_port = 9999  # default, should be changed on execution
MAX_CONNECTIONS = 200
BUFFER_SIZE = 4096
DEFAULT_FORWARD_HOST = "www.google.com"  # temporary


class MyProxy:

    inputs = []  # stores all the avaiable sockets
    channel = {}  # dictionary for associating endpoints: client-server

    def __init__(self, host, port):
        try:
            # creates an AF_INET (IPv4), STREAM socket (TCP)
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # socket configuration: 
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # bind address to newly created socket
            self.server.bind((host, port))
            # set up and start TCP listener
            self.server.listen(MAX_CONNECTIONS)
            print "Successfully created server, listening for connections..."
        except socket.error, msg:
            print "Failed to create socket! Error code: " + str(msg[0]) +
            ", Error message: " + msg[1]
            sys.exit(1)

    def main_loop(self):
        self.inputs.append(self.server)  # first available socket is server
        while 1:
            inputs_ready, outputs_ready, except_ready =
            select.select(self.inputs, [], [])
            # 
            for self.socket in inputs_ready:
                # each new connection will trigger accept on socket
                if self.socket == self.server:
                    self.trigger_accept()
                    break
                # if connection is not new, treat it as incoming data (no matter from which endpoint)
                self.data = self.socket.recv(BUFFER_SIZE)
                # if data is empty, then treat it as a close request
                if len(self.data) == 0:
                    self.trigger_close()
                # otherwise send incoming data to appropriate endpoint
                else:
                    self.trigger_recv()

    # creating a new connection with the server and accepting connection from client
    def trigger_accept(self):
        # start new connection with server
        connection = Connect().start(DEFAULT_FORWARD_HOST, HTTP_PORT)
        client_socket, client_addr = self.server.accept()
        if connection:
            print "New connection established with: ", client_addr
            # add client and server endpoints to inputs (they will be listened)
            self.inputs.append(client_socket)
            self.inputs.append(connection)
            # add endpoints to dictionary (to keep track of which client connects to which server)
            self.channel[client_socket] = connection
            self.channel[connection] = client_socket
        else:
            print "Cannot establish connection with remote server."
            print "Closing connection with client: ", client_addr
            client_socket.close()

    # disable and remove socket connection
    def trigger_close(self):
        print self.socket.getpeername(), " has disconnected"
        # remove endpoints from inputs (so they will not be listened)
        self.inputs.remove(self.socket)
        self.inputs.remove(self.channel[self.socket])
        out = self.channel[self.socket]
        # close both connections
        self.channel[out].close()
        self.channel[self.socket].close()
        # remove endpoints from dictionary (they will no longer be referenced)
        del self.channel[out]
        del self.channel[self.socket]

    # actual data processing (both ways)
    # data received from one endpoint is sent to another
    # no matter if client->server or server->client, because we keep track of them in a dictionary
    def trigger_recv(self):
        data = self.data
        # parsing goes here
        print data
        self.channel[self.socket].send(data)

# for calling class directly from terminal
if __name__ == "__main__":
    try:
        # user-defined port number
        arbitrary_port = int(raw_input("Arbitrary port for proxy server: "))
        # start proxy on that port
        myProxy = MyProxy(HOST, arbitrary_port)
    except ValueError, e:
        print arbitrary_port, " is not a valid integer!"
        sys.exit(1)

    try:
        myProxy.main_loop()
    except KeyboardInterrupt:
        print " ---> Caught SIGINT. Stopping server..."
        sys.exit(1)
