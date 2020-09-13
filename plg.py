import pathlib
import subprocess
import os
import shutil
import signal
import sublime
import sublime_plugin

from .plg_nrepl_server import start as start_server
from .plg_nrepl_server import stop as stop_server
from .plg_nrepl_client import start as start_client
from .plg_nrepl_client import stop as stop_client
from .plg_nrepl_client import commit as nrepl_commit
from .plg_nrepl_client import ping as nrepl_ping
from .plg_format_code import format_code
from .plg_generate_completion import generate_completion

# ============================================================================ #
#     _       _____ _      ____  ____           _____
#  /\| |/\   / ____| |    / __ \|  _ \   /\    / ____|
#  \ ` ' /  | |  __| |   | |  | | |_) | /  \  | (___
# |_     _| | | |_ | |   | |  | |  _ < / /\ \  \___ \
#  / , . \  | |__| | |___| |__| | |_) / ____ \ ____) |
#  \/|_|\/   \_____|______\____/|____/_/    \_\_____/
# ============================================================================ #

DEFAULT_SETTINGS = 'Jide.sublime-settings'
PLUGIN_TEMP_DIR = 'Jide'
PLUGIN_REPL_PROC = 'repl-proc'
JANET_EXEC = 'janet_executable'
JPM_EXEC = 'jpm_executable'
JPM_OPT_LIST = 'list-installed'
JPM_LIB_SPORK = 'spork'
NREPL_HOST = 'nrepl_host'
NREPL_PORT = 'nrepl_port'

server_ref = None
client_ref = None
symbols_map = {}
g_completion_list = []

# ============================================================================ #
#           _____ ____  __  __ __  __          _   _ _____   _____
#    _     / ____/ __ \|  \/  |  \/  |   /\   | \ | |  __ \ / ____|
#  _| |_  | |   | |  | | \  / | \  / |  /  \  |  \| | |  | | (___
# |_   _| | |   | |  | | |\/| | |\/| | / /\ \ | . ` | |  | |\___ \
#   |_|   | |___| |__| | |  | | |  | |/ ____ \| |\  | |__| |____) |
#          \_____\____/|_|  |_|_|  |_/_/    \_\_| \_|_____/|_____/
# ============================================================================ #

##
## JideStartNreplServerCommand
##
class JideStartNreplServerCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    if not start_nrepl_process():
      sublime.error_message('failed to start janet nrepl server process')      
      return
    set_nrepl_status_flag(True)

##
## JideStopNreplServerCommand
##
class JideStopNreplServerCommand(sublime_plugin.TextCommand):
  def run(self, edit):    
    terminate_nrepl_proc()
    set_nrepl_status_flag(False)

##
## JideStartNreplClientCommand
##
class JideStartNreplClientCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global client_ref    
    janet = configs_get(JANET_EXEC)
    host = configs_get(NREPL_HOST)
    port = int(configs_get(NREPL_PORT))
    client_ref = start_client(host, port)

##
## JideStopNreplClientCommand
##
class JideStopNreplClientCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global client_ref    
    stop_client(client_ref)

##
## JideFormatCommand
##
class JideFormatCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    if not is_janet_file(self.view):
      print('this is not a janet file')
      return    
    file_size = self.view.size()
    selection = self.view.substr(sublime.Region(0, file_size))
    formatted = format_code_section(selection)
    if not formatted:
      return
    self.view.replace(edit, sublime.Region(0, file_size), formatted)    

# ============================================================================ #
#          ________      ________ _   _ _______ _____
#    _    |  ____\ \    / /  ____| \ | |__   __/ ____|
#  _| |_  | |__   \ \  / /| |__  |  \| |  | | | (___
# |_   _| |  __|   \ \/ / |  __| | . ` |  | |  \___ \
#   |_|   | |____   \  /  | |____| |\  |  | |  ____) |
#         |______|   \/   |______|_| \_|  |_| |_____/
# ============================================================================ #

class JanetFileEvents (sublime_plugin.ViewEventListener):  
  def on_post_save_async(self):
    if not is_janet_file(self.view):
      return
    generate_file_completion(self.view.file_name())

  def on_query_completions(self, prefix, location):
    global g_completion_list
    print(g_completion_list)
    filtered = list(filter(lambda str: str.startswith(prefix), g_completion_list))
    print(prefix)
    print(filtered)
    return filtered

# ============================================================================ #
#          _      _____ ______ ______ _______     _______ _      ______
#    _    | |    |_   _|  ____|  ____/ ____\ \   / / ____| |    |  ____|
#  _| |_  | |      | | | |__  | |__ | |     \ \_/ / |    | |    | |__
# |_   _| | |      | | |  __| |  __|| |      \   /| |    | |    |  __|
#   |_|   | |____ _| |_| |    | |___| |____   | | | |____| |____| |____
#         |______|_____|_|    |______\_____|  |_|  \_____|______|______|
# ============================================================================ #

