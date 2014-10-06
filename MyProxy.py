#!/usr/bin/env python
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
from Parser import Parser

HTTP_PORT = 80
HOST = ""  # default; any address
arbitrary_port = 9999  # default, should be changed on execution
MAX_CONNECTIONS = 1000
BUFFER_SIZE = 16384
DEFAULT_URL = "http://www.google.com"
BAD_URL_HOST = "http://www.ida.liu.se/~TDTS04/labs/2011/ass2/error1.html"
BAD_CONTENT_HOST = "http://www.ida.liu.se/~TDTS04/labs/2011/ass2/error2.html"
SUFFIXES = [".png", ".jpg", ".jpeg", ".js", ".cs", ".gif"]  # these files wil be skipped on content checking
FILE_NAME = "forbidden.txt"     # file that contains forbidden keywords

class MyProxy:

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
        self.reader = FileReader(FILE_NAME)
        # init parser
        self.parser = Parser(SUFFIXES)

    def main_loop(self):
        while 1:
            connection, client_addr = self.server.accept()
            thread.start_new_thread(self.serve_connection, (connection, client_addr))
        self.server.close()

    def print_info(self, type, request, address):
        print address[0], "\t", type.upper(), "\t", request

    def serve_connection(self, connection, client_addr):
        # receive a request from client
        data = connection.recv(BUFFER_SIZE)
        first_line = data.split("\n")[0]
        url = self.parser.get_url(first_line)
        web_server = self.parser.url_to_web_server(url)
        badUrl = False

        # serve GET requests only
        if "GET" in first_line:
            self.print_info("request", first_line, client_addr)
            # check if url contains forbidden keywords
            badUrl = self.parser.contains_keywords(url, self.reader.keywords)
            if badUrl:
                self.print_info("blacklisted", url, client_addr)

        # if requested for file other than on specified list, check its content later
        content_check_needed = self.parser.check_for_content(url)

        try:
            # open socket
            served_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # connect to web server over HTTP port
            served_socket.connect((web_server, HTTP_PORT))
            # if url contains forbidden keywords, redirect to web page with error msg
            if badUrl:
                # server-side can be closed, we won't use it anymore
                served_socket.shutdown(socket.SHUT_RDWR)
                # client-side can be closed for rcv()
                connection.shutdown(socket.SHUT_RD)
                # create fake HTTP 302 response and send it to client
                connection.send(self.redirect_response(BAD_URL_HOST))
            else:
                # send request to server
                served_socket.send(data)
                # assume website doesn't contain forbidden keywords
                badContent = False
                # receive chunks of response from web server
                while 1:
                    new_chunk = served_socket.recv(BUFFER_SIZE)
                    # if something was actually received
                    if len(new_chunk) > 0:
                        # if not binary/css/js/... file, then check content for forbidden keywords
                        if content_check_needed:
                            for line in new_chunk.split("\n"):
                                badContent = self.parser.contains_keywords(line, self.reader.keywords)
                                # if any of keywords was found, print info and stop checking
                                if badContent:
                                    self.print_info("bad content", url, client_addr)
                                    break  # break for-loop
                        if badContent:
                            # in case of detecting forbidden keywords in web page:
                            # close server-side (we won't use it anymore)
                            served_socket.shutdown(socket.SHUT_RDWR)
                            # close client-side for rcv()
                            connection.shutdown(socket.SHUT_RD)
                            # # create fake HTTP 302 response and send it to client
                            connection.send(self.redirect_response(BAD_CONTENT_HOST))
                        else:
                            # if web page doesn't contain forbidden keywords, send data to client
                            connection.send(new_chunk)
                    else:
                        # break, because 0-length data was sent = close connection
                        break
            # close server-side
            served_socket.close()
        except socket.error, (value, message):
            self.print_info("Peer reset", first_line, client_addr)
        finally:
            # close client-side
            connection.close()
            print "\t> Connection closed. Thread exiting..."
            # dispose of thread
            thread.exit()

    # creates fake HTTP 302 response with redirection to url
    def redirect_response(self, url):
        return "HTTP/1.1 302 Found\r\nLocation: " + url + "\r\nHost: " + self.parser.url_to_web_server(url) + "\r\nConnection: close\r\n\r\n"


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
