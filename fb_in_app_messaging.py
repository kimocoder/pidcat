import re

RE_FIAM_ID = re.compile(r'^Starting InAppMessaging runtime with Instance ID (.*)$')

def on_create():
  return

def get_filters():
  return [
      { "tag": re.compile(r'FIAM.Headless') },
    ]

def format_new_entry(level, tag, owner, message):
  if tag != 'FIAM.Headless':
    return None

  m = RE_FIAM_ID.match(message)
  if m:
    return "\n\n\n\tIn-App Messaging ID: {0}\n\n\n".format(m.group(1))
  else:
    return None
