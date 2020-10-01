import subprocess
from .sj_utilities import get_full_path

def get_installable_packages(jpm):
  cmd_update = [jpm, 'update-pkgs']
  cmd_list = [jpm, 'list-pkgs']
  try:    
    p = subprocess.Popen(cmd_update, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()    
  except Exception as err:
    return False
  try:    
    p = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()        
    return list(filter(lambda p: p != '' , out.decode().split(sep='\n')))
  except Exception as err:
    return False
