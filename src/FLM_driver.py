### ODEMIS IMPORTS ###
try:
    from odemis.driver.smaract import MCS2
    from odemis.driver.ueye import Camera
    from odemis.driver.lle import LLE
    from odemis.driver.tmcm import TMCLController
except ImportError:
    pass

### SOFTWARE IMPORTS ###

# from msilib.schema import Error
from src.FLM.utils.logger import logger_server
import src.FLM.utils.config as config
import matplotlib.pyplot as plt
import numpy as np
import time
import os
import datetime
from copy import deepcopy
from numpy import save
import tifffile as tif


class FLM():  # ,CAMERA_CONFIG):
    def __init__(self):
        self.error_state = 0

        # Get the config parameters as class variables
        self.__CONFIG_CAMERA__ = config.CAMERA
        self.__CONFIG_3DOF__ = config.FOCUS
        self.__CONFIG_LIGHTSOURCE__ = config.LIGHTSOURCE
        self.__CONFIG_FILTERWHEEL__ = config.FILTERWHEEL

        # Connect to every hardware device of METEOR
        try:
            self.focus_dev = MCS2(**self.__CONFIG_3DOF__)
            # self.focus_dev.position.value
            self.cam_dev = Camera(**self.__CONFIG_CAMERA__)
            self.light_dev = LLE(**self.__CONFIG_LIGHTSOURCE__)
            self.filter_dev = TMCLController(**self.__CONFIG_FILTERWHEEL__)
            self.light_enabled_sources = []
        except NameError:
            logger_server.debug("Could not find the specified components")
            logger_server.debug("{}".format(e))
            self.error_state = 1
        except Exception as e:
            logger_server.error("Error during connection to a component")
            logger_server.debug("{}".format(e))
            self.error_state = 1
    
        # Get the fluorescence parameters from the config
        self._emission_rad = config.EMISSION_RAD
        self._excitation = config.EXCITATION
        self._emission = config.EMISSION
        self.channel = {
            'reflection': {'ex': self._excitation['cyan'],  'em': self._emission['ref']},
            'uv': {'ex': self._excitation['UV'],     'em': self._emission['green']},
            'green': {'ex': self._excitation['cyan'],   'em': self._emission['green']},
            'orange': {'ex': self._excitation['green'],   'em': self._emission['orange']},
            'red': {'ex': self._excitation['red'],    'em': self._emission['red']},
        }

        # Get the camera parameters from the device
        self.pixel_count = self.cam_dev.resolution.value #tuple (2456,2054)
        # Setting some default parameters #TODO write an own setter
        self.__pixel_size = self.cam_dev.pixelSize.value #tuple (3.45e-06, 3.45e-06)
        self.__pixel_unit = self.cam_dev.pixelSize.unit #'m'
        if self.__pixel_unit == 'm':
            self.__resolution = np.divide(1.0, self.__pixel_size)

        # Start lightsource and set initial values
        self.light_enabled_sources = []
        self.light_set_channel('reflection', 8.)
        self.cam_exposure = 0.01
        self.cam_set_exposure(self.cam_exposure)

        # A little dangerous: Initializing the autofocus with a saved "rough" focus position
        self.autofocus_result: dict = {'z': config.ROUGH_FOCUS_POS}
        
        # Bring the objective in a safe state
        self.focus_goto_safe()
        logger_server.debug("METEOR connection finished!")

    def disconnect(self):
        '''
        Disconnects all physical devices from the class. 
        '''
        try:
            self.focus_goto_safe()
            self.focus_dev.terminate()
        except Exception as e:
            logger_server.error("Focussing device could not be terminated")
            logger_server.debug("{}".format(e))
            self.error_state = 1

        try:
            self.light_disable_all()
            self.light_dev.terminate()
        except Exception as e:
            logger_server.error("Lumencor Lightengine could not be terminated")
            logger_server.debug("{}".format(e))
            self.error_state = 1

        try:
            self.filter_dev.terminate()
        except Exception as e:
            logger_server.error("Filter wheel could not be terminated")
            logger_server.debug("{}".format(e))
            self.error_state = 1

        try:
            self.cam_dev.terminate()
        except Exception as e:
            logger_server.error("uEye Camera could not be terminated")
            logger_server.debug("{}".format(e))
            self.error_state = 1

        if self.error_state == 0:
            logger_server.debug(
                "Disconnected gracefully, no need to restart the XT-server!")
        else:
            logger_server.debug(
                "Disconnected with a error,I could be wise to restart the XT-server! (unless you know what you're doing)")

        return

