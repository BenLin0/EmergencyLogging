# EmergencyLogging

A Python logging handler that stays silent during normal operation and only writes logs when something goes wrong.

## The problem

Verbose debug logging helps diagnose issues, but writing every `DEBUG` and `INFO` message to a file or console creates noise that obscures what matters. The usual workaround — raising the log level to `WARNING` — means you lose the context that would have explained *why* the warning happened.

## How it works

`EmergencyHandler` wraps any standard `logging.Handler`. It buffers `DEBUG` and `INFO` records silently. The moment a `WARNING`, `ERROR`, or `CRITICAL` is emitted, it flushes the buffered context followed by the triggering message — then clears the buffer and starts over.

```
Normal operation:        DEBUG INFO DEBUG INFO DEBUG INFO  →  (nothing written)
Something goes wrong:    DEBUG INFO DEBUG INFO ERROR       →  DEBUG INFO DEBUG INFO ERROR
```

The buffer holds the **most recent** N records (default 30). Older records are dropped as new ones arrive, so the buffer always contains the last N lines of context leading up to the problem.

## Installation

### Via pip (recommended)

```bash
pip install emergency-logging
```

### Manual

No dependencies outside the standard library. Copy `emergency_logging.py` directly into your project.

Requires Python 3.8+.

## Usage

### Basic — wrap the default stderr handler

```python
import logging
from emergency_logging import EmergencyHandler

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
logger.addHandler(EmergencyHandler())

logger.debug("connecting to database")   # buffered
logger.info("query executed in 4 ms")    # buffered
logger.error("connection pool exhausted") # flushes both lines above, then this
```

### With a custom handler and buffer size

```python
import logging
from emergency_logging import EmergencyHandler

stream = logging.StreamHandler()
stream.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
logger.addHandler(EmergencyHandler(target_handler=stream, buffer_size=50))
```

### With RotatingFileHandler

The log file stays empty during normal operation and only grows when an incident occurs — keeping file sizes minimal while preserving full diagnostic context when you need it.

```python
import logging
from logging.handlers import RotatingFileHandler
from emergency_logging import EmergencyHandler

rotating = RotatingFileHandler("app.log", maxBytes=1024 * 1024, backupCount=5)
rotating.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
logger.addHandler(EmergencyHandler(target_handler=rotating, buffer_size=30))
```

## API

### `EmergencyHandler(target_handler=None, buffer_size=30)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `target_handler` | `logging.Handler` | `StreamHandler()` | The handler that receives flushed records |
| `buffer_size` | `int` | `30` | Maximum number of `DEBUG`/`INFO` records to buffer; oldest are dropped when exceeded |

The handler passes through `WARNING`, `ERROR`, and `CRITICAL` records immediately (after flushing the buffer). `DEBUG` and `INFO` records are only ever written as part of a flush.

## Comparison to `MemoryHandler`

Python's standard library includes [`logging.handlers.MemoryHandler`](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.MemoryHandler), which is the closest built-in equivalent. Here's how they differ:

| | `MemoryHandler`                                   | `EmergencyHandler` |
|---|---------------------------------------------------|---|
| Flush trigger | `ERROR` (default) or buffer full                  | `WARNING` (default) |
| Buffer full behaviour | Flushes the entire buffer immediately             | Drops the **oldest** record, keeps the newest N |
| After a flush | Buffer cleared                                    | Buffer cleared |
| Most recent context guaranteed | No — a busy logger flushes everything on capacity | Yes — you always get the last N lines before the incident |

The practical difference:  `MemoryHandler` doesn't miss anything in the log. `EmergencyHandler` behaves like a ring buffer — it silently discards unimportant records that are too old to matter and always preserves the most recent context window.

## Running the demos

```bash
python3 demo.py
```

## Running the tests

```bash
python3 -m unittest test_emergency_logging -v
```
