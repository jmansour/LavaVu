#######################################
# init.py : LavaVu OmegaLib init script
#######################################
from omega import *
from euclid import *
import urllib2
import os

cmds = []
labels = dict()
objmnu = None
animate = 0

# add the current path to the data search paths.
addDataPath(os.getcwd())

# Functions used by some of the quick commands
def _resetCamera():
  getDefaultCamera().setPosition(Vector3(0, 0, 0))
  getDefaultCamera().setPitchYawRoll(Vector3(0, 0, 0))

def _setCamSpeed(speedLevel):
  global speedLabel
  s = 10 ** (speedLevel - 4)
  labels["Navigation Speed"].setText("Navigation Speed: " + str(s) + "x")
  cc = getDefaultCamera().getController()
  if(cc != None):
    cc.setSpeed(s)

def _displayWand(value):
  if value:
    queueCommand("getSceneManager().displayWand(0, 1)")
  else:
    queueCommand("getSceneManager().hideWand(0)")
    
def _setSoundServerVolume( value ):
  global labels
  newVolume = value - 30
  labels["Global Volume"].setText("Global Volume: " + str(newVolume) )
  soundEnv.setServerVolume(newVolume)

#LavaVu functions
def _sendCommand(cmd):
  if not isMaster():
    return
  url = 'http://localhost:8080/command=' + urllib2.quote(cmd)
  urllib2.urlopen(url)

def _addCommand(cmd):
  global cmds
  if not isMaster():
    return
  cmds = [cmd] + cmds

objectMenu = dict()
def _toggleObject(name):
  if not isMaster():
    return

  global objectMenu
  #Check state (this has already been switched so shows current state)
  if objectMenu[name].getButton().isChecked():
    _sendCommand('show "' + name + '"');
  else:
    _sendCommand('hide "' + name + '"');

def _setPointSize(sizeLevel):
  global labels
  _sendCommand('scale points ' + str(sizeLevel))
  labels["Point Size"].setText("Point Size: " + str(sizeLevel))

transp = 0.0
def _setTransparency(val):
  global labels, transp
  trval = (10 - val) / 10.0
  if trval <= 0.01: trval = 0.01
  trans = float("{0:.1f}".format(trval))
  if trans != transp:
    #_sendCommand('alpha ' + str(trans))
    _addCommand('alpha ' + str(trans))
    labels["Transparency"].setText("Transparency: " + str(trans))
    transp = trans

def _setFrameRate(val):
  global animate
  animate = val

def _setPosition():
  #TEST: TODO: allow saving/restoring positions
  getDefaultCamera().setPosition(Vector3(389.07, -5763.38, 725.44))
  print getDefaultCamera().getPosition()

def _onAppStart(binpath):
  global objmnu
  mm = MenuManager.createAndInitialize()
  mainmnu = mm.createMenu("Main Menu")

  im = loadImage("%slogo.jpg" % binpath)
  if im:
     mi = mainmnu.addImage(im)
     ics = mi.getImage().getSize() * 0.5
     mi.getImage().setSize(ics)
  
  mm.setMainMenu(mainmnu)
  sysmnu = mainmnu.addSubMenu("System")
  _addMenuItem(sysmnu, "Toggle freefly", ":freefly", True)
  _addMenuItem(sysmnu, "Reset", "_resetCamera()")
  _addMenuItem(sysmnu, "Auto Near / Far", "queueCommand(':autonearfar ' + ('on' if %value% else 'off'))", False)
  #_addMenuItem(sysmnu, "Display Wand", "_displayWand(%value%)", False) #Not working, getSceneManager not found
  _addSlider(sysmnu, "Navigation Speed", "_setCamSpeed(%value%)", 10, 4)
  
  if( isSoundEnabled() ):
    global soundEnv
    global serverVolume
    soundEnv = getSoundEnvironment()
    serverVolume = soundEnv.getServerVolume();
    _addSlider(sysmnu, "Global Volume", "_setSoundServerVolume(%value%)", 39, serverVolume + 30)
    
  _addMenuItem(sysmnu, "Enable Stereo", "toggleStereo()", True)
  _addMenuItem(sysmnu, "Toggle Console", ":c")
  _addMenuItem(sysmnu, "List Active Modules", "printModules()")
  _addMenuItem(sysmnu, "Exit omegalib", "oexit()")

  #LavaVu params
  objmnu = mainmnu.addSubMenu("Objects")
  objmnu.addLabel("Toggle Objects")
  _addSlider(mainmnu, "Point Size", "_setPointSize(%value%)", 50, 1)
  _addCommandMenuItem(mainmnu, "Scale points up", "scale points up")
  _addCommandMenuItem(mainmnu, "Scale points down", "scale points down")
  _addSlider(mainmnu, "Transparency", "_setTransparency(%value%)", 10, 0)
  _addCommandMenuItem(mainmnu, "Point Type", "pointtype all")
  _addCommandMenuItem(mainmnu, "Next Model", "model down")
  _addSlider(mainmnu, "Animate", "_setFrameRate(%value%)", 10, 1)
  _setFrameRate(0)
  #_addMenuItem(mainmnu, "Restore Position", "_setPosition()")

