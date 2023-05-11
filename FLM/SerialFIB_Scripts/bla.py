import os

#index_list=[0,2,4,5]
for i in range(6):
    pos=stagepositions[i]

    x=pos['x']
    y=pos['y']
    z=pos['z']
    t=pos['t']
    r=pos['r']

    print(x,y,z,t,r)

    #rel_move={'x':-2*x, 'y':-2*y ,'z':0,'r':3.14159,'t':-0.191986}
    rel_move={'x':-2*x, 'y':-2*y ,'z':0,'r':3.14159,'t':-0.244346}

    #
    fibsem.moveStageRelative(rel_move)
    #

    #rel_move={'x':-0026e-03, 'y':-0.71e-03 ,'z':0,'r':0,'t':0}

    #fibsem.moveStageRelative(rel_move)
    pos2=fibsem.getStagePosition()
    x=pos2['x']
    t=pos2['t']
    r=pos2['r']
    y=pos2['y']
    z=pos2['z']

    correction = {'x':0.0279e-3,'y':0.0688e-3,'z':0.0282e-3} #:
    offset=float(z)-float(y)

    meteor_x=float(x)+49.36e-03+correction['x']
    meteor_y=(4.185e-03-float(offset))/2.036+correction['y']
    meteor_z=((-1.036)*meteor_y)+4.185e-03+correction['z']

    print(meteor_x)
    print(meteor_y)
    print(meteor_z)

    print(pos)

    pos_meteor={'x':meteor_x,'y':meteor_y,'z':meteor_z,'t':t,'r':r}
    #print(pos_meteor)
    fibsem.moveStageAbsolute(pos_meteor)



    os.system('python '+r'D:/SharedData/iFLM_integratedLightModule/Client.py')

    pos=stagepositions[i]
    fibsem.moveStageAbsolute(pos)


    ### Testing cryo-FIB protocol milling ###

    ### User Input ###
    output_dir=r'D:/User Data/Sven/20220407_METEORDEV'
    img_index=i
    stagepos_index=i
    pattern_index=i
    protocol=r'D:/SharedData/SerialFIB/roughmill.pro'

    #############

    ### Definition of variables ###

    fibsem.output_dir=output_dir+'/'
    label=stagepositions[stagepos_index]['label']
    alignment_image=images[img_index]
    pattern_dir=output_dir+'/'+str(label)+'/'
    stagepos=stagepositions[stagepos_index]

    #print(patterns)
    fibsem.write_patterns(label,patterns[pattern_index],alignment_image,output_dir)


    ### Creating patternfile ###



    fibsem.run_milling_protocol(label,alignment_image,stagepos,pattern_dir,protocol)



    ####




    pos=stagepositions[i]

    x=pos['x']
    y=pos['y']
    z=pos['z']
    t=pos['t']
    r=pos['r']

    print(x,y,z,t,r)

    #rel_move={'x':-2*x, 'y':-2*y ,'z':0,'r':3.14159,'t':-0.191986}
    rel_move={'x':-2*x, 'y':-2*y ,'z':0,'r':3.14159,'t':-0.244346}

    #
    fibsem.moveStageRelative(rel_move)
    #

    #rel_move={'x':-0026e-03, 'y':-0.71e-03 ,'z':0,'r':0,'t':0}

    #fibsem.moveStageRelative(rel_move)
    pos2=fibsem.getStagePosition()
    x=pos2['x']
    t=pos2['t']
    r=pos2['r']
    y=pos2['y']
    z=pos2['z']

    correction = {'x':0.0279e-3,'y':0.0688e-3,'z':0.0282e-3} #:
    offset=float(z)-float(y)

    meteor_x=float(x)+49.36e-03+correction['x']
    meteor_y=(4.185e-03-float(offset))/2.036+correction['y']
    meteor_z=((-1.036)*meteor_y)+4.185e-03+correction['z']

    print(meteor_x)
    print(meteor_y)
    print(meteor_z)

    print(pos)

    pos_meteor={'x':meteor_x,'y':meteor_y,'z':meteor_z,'t':t,'r':r}
    #print(pos_meteor)
    fibsem.moveStageAbsolute(pos_meteor)



    os.system('python '+r'D:/SharedData/iFLM_integratedLightModule/Client.py')

    pos=stagepositions[i]
    fibsem.moveStageAbsolute(pos)