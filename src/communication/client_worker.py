import time, sys, os
from src.communication.data_container import TCP_Package
import datetime
from src.utils.logger import logger_client
from src.utils.config import SAVE_DEBUGGING_IMAGES
from src.communication.package_exchange import _send_package, _receive_package
import numpy as np
import tifffile as tif

def client_worker(conn,pkgList):
    try:
        data = ()
        conn.setblocking(True)
        while pkgList != []:
            pkg = pkgList.pop(0)
            logger_client.debug('Client asked for: %s', pkg.cmd)
            _send_package(conn,pkg,logger=logger_client)
            conn, pkg = _receive_package(conn,logger=logger_client)
            logger_client.debug('Server answered: %s', pkg.cmd)
            if not pkg:
                time.sleep(1)
                continue
            else:
                data = data + ( parse_client_package(pkg), )
                #data = parse_client_package(pkg)
        pkg = TCP_Package('EXIT')
        logger_client.debug('Client asked for: %s', pkg.cmd)
        _send_package(conn,pkg)

    except KeyboardInterrupt as ex:
        logger_client.exception(ex)
    except BrokenPipeError:
        logger_client.exception('Connection closed by client?')
    except Exception as ex:
        logger_client.exception('Exception:', ex, )
    except:
        logger_client.exception(sys.exc_info())
    finally:
        conn.close()
        logger_client.debug('Connection closed successfully')
        return data


def parse_client_package(p,logger=logger_client):
    if  not isinstance(p,TCP_Package):
        logger.error("Unrecognized or corrupted package")
        return -1
    elif p.cmd == 'RESULT PYTHONCODE':
        print("\n\nPYTHON RESULT:\n" + str(p.data) + "\n\n")
        return p.data
    elif p.cmd == "STATE":
        if p.data == 0:
            return 0
    elif p.cmd == 'IMAGE':
        img = stream_2_Image(p,logger)
        if SAVE_DEBUGGING_IMAGES:
        #process received image
            filename = os.path.join( os.getcwd(), "img", datetime.datetime.now().strftime("%y_%m_%d-%H_%M_%S") + ".tiff")
            import cv2
            cv2.imwrite(filename,img)
        return img
    elif p.cmd == 'ZSTACK':
        #process stack        
        stack = stream_2_Image(p,logger)
        if SAVE_DEBUGGING_IMAGES:
        #filename = os.path.join( os.getcwd(), "stack", datetime.datetime.now().strftime("%y_%m_%d-%H_%M_%S") + ".tif")
            filename =r'D:/SharedData/FluoStacks/' + datetime.datetime.now().strftime("%y_%m_%d-%H_%M_%S") + r'.tif'

            z_distance = 4.0  # TODO set correctly
            stack_order = 'TZCYX'  # obviously cannot be changed...
            fps = 10.0
            tif.imsave(filename, stack, imagej=True, resolution=(1.0/4.107142857142857e-02, 1.0/4.107142857142857e-02), \
                    photometric='minisblack', \
                    metadata={'spacing': z_distance, 'unit': 'um', 'axes': stack_order, 'finterval': fps})
        return stack
    else:
        return TCP_Package('Unrecognized command')

def stream_2_Image(package,logger=logger_client):
    stream = np.frombuffer(package.data, dtype=package.NP_dtype)
    img = np.reshape(stream,package.NP_shape)
    # setup stack in obviously unchangeable "TZCYX" dimensions for imagej hyperstack format
    #img = np.moveaxis(img, -2, -3)
    #img = np.expand_dims(img, axis=0)
    #img = np.moveaxis(img, -1, 0)
    #img = np.expand_dims(img, axis=0)
    logger.debug("Numpy shape before: %s", (np.shape(stream)))
    logger.debug("Numpy shape after: %s", (np.shape(img)))
    return img