import re

def on_create():
  return

def get_filters():
  return [
      { "tag": re.compile(r'^ActivityManager$'), "message": re.compile("^Displayed") },
    ]

def format_new_entry(level, tag, owner, message):
  return None
