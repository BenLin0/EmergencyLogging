## EmergencyLogging
This is a logging handler.
When user use this logging handler, it will save (buffer) the logging message of logging.INFO, logging.DEBUG for x (configurable, default 30) lines. When a logging of level logging.WARN or logging.ERROR is called, it will spit out all the buffered message, as well as the new message.

Write this handler, and test, and some demo program to demonstrate its usage.