import sys
import threading
from communication.server_listener import server_listener
from communication.package_exchange import socket_connect
from utils.config import SERVER_IP, SERVER_PORT, LOCAL_DEV
from utils.logger import logger_server

#import odemis wrapper from Sven
from FLM import FLM

#Crypto Stuff
#from Crypto.Cipher import AES
#CIPHER_KEY=b'bQeThWmZq4t7w!z%C*F-JaNdRfUjXn2r' #Shared Key 32 bytes for 256-bit encryption
#NONCE=b'dRgUkXp2s5v8y/B?E(G+KbPeShVmYq3t' #shared nonce key for validation. 

try:
    s = socket_connect(state='server',ip=SERVER_IP, port=SERVER_PORT, maxNumClients=2)

    #connect to METEOR
    try:
        METEOR = FLM()
    except:   
        METEOR = None

    while True:
        # --- accept client ---

        # accept client and create new socket `conn` (with different port) for this client only
        # and server will can use `s` to accept other clients (if you will use threading)
        logger_server.debug('accept ... waiting, press ctrl+C to stop')
        conn, addr = s.accept() # socket, address
        logger_server.debug(' addr: %s', addr)
        #old t = threading.Thread(target=handle_client, args=(conn))


        #Add threaded listerner loop to process data for this server-client connection. 
        t = threading.Thread(target=server_listener, args=(conn,METEOR,))
        t.start()
except Exception as ex:
    logger_server.exception(ex)
except KeyboardInterrupt as ex:
    logger_server.exception(ex)
except:
    logger_server.exception(sys.exc_info())
finally:
    # --- close socket ---
    s.close()
    logger_server.exception('socket closed')    
    METEOR.disconnect()