import subprocess
import time
import os
import signal

def is_running():
  pass

def start(janet, host, port, env=None):
  imports = '(import spork/netrepl) (import spork/fmt) (defn ping [] "pong")'
  default_env = '(fiber/getenv (fiber/current))'
  cmd = [janet, '-e']
  if(env):
    cmd.append('{} (netrepl/server "{}" "{}" "{}")'.format(imports, host, port, env))
  else:
    cmd.append('{} (netrepl/server "{}" "{}" {})'.format(imports, host, port, default_env))
  try:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    server = {'pid': p.pid, 'host': host, 'port': port, 'env': env }
    time.sleep(1)
    return server
  except Exception as err:
    print('start: ', str(err))
    return False

def stop(pid):
  try:    
    pid = int(pid)
    if (pid == 0):
      return False
    os.kill(pid, signal.SIGTERM)  
  except Exception as err:
    print('stop: ', str(err))
    return False