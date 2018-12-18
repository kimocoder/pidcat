import re, os
import subprocess
import threading

RE_DIPLAYED = re.compile(r'^Displayed (.*)/(.*): \+.*')
SS_DIR = 'out'
ss_counters = {}

def capture_ss(filename):
  print('shooting..' + filename)
  with open(filename, "w") as outfile:
    subprocess.call(['adb', 'exec-out', 'screencap', '-p'], stdout=outfile)  

def on_create():
  if os.path.isdir(SS_DIR):
    return
  if os.path.exists(SS_DIR):
    raise Exception('{0} must be a directory'.format(SS_DIR))

  os.mkdir(SS_DIR)
  return

def get_filters():
  return [
      { "tag": re.compile(r'^ActivityManager$'), "message": re.compile(r'^Displayed') },
    ]

def format_new_entry(level, tag, owner, message):
  if tag != 'ActivityManager':
    return None

  match = RE_DIPLAYED.match(message)
  if not match:
    return None

  package_name = match.group(1)
  activity_name = match.group(2)

  activity_abs_name = None
  if package_name[0] == '.':
    activity_abs_name = '{0}{1}'.format(package_name, activity_name)
  else:
    activity_abs_name = activity_name

  if activity_abs_name not in ss_counters:
    ss_counters[activity_abs_name] = 1
  else:
    ss_counters[activity_abs_name] += 1

  filename = os.path.join(
    SS_DIR,
    '{0}_{1:0>2d}.png'.format(activity_abs_name, ss_counters[activity_abs_name])
  )

  threading.Timer(10.0, capture_ss, args=[filename]).start()

  return filename