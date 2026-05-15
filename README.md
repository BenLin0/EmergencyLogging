# IncidentLogging

A Python logging handler that stays silent during normal operation and only writes logs when something goes wrong.

## The problem

Verbose debug logging helps diagnose issues, but writing every `DEBUG` and `INFO` message to a file or console creates noise that obscures what matters. The usual workaround — raising the log level to `WARNING` — means you lose the context that would have explained *why* the warning happened.

## How it works

`IncidentHandler` wraps any standard `logging.Handler`. It buffers records below `trigger_level` silently. The moment a record at or above `trigger_level` is emitted, it flushes the buffered context followed by the triggering message — then clears the buffer and starts over. The default `trigger_level` is `WARNING`.

```
Normal operation:        DEBUG INFO DEBUG INFO DEBUG INFO  →  (nothing written)
Something goes wrong:    DEBUG INFO DEBUG INFO ERROR       →  DEBUG INFO DEBUG INFO ERROR
```

The buffer holds the **most recent** N records (default 30). Older records are dropped as new ones arrive, so the buffer always contains the last N lines of context leading up to the problem.

## Installation

### Via pip (recommended)

```bash
pip install incident-logging
```

### Manual

No dependencies outside the standard library. Copy `incident_logging.py` directly into your project.

Requires Python 3.8+.

## Usage

### Basic — wrap the default stderr handler

```python
import logging
from incident_logging import IncidentHandler

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
logger.addHandler(IncidentHandler())

logger.debug("connecting to database")   # buffered
logger.info("query executed in 4 ms")    # buffered
logger.error("connection pool exhausted") # flushes both lines above, then this
```

### With a custom trigger level

Raise the trigger to `ERROR` to buffer `WARNING` records along with `DEBUG`/`INFO`:

```python
import logging
from incident_logging import IncidentHandler

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
logger.addHandler(IncidentHandler(trigger_level=logging.ERROR))

logger.warning("slow query: 2.3 s")  # buffered
logger.error("database unreachable")  # flushes the warning above, then this
```

### With a custom handler and buffer size

```python
import logging
from incident_logging import IncidentHandler

stream = logging.StreamHandler()
stream.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
logger.addHandler(IncidentHandler(target_handler=stream, buffer_size=50))
```

### With RotatingFileHandler

The log file stays empty during normal operation and only grows when an incident occurs — keeping file sizes minimal while preserving full diagnostic context when you need it.

```python
import logging
from logging.handlers import RotatingFileHandler
from incident_logging import IncidentHandler

rotating = RotatingFileHandler("app.log", maxBytes=1024 * 1024, backupCount=5)
rotating.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
logger.addHandler(IncidentHandler(target_handler=rotating, buffer_size=30))
```

## API

### `IncidentHandler(target_handler=None, buffer_size=30, trigger_level=logging.WARNING)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `target_handler` | `logging.Handler` | `StreamHandler()` | The handler that receives flushed records |
| `buffer_size` | `int` | `30` | Maximum number of buffered records to keep; oldest are dropped when exceeded |
| `trigger_level` | `int` | `logging.WARNING` | Records at or above this level trigger a flush; records below are buffered |

Records at or above `trigger_level` are passed through immediately (after flushing the buffer). Records below `trigger_level` are only ever written as part of a flush.

## Comparison to `MemoryHandler`

Python's standard library includes [`logging.handlers.MemoryHandler`](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.MemoryHandler), which is the closest built-in equivalent. Here's how they differ:

| | `MemoryHandler` | `IncidentHandler` |
|---|---|---|
| Flush trigger | `ERROR` (default) or buffer full | configurable `trigger_level` (default `WARNING`) |
| Buffer full behaviour | Flushes the entire buffer immediately | Drops the **oldest** record, keeps the newest N |
| After a flush | Buffer cleared | Buffer cleared |
| Most recent context guaranteed | No — a busy logger flushes everything on capacity | Yes — you always get the last N lines before the incident |

The practical difference: `MemoryHandler` doesn't miss anything in the log. `IncidentHandler` behaves like a ring buffer — it silently discards unimportant records that are too old to matter and always preserves the most recent context window.

## Recommended pattern: combine both

Use a regular handler for full bookkeeping and an `IncidentHandler` for focused incident output. The regular handler captures everything for audit trails or offline analysis; the `IncidentHandler` surfaces only what's relevant when something goes wrong.

```python
import logging
from logging.handlers import RotatingFileHandler
from incident_logging import IncidentHandler

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)

# Full audit log — every record, always
audit = RotatingFileHandler("audit.log", maxBytes=10 * 1024 * 1024, backupCount=5)
audit.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
logger.addHandler(audit)

# Incident log — only emits when WARNING or above fires, with recent context
incident = RotatingFileHandler("incidents.log", maxBytes=1024 * 1024, backupCount=3)
incident.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
logger.addHandler(IncidentHandler(target_handler=incident, buffer_size=30))
```

`audit.log` grows continuously and is the source of truth. `incidents.log` stays small and contains only the context windows around each problem — easy to tail in production or attach to a bug report.

## Running the demos

```bash
python3 demo.py
```

## Running the tests

```bash
python3 -m unittest test_incident_logging -v
```
