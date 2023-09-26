from struct import pack
import sys
import threading
from src.FLM.package_exchange import socket_connect
from src.FLM.client_worker import client_worker
from src.FLM.utils.config import SERVER_IP, SERVER_PORT
from src.FLM.data_container import TCP_Package
from src.FLM.utils.logger import logger_client

#from Crypto.Cipher import AES
#CIPHER_KEY=b'bQeThWmZq4t7w!z%C*F-JaNdRfUjXn2r' #Shared Encryption/decryption Key
#NONCE=b'dRgUkXp2s5v8y/B?E(G+KbPeShVmYq3t' #shared NONCE key for validity

#clientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP socket creation
#clientA.connect((SERVER_IP, SERVER_PORT)) #TCP connection


#while True:
	# if CLIENTSIDE_CRYPTO:
	# 	Secret_Message_Input= getpass.getpass(prompt='Enter Secret Message.. : ' )
	# 	print("Message will Encrypt with AES")
	# 	print()
	# 	raw_message=Secret_Message_Input.encode() #Encode message to bytes
	# 	CIPHER = AES.new(CIPHER_KEY, AES.MODE_EAX, NONCE) #AES encryption using EAX mode with predefined cipher key and nonce key for validation
	# 	ciphertext, tag = CIPHER.encrypt_and_digest(raw_message)
	# 	print("Sending Encrypted Message:",ciphertext)
	# else:
	#	ciphertext = input("Please submit a test string\n")
		#if ciphertext == 'exit':
			#break
	#clientA.send(ciphertext).encode() #send ciphertext of raw message
	#clientA.close()#close socket
	#print()
	#break
#clientA.close()
#print('Message Sent..Goodbye')
#print()
 
class Client():

	def __init__(self):		
		self.socket = self._connect_to_server()
		self.packages = self._get_TEST_packages()
		self.logger = logger_client

	def __del__(self):
		try:
			self.socket.close()
		except:
			self.logger.warn("Connection close failed")
		

	def execute_TEST(self):
		try:
			answer = self._execute_command()[-1]
		except:
			self.logger.error('This command did not work')
		finally:
			return answer
		

	def _get_TEST_packages(self):
		#pkgList = [TCP_Package('Hello World of Sockets in Python')]
		#pkgList.append(TCP_Package('PYTHONCODE',create_remote_python_function()))

		#pkgList = [TCP_Package('PYTHONCODE','import sys; r=sys.version')]
		pkgList = [TCP_Package('ACQUIRE_Z',[30e-06,5e-06])]
		#pkgList = [TCP_Package('ACQUIRE_Z',[30e-06,15e-06])]
		return pkgList

	

	def _connect_to_server(self,ip=SERVER_IP, port=SERVER_PORT):
		try:
			s = socket_connect('client', ip, port)
		except Exception as ex:
			self.logger.exception(ex)
		except KeyboardInterrupt as ex:
			self.logger.exception(ex)
		except:
			self.logger.exception(sys.exc_info())
		finally:
			return s
	
	def _execute_command(self,package = None):
		# what advantage would threading bring?
		#threading.Thread(target=client_worker, args=(self.socket,self.packages,)).start()
		if package == None:
			package = self._get_TEST_packages()
		try:
		# get actions to do
			result = client_worker(self.socket,package)
		except:
			self.logger.error('This command did not work')
		finally:
			return result

	
	def get_single_image(self, autofocus = True, exposure_ms=100, intensity=0.9):
		'''Returns a single image from the server, intensity:]0.0;1.0]
		'''
		packages = []
		if autofocus:
			packages.append(TCP_Package("AUTOFOCUS"))
		
		packages.append(TCP_Package("SET_INTENSITY",int(intensity*255)))
		packages.append(TCP_Package("SET_EXPOSURE",exposure_ms))
		packages.append(TCP_Package("ACQUIRE"))
		
		return self._execute_command(packages)[-1]

	def get_z_stack(self,autofocus=True, exposure_ms=100, intensity=0.9, stack_params=[5e-6, .5e-6]):
		'''Returns a TZCYX formatted stack from the server, intensity:]0.0;1.0],
		stack_params =[stack_length stack_step]
		'''
		packages = []
		if autofocus:
			packages.append(TCP_Package("AUTOFOCUS"))
		
		packages.append(TCP_Package("SET_INTENSITY",int(intensity*255)))
		packages.append(TCP_Package("SET_EXPOSURE",exposure_ms))
		packages.append(TCP_Package("ACQUIRE_Z",stack_params))
		
		return self._execute_command(packages)[-1]

	def set_color(self,color):
		''' Tries to initialize a certain ex/em filter combination:
        'ref': Reflective, green excitation
        'UV': EX=UV, EM=green
        'green': EX=cyan
        'orange': EX=green
        'red': EX=red
        '''
		packages = []
		packages.append(TCP_Package("SET_FLUOCOLOR", color))		
		return self._execute_command(packages)[-1]

	def set_intensity(self, intensity=0.9):			
		'''Sets the intensity (]0.0;1.0])'''		
		packages = []
		packages.append(TCP_Package("SET_INTENSITY",int(intensity*255)))		
		return self._execute_command(packages)[-1]

	def set_exposure(self, exposure=100):	
		'''Sets the exposure [ms]'''	
		packages = []
		packages.append(TCP_Package("SET_EXPOSURE",exposure))		
		return self._execute_command(packages)[-1]



