import os.path

class FileReader:

    # load keywords from file
    def __init__(self, filename):
        self.keywords = []
        self.load_keywords(filename)

    # add keywords to the list
    def append_keyword(self, keyword):
        self.keywords.append(keyword)

    # check if file exists and load keywords (1 line = 1 keyword)
    def load_keywords(self, filename):
        if(os.path.isfile(filename)):
            with open(filename) as f:
                # one keyword per line
                for line in f:
                    # append each keyword mapped to lowercase and without '\n'
                    self.append_keyword(line.strip().lower())
        else:
            print "File: ", filename, " not available!"
            exit(1)