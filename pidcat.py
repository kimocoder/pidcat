#!/usr/bin/python -u

'''
Copyright 2009, The Android Open Source Project

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

# Script to highlight adb logcat output for console
# Originally written by Jeff Sharkey, http://jsharkey.org/
# Piping detection and popen() added by other Android team members
# Package filtering and output improvements by Jake Wharton, http://jakewharton.com

import argparse
import sys
import re
import subprocess
from subprocess import PIPE

__version__ = '2.1.0'

LOG_LEVELS = 'VDIWEF'
LOG_LEVELS_MAP = dict([(LOG_LEVELS[i], i) for i in range(len(LOG_LEVELS))])
parser = argparse.ArgumentParser(description='Filter logcat by package name')
parser.add_argument('package', nargs='*', help='Application package name(s)')
parser.add_argument('-w', '--tag-width', metavar='N', dest='tag_width', type=int, default=23, help='Width of log tag')
parser.add_argument('-l', '--min-level', dest='min_level', type=str, choices=LOG_LEVELS+LOG_LEVELS.lower(), default='V', help='Minimum level to be displayed')
parser.add_argument('--color-gc', dest='color_gc', action='store_true', help='Color garbage collection')
parser.add_argument('--always-display-tags', dest='always_tags', action='store_true',help='Always display the tag name')
parser.add_argument('--current', dest='current_app', action='store_true',help='Filter logcat by current running app')
parser.add_argument('-s', '--serial', dest='device_serial', help='Device serial number (adb -s option)')
parser.add_argument('-d', '--device', dest='use_device', action='store_true', help='Use first device for log input (adb -d option)')
parser.add_argument('-e', '--emulator', dest='use_emulator', action='store_true', help='Use first emulator for log input (adb -e option)')
parser.add_argument('-c', '--clear', dest='clear_logcat', action='store_true', help='Clear the entire log before running')
parser.add_argument('-t', '--tag', dest='tag', action='append', help='Filter output by specified tag(s)')
parser.add_argument('-i', '--ignore-tag', dest='ignored_tag', action='append', help='Filter output by ignoring specified tag(s)')
parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print the version number and exit')
parser.add_argument('-a', '--all', dest='all', action='store_true', default=False, help='Print all log messages')
parser.add_argument('--timestamp', dest='add_timestamp', action='store_true', help='Prepend each line of output with the current time.')
parser.add_argument('--header-width', metavar='N', dest='header_width', type=int, default=0, help='Width of customized log header. If you have your own header besides Android log header, this option will further indent your wrapped lines with additional width')
parser.add_argument('--grep', dest='grep_words', type=str, default='', help='Filter lines with words in log messages. The words are delimited with \'\\|\', where each word can be tailed with a color initialed with \'\\\\\'. If no color is specified, \'RED\' will be the default color. For example, option --grep=\"word1\\|word2\\\\CYAN\" means to filter out all lines containing either word1 or word2, and word1 will appear in default color RED while word2 will be in CYAN. Supported colors (case ignored): {BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE}')
parser.add_argument('--highlight', dest='highlight_words', type=str, default='', help='Words to highlight in log messages. Unlike --grep option, this option will only highlight the specified words with specified color but does not filter any lines. Except this, the format and supported colors are the same as --grep')
parser.add_argument('--grepv', dest='grepv_words', type=str, default='', help='Exclude lines with words from log messages. The format and supported colors are the same as --grep. Note that if both --grepv and --grep are provided and they contain the same word, the line will always show, which means --grep overwrites --grepv for the same word they both contain')
parser.add_argument('--igrep', dest='igrep_words', type=str, default='', help='The same as --grep, just ignore case')
parser.add_argument('--ihighlight', dest='ihighlight_words', type=str, default='', help='The same as --highlight, just ignore case')
parser.add_argument('--igrepv', dest='igrepv_words', type=str, default='', help='The same as --grepv, just ignore case')
parser.add_argument('--tee', dest='file_name', type=str, default='', help='Besides stdout output, also output the filtered result (after grep/grepv) to the file')
parser.add_argument('--tee-original', dest='original_file_name', type=str, default='', help='Besides stdout output, also output the unfiltered result (no grep/grepv, i.e., original adb output) to the file')

args = parser.parse_args()
min_level = LOG_LEVELS_MAP[args.min_level.upper()]

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

color_dict = {'BLACK': BLACK, 'RED': RED, 'GREEN': GREEN, 'YELLOW': YELLOW, 'BLUE': BLUE, 'MAGENTA': MAGENTA, 'CYAN': CYAN, 'WHITE': WHITE}

def extract_color_from_word(word):
  w = word
  c = RED
  delimiter='\\'
  index = word.rfind(delimiter)
  if index is not -1:
    w = word[0:index]
    try:
      c = color_dict[word[index + len(delimiter):].upper()]
    except KeyError:
      c = RED
  return w, c


def parse_words_with_color(words):
  words_with_color = []
  for word in words:
    words_with_color.append(extract_color_from_word(word))
  return words_with_color

grep_words_with_color = None
highlight_words_with_color = None
excluded_words = None
igrep_words_with_color = None
ihighlight_words_with_color = None
iexcluded_words = None

if args.grep_words is not None and len(args.grep_words) > 0:
  grep_words_with_color = parse_words_with_color(args.grep_words.split('\|'))
if args.highlight_words is not None and len(args.highlight_words) > 0:
  highlight_words_with_color = parse_words_with_color(args.highlight_words.split('\|'))
if args.grepv_words is not None and len(args.grepv_words) > 0:
  excluded_words = args.grepv_words.split('\|')

if args.igrep_words is not None and len(args.igrep_words) > 0:
  igrep_words_with_color = parse_words_with_color(args.igrep_words.split('\|'))
if args.ihighlight_words is not None and len(args.ihighlight_words) > 0:
  ihighlight_words_with_color = parse_words_with_color(args.ihighlight_words.split('\|'))
if args.igrepv_words is not None and len(args.igrepv_words) > 0:
  iexcluded_words = args.igrepv_words.split('\|')

package = args.package

base_adb_command = ['adb']
if args.device_serial:
  base_adb_command.extend(['-s', args.device_serial])
if args.use_device:
  base_adb_command.append('-d')
if args.use_emulator:
  base_adb_command.append('-e')

if args.current_app:
  system_dump_command = base_adb_command + ["shell", "dumpsys", "activity", "activities"]
  system_dump = subprocess.Popen(system_dump_command, stdout=PIPE, stderr=PIPE).communicate()[0]
  running_package_name = re.search(".*TaskRecord.*A[= ]([^ ^}]*)", system_dump).group(1)
  package.append(running_package_name)

if len(package) == 0:
  args.all = True

# Store the names of packages for which to match all processes.
catchall_package = filter(lambda package: package.find(":") == -1, package)
# Store the name of processes to match exactly.
named_processes = filter(lambda package: package.find(":") != -1, package)
# Convert default process names from <package>: (cli notation) to <package> (android notation) in the exact names match group.
named_processes = map(lambda package: package if package.find(":") != len(package) - 1 else package[:-1], named_processes)

header_size = args.tag_width + 1 + 3 + 1 # space, level, space

width = -1
try:
  # Get the current terminal width
  import fcntl, termios, struct
  h, width = struct.unpack('hh', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('hh', 0, 0)))
except:
  pass

RESET = '\033[0m'

def termcolor(fg=None, bg=None):
  codes = []
  if fg is not None: codes.append('3%d' % fg)
  if bg is not None: codes.append('10%d' % bg)
  return '\033[%sm' % ';'.join(codes) if codes else ''

def colorize(message, fg=None, bg=None):
  return termcolor(fg, bg) + message + RESET

tee_file = None
if args.file_name is not None and len(args.file_name) > 0:
  tee_file = open(args.file_name, 'w')

tee_original_file = None
if args.original_file_name is not None and len(args.original_file_name) > 0:
  tee_original_file = open(args.original_file_name, 'w')

def output_line(line, filtered_on_stdout = False):
  if not filtered_on_stdout:
    print(line)
    if tee_file is not None:
      tee_file.write(line)
      tee_file.write('\n')
      tee_file.flush()

  if tee_original_file is not None:
    tee_original_file.write(line)
    tee_original_file.write('\n')
    tee_original_file.flush()


def grep(message, grep_words_with_color, ignore_case):
  if grep_words_with_color is not None and len(grep_words_with_color) > 0:
    found = False
    for word,color in grep_words_with_color:
      if len(word) > 0 and ((not ignore_case and word in message) or (ignore_case and word.upper() in message.upper())):
        found = True
        break
    if not found:
      return False
  return True

def grepv(message, grepv_words, ignore_case):
  if grepv_words is not None and len(grepv_words) > 0:
    for word in grepv_words:
      if len(word) > 0 and ((not ignore_case and word in message) or (ignore_case and word.upper() in message.upper())):
        return False
  return True

def colorize_substr(str, start_index, end_index, color):
  colored_word = colorize(str[start_index:end_index], fg=color)
  return str[:start_index] + colored_word + str[end_index:], start_index + len(colored_word)

def highlight(line, words_to_color, ignore_case, prev_line, next_line):
  for word, color in words_to_color:
    if len(word) > 0:
      index = 0
      while True:
        try:
          if ignore_case:
            index = line.upper().index(word.upper(), index)
          else:
            index = line.index(word, index)
        except ValueError:
          break
        line, index = colorize_substr(line, index, index + len(word), color)

      for i in range(1, len(word)):
        if word == prev_line[-i:] + line[:len(word) - i]:
          line, index = colorize_substr(line, 0, len(word) - i, color)
          break

      for i in range(1, len(word)):
        if word == line[-i:] + next_line[:len(word) - i]:
          line, index = colorize_substr(line, len(line) - i, len(line), color)
          break

  return line

def indent_wrap(message):
  if width == -1:
    return message
  message = message.replace('\t', '    ')
  wrap_area = width - header_size - args.header_width
  messagebuf = ''
  current = 0
  while current < len(message):
    next = min(current + wrap_area, len(message))
    messagebuf += message[current:next]
    if next < len(message):
      messagebuf += '\n'
      messagebuf += ' ' * (header_size +  + args.header_width)
    current = next
  return messagebuf

def split_to_lines(message):
  if width == -1:
    return message
  message = message.replace('\t', '    ')
  lines = []
  current = 0
  while current < len(message):
    if current == 0:
      wrap_area = width - header_size
    else:
      wrap_area = width - header_size - args.header_width
    next = min(current + wrap_area, len(message))
    lines.append(message[current:next])
    current = next
  return lines


LAST_USED = [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN]
KNOWN_TAGS = {
  'dalvikvm': WHITE,
  'Process': WHITE,
  'ActivityManager': WHITE,
  'ActivityThread': WHITE,
  'AndroidRuntime': CYAN,
  'jdwp': WHITE,
  'StrictMode': WHITE,
  'DEBUG': YELLOW,
}

def allocate_color(tag):
  # this will allocate a unique format for the given tag
  # since we dont have very many colors, we always keep track of the LRU
  if tag not in KNOWN_TAGS:
    KNOWN_TAGS[tag] = LAST_USED[0]
  color = KNOWN_TAGS[tag]
  if color in LAST_USED:
    LAST_USED.remove(color)
    LAST_USED.append(color)
  return color


RULES = {
  # StrictMode policy violation; ~duration=319 ms: android.os.StrictMode$StrictModeDiskWriteViolation: policy=31 violation=1
  re.compile(r'^(StrictMode policy violation)(; ~duration=)(\d+ ms)')
  : r'%s\1%s\2%s\3%s' % (termcolor(RED), RESET, termcolor(YELLOW), RESET),
}

# Only enable GC coloring if the user opted-in
if args.color_gc:
  # GC_CONCURRENT freed 3617K, 29% free 20525K/28648K, paused 4ms+5ms, total 85ms
  key = re.compile(r'^(GC_(?:CONCURRENT|FOR_M?ALLOC|EXTERNAL_ALLOC|EXPLICIT) )(freed <?\d+.)(, \d+\% free \d+./\d+., )(paused \d+ms(?:\+\d+ms)?)')
  val = r'\1%s\2%s\3%s\4%s' % (termcolor(GREEN), RESET, termcolor(YELLOW), RESET)

  RULES[key] = val


TAGTYPES = {
  'V': colorize(' V ', fg=WHITE, bg=BLACK),
  'D': colorize(' D ', fg=BLACK, bg=BLUE),
  'I': colorize(' I ', fg=BLACK, bg=GREEN),
  'W': colorize(' W ', fg=BLACK, bg=YELLOW),
  'E': colorize(' E ', fg=BLACK, bg=RED),
  'F': colorize(' F ', fg=BLACK, bg=RED),
}

PID_LINE = re.compile(r'^\w+\s+(\w+)\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w\s([\w|\.|\/]+)$')
PID_START = re.compile(r'^.*: Start proc ([a-zA-Z0-9._:]+) for ([a-z]+ [^:]+): pid=(\d+) uid=(\d+) gids=(.*)$')
PID_START_5_1 = re.compile(r'^.*: Start proc (\d+):([a-zA-Z0-9._:]+)/[a-z0-9]+ for (.*)$')
PID_START_DALVIK = re.compile(r'^E/dalvikvm\(\s*(\d+)\): >>>>> ([a-zA-Z0-9._:]+) \[ userId:0 \| appId:(\d+) \]$')
PID_KILL  = re.compile(r'^Killing (\d+):([a-zA-Z0-9._:]+)/[^:]+: (.*)$')
PID_LEAVE = re.compile(r'^No longer want ([a-zA-Z0-9._:]+) \(pid (\d+)\): .*$')
PID_DEATH = re.compile(r'^Process ([a-zA-Z0-9._:]+) \(pid (\d+)\) has died.?$')
LOG_LINE  = re.compile(r'^[0-9-]+ ([0-9:.]+) ([A-Z])/(.+?)\( *(\d+)\): (.*?)$')
BUG_LINE  = re.compile(r'.*nativeGetEnabledTags.*')
BACKTRACE_LINE = re.compile(r'^#(.*?)pc\s(.*?)$')

adb_command = base_adb_command[:]
adb_command.append('logcat')
adb_command.extend(['-v', 'time', 'brief'])

# Clear log before starting logcat
if args.clear_logcat:
  adb_clear_command = list(adb_command)
  adb_clear_command.append('-c')
  adb_clear = subprocess.Popen(adb_clear_command)

  while adb_clear.poll() is None:
    pass

# This is a ducktype of the subprocess.Popen object
class FakeStdinProcess():
  def __init__(self):
    self.stdout = sys.stdin
  def poll(self):
    return None

if sys.stdin.isatty():
  adb = subprocess.Popen(adb_command, stdin=PIPE, stdout=PIPE)
else:
  adb = FakeStdinProcess()
pids = set()
last_tag = None
app_pid = None

def match_packages(token):
  if len(package) == 0:
    return True
  if token in named_processes:
    return True
  index = token.find(':')
  return (token in catchall_package) if index == -1 else (token[:index] in catchall_package)

def parse_death(tag, message):
  if tag != 'ActivityManager':
    return None, None
  kill = PID_KILL.match(message)
  if kill:
    pid = kill.group(1)
    package_line = kill.group(2)
    if match_packages(package_line) and pid in pids:
      return pid, package_line
  leave = PID_LEAVE.match(message)
  if leave:
    pid = leave.group(2)
    package_line = leave.group(1)
    if match_packages(package_line) and pid in pids:
      return pid, package_line
  death = PID_DEATH.match(message)
  if death:
    pid = death.group(2)
    package_line = death.group(1)
    if match_packages(package_line) and pid in pids:
      return pid, package_line
  return None, None

def parse_start_proc(line):
  start = PID_START_5_1.match(line)
  if start is not None:
    line_pid, line_package, target = start.groups()
    return line_package, target, line_pid, '', ''
  start = PID_START.match(line)
  if start is not None:
    line_package, target, line_pid, line_uid, line_gids = start.groups()
    return line_package, target, line_pid, line_uid, line_gids
  start = PID_START_DALVIK.match(line)
  if start is not None:
    line_pid, line_package, line_uid = start.groups()
    return line_package, '', line_pid, line_uid, ''
  return None

def tag_in_tags_regex(tag, tags):
  return any(re.match(r'^' + t + r'$', tag) for t in map(str.strip, tags))

ps_command = base_adb_command + ['shell', 'ps']
ps_pid = subprocess.Popen(ps_command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
while True:
  try:
    line = ps_pid.stdout.readline().decode('utf-8', 'replace').strip()
  except KeyboardInterrupt:
    break
  if len(line) == 0:
    break

  pid_match = PID_LINE.match(line)
  if pid_match is not None:
    pid = pid_match.group(1)
    proc = pid_match.group(2)
    if proc in catchall_package:
      seen_pids = True
      pids.add(pid)

while adb.poll() is None:
  try:
    line = adb.stdout.readline().decode('utf-8', 'replace').strip()
  except KeyboardInterrupt:
    break
  if len(line) == 0:
    break

  bug_line = BUG_LINE.match(line)
  if bug_line is not None:
    continue

  log_line = LOG_LINE.match(line)
  if log_line is None:
    continue

  time, level, tag, owner, message = log_line.groups()
  tag = tag.strip()
  start = parse_start_proc(line)
  if start:
    line_package, target, line_pid, line_uid, line_gids = start
    if match_packages(line_package):
      pids.add(line_pid)

      app_pid = line_pid

      linebuf  = '\n'
      linebuf += colorize(' ' * (header_size - 1), bg=WHITE)
      linebuf += indent_wrap(' Process %s created for %s\n' % (line_package, target))
      linebuf += colorize(' ' * (header_size - 1), bg=WHITE)
      linebuf += ' PID: %s   UID: %s   GIDs: %s' % (line_pid, line_uid, line_gids)
      linebuf += '\n'
      output_line(linebuf)
      last_tag = None # Ensure next log gets a tag printed

  dead_pid, dead_pname = parse_death(tag, message)
  if dead_pid:
    pids.remove(dead_pid)
    linebuf  = '\n'
    linebuf += colorize(' ' * (header_size - 1), bg=RED)
    linebuf += ' Process %s (PID: %s) ended' % (dead_pname, dead_pid)
    linebuf += '\n'
    output_line(linebuf)
    last_tag = None # Ensure next log gets a tag printed

  # Make sure the backtrace is printed after a native crash
  if tag == 'DEBUG':
    bt_line = BACKTRACE_LINE.match(message.lstrip())
    if bt_line is not None:
      message = message.lstrip()
      owner = app_pid

  if not args.all and owner not in pids:
    continue
  if level in LOG_LEVELS_MAP and LOG_LEVELS_MAP[level] < min_level:
    continue
  if args.ignored_tag and tag_in_tags_regex(tag, args.ignored_tag):
    continue
  if args.tag and not tag_in_tags_regex(tag, args.tag):
    continue

  linebuf = ''

  if args.tag_width > 0:
    # right-align tag title and allocate color if needed
    if tag != last_tag or args.always_tags:
      last_tag = tag
      color = allocate_color(tag)
      tag = tag[-args.tag_width:].rjust(args.tag_width)
      linebuf += colorize(tag, fg=color)
    else:
      linebuf += ' ' * args.tag_width
    linebuf += ' '

  # write out level colored edge
  if level in TAGTYPES:
    linebuf += TAGTYPES[level]
  else:
    linebuf += ' ' + level + ' '
  linebuf += ' '

  filter_on_stdout = False

  keep_line = grep(message, grep_words_with_color, False)
  if not keep_line:
    filter_on_stdout = True
  else:
    keep_line = grep(message, igrep_words_with_color, True)
    if not keep_line:
      filter_on_stdout = True
    else:
      if not keep_line:
        if not grepv(message, excluded_words, False):
          filter_on_stdout = True
        else:
          if not grepv(message, iexcluded_words, True):
            filter_on_stdout = True

  words_to_color=[]
  if grep_words_with_color is not None:
    words_to_color += grep_words_with_color
  if highlight_words_with_color is not None:
    words_to_color += highlight_words_with_color

  iwords_to_color=[]
  if igrep_words_with_color is not None:
    iwords_to_color += igrep_words_with_color
  if ihighlight_words_with_color is not None:
    iwords_to_color += ihighlight_words_with_color

  # format tag message using rules
  for matcher in RULES:
    replace = RULES[matcher]
    message = matcher.sub(replace, message)

  if args.add_timestamp:
    message = time + " | " + message

  lines = split_to_lines(message)

  if len(lines) > 0:
    n = 0
    prev_line = ''
    for line in lines:
      if n > 0:
        linebuf += '\n'
        linebuf += ' ' * (header_size + + args.header_width)
      cur_line = line
      if n < len(lines) - 1:
        next_line = lines[n + 1]
      else:
        next_line = ''
      line = highlight(line, words_to_color, False, prev_line, next_line)
      line = highlight(line, iwords_to_color, True, prev_line, next_line)
      linebuf += line
      n += 1
      prev_line = cur_line

  output_line(linebuf.encode('utf-8'), filter_on_stdout)