### FOCUS FUNCTIONS ###
    def focus_goto_safe(self):
        self.focus_set_abs({'z': -0.9e-03})
        return ()

    def focus_get_position(self) -> dict:
        return (self.focus_dev.position.value)

    def focus_set_abs(self, pos: dict):
        '''
        Drives to an absolute focus position, blocks the execution
        pos: dict {z: position}
        '''
        task = self.focus_dev._createMoveFuture()
        self.focus_dev._doMoveAbs(task, pos)

    def focus_set_rel(self, pos):
        '''
        Drives to a relative focus position, blocks the execution  
        pos: dict {z: position}
        '''
        task = self.focus_dev._createMoveFuture()
        self.focus_dev._doMoveRel(task, pos)

    def focus_stop(self):
        self.focus_dev.stop()

# LIGHT SOURCE FUNCTIONS:
    def light_set_channel(self, channel='reflection', intensity=20.):
        '''
        Top-level wrapper to set a certain channel configuration.
        Sets a certain _excitation source and _emission filter combination
        channel: 'reflection': EX=green, EM=None
                 'UV': EX=UV, EM=green
                 'green': EX=cyan, EM= green
                 'orange': EX=green, EM=orange
                 'red': EX=red, EM=red
        intensity: float, light intensity in percent (0-100)
        '''
        try:

            logger_server.debug('requested channel: {}'.format(channel))
            self.light_set_filter_wheel(self.channel[channel]['em'])
            self.light_disable_all()  # clean start
            self.light_set_source(channel, intensity)
            return
        except Exception as e:
            logger_server.error('Could not set channel')
            logger_server.debug('{}'.format(e))
            return -1

    def light_set_filter_wheel(self, val: int):
        '''
        Low-level function to set a certain filter-wheel angle in radians.
        val: Integer selection of predefined position.
        '''
        try:
            task = self.filter_dev._createMoveFuture()
            self.filter_dev._doMoveAbs(task, {"fw": self._emission_rad[val]})
        except Exception as e:
            logger_server.error('Move to {} by the filter wheel failed.'.format(
                {"fw": self._emission_rad[val]}))
            logger_server.debug('{}'.format(e))
        return

    def light_set_source(self, channel: str, intensity: float):
        '''
        Top-level wrapper for LED selection. Activates a specific LED and sets its intensity.
        channel: Selection from 'reflection', 'UV', 'green', 'orange', 'red'
        intensity: Brightness of LED, float, 0 - 100 (%)
        '''
        intensity = int(np.round(intensity / 100 * 255)
                        )  # scale intensity from percent to 8bit int for odemis api
        source = self.channel[channel]['ex']
        if source in self.light_enabled_sources:
            self.light_dev._setSourceIntensity(source, intensity)
        else:
            self.light_enable(source)
            self.light_dev._setSourceIntensity(source, intensity)
        return ()

    def light_enable(self, source):
        '''
        Enables a specific light source (LED).
        '''
        self.light_dev._enableSources([source])
        self.light_enabled_sources.append([source])
        return ()

    def light_get_intensity(self):
        '''
        Get the current light intensitv of green and yellow
        '''
        return (self.light_dev._getIntensityGY())

    def light_disable_all(self):
        '''
        Switches all light sources to the intensity 0
        '''
        chans = list(self._excitation.keys())
        for i in range(len(chans)):
            # logger_server.info('Resetting channel: {}'.format(chans[i]))
            self.light_disable_single(chans[i])
        return

    def light_disable_single(self, excitation_channel: str):
        '''
        Disables a single light source by setting the intensity to zero.
        '''
        try:
            self.light_dev._setSourceIntensity(
                self._excitation[excitation_channel], 0)
        except Exception as e:
            logger_server.error(
                'Setting source {} to zero'.format(excitation_channel))
            logger_server.debug('{}'.format(e))
        return

    def light_shutdown(self):
        '''
        Kills the light source
        '''
        # TODO not right, disconnects from the source
        self.light_dev.terminate()
        return ()


