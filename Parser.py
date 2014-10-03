
class Parser:

    def __init__(self, list_of_suff):
        self.suffixes = list_of_suff

    def url_to_webserver(self, url):
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
        if any (url.endswith(suffix) for suffix in self.suffixes):
            return False
        else:
            return True