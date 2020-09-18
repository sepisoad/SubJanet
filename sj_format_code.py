import subprocess
from .sj_utilities import get_full_path


def format_code(janet, text):
  script = get_full_path('janet', 'format_code.janet')  
  cmd = [janet, script, '{}'.format(text).encode('utf-8')]
  try:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)    
    out, err = p.communicate()
    return out
  except Exception as err:
    print('start: ', str(err))
    return False