### CAMERA FUNCTIONS ###

    def cam_get_image(self):
        '''
        Acquire an image with the camera.
        Start the generation of images, resets the capture status, 
        gets an image when the camera is ready (thread-safe) and stops the acquisition again
        '''
        
        #tic = time.time()
        self.cam_dev.start_generate()
        self.cam_dev.ResetCaptureStatus()
        img = self.cam_dev.data.get(asap=False)
        self.cam_dev.stop_generate()
        #toc = time.time() - tic

        return (img)

    def cam_get_exposure(self):
        '''
        Get the camera exposure time im s
        '''
        return (self.cam_dev.exposureTime.value)

    def cam_set_exposure(self, exp, gain=1):
        '''
        Sets the camera exposure time in s
        exp: exposure time in s
        gain: camera gain factor
        '''
        self.cam_exposure = exp
        try:
            # self.cam_dev.SetHardwareGain(gain) #master gain, and single RGB gains
            self.cam_dev._setExposureTime(exp)  # exposure in secs
            logger_server.error('Measuredxposure time: {} s'.format(
                self.cam_dev.GetExposure()))
        except Exception as e:
            logger_server.error(
                'Setting gain to {} and exposure to {}'.format(gain, exp))
            logger_server.debug('{}'.format(e))
        return ()
    

    def cam_set_binning(self):
        '''
        Not implemented yet
        '''
        logger_server.info("binning is not implemented yet")
        # _setBinning(value) e.g. (1,1)
        return ()


