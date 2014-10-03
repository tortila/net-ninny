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
MAX_CONNECTIONS = 1000
DEFAULT_URL = "https://www.google.se/?gfe_rd=cr&ei=OqUoVMbVKYmr8weTrILABA&gws_rd=ssl"
BUFFER_SIZE = 16384
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

    def contains_keywords(self, string):
        if any(s in string.lower() for s in self.reader.keywords):
            return True
        else:
            return False

    def serve_connection(self, connection, client_addr):
        # receive a request from client
        data = connection.recv(BUFFER_SIZE)
        first_line = data.split("\n")[0]
        # in case some requests were not caught
        url = DEFAULT_URL
        webserver = self.parse_url_to_webserver(url)
        badUrl = False
        # serve GET requests only
        if "GET" in first_line:
            # remember url
            url = first_line.split(" ")[1]
            webserver = self.parse_url_to_webserver(url)
            self.print_info("request", first_line, client_addr)
            # check if url contains forbidden keywords
            badUrl = self.contains_keywords(first_line)
            if badUrl:
                self.print_info("blacklisted", first_line, client_addr)

        web_url = ""
        hostname = ""
        # remember hostname and web_url of GET request
        for line in data.split("\n"):
            if "GET" in line:
                web_url = line.split(" ")[1]
            if "Host" in line:
                hostname = line.split(" ")[1]

        # if requested url contains forbidden keywords,
        # replace url and host in get request
        if badUrl:
            data = self.get_request(BAD_URL_HOST)
            print data
        # if requested for file other than on specified list, check its content later
        content_check_needed = self.check_for_content(web_url)

        # establish connection and send GET request
        try:
            served_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            served_socket.connect((webserver, HTTP_PORT))
            # send request
            served_socket.send(data)
            badContent = False
            # receive chunk of response from web server
            while 1:
                new_chunk = served_socket.recv(BUFFER_SIZE)
                if len(new_chunk) > 0:
                    # if needed, check for content
                    if content_check_needed:
                        for line in new_chunk.split("\n"):
                            badContent = self.contains_keywords(line)
                            if badContent:
                                print "\nBAD CONTENT DETECTED\n"
                                # send new get request
                                served_socket.send(self.get_request(BAD_CONTENT_HOST))
                                break  # break for-loop
                    if not badContent:
                        connection.send(new_chunk)
                else:
                    break  # break, because 0-length data was sent = close connection
            served_socket.close()
        except socket.error, (value, message):
            self.print_info("Peer reset", first_line, client_addr)

        finally:
            connection.close()
            print "Connection closed.\nThread exiting..."
            thread.exit()

    def bad_content_response(self):
        return "HTTP/1.1 302 Found\r\nLocation: http://www.ida.liu.se/~TDTS04/labs/2011/ass2/badtest1.html\r\nConnection: close\r\n\r\n"

    def get_request(self, url):
        return "GET " + url + " HTTP/1.1" + "\r\nHost:" + self.parse_url_to_webserver(url) + "\r\nConnection: close\r\n\r\n"

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

    def check_for_content(self, url):
        no_need_for_check = [".png", ".jpg", ".jpeg", ".js", ".cs", ".gif"]
        if any (url.endswith(suffix) for suffix in no_need_for_check):
            return False
        else:
            return True

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
