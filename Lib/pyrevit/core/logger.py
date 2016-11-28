import logging
import sys
from os.path import sep

from ..config import FORCED_DEBUG_MODE_PARAM
from ..config.coreconfig import DEBUG_ISC_NAME, VERBOSE_ISC_NAME

from .coreutils import set_interscript_comm_data, get_interscript_comm_data
from .emoji import emojize

RUNTIME_LOGGING_LEVEL = logging.WARNING
LOG_RECORD_FORMAT = "%(levelname)s: [%(name)s] %(message)s"
LOG_RECORD_FORMAT_ERROR = '<div style="background:#EEE;padding:10;margin:10 0 10 0">{}</div>'.format(LOG_RECORD_FORMAT)
LOG_RECORD_FORMAT_CRITICAL = '<div style="background:#ffdabf;padding:10;margin:10 0 10 0">{}</div>'.format(LOG_RECORD_FORMAT)


# Setting session-wide debug/verbose status so other individual scripts know about it.
# individual scripts are run at different time and the level settings need to be set inside current host session
# so they can be retreieved later.
if get_interscript_comm_data(VERBOSE_ISC_NAME):
    RUNTIME_LOGGING_LEVEL = logging.INFO

if get_interscript_comm_data(DEBUG_ISC_NAME):
    RUNTIME_LOGGING_LEVEL = logging.DEBUG

# the loader assembly sets FORCED_DEBUG_MODE_PARAM to true if user Shift-clicks on the button
# FORCED_DEBUG_MODE_PARAM will be set by the LOADER_ADDIN_COMMAND_INTERFACE_CLASS_EXT at script runtime
if FORCED_DEBUG_MODE_PARAM:
    RUNTIME_LOGGING_LEVEL = logging.DEBUG


# custom logger methods (for module consistency and custom adjustments) ------------------------------------------------
class DispatchingFormatter:
    def __init__(self, formatters, default_formatter):
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record):
        formatter = self._formatters.get(record.levelno, self._default_formatter)
        return formatter.format(record)


class LoggerWrapper(logging.Logger):
    def __init__(self, *args):
        logging.Logger.__init__(self, *args)

    def _log(self, level, msg, args, exc_info=None, extra=None):
        edited_msg = emojize(str(msg).replace(sep,'/'))
        logging.Logger._log(self, level, edited_msg, args, exc_info=None, extra=None)

    def getEffectiveLevel(self):
        """Overrides the parent class method to check handler.level instead of self.level.
        All loggers generated by this module use the same handler. All set level methods set handler.level instead
        of self.level. This ensures that the level set on any logger affects all the other logger modules."""
        logger = self
        while logger:
            if len(logger.handlers) > 0 and logger.handlers[0].level:
                return logger.handlers[0].level
            elif logger.level:
                return logger.level
            logger = logger.parent
        return logging.NOTSET

    def set_level(self, level):
        self.handlers[0].setLevel(level)

    def set_verbose_mode(self):
        set_interscript_comm_data(VERBOSE_ISC_NAME, True)
        self.handlers[0].setLevel(logging.INFO)

    def set_debug_mode(self):
        set_interscript_comm_data(DEBUG_ISC_NAME, True)
        self.handlers[0].setLevel(logging.DEBUG)

    def reset_level(self):
        set_interscript_comm_data(VERBOSE_ISC_NAME, False)
        set_interscript_comm_data(DEBUG_ISC_NAME, False)
        self.handlers[0].setLevel(RUNTIME_LOGGING_LEVEL)

    def get_level(self):
        return self.level

# setting up handlers and formatters -----------------------------------------------------------------------------------
stdout_hndlr = logging.StreamHandler(sys.stdout)
# e.g [parser] DEBUG: Can not create command.
stdout_hndlr.setFormatter(DispatchingFormatter({logging.ERROR: logging.Formatter(LOG_RECORD_FORMAT_ERROR),
                                                logging.CRITICAL: logging.Formatter(LOG_RECORD_FORMAT_CRITICAL)},
                                                logging.Formatter(LOG_RECORD_FORMAT)))
stdout_hndlr.setLevel(RUNTIME_LOGGING_LEVEL)

# todo: file handler
# file_hndlr = logging.FileHandler(file_address)
# # Custom formater for file
# file_formatter = logging.Formatter(LOG_RECORD_FORMAT)
# file_hndlr.setFormatter(file_formatter)


# setting up public logger. this will be imported in with other modules ------------------------------------------------
logging.setLoggerClass(LoggerWrapper)


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)    # type: LoggerWrapper
    logger.addHandler(stdout_hndlr)
    return logger
