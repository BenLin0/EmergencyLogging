import logging
import collections


class IncidentHandler(logging.Handler):
    """
    Buffers records below `trigger_level` and flushes them when a record at or
    above `trigger_level` is emitted. Defaults to WARNING.
    Keeps the last `buffer_size` buffered records (oldest are dropped when full).
    """

    def __init__(self, target_handler=None, buffer_size=30, trigger_level=logging.WARNING):
        super().__init__()
        self.target_handler = target_handler or logging.StreamHandler()
        self.buffer_size = buffer_size
        self.trigger_level = trigger_level
        self._buffer = collections.deque(maxlen=buffer_size)

    def emit(self, record):
        if record.levelno >= self.trigger_level:
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
