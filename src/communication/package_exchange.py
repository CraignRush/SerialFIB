from asyncio import protocols
import sys
import socket, pickle
import time
import tqdm
from src.utils.config import CODEC, PICKLE_PROTOCOL, TCP_BUFFER, DISPLAY_PROGESS
from src.communication.data_container import TCP_Package
from src.utils.logger import logger_client, logger_server
import codecs

def unpack(package):
    return pickle.loads(codecs.decode(package, encoding=CODEC)) #protocol is detected automatically


def socket_connect(state='server', ip='127.0.0.1', port=9000, maxNumClients=2):
    try:
        # --- create socket ---
        if state == 'server':
            logger_server.debug('create socket')
        else:
            logger_client.debug('create socket')
        s = socket.socket(socket.AF_INET,
                          socket.SOCK_STREAM)  # default value is (socket.AF_INET, socket.SOCK_STREAM) so you don't have to use it

        # solution for "[Error 89] Address already in use". Use before bind()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if state == 'server':
            # --- assign socket to local IP (local NIC) ---
            logger_server.debug('Server bind: %s , %s', ip, port)
            s.bind((ip, port))  # one tuple (HOST, PORT), not two arguments
            # --- set size of queue ---
            logger_server.debug('Server listen')
            s.listen(maxNumClients)  # number of clients waiting in queue for "accept".
            # If queue is full then client can't connect.
        elif state == 'client':
            # --- connect to server ---
            logger_client.debug('Client connect: %s , %s', ip, port)
            s.connect((ip, port))  # one tuple (HOST, PORT), not two

        else:
            raise Exception('only state \'client\' or \'server\' allowed')

    except Exception as ex:
        logger_client.exception(ex)
    finally:
        return s

def _send_package(conn, data, encode=True, logger=logger_server):
    try:
        if encode and not isinstance(data,TCP_Package):
            dataEncoded = codecs.encode(pickle.dumps(data, protocol=PICKLE_PROTOCOL),encoding=CODEC)
        elif isinstance(data,TCP_Package):
            dataEncoded = data.encode()
        else:
            dataEncoded = data

        while True:
            # get data length
            length = len(dataEncoded)
            # logger.debug('Data length: %s', str(length))

            # send length
            conn.sendall(TCP_Package('BYTES TO SEND', length).encode())
            logger.debug('Sent BYTES TO SEND: %s', str(length))
            # receive acceptance
            answer = unpack(conn.recv(TCP_BUFFER))
            logger_server.debug('Client Answer: %s', answer.cmd)
            if answer == TCP_Package('READY TO RECEIVE'):
                if DISPLAY_PROGESS:
                    progress = tqdm.tqdm(range(length), "Sending " + str(data.cmd), unit="B", unit_scale=True, unit_divisor=1024, delay=0)
                logger.debug('Starting to transmit')
                # start sending data

                while True:
                    if len(dataEncoded) > TCP_BUFFER:
                        # if len(dataEncoded) < 5000:
                        #    time.sleep(1)
                        # read the bytes from the file
                        bytesToSend = dataEncoded[0:TCP_BUFFER - 1]
                        if not bytesToSend:
                            # file transmitting is done
                            break
                        # we use sendall to assure transimission in
                        # busy networks
                        conn.sendall(bytesToSend)
                        # update the progress bar
                        if DISPLAY_PROGESS:
                            progress.update(len(bytesToSend))
                        dataEncoded = dataEncoded[TCP_BUFFER - 1:]
                    else:
                        bytesToSend = dataEncoded
                        # we use sendall to assure transimission in
                        # busy networks
                        conn.sendall(bytesToSend)
                        # update the progress bar
                        if DISPLAY_PROGESS:
                            progress.update(len(bytesToSend))
                        break
                    #time.sleep(0.4)
                logger.debug('Transmission finished')
                try:
                    result = unpack(conn.recv(TCP_BUFFER))
                finally:
                    if result == TCP_Package('SUCCESS'):
                        break

    except KeyboardInterrupt as ex:
        logger.error(ex)
    except BrokenPipeError:
        logger.error('Connection closed by client?')
    except Exception as ex:
        logger.error('Exception:', ex, )
    except:
        logger.error(sys.exc_info())
    finally:
        return conn


def _receive_package(conn, logger=logger_server):
    try:

        pkg = unpack(conn.recv(TCP_BUFFER))
        if not isinstance(pkg, TCP_Package):
            logger.debug("Received empty message!")
            package = None
        elif pkg.cmd == 'EXIT':
            answer = 'Exiting'
            conn.sendall(answer.encode())
            logger.debug("Exiting")
            package = None
        elif pkg.cmd == 'BYTES TO SEND':
            dataSize = int(pkg.data)
            conn.sendall(TCP_Package('READY TO RECEIVE').encode())
            logger.debug("Sent READY TO RECEIVE")
            #data = bytes(dataSize)
            if DISPLAY_PROGESS:
                progress = tqdm.tqdm(range(dataSize), "Receiving ", unit="B", unit_scale=True, unit_divisor=1024, delay=0)
            data = bytearray()
            while len(data) < dataSize:
                chunk = conn.recv(dataSize - len(data))
                if not chunk:
                    break
                data.extend(chunk)

                # read 4096 bytes from the socket (receive)
                #bytesRead = conn.recv(TCP_BUFFER)
                #if not bytesRead:
                    # nothing is received
                    # file transmitting is done
                #    break
                # write to the file the bytes we just received
                #recvLength = len(bytesRead)
                #data[n:recvLength+n-1] = bytesRead
                #n += recvLength

                #if (n+bytesRead == dataSize):
                #    break
                # update the progress bar
                if DISPLAY_PROGESS:
                    progress.update(len(chunk))
            # TODO handle case where transmission was not successful
            logger.debug('Sent SUCCESS')
            conn.sendall(TCP_Package('SUCCESS').encode())

            package = unpack(data)

    except KeyboardInterrupt as ex:
        logger.error(ex)
    except BrokenPipeError:
        logger.error('Connection closed by client?')
    except Exception as ex:
        logger.error('Exception:', ex, )
    except:
        logger.error(sys.exc_info())
    finally:
        return conn, package
