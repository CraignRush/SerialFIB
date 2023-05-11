# iFLM_integratedLightModule

## Important notice
Close Odemis with ```odemis-stop``` before the start of this package.

## DEPRECATED: How to clone the repo
This repo uses submodules. Therefore, after
> `git clone --recurse-submodules https://github.com/CraignRush/iFLM_integratedLightModule`

call additionaly from the root folder of the submodule (in our case `iFLM_integratedLightModule/meteor_dev`)

> `git submodule init`

> `git submodule update`

to be sure that the submodule works nicely.

# Working with the submodule
In order to receive or upload changes either to the root module or submodule, move into the respective top folder and execute `git stash,fetch, add, commit, push etc.`

## Data Structure

**TCP_PACKAGE(** *COMMAND, DATA, NP_SHAPE, NP_DTYPE* **)** : Communicates a desired *COMMAND* and arbitrary *DATA* between server and client.
*NP_SHAPE* and *NP_DTYPE* contain information about the numpy array.

For TCP-transmission an instance of the package is first pickled (defined by PICKLE_PROTOCOL in config.py) and then encoded (defined by CODEC in config.py). The current settings are:
`PICKLE_PROTOCOL = 4` and `CODEC = 'base64_codec'`

## Communication Protocol
After connection is established, the folling packages are exchanged:

1. CLIENT: sends Message, pe. intensity change or image aquisition
2. SERVER: encodes data
3. SERVER: sends "BYTES TO SEND" with the length in bytes in data
4. CLIENT: answers "READY TO RECEIVE"
5. SERVER: sends data with a buffer of currently 4096 bytes
6. CLIENT: After successful decoding of the package, he sends ""SUCCESS"

This cycle is repeated until an error occurs (most probable) or the client sends the final package "EXIT" and the connection is closed (least probable).

### Typical Client-Side Packages
- "ACQUIRE": Take single image
- ("ACQUIRE_Z",stack_params=[ stack_range, stack_steps ]): Take z-stack
- ("SET_FOCUS", float FocusValue): Adjust camera focus. ]0;1000[
- ("SET_INTENTSITY", int IntensityValue): Adjust light intensity. [0.;1.]
- ("PYTHONCODE", PythonCodeAsString): Execute custom python code. *CAVEAT* this is a highly insecure feature and might not lead the desired results...
- "EXIT": Terminate the socket connection and thread


### Typical Server-Side Packages
- "IMAGE": a 2d numpy array (x,y) in *DATA*, the corresponding shape and data type in *NP_shape* and *NP_dtype*, respectively.
- "ZSTACK": a 3d numpy array (slice,x,y) in *DATA*, the corresponding shape and data type in *NP_shape* and *NP_dtype*, respectively.
- "RESULT PYTHONCODE": Returns the result of the executed python code as string in *DATA*
- "STATE": *DATA* contains either 0 upon successful change of intensity or focus or -1 upon failure






