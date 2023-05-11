#### IMPORT MICROSCOPE
from matplotlib.pyplot import get
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
# Set Up Microscope
microscope = SdbMicroscopeClient()


from autoscript_toolkit.template_matchers import *
import autoscript_toolkit.vision as vision_toolkit

from src.utils.custom_matchers_v2 import *
from src.utils.read_SAV import read_SAV_params
import cv2
import numpy as np
import time
import xml.etree.ElementTree as ET
import os
import datetime
import sys

from src.utils.CoRCalculations import get_rotation_coord, dict_2_numpy, get_center_of_rotation

try:
    microscope.connect()
except:
    print("Couldn't connect to microscope, connecting to localhost")
    try:
        microscope.connect('localhost')
    except:
        print("Loading Testimages")

class fibsem:
    def __init__(self):
        '''
        Definition of directories and intrinsic handlers
        '''

        # History for milling actions
        self.history=[]

        # Output
        self.output_dir=''
        self.log_output = ''
        self.lamella_name=''
        self.alignment_img_buffer=None
        self.SAVparamsfile=''

        # Default alignment current
        self.alignment_current = float(1e-11)
        self.trench_offset = 4e-06
        # Variable for stopping operation
        self.continuerun = True

    def define_output_dir(self,directory):
        '''
        Input: directory as string
		Output: None
		Action: defines output directory
        '''
        self.output_dir=directory+'/'
        return()
    def stop(self):
        '''
        Input: None
        Ouput: None
        Action: Stop operation by setting class variable "continuerun"
        '''
        self.continuerun=False
        return()

    def disconnect(self):
        '''
        Input: None
        Output: None
        Action: Disconnect AutoScript4 server
        '''
        microscope.disconnect()
    def connect(self):
        '''
        Input: None
        Output: None
        Action: Connect AutoScript4 server
        '''
        microscope.connect()

    def is_idle(self):
        '''
        Input: None
        Output: Returns True if microscope is idle, returns false if microscope is milling
        Action: None
        '''
        if microscope.patterning.state==PatterningState.IDLE:
            return(True)
        else:
            return(False)

    def get_current(self):
        '''
        Input: None
        Output: Returns the current ion beam current as float
        Action: None
        '''
        try:
            return(float(microscope.beams.ion_beam.beam_current.value))
        except:
            print("No microscope connected.")
    def take_image_IB(self):
        '''
        Input: None
        Output: AdornedImage
        Action: Take IB image with standard parameters
        '''
        try:
            # Set view to electron beam
            microscope.imaging.set_active_view(2)


            #Check if EB is on, Turn on EB if not the case
            if microscope.beams.ion_beam.is_blanked:
                print("Ion beam blanked ")
                microscope.beams.ion_beam.turn_on()
            else:
                print("Ion beam turned on")     

            # Aquire Snapshot in EB window
            print("Acquiring IB snapshot")
            framesettings = GrabFrameSettings(bit_depth=8)
            img = microscope.imaging.grab_frame(framesettings)
            array = img.data


            #microscope.beams.electron_beam.turn_off()
            #print("Electron beam turned off")
            return(img)
        except:
            print("ERROR: No Microscope connected")
        return()
    def take_image_EB(self):
        '''
        Input: None
        Output: Image as numpy array
        Action: Take EB image with standard parameters
        '''
        try:
            # Set view to electron beam
            microscope.imaging.set_active_view(1)


            #Check if EB is on, Turn on EB if not the case
            if microscope.beams.electron_beam.is_blanked:
                print("Ion beam blanked ")
            else:
                print("Electron beam turned on")
                microscope.beams.electron_beam.turn_on()



            # Aquire Snapshot in EB window
            print("Acquiring EB snapshot")
            img = microscope.imaging.grab_frame()
            array = img.data


            return(img)
        except:
            print("ERROR: No Microscope connected")
        return()

    def take_image_EB_SAV(self):
        '''
        Input: None
        Output: list of images as numpy array depending on amount of active Detectors in Quadrants (ETD, T1, T2)
        Action: Take EB image with defined parameters from SAVparamsfile
        '''

        try:
            # Set view to electron beam
            microscope.imaging.set_active_view(1)

            # Read parameters from defined SAVparams file
            paramsfile=self.SAVparamsfile
            params = read_SAV_params(paramsfile)
            res=params['Resolution']
            dwell=float(params['DwellTime'])
            LI=int(params['LineIntegration'])

            # Aquire Snapshot in EB window
            print("Acquiring EB snapshot")
            images = microscope.imaging.grab_multiple_frames(GrabFrameSettings(dwell_time=dwell,resolution=res,line_integration=LI))
            array = images[0].data


            return(images)
        except:
            print("ERROR: No Microscope connected or no active detector in quadrants")
            return()

    def getStagePosition(self):
        '''
        Input: None
        Output: current stageposition as directory
        Action: None
        '''

        #### Microscope dependent code ####
        try:
            stageposition=microscope.specimen.stage.current_position
        except:
            stageposition=StagePosition(x=0,y=0,z=0,r=0,t=0)
        x=stageposition.x
        y=stageposition.y
        z=stageposition.z
        r=stageposition.r
        t=stageposition.t
        

        #### Microscope independent code####
        stage_dict={'x':float(x),'y':float(y),'z':float(z),'r':float(r),'t':float(t)}
        return(stage_dict)

    def moveStageAbsolute(self, stageposition):
        '''
        Input: Stage position as dictionnary
        Output: None
        Action: Move stage to provided stage position
        '''
        ### Microscope Independet Code ###
        x=float(stageposition['x'])
        y=float(stageposition['y'])
        z=float(stageposition['z'])
        r=float(stageposition['r'])
        t=float(stageposition['t'])
        #print(x,y,z,r,t)
        

        ### Microscope Dependent Code ###
        stagepos=StagePosition(x=x,y=y,z=z,t=t,r=r)
        microscope.specimen.stage.absolute_move(stagepos)
        return()

    def moveStageRelative(self,stageposition):
        '''
        Input: Change in stage position as directory
        Output: None
        Action: Move stage relative to previous position by given parameters
        '''
        ### Microscope Independet Code ###
        x=float(stageposition['x'])
        y=float(stageposition['y'])
        z=float(stageposition['z'])
        r=float(stageposition['r'])
        t=float(stageposition['t'])

        ### Microscope Dependent Code ###
        stagepos=StagePosition(x=x,y=y,z=z,t=t,r=r)
        microscope.specimen.stage.relative_move(stagepos)
        return("Stage Moved")



