from time import ctime


class LogTypes:
    # Define as:
    # Type = DisplayName

    INFO = "INFO"
    ERROR = "ERROR"


class Logger:
    @staticmethod
    def log(type, message):
        print("[{time}] [{type}]: {msg}".format(time=ctime(), type=str(type), msg=str(message)))
