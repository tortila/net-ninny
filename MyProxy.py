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
import thread
from FileReader import FileReader

HTTP_PORT = 80
HOST = ""  # default; any address
arbitrary_port = 9999  # default, should be changed on execution
MAX_CONNECTIONS = 200
DEFAULT_URL = "https://www.google.se/?gfe_rd=cr&ei=OqUoVMbVKYmr8weTrILABA&gws_rd=ssl"
BUFFER_SIZE = 4096
BAD_URL_HOST = "http://www.ida.liu.se/~TDTS04/labs/2011/ass2/error1.html"
BAD_CONTENT_HOST = "http://www.ida.liu.se/~TDTS04/labs/2011/ass2/error2.html"


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
            print "Failed to create socket! Error code: ", str(msg[0]),", Error message: ", msg[1]
            sys.exit(1)

        # load forbidden keywords
        self.reader = FileReader("forbidden.txt")

    def main_loop(self):
        while 1:
            connection, client_addr = self.server.accept()
            thread.start_new_thread(self.serve_connection, (connection, client_addr))
        self.server.close()

    def print_info(self, type, request, address):
        print address[0], "\t", type.upper(), "\t", request

    def serve_connection(self, connection, client_addr):
        data = connection.recv(BUFFER_SIZE)
        first_line = data.split("\n")[0]
        # in case some requests were not caught
        url = DEFAULT_URL
        webserver = self.parse_url_to_webserver(url)
        badUrl = False
        if "GET" in first_line:
            url = first_line.split(" ")[1]
            webserver = self.parse_url_to_webserver(url)
            self.print_info("request", first_line, client_addr)
            if any (s in first_line for s in self.reader.keywords):
                self.print_info("blacklisted", first_line, client_addr)
                webserver = self.parse_url_to_webserver(BAD_URL_HOST)
                badUrl = True
        # requested url contains forbidden keywords
        # replace url and host in get request
        if(badUrl):
            for line in data.split("\n"):
                if "GET" in line:
                    weburl = line.split(" ")[1]
                    data = data.replace(weburl, BAD_URL_HOST)
                if "Host" in line:
                    hostname = line.split(" ")[1]
                    data = data.replace(hostname, self.parse_url_to_webserver(BAD_URL_HOST))
        try:
            served_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            served_socket.connect((webserver, HTTP_PORT))
            served_socket.send(data)
            badContent = False
            while 1:
                # receive data from web server
                data = served_socket.recv(BUFFER_SIZE)
                ###
                # parsing for forbidden content goes here
                ###
                if (len(data) > 0):
                    # send to browser
                    connection.send(data)
                else:
                    break
            served_socket.close()
        except socket.error, (value, message):
            self.print_info("Peer reset", first_line, client_addr)

        finally:
            connection.close()
            thread.exit()

    def parse_url_to_webserver(self, url):
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        return temp[:webserver_pos]


# for calling class directly from terminal
if __name__ == "__main__":
    try:
        # user-defined port number
        arbitrary_port = int(raw_input("Arbitrary port for proxy server: "))
    except ValueError, e:
        print "Provided value is not an integer. Starting server at default port: ", arbitrary_port
    finally:
        # start proxy on that port
        myProxy = MyProxy(HOST, arbitrary_port)

    try:
        print "Forbidden keywords:", myProxy.reader.keywords
        myProxy.main_loop()
    except KeyboardInterrupt:
        print " ---> Caught SIGINT. Stopping server..."
        sys.exit(1)
