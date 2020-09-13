import socket

def start(host, port, name='#', timeout=0):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  if (timeout > 0):
    s.settimeout(3)
  port = int(port)
  try:
    s.connect((host, port))
    client = {'socket': s, 'host': host, 'port': port, 'name': name }
    send(client, name)
    recv(client)
    return client
  except Exception as err:
    print('start: ', str(err))
    return False  

def stop(client):
  try:
    s = client['socket']
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    return True
  except Exception as err:
    print('stop: ', str(err))
    return False

def send(client, msg):
  try:
    if (msg == ''):
      return None    
    s = client['socket']
    length = len(msg)
    # prefix = chr(length & 0xFF) + chr((length >> 8) & 0xFF) + chr((length >> 16) & 0xFF) + chr((length >> 24) & 0xFF)    
    prefix = ''.join(
      map(lambda x: chr(x), 
      [(length & 0xFF),  ((length >> 8) & 0xFF), ((length >> 16) & 0xFF), ((length >> 24) & 0xFF)]))
    msg = (prefix + msg).encode('utf-8')
    s.send(msg)    
    return True
  except Exception as err:
    print('send: ', str(err))
    return False

def recv(client):
  try:
    s = client['socket']
    byte1, byte2, byte3, byte4 = s.recv(4)
    length = byte1 + (byte2 * 0x100) + (byte3 * 0x10000) + (byte4 * 0x1000000)          
    if (length < 1):      
      return False    
    response = s.recv(length)    
    return response.decode('utf-8').strip('\n').strip('\t')
  except Exception as err:
    print('recv: ', str(err))
    return False

def commit(client, msg):
  send(client, msg)
  response = recv(client)
  prompt  = recv(client)  
  return response

def ping(client):
  pong = commit(client, '(ping)')
  if not pong:
    return False
  pong = (pong.strip())
  return pong == '"pong"'

