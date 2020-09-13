import subprocess
from .plg_utils import get_full_path


def format_code(janet, text):
  script = get_full_path('janet', 'format_code.janet')  
  cmd = [janet, script, '{}'.format(text).encode('utf-8')]
  try:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)    
    out, err = p.communicate()
    print(out)
    print(err)
    return out    
  except Exception as err:
    print('start: ', str(err))
    return False