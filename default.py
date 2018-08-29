import re

def on_create():
  """
  If your module requires an initialization.
  Do it here.
  """
  return

def get_filters():
  """
  The filters define rules for what log entries
  must be shown.
  Each filter 

  Returns:
    An array of filters
  """
  return [
      { "tag": re.compile(r'.*') },
    ]

def format_new_entry(level, tag, owner, message):
  """
  Format your log entries to be printed.

  Warn/Tip: you can use each log entry to change the internal state for your module.
            Be careful with stateful modules, the log capture starts at any time.

  Args:
    level: level from log entry.
    tag: tag from log entry.
    owner: owner from log entry.
    message: message from log entry.

  Returns:
    return the formatted message.
  """
  return None