##
## plugin_loaded
##
def plugin_loaded():
  janet = configs_get(JANET_EXEC)
  jpm = configs_get(JPM_EXEC)
  if not is_janet_installed(janet):
    sublime.message_dialog('janet executable cannot be found on your system')
    return
  if not is_jpm_installed(jpm):
    sublime.message_dialog('jpm (janet package manager) executable cannot be found on your system')
    return
  if not is_spork_installed(jpm):
    sublime.message_dialog('spork library for janet is not installed')
    return

  # if is_nrepl_process_running():
  #   set_nrepl_status_flag(True)
  # else:
  #   set_nrepl_status_flag(False)

##
## plugin_unloaded
##
def plugin_unloaded():
  # terminate_nrepl_proc()
  pass

# ============================================================================ #
#           _      ____   _____ _____ _____
#          | |    / __ \ / ____|_   _/ ____|
#  ______  | |   | |  | | |  __  | || |
# |______| | |   | |  | | | |_ | | || |
#          | |___| |__| | |__| |_| || |____
#          |______\____/ \_____|_____\_____|
# ============================================================================ #

##
## create_janet_temp
##
def get_temp_dir():
  global PLUGIN_TEMP_DIR  
  temp = pathlib.Path(sublime.cache_path(), PLUGIN_TEMP_DIR)  
  if not temp.exists():
    temp.mkdir(parents=True)
  return temp

##
## get_proc_file
##
def get_proc_file():  
  global PLUGIN_REPL_PROC
  temp = get_temp_dir()
  proc = pathlib.Path(sublime.cache_path(), temp, PLUGIN_REPL_PROC)  
  if not proc.exists():
    proc.touch()
  return proc

##
## save_nrepl_pid
##
def save_nrepl_pid(pid):
  procFile = get_proc_file()
  with procFile.open('w') as proc:
    proc.write(str(pid))

##
## get_nrepl_pid
##
def get_nrepl_pid():
  procFile = get_proc_file()
  with procFile.open('r') as proc:
    return proc.read()
  return None

def does_pid_exist(pid):
  pid = int(pid)
  try:
    if (pid == 0):
      return False
    os.getpgid(pid)    
    return True
  except Exception as err:    
    print(err)
    return False

##
## terminate_nrepl_proc
##
def terminate_nrepl_proc():
  server_pid = get_nrepl_pid()
  if (server_pid != 0):
    stop_server(server_pid)
    save_nrepl_pid(0)

##
## is_nrepl_process_healthy
##
def is_nrepl_process_healthy():    
    host = configs_get(NREPL_HOST)
    port = configs_get(NREPL_PORT)

    client = start_client(host, port)    
    if client == False:
      return False

    pong = nrepl_ping(client)    
    if not pong:
      return False

    stop_client(client)
    return True

##
## is_nrepl_process_running`
##
def is_nrepl_process_running():  
  pid = get_nrepl_pid()  
  if pid == None:
    return False

  if not does_pid_exist(pid):
    return False

  if not is_nrepl_process_healthy(): # or fucked up    
    terminate_nrepl_proc()
    return False

  return True

##
## start_nrepl_process
##
def start_nrepl_process():
  if is_nrepl_process_running():    
    return True

  janet = configs_get(JANET_EXEC)
  host = configs_get(NREPL_HOST)
  port = configs_get(NREPL_PORT)
  server = start_server(janet, host, port)
  if server == False:
    return False
  pid = server.get('pid')  
  save_nrepl_pid(pid)
  return True

##
## set_nrepl_status_flag
##
def set_nrepl_status_flag(is_running):
  if is_running:
    update_status_message('janet nrepl server is running', 'jide', '█')
  else:
    update_status_message('janet nrepl server is not running', 'jide', '░')

##
## is_janet_installed
##
def is_janet_installed(janet):
  return shutil.which(janet) is not None

##
## is_jpm_installed
##
def is_jpm_installed(jpm):
  return shutil.which(jpm) is not None

##
## is_spork_installed
##
def is_spork_installed(jpm):
  with subprocess.Popen([jpm, JPM_OPT_LIST], stdout=subprocess.PIPE) as proc:
    pkgs = proc.stdout.read().decode('utf-8').split('\n')
    if JPM_LIB_SPORK in pkgs:      
      return True
  return False

##
## configs_ref
##
def configs_ref():
  return sublime.load_settings(DEFAULT_SETTINGS)

##
## configs_get
##
def configs_get(key):
  return configs_ref().get(key)

##
## configs_set
##
def configs_set(key, val):
  return configs_ref().set(key, val)

##
## update_status_message
##
def update_status_message(msg, key=None, val=None):
  windows = sublime.windows()
  for window in windows:
    if (key != None and val != None):
      view = window.active_view() 
      view.set_status(key, val)
    window.status_message(msg)

##
## is_janet_file
##
def is_janet_file(view):
  selection = view.sel()[-1]
  source = view.scope_name(selection.b)
  return source.strip().startswith('source.janet')


##
## format_code_section
##
def format_code_section(code):  
  janet = configs_get(JANET_EXEC)
  res = format_code(janet, code).decode()
  return res[:-1]

##
## get_file_completion
##
def generate_file_completion(file):
  global g_completion_list
  janet = configs_get(JANET_EXEC)
  g_completion_list = generate_completion(janet, file)
  print(g_completion_list)  
