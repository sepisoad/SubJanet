import re
import os
import subprocess
import shutil
import signal
import sublime
import sublime_plugin

from .sj_format_code import format_code
from .sj_format_file import format_file
from .sj_generate_module_completion import generate_module_completion as generate_module_completion_ex
from .sj_generate_builtin_completion import generate_builtin_completion as generate_builtin_completion_ex

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
NO_COMPLETION = ([], sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
DEFAULT_COMPLETION = []


##
## CompletionMap
##
class CompletionMap():
  builtin = {}
  module = {}

  def __init__(self):
    self.builtin = {}
    self.module = {}

  def flush(self):
    self.builtin.clear()
    self.module.clear()

  def update_builtin(self, symbol):    
    self.builtin.update({ symbol : symbol })

  def update_module(self, file, symbol):
    if not file in self.module:
      self.module.update({ file : {} })
    self.module[file].update({ symbol : symbol })

  def clear_module(self, file):
    if file in self.module:
      self.module[file].clear()

  def get_builtin(self):    
    return self.builtin

  def get_module(self, file):
    if not file in self.module:
      return {}
    return self.module[file]

g_completion_map = CompletionMap()

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
  global g_completion_map
  g_completion_map.flush()
  generate_builtin_completion()
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
  global g_completion_map
  g_completion_map.flush()

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
      return    
    file_size = self.view.size()
    selection = self.view.substr(sublime.Region(0, file_size))
    formatted = format_code_section(selection)
    if not formatted:
      return
    self.view.replace(edit, sublime.Region(0, file_size), formatted)

##
## SubjanetFormatFileCommand
##
class SubjanetFormatFileCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    if not is_janet_file(self.view):
      return    
    janet = configs_get(JANET_EXEC)
    file = self.view.file_name()
    format_file(janet, file)

#  ________      ________ _   _ _______ _____
# |  ____\ \    / /  ____| \ | |__   __/ ____|
# | |__   \ \  / /| |__  |  \| |  | | | (___
# |  __|   \ \/ / |  __| | . ` |  | |  \___ \
# | |____   \  /  | |____| |\  |  | |  ____) |
# |______|   \/   |______|_| \_|  |_| |_____/

class SubjanetEvents (sublime_plugin.ViewEventListener):  
  def on_post_save_async(self):
    file = self.view.file_name()
    if not is_janet_file(self.view):
      return
    if configs_get('format_on_save'):
      janet = configs_get(JANET_EXEC)      
      format_file(janet, file)
    global g_completion_map
    g_completion_map.clear_module(file)
    generate_module_completion(self.view.file_name())

  def on_activated_async(self):
    if not is_janet_file(self.view):
      return
    generate_module_completion(self.view.file_name())  

  def on_query_completions(self, prefix, location):    
    if not is_janet_file(self.view):
      return DEFAULT_COMPLETION

    view = self.view
    file = view.file_name()    
    current_pos = view.sel()[0]
    if current_pos.empty():
      current_line = view.line(current_pos)
      current_line_text = view.substr(current_line)      
      prefix_new = current_line_text.split()[-1].replace('(', '').replace(')', '').strip()      
      suggestions = generate_suggestions(file, prefix_new)
      completions = generate_suggestions_tuple(suggestions)      
      return completions
    
    prefix = re.sub(r'[\(\)\.\,\;\'\[\]\:\"]', '', prefix)
    if (prefix == '' or len(prefix) < 2):
      return NO_COMPLETION
    
    suggestions = generate_suggestions(file, prefix)
    completions = generate_suggestions_tuple(suggestions)
    return completions

  def on_modified_async(self):    
    if not is_janet_file(self.view) or self.view.is_auto_complete_visible():
      return

    view = self.view
    file = view.file_name()
    current_pos = view.sel()[0]
    current_line = view.line(current_pos)
    current_line_text = view.substr(current_line)
    if len(current_line_text) < 1:
      return
    prefix_new = current_line_text.split()[-1].replace('(', '').replace(')', '').strip()      
    suggestions = generate_suggestions(file, prefix_new)
    if len(suggestions) > 1:
      view.run_command('auto_complete', {
        'disable_auto_insert': True,
        'api_completions_only': False,
        'next_competion_if_showing': True})

#  _      ____   _____ _____ _____  _____
# | |    / __ \ / ____|_   _/ ____|/ ____|
# | |   | |  | | |  __  | || |    | (___
# | |   | |  | | | |_ | | || |     \___ \
# | |___| |__| | |__| |_| || |____ ____) |
# |______\____/ \_____|_____\_____|_____/

##
## get_full_path
##
def get_full_path(base, script):  
  return os.path.join(
    sublime.packages_path(),
    os.path.split(os.path.dirname(__file__))[1],
    base,
    script)

##
## is_janet_file
##
def is_janet_file(view):
  selection = view.sel()[-1]
  source = view.scope_name(selection.b)
  return source.strip().startswith('source.janet')

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
## generate_builtin_completion
##
def generate_builtin_completion():
  global g_completion_map
  janet = configs_get(JANET_EXEC)
  symbols = generate_builtin_completion_ex(janet)
  for symbol in symbols:
    if symbol.strip() != '':
      g_completion_map.update_builtin(symbol)

##
## generate_module_completion
##
def generate_module_completion(file):
  global g_completion_map
  janet = configs_get(JANET_EXEC)
  symbols = generate_module_completion_ex(janet, file)
  for symbol in symbols:
    if symbol.strip() != '':
      g_completion_map.update_module(file, symbol)

##
## generate_suggestions 
##
def generate_suggestions(file, prefix):
  global g_completion_map
  symbols = g_completion_map.get_builtin().copy()
  symbols.update(g_completion_map.get_module(file))  
  filtered_items = list(filter(lambda str: str.startswith(prefix), symbols))
  return filtered_items

##
## make_suggestion_tuple
##
def generate_suggestions_tuple(suggestions):
  items_dict = {}
  for item in suggestions:
    items_dict.update({ item: item })    
  suggestion = [(k, v) for k, v in items_dict.items()]  
  return suggestion
