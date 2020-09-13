import subprocess
from .utilities import get_full_path


def format_file(janet, file):
  script = get_full_path('janet', 'format_file.janet')  
  cmd = [janet, script, file]  
  try:
    p = subprocess.Popen(cmd)
    p.communicate()    
  except Exception as err:
    print('start: ', str(err))
    return False