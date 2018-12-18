import re

def on_create():
  return

def get_filters():
  return [
      { "tag": re.compile(r'^Choreographer$') },
    ]

def format_new_entry(level, tag, owner, message):
  return None
