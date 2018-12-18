import re

def on_create():
  return

def get_filters():
  return [
      { "tag": re.compile(r'^SPRENGEL$') },
      { "message": re.compile(r'SPRENGEL') },
    ]

def format_new_entry(level, tag, owner, message):
  return None
