# OverviewOne
SpaceVR's Overview 1 flight software

@author Blaze Sanders - Email: blaze@spacevr.co Skype: blaze.sanders Twitter: @BLazeDSanders

Overview 1 will be the world's first free flying virtual reality space satellite.  Overview 1 uses eigth 4K sensors combined with wide field of view lenses to capture an immersive sphere of video. Our goal is to give everyone the opportunity to experience the truly infinite, boundless universe that we live in...through virtual reality.

This Git repo holds code that will run onboard the Overview 1. It's broken down into the following two directories (UVCstill, GPIOcontrol), and we will continue to update the code base as the mission unfolds. We look forward to community support to help push VR in space to the next step.

***UVCstill: Custom UVC USB 3.0 driver to caputure 4K (4224x3106) images from multiple cameras on any Linux OS. Tested on the Abaco COM10K1 with Sony FCB-MA133 cameras. Contact SpaceVR at blaze@spacevr.co to purchase our custom Camera Interface Hub (CIH) hardware, which connects four Sony FCB-MA133 cameras to one USB 3.0 port.

To run the UVCstill code complete the following steps:
1) Load the uvcstill module. THIS IS THE MOST IMPORTANT STEP. It needs to be done only once every time you are about to record for the first time or connect everything. IF you unplug a camera, you need to run this again before recording. 
2) Run the command "./run_init.py" in the Linux or Windows Cygwin terminal. Make sure it says eigth cameras and all cam 0 through 7 read “Ok” for 1280 X 720. Don’t worry if anything says “incomplete”. As long as they don’t “Timeout”, you’re good. 
3) Start recording  still images by running the "./run_capture.py" command in the Linux or Windows Cygwin terminal.
4) The images will be stored in the current directory you are in but you can change this by opening unity.py script and adding the path in the line that says filename = “cam%d%yuyv”. For example, to save it in documents, just change filename = “/documents/cam%d%yuyv”
5) To view the images you will (probably) need to convert the raw .yuyv files to .jpg files. To do so run the "./yuyv2jpg *.yuyv" command in the Linux or Windows Cygwin terminal. If you saved the images in a different folder, documents for example, you would run the "./yuyv2jpg  /documents/*.yuyv" command in the Linux or Windows Cygwin terminal.
6) Stitch images together using PTgui (www.ptgui.com) and you have a 360 image :)

***GPIOcontrol: Control the four input and four output pins on the Abaco COM10K1 single board Linux computer, when attached to the Connect Tech CCG020 carrier board.

To run the GPIOcontrol code complete the following steps:
1) Purchase an Abaco mCOM10K1 (https://goo.gl/KHcO28) Single Board Linux Computer (SBC) and Connect Tech CCG020 (https://goo.gl/IUNXin) carrier board
2) Run the command "./GPIOTestApp 1" or "./GPIOTestApp 2" to run Unit test number 1 or 2 respectively.
3) You should see a lot of debug statements and no assert failures. You can turn off the debug statements by redefining to "DEBUG_STATEMENTS_ON 0" in the COM10K1GPIO.h file
4) Make edits to "GPIOTestAPp.c" to begin writing your own code. Run the "make clean" and then "make" commands in the Linux or Windows Cygwin terminal to recompile your code.