# Stack Acquisition functions

    def get_raw_stack(self, step: float = 1e-6, slices: int = 1, focusPos: dict ={'z': 10.3e-3}):
        '''
        Lowlevel stack acquistion. Drives to the supplied focus postion, captures an 
        stack symmetrically around the 0 position with the numer of slices in the step(-size), finally returns to the
        original focus position. 
        step: Stack step size
        slices: int, total number of stack slices
        focusPos= dict, {'z': absoluteZPos} absolute focus position of center slice
        Returns: XYZ formatted, np.uint16 array.
        '''
        self.focus_set_abs(focusPos)
        pos = self.focus_get_position()['z']
        stack = np.zeros(
            (self.pixel_count['x'], self.pixel_count['y'], slices), dtype='uint16')

        try:
            for slice in range(slices):
                ipos = pos + (slice - slices // 2) * step
                self.focus_set_abs({'z': ipos})
                stack[:, :, slice] = np.transpose(self.cam_get_image()).astype(np.uint16)
        except:
            # TODO do something smart here
            self.focus_goto_safe()
            pass
        finally:
            # return to original position
            self.focus_set_abs({'z': pos})

        # Transform stack due to optics transposition and mirroring
        # for a TZCYX stack you would need to do
        # np.flip(np.transpose(stack[0,:,0,:,:], axes=(2,1,0)), axis=0)
        # for an xyz stack as here you need to mirror the stack along the horizontal-axis
        stack = np.flip(stack, axis=0)
        return stack

    def save_stack_imagej(self, stack, filename, z_distance=4.0):
        '''
        Saves a preformatted stack in TZCYX order with the microscope scaling and ImageJ formatting.
        '''
        stack_order = 'TZCYX'  # obviously cannot be changed...
        fps = 10.0
        tif.imwrite(filename, stack, imagej=True, shaped=True, resolution=self.__resolution,
                    photometric='minisblack',
                    metadata={'spacing': z_distance*1e6, 'unit': 'um', 'axes': stack_order, 'finterval': fps})
        print(filename)
        return

    def save_stack_ome(self, stack, filename, pixel_z, exposure_time=0.01, fps=1):
        '''
        Saves a preformatted stack in TZCYX order with the microscope scaling as ome-tif.
        stack: arbitrary filename, has to end with .ome.tif
        '''
        stack_order = 'TZCYX'  # obviously cannot be changed...

        tif.imwrite(filename, stack, photometric='minisblack',
                    metadata={'PhysicalSizeZ': pixel_z*1e6, 'PhysicalSizeXUnit': 'microns', 'PhysicalSizeYUnit': 'microns', 'PhysicalSizeZUnit': 'microns',
                              'axes': stack_order, 'TimeIncrement': fps, 'TimeIncrementUnit': 's', })
        print(filename)
        return

    def start_acquisition(self, stackrange, step, filters: 'list[str]' = ['reflection'],
                          intensity: 'list[float]' = [8.], exposure: 'list[float]' = [0.03], focus_pos=None, format: str = "TZCYX",
                          SAVE_STACK: bool = True, FINISH_IN_SAFE: bool = True, SUPPRESS_AUTOFOCUS=False) -> np.ndarray:
        '''
        Starts the acquistion of a stack. If no focus position is given, autofocus is carried out.
        Loops through every channel and returns a TZCYX formatted stack.

        stackrange: float, unit: meter, range of the total stack, symmetrically around the focus position.
        step: float, unit: meter, step size of the stack
        filters: list[str], list of image channels, 'reflection','uv','green','orange','red'
        intensity: list[float], unit: 0-100 percent, list of intensities per channel
        exposure: list[float], unit: s, list of exposure time per channel        
        focus_pos: dict {'z': fpos}. unit: meter, absolute focus position. Autofocus is carried out if not given or None
        format: str, "TZCYX" or "XYZ"
        SAVE_STACK: Save a stack with name "%y_%m_%d%H_%M"_len_{:.1e}_step_{:.1e}.tiff into current working directory
        FINISH_IN_SAVE: Drive objective to a save position after last step.

        RETURN: np.uint16, TZCYX-formatted stack (x,y =2456,2054 px)
        '''
        if focus_pos is None and not SUPPRESS_AUTOFOCUS:
            focus_pos = self.autofocus(self.autofocus_result)
        elif not SUPPRESS_AUTOFOCUS:
            focus_pos = self.autofocus(focus_pos)

        # initalize variables
        slices = np.fix(stackrange/step).astype(int) + 1

        # init final stack with zeros
        try:
            # this is not urgently neccesarry but for later other formats such as ome-tiff
            if format == 'TZCYX':
                constack = np.zeros(
                        (1, slices, filters.__len__(), self.pixel_count['y'], self.pixel_count['x']), dtype='uint16')
            elif format == 'XYZ':
                constack = np.zeros(
                    (self.pixel_count['x'], self.pixel_count['y'], slices), dtype='uint16')
            else:
                raise Exception(
                    "Unsupported Stack Format, only XYZ and TZCYX...")
        except Exception as e:
            logger_server.error("Allocation of stack failed.")
            logger_server.debug("{}".format(e))
            self.error_state = 1
            return None
        else:

            # start channel-by-channel acquisition of stacks
            try:
                for channel in range(filters.__len__()):
                    # initialize light source and filters
                    try:
                        self.light_set_channel(
                            filters[channel], intensity[channel])
                        self.cam_set_exposure(exposure[channel])
                    except Exception as e:
                        logger_server.error(
                            "Error during the preparation of the filter or camera")
                        logger_server.debug("{}".format(e))
                        self.error_state = 1
                        break
                    else:
                        try:
                            val = self.get_raw_stack(step,slices,focus_pos)
                            if format == 'TZCYX':
                                constack[0, :, channel, :, :] = np.transpose(
                                    val[:, :, :], axes=(2, 1, 0))  # XYZ -> ZYX
                            elif format == 'XYZ':
                                constack = val
                        except Exception as e:
                            logger_server.error(
                                "Error during the physical stack acquisition and formatting")
                            logger_server.debug("{}".format(e))
                            self.error_state = 1
                            break
            except Exception as e:
                logger_server.error("Error during the stack acquisition")
                logger_server.debug("{}".format(e))
                self.focus_goto_safe()
                self.light_disable_all()
                self.disconnect()
                return None
            else:
                if SAVE_STACK:
                    filename = os.path.join(os.getcwd(), datetime.datetime.now().strftime("%y_%m_%d%H_%M") +
                                            "_len_{:.1e}_step_{:.1e}.tiff".format(stackrange, step))
                    self.save_stack_imagej(constack, filename, z_distance=step)

                if FINISH_IN_SAFE:
                    self.focus_goto_safe()

                return constack


# Autofocus functions #########################33


    def autofocus(self, initial_focus=None, autofocus_param_coarse=(500e-6, 50e-6),
                  autofocus_param_fine=(50e-6, 2e-6)) -> dict:
        '''
        The top-level-wrapper for the autofocus function. Starts at an initial focus point or the previous determined
        autofocus result, performs a corse iteration with 600 micron stack size and 20 micron slices
        Subsequently, a fine iteration with 50 micron and 2.5 micron steps is carried out. 

        Sets the result to the member variable self.autofocusResult and returns the float value in microns.
        '''
        logger_server.info('Starting autofocus.')

        if initial_focus is None:
            initial_focus = self.autofocus_result

        focus_pos = self.find_focus(autofocus_param_coarse, initial_focus)
        logger_server.debug('New Focus position: {}'.format(focus_pos))

        focus_pos = self.find_focus(autofocus_param_fine, focus_pos)
        logger_server.debug('New Focus position: {}'.format(focus_pos))

        if focus_pos is not None and focus_pos != 0:
            self.autofocus_result = focus_pos
            return focus_pos
        else:
            raise Exception("Autofocus could not be determined!")

    def find_focus(self, focus_params, focus: dict = None):
        '''
        Acquires a stack and executes the focus determination function to determine the best focused slice.
        Returns the best focus position in micron and sets it also to the microscope.

        Return: focus, dict

        '''
        # expand step size, stack depth, and number of slices
        stack_range, stack_step = focus_params
        slices = np.fix(stack_range/stack_step).astype(int) + 1
        if focus == None:
            focus = self.autofocus_result

        try:
            self.light_set_channel('reflection', 8)
            self.cam_set_exposure(0.01)
            stack = self.get_raw_stack(stack_step, slices, focus)
        except:
            logger_server.debug('Autofocus could not acquire a stack!')
            raise Warning(
                'Stack acquisition for autofocus raised an exception')
        else:
            best_focused_slice = self.find_focus_from_stack(stack)
            focus['z'] = focus['z'] + \
                (best_focused_slice - (slices // 2)) * stack_step
            try:
                self.focus_set_abs(focus)
            except:
                logger_server.debug(
                    'New Focus position {} out of range'.format(focus['z']))
                return None
            else:
                return focus

    def find_focus_from_stack(self, stack, PLOT_SCORE=False):
        """
        Finds the best focus position inside an alread acquired stack by applying a discrete wavelet transform with 
        LeGall's filter pair. Returns the slice index of the best focus.
        stack: XYZ-stack
        """
        # CREDIT:  sourtin/igem15-sw
        def low_res_score(IMAGE):

            def dwt(X, h1=np.array([-1, 2, 6, 2, -1])/8, h2=np.array([-1, 2 - 1])/4):
                """ 
                From 3rd year engineering project SF2
                DWT Discrete Wavelet Transform 
                Y = dwt(X, h1, h2) returns a 1-level 2-D discrete wavelet
                transform of X.

                If filters h1 and h2 are given, then they are used, 
                otherwise the LeGall filter pair are used.
                """
                m = X.shape[0]  # no: of rows in image X
                n = X.shape[1]  # no: of columns in image X
                Y = np.zeros((m, n))
                # print('Output image is of shape ',Y.shape)

                n2 = int(n/2)
                t = np.array(range(n2))
                # print('Editing this part of Y: ',Y[:,t].shape)
                # print(X.shape, h1.shape)

                Y[:, t] = rowdec(X, h1)
                Y[:, t+n2] = rowdec2(X, h2)

                X = Y.T
                m2 = int(m/2)
                t = np.array(range(m2))
                # print(Y[t,:].shape)
                # print(X.shape)
                Y[t, :] = rowdec(X, h1).T
                Y[t+m2, :] = rowdec2(X, h2).T
                return Y

            def rowdec(X, h):
                """"
                ROWDEC Decimate rows of a matrix
                Y = ROWDEC(X, H) Filters the rows of image X using H, and
                decimates them by a factor of 2.
                If length(H) is odd, each output sample is aligned with the first of
                each pair of input samples.
                If length(H) is even, each output sample is aligned with the mid point
                of each pair of input samples.
                """
                c = X.shape[1]
                r = X.shape[0]
                m = h.size
                m2 = int(m/2)

                if np.remainder(m, 2) > 0:
                    # Odd h: symmetrically extend indices without repeating end samples.
                    xe = np.array(
                        [x for y in [range(m2, 0, -1), range(c), range(c-2, c-m2-2, -1)] for x in y])
                else:
                    # Even h: symmetrically extend with repeat of end samples.
                    xe = np.array(
                        [x for y in [range(m2, -1, -1), range(c+1), range(c-1, c-m2-2, -1)] for x in y])

                t = np.array(range(0, c-1, 2))

                Y = np.zeros((r, t.size))
                # Loop for each term in h.
                for i in range(m):
                    Y = Y + h[i] * X[:, xe[t+i]]

                return Y

            def rowdec2(X, h):
                """"
                ROWDEC2 Decimate rows of a matrix
                Y = ROWDEC2(X, H) Filters the rows of image X using H, and
                decimates them by a factor of 2.
                If length(H) is odd, each output sample is aligned with the first of
                each pair of input samples.
                If length(H) is even, each output sample is aligned with the mid point
                of each pair of input samples.
                """
                c = X.shape[1]
                r = X.shape[0]
                m = h.size
                m2 = int(m/2)

                if np.remainder(m, 2) > 0:
                    # Odd h: symmetrically extend indices without repeating end samples.
                    xe = np.array(
                        [x for y in [range(m2, 0, -1), range(c), range(c-2, c-m2-2, -1)] for x in y])
                else:
                    # Even h: symmetrically extend with repeat of end samples.
                    xe = np.array(
                        [x for y in [range(m2, -1, -1), range(c+1), range(c-1, c-m2-2, -1)] for x in y])

                t = np.array(range(1, c, 2))

                Y = np.zeros((r, t.size))
                # Loop for each term in h.
                for i in range(m):
                    Y = Y + h[i] * X[:, xe[t+i]]

                return Y

            def nleveldwt(X, N=3):
                """ N level DWT of image
                Returns an array of the smaller resolution images
                """
                # print('N = ', N)
                Xs = [X]
                if N > 0:
                    h, w = X.shape[:2]
                    Xs += nleveldwt(dwt(X)[:h//2, :w//2], N-1)
                return Xs

            def focus_score(X):
                """ Focus score is the sum of the squared values of the low resolution images.
                """
                score = 0
                for i in X:
                    i += 1
                    score += np.var(i)
                return score

            return focus_score(nleveldwt(IMAGE))

        score = []

        for i in range(stack.shape[2]):
            # score.append(focus_score(i))
            score.append(low_res_score(stack[:, :, i]))

        max_score = max(score)
        best_focused_slice = score.index(max_score)
        logger_server.debug("Max Score: {}".format(max_score))
        logger_server.debug(
            "Index of max focus Value: {}".format(best_focused_slice))
        if PLOT_SCORE:
            import matplotlib.pyplot as plt
            plt.plot(range(len(score)), score)
            plt.ylabel('Variance')
            plt.xlabel('Position')
            plt.title('Focus score varying with position')
            plt.show()

        return best_focused_slice

    def get_formatted_stack(self, stackrange, step, dictf=None, format="TZCYX", FINISH_IN_SAFE=True):
        '''
        RELICT: !!! Wrapper to acqurire different formatted stacks. Calls *get_raw_stack*, and returns either a TZCYX or XYZ formatted
        stack. 
        stackrange: see the reference for start_acquisition
        SAVE_STACK: Saves the stack as tiff with the current datetime to the CWD
        FINISH_IN_SAFE: Returns to a save position for future stage moves.
        '''
        if dictf == None:
            dictf = self.autofocus_result
        slices = int(stackrange/step)
        constack = np.zeros(
            (1, slices, 1, self.pixel_count['y'], self.pixel_count['x']), dtype='uint16')

        stack = self.get_raw_stack(stackrange, step, focusPos=dictf)
        constack[0, :, 0, :, :] = np.transpose(
            stack, axes=(2, 1, 0))  # transpose stack from XYZ to ZYX

        if SAVE_DEBUGGING_IMAGES:
            filename = os.path.join(os.getcwd(), datetime.datetime.now().strftime(
                "%y_%m_%d-%H_%M_%S") + ".tiff")
            self.save_stack_imagej(constack, filename, z_distance=step)

        if FINISH_IN_SAFE:
            self.focus_goto_safe()

        if format == "TZCYX":
            return constack
        elif format == "XYZ":
            return stack
        else:
            raise Exception("Unsupported stack format!")
