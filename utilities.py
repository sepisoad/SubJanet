import os
import sublime

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
