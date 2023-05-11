import time, sys
from .data_container import TCP_Package
from .server_METEOR_wrapper import parsePackage
from .package_exchange import _send_package, _receive_package
from ..utils.logger import logger_server


def server_listener(conn,METEOR):
    try:
        conn.setblocking(True)
        while True:
            conn, pkg = _receive_package(conn,logger=logger_server)
            if not pkg:   
                time.sleep(1)
                continue
            elif pkg == TCP_Package('EXIT'):
                break
            else:
                logger_server.debug('Server received command: %s', pkg.cmd)
                pkg = parsePackage(pkg,METEOR)
                conn = _send_package(conn,pkg,logger=logger_server)

    except KeyboardInterrupt as ex:
        logger_server.exception(ex)
    except BrokenPipeError:
        logger_server.exception('Connection closed by client?')
    except Exception as ex:
        logger_server.exception('Exception:', ex, )	
    except:
        logger_server.exception(sys.exc_info())
    finally:
        conn.close()       
        logger_server.debug('Connection closed successfully')
        return

""" legacy versions
def handle_client(conn, addr):
    try:
        while True:
            message = conn.recv(TCP_BUFFER).decode()
            if message == '':                
                print("[DEBUG] Server received empty message!")
            else:
                print("[DEBUG] Server received:", message)
            if message == 'exit':  
                answer = 'Shutting down'                
                conn.sendall(answer.encode())
                print("[DEBUG] Server sent:", answer )
                break
            elif message.startswith('PYTHONCODE'):
                code = message.replace('PYTHONCODE ','')
                print("Executing code:",code)
                loc = {}
                exec(code, globals(), loc)
                if loc != {}:
                    answer = loc['r']

            elif message.startswith('ACQUIRE '):                
                filename = './test.tiff'    
                filesize = os.path.getsize(filename)   
                conn.send(filename.encode()) 
                while conn.recv(TCP_BUFFER).decode() != 'Received Data': time.sleep(0.01)	
                conn.send(str(filesize).encode())          
                #progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=512)
                with open(filename, "rb") as f:
                    while True:
                        # read the bytes from the file
                        bytes_read = f.read(TCP_BUFFER)
                        if not bytes_read:
                            # file transmitting is done
                            break
                        # we use sendall to assure transimission in 
                        # busy networks
                        conn.sendall(bytes_read)
                        # update the progress bar
                        #progress.update(len(bytes_read))
                
                answer = 'Success'
            else:
                answer = 'I don\'t know what to do with this chunk of garbage data'
            conn.sendall(answer.encode())
            print("[DEBUG] Server sent:", answer )
            time.sleep(1)
    except Exception as ex:
        print(ex)
    except KeyboardInterrupt as ex:
        print(ex)
    except BrokenPipeError:
        print('[DEBUG] addr:', addr, 'Connection closed by client?')
    except Exception as ex:
        print('[DEBUG] addr:', addr, 'Exception:', ex, )	
    except:
        print(sys.exc_info())
    finally:
        conn.close()
        return


def handle_server(s,msgList):
	try:
		while msgList != []:			
			msg = msgList.pop(0)
			s.send(msg.encode())
			print('sent:', msg)
			if msg.startswith('ACQUIRE '):				
				filename = s.recv(TCP_BUFFER).decode()
				s.send('Received Data'.encode())			
				filesize = int(s.recv(TCP_BUFFER).decode())
				filename = filename[0:2] + "2_" + filename [2:]
				print('Name and Size: ',(filename,filesize))
				#progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
				with open(filename, "wb") as f:
					end = filesize
					while end > 0:
						# read 1024 bytes from the socket (receive)
						bytes_read = s.recv(TCP_BUFFER)
						if not bytes_read:    
							# nothing is received
							# file transmitting is done
							break
						# write to the file the bytes we just received
						f.write(bytes_read)
						# update the progress bar
						#progress.update(len(bytes_read))
						end -= TCP_BUFFER
				answer = 'Transmission finished'
			else:
				answer = s.recv(TCP_BUFFER).decode()
			if answer:
				print('received:', answer)				
			if msg == 'exit':
				break
			print('--- sleep ---')			
			time.sleep(1)
	except Exception as ex:
		print(ex)
	except KeyboardInterrupt as ex:
		print(ex)
	except:
		print(sys.exc_info())
	finally:
		s.close()
"""