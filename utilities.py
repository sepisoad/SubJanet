import os
import sublime

def get_full_path(base, script):  
  return os.path.join(
      sublime.packages_path(),
      os.path.split(os.path.dirname(__file__))[1],
      base,
      script)