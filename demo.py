r"""
Demo: EmergencyHandler buffers DEBUG/INFO silently until a WARNING or ERROR fires,
then dumps the recent context together with the triggering message.

Also demonstrates wrapping a RotatingFileHandler so the log file only grows
when something worth investigating actually happens.
"""
import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from emergency_logging import EmergencyHandler

logging.basicConfig()  # root logger won't be used, but sets up format defaults

logger = logging.getLogger("demo")
logger.setLevel(logging.DEBUG)
logger.propagate = False

import sys
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(levelname)-8s %(name)s: %(message)s"))

emergency = EmergencyHandler(target_handler=stream_handler, buffer_size=10)
logger.addHandler(emergency)

print("=== Normal operation — DEBUG/INFO are buffered silently ===")
logger.debug("Starting request processing")
logger.info("Fetching user record id=42")
logger.debug("Cache miss — querying database")
logger.info("Query returned 1 row")
print("(nothing printed yet)\n")

print("=== An error occurs — buffered context + error are flushed ===")
logger.error("Database connection lost unexpectedly")
print()

print("=== Buffer is now empty; new messages accumulate again ===")
logger.info("Retrying connection")
logger.debug("Attempt 1/3")
logger.info("Reconnected successfully")
print("(nothing printed yet)\n")

print("=== A warning — flushed again ===")
logger.warning("Response time exceeded 500 ms threshold")
print()

print("=== Enough buffered messages to exceed buffer_size (10) ===")
for i in range(15):
    logger.debug(f"step {i}")
logger.error("Pipeline stalled")


# ---------------------------------------------------------------------------
# Demo 2: EmergencyHandler wrapping a RotatingFileHandler
# ---------------------------------------------------------------------------
print("\n\n=== Demo 2: EmergencyHandler + RotatingFileHandler ===\n")

log_path = os.path.join(tempfile.gettempdir(), "emergency_demo.log")

rotating = RotatingFileHandler(
    log_path,
    maxBytes=1024 * 10,   # rotate at 10 KB
    backupCount=3,
)
rotating.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))

file_logger = logging.getLogger("demo.file")
file_logger.setLevel(logging.DEBUG)
file_logger.propagate = False
file_logger.addHandler(EmergencyHandler(target_handler=rotating, buffer_size=30))

print(f"Logging to: {log_path}")
print("Emitting DEBUG/INFO — file stays empty until something goes wrong.")

file_logger.debug("Worker started, pid=%d", os.getpid())
file_logger.info("Processing batch job id=7")
file_logger.debug("Reading input file")
file_logger.info("Parsed 1000 records")
file_logger.debug("Running validation pass")

with open(log_path) as f:
    content = f.read()
print(f"File size after 5 debug/info calls: {len(content)} bytes (expected 0)\n")

file_logger.error("Validation failed: 42 records had missing required fields")

with open(log_path) as f:
    content = f.read()
print(f"File contents after error:\n{content}")

# Clean up
rotating.close()
os.remove(log_path)
