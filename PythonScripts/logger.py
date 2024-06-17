import logging
import datetime as dt
import pytz
TZ = pytz.timezone('America/Detroit')


class Formatter(logging.Formatter):
    """
        Class that overrides logging.Formatter to use a timezone aware datetime object.
    """

    @staticmethod
    def converter(timestamp):
        """
            Changes a UTC datetime object to specific timezone based on global variable TZ.
        """
        dtz = dt.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        return dtz.astimezone(TZ)

    def formatTime(self, record, datefmt=None):
        """
            Returns custom or default formatted datetime object.
        """
        dtz = self.converter(record.created)
        if datefmt:
            s = dtz.strftime(datefmt)
        else:
            try:
                s = dtz.isoformat(timespec='milliseconds')
            except TypeError:
                s = dtz.isoformat()
        return s


def setup_logger(name, log_file, level=logging.INFO):
    """
        Factory function to create separate and customizable logging instances.
    """
    formatter = Formatter('%(asctime)s | %(levelname)s | %(message)s', '%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(log_file, mode='a')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


execution_logger = setup_logger('execution_log', '../data/logs/execution_log.txt', level=logging.INFO)
error_logger = setup_logger('error_log', '../data/logs/error_log.txt', level=logging.ERROR)
