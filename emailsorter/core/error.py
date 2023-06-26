class EmailSorterException(Exception):
    pass


class ConfigSetupException(EmailSorterException):
    def __init__(self, msg: str, attr: str = ""):
        self._msg = msg
        self._attr = attr

    def __str__(self):
        return f"{self._attr}: {self._msg}" if self._attr else self._msg


class CliArgException(EmailSorterException):
    pass
