class Error(Exception):
    def __str__(self):
        return f"code: {self.code}, message: {self.msg}"


class LodisError(Error):
    def __init__(self, response):
        self.response = response
        self.code = response._error_code
        self.msg = response._error_msg


class CodeError(Error):
    def __init__(self):
        self.response = None
        self.code = -1000
        self.msg = "Lodis code error"
