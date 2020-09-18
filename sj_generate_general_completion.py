import subprocess
from .sj_utilities import get_full_path

def generate_general_completion(janet):  
  script = get_full_path('janet', 'generate_general_completion.janet')
  cmd = [janet, script]
  try:    
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()        
    return out.decode().split(sep=' ')
  except Exception as err:
    print('start: ', str(err))
    return False