####################################################



    def findRotationCenter(self):
            
        import pyautogui

        # check if old config exists and prompt user to load?


        ## Goto t=0 and r=0        
        currentPosition = self.getStagePosition()
        ### Travel at 10mm working distance
        z_tmp = currentPosition['z']
        currentPosition['z'] = 0.010
        currentPosition['t'] = 0
        currentPosition['r'] = 0
        self.moveStageAbsolute(currentPosition) # is this method travelling safely? If yes revise the code
        currentPosition['z'] = z_tmp
        self.moveStageAbsolute(currentPosition)


        # Prompt user to find feature in x-y with sufficient distance to the "midpoint" of the stage, p.e the screw of the shuttle
        # wait for "OK"
        # is maybe the coincident point already crucial? Lets adjust to that also
        answer = pyautogui.confirm('Prompt user to find feature in x-y with sufficient distance to the "midpoint" of the stage, p.e the screw of the shuttle.\
            Have you thought of the coincident point?', buttons=['Ok', 'Abort'])
        if answer == 'Abort':
            return
        # get coordinates
        originalFeature = self.getStagePosition()


        # init loop variables
        currentCoR_stage = {'x':0.0,'y':0.0,'z':0.0,'t':0.0,'r':0.0}
        newCoR = dict_2_numpy(currentCoR_stage,2)
        oldCoR = newCoR

        adjustedPosition = originalFeature

        error = 1
        angularSteps = 45

        calculatedVectors = np.zeros((5,int(360-angularSteps/angularSteps)))
        adjustedVectors = np.zeros((5,int(360-angularSteps/angularSteps)))
        adjustedCoR = np.zeros((2,int(360-angularSteps/angularSteps)))
        # loop over 360/10° or until epsilon < serveral micron?
        for theta in range(angularSteps,360-angularSteps,angularSteps):
            i = int(theta/angularSteps)-1
            if error < 5e-6:
                break

            # compute vector rotation around machine origin (0,0)
            compucentricRotated = get_rotation_coord(originalFeature, theta, newCoR, returnDict=1)

            #add to ndarray of "bad positions"
            calculatedVectors[:,i] = dict_2_numpy(compucentricRotated)

            # move absolute to these new coordinates
            self.moveStageAbsolute(compucentricRotated)

            # prompt user to move to selected feature in EB
            # wait for "ok"
            # maybe also abort button if sufficiently low error is reached            
            answer = pyautogui.confirm('Please center the desired feature under the cross as exact as possible', buttons=['Ok', 'Abort'])
            if answer == 'Abort':
                break

            # get new coordinates from microscope
            adjustedPosition = self.getStagePosition()   

            # add to ndarray of "good positions"         
            adjustedVectors[:,i] = dict_2_numpy(adjustedPosition)

            # compute new CenterOfRotation (CoR)
            newCoR, numericalError, radius = get_center_of_rotation(adjustedVectors)
            adjustedCoR[:,i] = newCoR

            # Calculate error
            error = np.linalg.norm(oldCoR-newCoR)
            oldCoR = newCoR

            # rotate back to origin, do you need that überhaups??
            # maybe over origin and back?
            originalFeature['r'] = np.deg2rad(3.0)
            self.moveStageAbsolute(originalFeature)

            originalFeature['r'] = np.deg2rad(0.0)
            self.moveStageAbsolute(originalFeature)

        # save center of origin for further usage
        filename = os.path.join( os.getcwd(), "vardump" + datetime.datetime.now().strftime("%y_%m_%d-%H_%M_%S") + ".csv")
        import pandas as pd
        pd.DataFrame([adjustedCoR.T, calculatedVectors.T, adjustedVectors.T]).to_csv(filename)
        





