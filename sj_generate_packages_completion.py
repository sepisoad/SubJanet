import subprocess
from .sj_utilities import get_full_path

def generate_packages_completion(jpm):
  cmd = [jpm, 'list-installed']
  try:    
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()        
    return list(filter(lambda p: p != '' , out.decode().split(sep='\n')))
  except Exception as err:
    return False