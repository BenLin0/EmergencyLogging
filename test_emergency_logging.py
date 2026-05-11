import logging
import unittest
from emergency_logging import EmergencyHandler


class CapturingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self):
        return [r.getMessage() for r in self.records]

    def levelnames(self):
        return [r.levelname for r in self.records]


def make_logger(buffer_size=30):
    capture = CapturingHandler()
    handler = EmergencyHandler(target_handler=capture, buffer_size=buffer_size)
    logger = logging.getLogger(f"test.{id(handler)}")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.propagate = False
    return logger, handler, capture


class TestEmergencyHandler(unittest.TestCase):

    def test_debug_and_info_are_not_emitted_immediately(self):
        logger, _, capture = make_logger()
        logger.debug("d1")
        logger.info("i1")
        self.assertEqual(capture.records, [])

    def test_warning_flushes_buffer_and_emits_itself(self):
        logger, _, capture = make_logger()
        logger.debug("d1")
        logger.info("i1")
        logger.warning("w1")
        self.assertEqual(capture.messages(), ["d1", "i1", "w1"])
        self.assertEqual(capture.levelnames(), ["DEBUG", "INFO", "WARNING"])

    def test_error_flushes_buffer_and_emits_itself(self):
        logger, _, capture = make_logger()
        logger.debug("d1")
        logger.error("e1")
        self.assertEqual(capture.messages(), ["d1", "e1"])

    def test_buffer_is_cleared_after_flush(self):
        logger, _, capture = make_logger()
        logger.debug("d1")
        logger.warning("w1")
        capture.records.clear()
        logger.debug("d2")
        logger.info("i2")
        # No warning yet — nothing should reach capture
        self.assertEqual(capture.records, [])

    def test_second_warning_flushes_only_messages_since_last_flush(self):
        logger, _, capture = make_logger()
        logger.debug("d1")
        logger.warning("w1")
        capture.records.clear()
        logger.debug("d2")
        logger.info("i2")
        logger.warning("w2")
        self.assertEqual(capture.messages(), ["d2", "i2", "w2"])

    def test_warning_with_no_buffered_messages(self):
        logger, _, capture = make_logger()
        logger.warning("w1")
        self.assertEqual(capture.messages(), ["w1"])

    def test_buffer_size_limit_keeps_most_recent(self):
        logger, _, capture = make_logger(buffer_size=3)
        for i in range(10):
            logger.debug(f"d{i}")
        logger.warning("w")
        # Only the last 3 debug messages should appear
        self.assertEqual(capture.messages(), ["d7", "d8", "d9", "w"])

    def test_default_buffer_size_is_30(self):
        capture = CapturingHandler()
        handler = EmergencyHandler(target_handler=capture)
        self.assertEqual(handler.buffer_size, 30)

    def test_multiple_errors_each_flush_correctly(self):
        logger, _, capture = make_logger()
        logger.info("i1")
        logger.error("e1")
        logger.info("i2")
        logger.error("e2")
        self.assertEqual(capture.messages(), ["i1", "e1", "i2", "e2"])

    def test_critical_also_flushes(self):
        logger, _, capture = make_logger()
        logger.debug("d1")
        logger.critical("c1")
        self.assertEqual(capture.messages(), ["d1", "c1"])


if __name__ == "__main__":
    unittest.main()