#######################################################################
    def align(self,image,beam,current=1.0e-11):
        '''
        Input: Alignment image, Beam ("ION" or "ELECTRON"), optionally current but replaced by the GUI option
        Output: None
        Action: Align the stage and beam shift to the reference image at the current stage position
        '''
        current=self.alignment_current


        try:
            if beam=='ION':
                print('Running alignment')
                microscope.imaging.set_active_view(2)

                # Get old resolution of images to go back after alignment
                old_resolution=microscope.beams.ion_beam.scanning.resolution.value
                old_mag=microscope.beams.ion_beam.horizontal_field_width.value

                # Get resolution of reference image and set microscope to given HFW
                img_resolution=str(np.shape(image.data)[1])+'x'+str(np.shape(image.data)[0])
                microscope.beams.ion_beam.scanning.resolution.value=img_resolution
                microscope.beams.ion_beam.beam_current.value=current
                beam_current_string=str(microscope.beams.ion_beam.beam_current.value)


                # Get HFW from Image

                # Run auto contrast brightness and reset beam shift. Take an image as reference for alignment
                microscope.beams.ion_beam.horizontal_field_width.value=image.metadata.optics.scan_field_of_view.width
                microscope.auto_functions.run_auto_cb()
                microscope.beams.ion_beam.beam_shift.value=Point(0,0)
                current_img=self.take_image_IB()


                # Load Matcher function and locate feature
                favourite_matcher = CustomCVMatcher(cv2.TM_CCOEFF_NORMED, tiling=False)
                l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                print("Current confidence: " + str(l.confidence))
                self.log_output=self.log_output+"Step Clarification: Initial Alignment after Stage move \n"
                self.log_output=self.log_output+"Current confidence: " + str(l.confidence)+'\n'


                # Start movements and log images
                move_count = 0

                now = datetime.datetime.now()
                current_img.save(self.output_dir + self.lamella_name+'_out/'+now.strftime("%Y-%m-%d_%H_%M_%S_")+self.lamella_name +'_'+ beam_current_string + '_first_move_'+str(move_count)+'.tif')
                self.log_output=self.log_output+"Saved Image as : "+self.output_dir + self.lamella_name+'_out/'+now.strftime("%Y-%m-%d_%H_%M_%S_")+self.lamella_name +'_'+ beam_current_string + '_first_move_'+str(move_count)+'.tif'+'\n'

                # If cross correlation metric too low, continue movements for maximum 3 steps
                while l.confidence < 0.98 and move_count < 3:
                    self.log_output = self.log_output + "Move Count =" + str(move_count) + '\n'
                    x = l.center_in_meters.x * -1 # sign may need to be flipped depending on matcher
                    y = l.center_in_meters.y * -1
                    distance = np.sqrt(x ** 2 + y ** 2)
                    print("Deviation (in meters): " + str(distance))
                    self.log_output = self.log_output + "Deviation (in meters): " + str(distance) + '\n'


                    # If distance, meaning offset between images low enough, stop.
                    if distance < 82.9e-06/3072/2:
                        break
                    elif distance > 1e-05:
                        # move stage and reset beam shift
                        print("Moving stage by ("+str(x)+","+str(y)+") and resetting beam shift...")
                        self.log_output = self.log_output + "Moving stage by ("+str(x)+","+str(y)+") and resetting beam shift... \n"
                        rotation=microscope.beams.electron_beam.scanning.rotation.value
                        possible_rotations=[0,3.14]
                        #print(min(possible_rotations, key=lambda x: abs(x - rotation)))

                        pos_corr = StagePosition(coordinate_system='Specimen', x=x, y=y)
                        microscope.specimen.stage.relative_move(pos_corr)
                        microscope.beams.ion_beam.beam_shift.value = Point(0,0)

                    else:
                        # apply (additional) beam shift
                        print("Shifting beam by ("+str(x)+","+str(y)+")...")
                        self.log_output = self.log_output + "Shifting beam by ("+str(x)+","+str(y)+")... \n"
                        print(microscope.beams.ion_beam.beam_shift.value)
                        microscope.beams.ion_beam.beam_shift.value += Point(x,y) # incremental

                    move_count += 1

                    current_img = self.take_image_IB()
                    now = datetime.datetime.now()
                    current_img.save(self.output_dir+ self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_") + self.lamella_name +'_'+ beam_current_string + '_first_move_' + str(move_count)+'.tif')

                    self.log_output = self.log_output + "Saved Image as : " +self.output_dir+ self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_") + self.lamella_name +'_'+ beam_current_string + '_first_move_' + str(move_count)+'.tif'+'\n'
                    l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                    print("Current confidence: " + str(l.confidence))
                    self.log_output = self.log_output + "Current confidence: " + str(l.confidence) + '\n'

                # Go back to old resolution
                microscope.beams.ion_beam.scanning.resolution.value = old_resolution
                microscope.beams.ion_beam.horizontal_field_width.value = old_mag

                self.alignment_img_buffer = current_img
                print("Done.")



            if beam=="ELECTRON":
                # Same as above, just for alignment in SEM imaging
                print('Running alignment')
                microscope.imaging.set_active_view(1)
                old_resolution = microscope.beams.electron_beam.scanning.resolution.value
                old_mag = microscope.beams.electron_beam.horizontal_field_width.value

                img_resolution = str(np.shape(image.data)[1]) + 'x' + str(np.shape(image.data)[0])
                microscope.beams.electron_beam.scanning.resolution.value = img_resolution
                microscope.beams.electron_beam.horizontal_field_width.value = image.metadata.optics.scan_field_of_view.width
                microscope.beams.electron_beam.beam_shift.value = Point(0, 0)

                current_img = self.take_image_EB()


                favourite_matcher = CustomCVMatcher(cv2.TM_CCOEFF_NORMED, tiling=False)
                l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                print("Current confidence: " + str(l.confidence))
                move_count = 0

                while l.confidence < 0.98 and move_count < 1:
                    x = l.center_in_meters.x * -1  # sign may need to be flipped depending on matcher
                    y = l.center_in_meters.y * -1
                    distance = np.sqrt(x ** 2 + y ** 2)
                    print("Deviation (in meters): " + str(distance))


                    if distance > 1e-05:
                        # move stage and reset beam shift
                        print("Moving stage by ("+str(x)+","+str(y)+") and resetting beam shift...")
                        #self.log_output = self.log_output + "Moving stage by ("+str(x)+","+str(y)+") and resetting beam shift... \n"

                        rotation = microscope.beams.electron_beam.scanning.rotation.value
                        possible_rotations = [0, 3.14]
                        num=min(possible_rotations, key=lambda x: abs(x - rotation))
                        print(num)
                        if num==0:
                            pos_corr = StagePosition(coordinate_system='Specimen', x=-x, y=-y)
                        if num==3.14:
                            pos_corr = StagePosition(coordinate_system='Specimen', x=x, y=y)
                        microscope.specimen.stage.relative_move(pos_corr)
                        microscope.beams.electron_beam.beam_shift.value = Point(0,0)

                    else:
                        # apply (additional) beam shift
                        print("Shifting beam by ("+str(x)+","+str(y)+")")
                        #self.log_output = self.log_output + "Shifting beam by ("+str(x)+","+str(y)+")... \n"
                        print(microscope.beams.electron_beam.beam_shift.value)
                        microscope.beams.electron_beam.beam_shift.value += Point(x,y) # incremental

                    move_count += 1
                    current_img = self.take_image_EB()
                    l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                microscope.beams.electron_beam.scanning.resolution.value = old_resolution
                microscope.beams.electron_beam.horizontal_field_width.value = old_mag
                #self.alignment_img_buffer = current_img

        except:
            if beam == 'ION':
                print('Running alignment')
                microscope.imaging.set_active_view(2)
                old_resolution = microscope.beams.ion_beam.scanning.resolution.value
                old_mag = microscope.beams.ion_beam.horizontal_field_width.value

                # microscope.beams.ion_beam.scanning.resolution.value='768x512'
                img_resolution = str(np.shape(image.data)[1]) + 'x' + str(np.shape(image.data)[0])
                microscope.beams.ion_beam.scanning.resolution.value = img_resolution
                microscope.beams.ion_beam.beam_current.value = current

                # Get HFW from Image

                microscope.beams.ion_beam.horizontal_field_width.value = image.metadata.optics.scan_field_of_view.width
                microscope.auto_functions.run_auto_cb()
                microscope.beams.ion_beam.beam_shift.value = Point(0, 0)
                current_img = self.take_image_IB()


                favourite_matcher = CustomCVMatcher(cv2.TM_CCOEFF_NORMED, tiling=False)
                l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                print("Current confidence: " + str(l.confidence))

                self.log_output = self.log_output + "Step Clarification: Initial Alignment after Stage move \n"
                self.log_output = self.log_output + "Current confidence: " + str(l.confidence) + '\n'

                move_count = 0

                while l.confidence < 0.98 and move_count < 3:
                    self.log_output = self.log_output + "Move Count =" + str(move_count) + '\n'
                    x = l.center_in_meters.x * -1  # sign may need to be flipped depending on matcher
                    y = l.center_in_meters.y * -1
                    distance = np.sqrt(x ** 2 + y ** 2)
                    print("Deviation (in meters): " + str(distance))
                    self.log_output = self.log_output + "Deviation (in meters): " + str(distance) + '\n'

                    if distance < 82.9e-06 / 3072 / 2:
                        break
                    elif distance > 1e-05:
                        # move stage and reset beam shift
                        print("Moving stage by (" + str(x) + "," + str(y) + ") and resetting beam shift...")
                        self.log_output = self.log_output + "Moving stage by (" + str(x) + "," + str(
                            y) + ") and resetting beam shift... \n"
                        pos_corr = StagePosition(coordinate_system='Specimen', x=x, y=y)
                        microscope.specimen.stage.relative_move(pos_corr)
                        microscope.beams.ion_beam.beam_shift.value = Point(0, 0)

                    else:
                        # apply (additional) beam shift
                        print("Shifting beam by (" + str(x) + "," + str(y) + ")...")
                        self.log_output = self.log_output + "Shifting beam by (" + str(x) + "," + str(y) + ")... \n"
                        print(microscope.beams.ion_beam.beam_shift.value)
                        microscope.beams.ion_beam.beam_shift.value += Point(x, y)  # incremental

                    move_count += 1

                    current_img = self.take_image_IB()
                    l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                    print("Current confidence: " + str(l.confidence))
                    self.log_output = self.log_output + "Current confidence: " + str(l.confidence) + '\n'
                microscope.beams.ion_beam.scanning.resolution.value = old_resolution
                microscope.beams.ion_beam.horizontal_field_width.value = old_mag

                print("Done.")

            if beam=="ELECTRON":
                #print("Not implemented yet")
                print('Running alignment')
                microscope.imaging.set_active_view(1)
                old_resolution = microscope.beams.electron_beam.scanning.resolution.value
                old_mag = microscope.beams.electron_beam.horizontal_field_width.value

                img_resolution = str(np.shape(image.data)[1]) + 'x' + str(np.shape(image.data)[0])
                microscope.beams.electron_beam.scanning.resolution.value = img_resolution
                microscope.beams.electron_beam.horizontal_field_width.value = image.metadata.optics.scan_field_of_view.width
                microscope.beams.electron_beam.beam_shift.value = Point(0, 0)

                current_img = self.take_image_EB()

                favourite_matcher = CustomCVMatcher(cv2.TM_CCOEFF_NORMED, tiling=False)
                l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                print("Current confidence: " + str(l.confidence))
                move_count = 0

                while l.confidence < 0.98 and move_count < 1:
                    x = l.center_in_meters.x * -1  # sign may need to be flipped depending on matcher
                    y = l.center_in_meters.y * -1
                    distance = np.sqrt(x ** 2 + y ** 2)
                    print("Deviation (in meters): " + str(distance))


                    if distance > 1e-05:
                        # move stage and reset beam shift
                        print("Moving stage by ("+str(x)+","+str(y)+") and resetting beam shift...")
                        #self.log_output = self.log_output + "Moving stage by ("+str(x)+","+str(y)+") and resetting beam shift... \n"
                        #pos_corr = StagePosition(coordinate_system='Specimen', x=x, y=y)
                        if num==0:
                            pos_corr = StagePosition(coordinate_system='Specimen', x=-x, y=-y)
                        if num==3.14:
                            pos_corr = StagePosition(coordinate_system='Specimen', x=x, y=y)
                        microscope.specimen.stage.relative_move(pos_corr)
                        microscope.beams.electron_beam.beam_shift.value = Point(0,0)

                    else:
                        # apply (additional) beam shift
                        print("Shifting beam by ("+str(x)+","+str(y)+")...")
                        #self.log_output = self.log_output + "Shifting beam by ("+str(x)+","+str(y)+")... \n"
                        print(microscope.beams.electron_beam.beam_shift.value)
                        microscope.beams.electron_beam.beam_shift.value += Point(x,y) # incremental
                        if num==0:
                            microscope.beams.electron_beam.beam_shift.value += Point(-x, -y)  # incremental
                        if num==3.14:
                            microscope.beams.electron_beam.beam_shift.value += Point(x, y)  # incremental

                    move_count += 1
                    current_img = self.take_image_EB()
                    l = vision_toolkit.locate_feature(current_img, image, favourite_matcher)
                microscope.beams.electron_beam.scanning.resolution.value = old_resolution
                microscope.beams.electron_beam.horizontal_field_width.value = old_mag

        return()

    def align_current(self,new_current,beam='ION'):
        '''
        Input: Current to change towards, beam (currently "ION" only)
        Output: None
        Action: Take a reference image at the old current, change current and align to that reference image
        '''
        if beam=="ION":
            microscope.imaging.set_active_view(2)
            #pos1=microscope.specimen.stage.current_position
            microscope.auto_functions.run_auto_cb()
            beam_current_string = str(microscope.beams.ion_beam.beam_current.value)
            ref_img=self.take_image_IB()
            now = datetime.datetime.now()
            try:
                ref_img.save(self.output_dir + self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_")+ self.lamella_name + '_' + beam_current_string + '_align_current_refimg' + '.tif')
                self.log_output=self.log_output+"Saved Image as : " + self.output_dir + self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_")+ self.lamella_name + '_' + beam_current_string + '_align_current_refimg' + '.tif'+'\n'
            except:
                print("Run in Scripting Mode")
            microscope.beams.ion_beam.beam_current.value = new_current
            microscope.beams.ion_beam.scanning.dwell_time.value=200e-09
            microscope.beams.ion_beam.scanning.resolution.value = '768x512'
            microscope.auto_functions.run_auto_cb()
            current_img=microscope.imaging.grab_frame()


            move_count = 0
            now = datetime.datetime.now()
            try:
                current_img.save(self.output_dir + self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_")+ self.lamella_name  + '_'+ beam_current_string +  '_align_current_' + str(move_count)+'.tif')
                self.log_output = self.log_output + "Saved Image as : " + self.output_dir + self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_")+ self.lamella_name  + '_'+ beam_current_string +  '_align_current_' + str(move_count)+'.tif'+'\n'
            except:
                pass

            favourite_matcher = CustomCVMatcher(cv2.TM_CCOEFF_NORMED, tiling=False)
            l = vision_toolkit.locate_feature(current_img, ref_img, favourite_matcher)
            
            print("Current confidence: " + str(l.confidence))

            self.log_output = self.log_output + "Step Clarification: Current Alignment \n"
            self.log_output = self.log_output + "Current confidence: " + str(l.confidence) + '\n'


            while l.confidence < 0.999 and move_count < 3:
                self.log_output = self.log_output + "Move Count =" +str(move_count) +'\n'
                x = l.center_in_meters.x * -1
                y = l.center_in_meters.y * -1
                distance = np.sqrt(x ** 2 + y ** 2)

                
                print("Deviation (in meters): " + str(distance))
                self.log_output = self.log_output + "Deviation (in meters): " + str(distance) + '\n'
                if distance < 82.9e-06/768/2:
                    break
                elif distance < 1e-05:
                    print("Shifting beam by ("+str(x)+","+str(y)+")...")
                    self.log_output = self.log_output + "Shifting beam by (" + str(x) + "," + str(y) + ")... \n"
                    microscope.beams.ion_beam.beam_shift.value += Point(x,y)
                    move_count += 1
                    current_img = self.take_image_IB()
                    now = datetime.datetime.now()
                    try:
                        current_img.save(self.output_dir + self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_")+ self.lamella_name + '_'+ beam_current_string + '_align_current_' + str(move_count)+'.tif')
                        self.log_output = self.log_output + "Saved Image as : " + self.output_dir + self.lamella_name + '_out/' +now.strftime("%Y-%m-%d_%H_%M_%S_")+ self.lamella_name + '_'+ beam_current_string + '_align_current_' + str(move_count)+'.tif'+'\n'
                    except:
                        pass
                    l = vision_toolkit.locate_feature(current_img, ref_img, favourite_matcher)
                    print("Current confidence: " + str(l.confidence))
                    self.log_output = self.log_output + "Current confidence: " + str(l.confidence) + '\n'
                else:
                    print("Distance is greater than 10 microns. Abort.")
                    self.log_output = self.log_output + "Distance is greater than 10 microns. Abort.\n"
                    break
            microscope.auto_functions.run_auto_cb()



        return()



    def auto_focus(self,beam="ELECTRON"):
        '''
        Input: Beam , currently only "ELECTRON" as autofocus in ION is damaging (also on a smaller sacrifice area...)
        Output: None
        Action: Autofocus function from the xT server
        '''
        active_view=microscope.imaging.get_active_view()
        if beam=="ELECTRON":
            microscope.imaging.set_active_view(1)
        else:
            microscope.imaging.set_active_view(2)
        microscope.auto_functions.run_auto_focus()
        microscope.imaging.set_active_view(active_view)
        return()


scope = fibsem()

scope.findRotationCenter()