def _addMenuItem(menu, label, call, checked=None):
  #Adds menu item, checkable optional
  mi = menu.addButton(label, call)
  if not checked == None:
    mi.getButton().setCheckable(True)
    mi.getButton().setChecked(checked)
  return mi

def _addSlider(menu, label, call, ticks, value):
  global labels
  l = menu.addLabel(label)
  labels[label] = l
  ss = menu.addSlider(ticks, call)
  ss.getSlider().setValue(value)
  ss.getWidget().setWidth(200)

def _addCommandMenuItem(menu, label, command):
  #Adds a menu item to issue a command to the control server
  return _addMenuItem(menu, label, "_sendCommand('"  + command + "')")

def _addObjectMenuItem(name, state):
  #Adds a toggle menu item to hide/show object
  global objectMenu, objmenu
  mitem = objmnu.addButton(name, "_toggleObject('"  + name + "')")
  mitem.getButton().setCheckable(True)
  mitem.getButton().setChecked(state)
  objectMenu[name] = mitem

def onUpdate(frame, t, dt):
  global animate, cmds, labels
  #print getDefaultCamera().getPosition()
  if animate > 0 and frame % animate == 0:
    _sendCommand("next")
    labels["Animate"].setText("Animate: " + str(int(round(1.0 / (animate * dt)))) + "fps")

  if frame % 10 == 0:
    while len(cmds):
      _sendCommand(cmds.pop())

saveAnimate = 1
def onEvent():
  global animate, saveAnimate
  if not isMaster():
    return

  e = getEvent()
  type = e.getServiceType()

  if e.isButtonDown(EventFlags.ButtonLeft): 
    print("Left button pressed")
  if e.isButtonDown(EventFlags.ButtonUp): 
    print("Up button pressed")

  # If we want to check multiple controllers or other tracked objects,
  # we could also check the sourceID of the event
  sourceID = e.getSourceId()

  # Check to make sure the event we're checking is a Wand event
  if type == ServiceType.Wand:
    #Turn animate on/off
    if(e.isButtonDown( EventFlags.ButtonUp )): # D-Pad up
      if animate:
        saveAnimate = animate
        animate = 0
      else:
        animate = saveAnimate

    return

    """
    # If a button is pressed down do something
    if(e.isButtonDown( EventFlags.Button3 )): # Cross
    if(e.isButtonDown( EventFlags.Button2 )): # Circle
    if(e.isButtonDown( EventFlags.ButtonDown )): # D-Pad down
    if(e.isButtonDown( EventFlags.ButtonLeft )): # D-Pad left
    if(e.isButtonDown( EventFlags.ButtonRight )): # D-Pad right
    if(e.isButtonDown( EventFlags.Button6 )): # Analog stick button (L3)
    if(e.isButtonUp( EventFlags.Button3 )): # Cross
    if(e.isButtonUp( EventFlags.Button2 )): # Circle
    if(e.isButtonDown( EventFlags.Button5 )): # L1 button
    if(e.isButtonDown( EventFlags.Button7 )): # Analog Trigger (L2)

    # Grab the analog stick horizontal axis
    analogLR = e.getAxis(0)
    # Grab the analog stick vertical axis
    analogUD = e.getAxis(1)

    if( (analogUD + analogLR) > 0.001 or  (analogUD + analogLR) < -0.001 ):
      #print("Wand ", sourceID, "Analog stick: ", analogUD, " ", analogLR)
      x = analogLR
      y = analogUD

    ## Grab the analog trgger
    analogL2 = e.getAxis(4)

    if( analogL2 > 0.001 ):
      print("Wand ", sourceID, "Analog trigger L2: ", analogL2 )

    ## Grab the analog trgger
    analogL1 = e.getAxis(4)

    if( analogL2 > 0.001 ):
      print("Wand ", sourceID, "Analog trigger L2: ", analogL2 )

    #Wand Motion Tracker...
    #elif(e.getServiceType() == ServiceType.Mocap):
    #  print("Trackable ", sourceID, " position: ", e.getPosition() )
    #  print("Trackable ", sourceID, " orientation: ", e.getOrientation() )
    """

setEventFunction(onEvent)
setUpdateFunction(onUpdate)

queueCommand(":freefly")