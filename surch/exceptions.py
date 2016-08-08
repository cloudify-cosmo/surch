class SurchError(Exception):
    def __init__(self, message, error_code=1):
        self.message = message
        self.error_code = error_code

    def __str__(self):
        return '{0} (Error Code: {1})'.format(self.message, self.error_code)
