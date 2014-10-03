
class Parser:

    # load suffixes of the files that won't be checked for content
    def __init__(self, list_of_suff):
        self.suffixes = list_of_suff

    # parse "http://www.something.com/something_/else.html" to "www.something.com"
    def url_to_web_server(self, url):
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]
        web_server_pos = temp.find("/")
        if web_server_pos == -1:
            web_server_pos = len(temp)
        return temp[:web_server_pos]

    # return False if client requested for file that ends with suffix specified in SUFFIXES list
    def check_for_content(self, url):
        if any (url.endswith(suffix) for suffix in self.suffixes):
            return False
        else:
            return True

    # return True if any of the keywords was found in string
    def contains_keywords(self, string, keywords):
        if any(s in string.lower() for s in keywords):
            return True
        else:
            return False

    # parse first line of request to get the url
    def get_url(self, string):
        return string.split(" ")[1]
