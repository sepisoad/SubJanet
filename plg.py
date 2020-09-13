import pathlib
import subprocess
import os
import shutil
import signal
import sublime
import sublime_plugin

from .plg_format_code import format_code
from .plg_generate_completion import generate_completion

#   _____ _      ____  ____          _       _____
#  / ____| |    / __ \|  _ \   /\   | |     / ____|
# | |  __| |   | |  | | |_) | /  \  | |    | (___
# | | |_ | |   | |  | |  _ < / /\ \ | |     \___ \
# | |__| | |___| |__| | |_) / ____ \| |____ ____) |
#  \_____|______\____/|____/_/    \_\______|_____/

DEFAULT_SETTINGS = 'subjanet.sublime-settings'
PLUGIN_TEMP_DIR = 'subjanet'
PLUGIN_REPL_PROC = 'repl-proc'
JANET_EXEC = 'janet_executable'
JPM_EXEC = 'jpm_executable'
JPM_OPT_LIST = 'list-installed'
JPM_LIB_SPORK = 'spork'
g_completion_list = []

#   _____ ____  __  __ __  __          _   _ _____   _____
#  / ____/ __ \|  \/  |  \/  |   /\   | \ | |  __ \ / ____|
# | |   | |  | | \  / | \  / |  /  \  |  \| | |  | | (___
# | |   | |  | | |\/| | |\/| | / /\ \ | . ` | |  | |\___ \
# | |___| |__| | |  | | |  | |/ ____ \| |\  | |__| |____) |
#  \_____\____/|_|  |_|_|  |_/_/    \_\_| \_|_____/|_____/

##
## SubjanetFormatCommand
##
class SubjanetFormatCommand(sublime_plugin.TextCommand):
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

#  ________      ________ _   _ _______ _____
# |  ____\ \    / /  ____| \ | |__   __/ ____|
# | |__   \ \  / /| |__  |  \| |  | | | (___
# |  __|   \ \/ / |  __| | . ` |  | |  \___ \
# | |____   \  /  | |____| |\  |  | |  ____) |
# |______|   \/   |______|_| \_|  |_| |_____/

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

#  _      _____ ______ ______ _______     _______ _      ______
# | |    |_   _|  ____|  ____/ ____\ \   / / ____| |    |  ____|
# | |      | | | |__  | |__ | |     \ \_/ / |    | |    | |__
# | |      | | |  __| |  __|| |      \   /| |    | |    |  __|
# | |____ _| |_| |    | |___| |____   | | | |____| |____| |____
# |______|_____|_|    |______\_____|  |_|  \_____|______|______|

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

##
## plugin_unloaded
##
def plugin_unloaded():
  pass

#  _      ____   _____ _____ _____  _____
# | |    / __ \ / ____|_   _/ ____|/ ____|
# | |   | |  | | |  __  | || |    | (___
# | |   | |  | | | |_ | | || |     \___ \
# | |___| |__| | |__| |_| || |____ ____) |
# |______\____/ \_____|_____\_____|_____/

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
