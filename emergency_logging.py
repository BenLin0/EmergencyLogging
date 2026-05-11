import logging
import collections


class EmergencyHandler(logging.Handler):
    """
    Buffers DEBUG/INFO records and flushes them only when WARN or ERROR is emitted.
    Keeps the last `buffer_size` buffered records (oldest are dropped when full).
    """

    def __init__(self, target_handler=None, buffer_size=30):
        super().__init__()
        self.target_handler = target_handler or logging.StreamHandler()
        self.buffer_size = buffer_size
        self._buffer = collections.deque(maxlen=buffer_size)

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            for buffered in self._buffer:
                self.target_handler.emit(buffered)
            self._buffer.clear()
            self.target_handler.emit(record)
        else:
            self._buffer.append(record)

    def flush(self):
        self.target_handler.flush()

    def close(self):
        self.target_handler.close()
        super().close()
