from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMessageBox, QSystemTrayIcon, QMenu, QAction, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap, QIcon, QCursor, QPainterPath, QRegion, QTransform
from winreg import OpenKey, QueryValueEx, HKEY_CURRENT_USER
from configparser import ConfigParser
from win32api import GetKeyState
from datetime import datetime
from os.path import join as pathj
import capsWatcherResources, sys, os, json, subprocess, psutil

appVersion = [1, 0, 1, 9]

class capsWatcher_customQMenu(QMenu):
    def __init__(self):

        super(capsWatcher_customQMenu, self).__init__()
        self.radius = 5
        self.setLightMode()
    
    def setDarkMode(self):
        self.setStyleSheet('''
        QMenu {{
            padding:5px;
            background: #282828;
            border: 2px solid #3E3E3E;
            border-radius: {}px;
        }}
        QMenu::item {{
            color: white;
            padding: 4px 40px 4px 30px;
        }}
        QMenu::item:disabled {{
            color: #7D7D7D;
        }}
        QMenu::item:selected {{
            background: #404040;
            border-radius: 3px;
        }}
        QMenu::separator {{
            background-color: #3E3E3E;
            height: 1px;
            margin-top: 5px;
            margin-bottom: 5px;
        }}
        '''.format(self.radius))

    def setLightMode(self):
        self.setStyleSheet('''
        QMenu {{
            padding:5px;
            background: #DEDEDE;
            border: 2px solid #B3B3B3;
            border-radius: {}px;
        }}
        QMenu::item {{
            color: #000000;
            padding: 4px 40px 4px 30px;
        }}
        QMenu::item:disabled {{
            color: #6E6E6E;
        }}
        QMenu::item:!disabled:selected {{
            background: #C4C4C4;
            border-radius: 3px;
        }}
        QMenu::separator {{
            background-color: #C4C4C4;
            height: 1px;
            margin-top: 5px;
            margin-bottom: 5px;
        }}
        '''.format(self.radius))

    def resizeEvent(self, event):
        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(.5, .5, -1.5, -1.5)
        path.addRoundedRect(rect, self.radius, self.radius)
        region = QRegion(path.toFillPolygon(QTransform()).toPolygon())
        self.setMask(region)

class capsWatcher_Overlay(QWidget):
    def __init__(self):
        super().__init__()

        self.checkForExistingProcess()
        self.parsePaths()
        self.parseConfig()
        self.parseTray()
        self.parseElements()
        self.parseColorScheme()
        self.parseElementsConfig()
        self.parseTheme()
        self.setupThreads()

        self.checkReloadTimer = QTimer(self)
        self.checkReloadTimer.timeout.connect(self.checkReloadFile)
        self.checkReloadTimer.start(1000)
    
    def checkForExistingProcess(self):
        processRunning = 1
        for process in psutil.process_iter(['name']):
            if 'capsWatcher.exe' in process.info['name']:
                if processRunning > 1:
                    self.showMessageBox("capsWatcher launch error", "Only one instance of capsWatcher is allowed, try closing the existing one with capsWatcher Interface if you need it.", "critical")
                    self.overlayQuit()
                processRunning += 1

    def checkReloadFile(self):
        if os.path.exists(self.reloadFile):
            self.reloadElements()
            os.remove(self.reloadFile)

        if os.path.exists(self.terminateFile):
            for instance in self.capsWatcherKeyStateInstances : instance.terminate()
            os.remove(self.terminateFile)
            self.overlayQuit()
    
    def reloadElements(self):
        for instance in self.capsWatcherKeyStateInstances : instance.terminate()
        self.parseConfig()
        self.parseColorScheme()
        self.parseElementsConfig()
        self.parseTheme()
        self.setupThreads()

    def setupThreads(self):
        if len(self.overlayKeysToWatch) > 0:
            for instance in self.capsWatcherKeyStateInstances:
                instance.stateChanged.connect(self.overlayShow)
                instance.start()
        else:
            self.appException("Unable to load configuration file.", 'Nothing to watch.\nPlease select at least one key to watch.')

    def parseElements(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

        self.imageOverlay = QLabel(self)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.imageOverlay)
        self.setLayout(self.mainLayout)

        self.displayTimer = QTimer(self)
        self.displayTimer.timeout.connect(self.overlayFadeOut)

        self.fadeEffect = QPropertyAnimation(self, b"windowOpacity")
        self.fadeEffect.setEasingCurve(QEasingCurve.OutQuad)
        self.fadeEffect.setDuration(self.overlayFadeEffectTime)

        self.hideTimer = QTimer(self)
        self.hideTimer.timeout.connect(self.overlayHide)

        self.imageOpacity = QGraphicsOpacityEffect()
        self.imageOpacity.setOpacity(self.overlayOpacity)

        self.numLockEnabledOverlay, self.numLockDisabledOverlay = None, None
        self.capsLockEnabledOverlay, self.capsLockDisabledOverlay = None, None
        self.scrollLockEnabledOverlay, self.scrollLockDisabledOverlay = None, None
    
    def parseElementsConfig(self):
        if self.settingsTrayIcon:
            self.tray.show()
            colorScheme = self.parseColorScheme()
            if colorScheme == 0 : self.trayMenu.setDarkMode()
            elif colorScheme == 1 : self.trayMenu.setLightMode()
        else:
            self.tray.hide()
        self.fadeEffect.setDuration(self.overlayFadeEffectTime)
        self.imageOpacity.setOpacity(self.overlayOpacity)

    def parseConfig(self):
        self.configParser = ConfigParser()
        if not os.path.exists(self.cfgFilePath):
            self.showMessageBox("capsWatcher launch error", "Configuration file not found, please open capsWatcher configuration interface to manage.", "critical")
            sys.exit(1)
        self.configParser.read(self.cfgFilePath)

        self.overlayDisplayTime = int(self.configParser.get('overlay', 'displayTime'))
        self.overlayOpacity = float(int(self.configParser.get('overlay', 'opacity'))/100)
        self.overlayFadeEffectTime = int(self.configParser.get('overlay', 'fadeEffectTime'))
        self.overlayPositionOnScreen = int(self.configParser.get('overlay', 'positionOnScreen'))
        self.overlayTheme = self.configParser.get('overlay', 'theme')
        self.currentThemeFile = pathj(pathj(self.themesPath, self.overlayTheme), f"{self.overlayTheme}.json")
        self.currentThemeExists = os.path.exists(self.currentThemeFile)
        self.overlayColorScheme = int(self.configParser.get('overlay', 'colorScheme'))
        self.overlayKeysToWatch = list(map(int, self.configParser.get('overlay', 'keysToWatch').split(',')))
        self.settingsTrayIcon = bool(int(self.configParser.get('settings', 'trayicon')))
        self.themeFolder = pathj(self.themesPath, self.overlayTheme)

        if not 500 <= self.overlayDisplayTime <= 2000 : self.appException("Unable to load configuration file.", "Display Time not in allowed range (500, 2000).", configRelated=True)
        if not 0.10 <= self.overlayOpacity <= 1.00 : self.appException("Unable to load configuration file.", "Opacity value not in allowed range (10, 100).", configRelated=True)
        if not 50 <= self.overlayFadeEffectTime <= 500 : self.appException("Unable to load configuration file.", "Fade Time value not in allowed range (50, 500).", configRelated=True)
        if self.overlayPositionOnScreen not in [0, 1, 2, 3, 4, 5] : self.appException("Unable to load configuration file.", "Position on screen value not in allowed options (0, 1, 2, 3, 4, 5).", configRelated=True)
        if not self.overlayTheme or not self.currentThemeExists : self.appException("Unable to load configuration file.", f"The theme file '{self.overlayTheme}.json' is not found or is corrupted.", configRelated=True)
        if self.overlayColorScheme not in [0, 1, 2] : self.appException("Unable to load configuration file.", "Color scheme not in allowed options (0, 1, 2)", configRelated=True)
        if any(item not in [20,144,145] for item in self.overlayKeysToWatch) : self.appException("Unable to load configuration file.", f"Invalid key {[x for x in self.overlayKeysToWatch]} to define to capsWatcher, supported keys is (20, 144, 145)", configRelated=True)

        self.capsWatcherKeyStateInstances = []
        if 20 in self.overlayKeysToWatch : self.capsWatcherKeyStateInstances.append(capsWatcher_KeyState("capslock"))
        if 144 in self.overlayKeysToWatch : self.capsWatcherKeyStateInstances.append(capsWatcher_KeyState("numlock"))
        if 145 in self.overlayKeysToWatch : self.capsWatcherKeyStateInstances.append(capsWatcher_KeyState("scrolllock"))

    def parseColorScheme(self):
        regScheme = QueryValueEx(OpenKey(HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'), 'AppsUseLightTheme')[0]
        if self.overlayColorScheme == 0 or (self.overlayColorScheme == 2 and regScheme == 0) : return 0
        elif self.overlayColorScheme == 1 or (self.overlayColorScheme == 2 and regScheme == 1) : return 1

    def parseTheme(self):
        themeFile = self.currentThemeFile
        try:
            if not os.path.exists(themeFile) : raise Exception()
            data = json.load(open(themeFile, encoding='utf-8'))
            colorScheme = self.parseColorScheme()
            if colorScheme == 0 and data['darkMode']['isSupported'] : self.treatThemeScheme(data, 'darkMode')
            elif colorScheme == 1 and data['lightMode']['isSupported'] : self.treatThemeScheme(data, 'lightMode')
        except:
            self.appException("Unable to set current selected theme.", f'The selected theme "{self.overlayTheme.capitalize()}", cannot be loaded, check integrity or reinstall.')

    def parseTray(self):
        self.tray = QSystemTrayIcon(QIcon(":/capsWatcher/appicon.png"))
        self.trayMenu = capsWatcher_customQMenu()
        self.tray.setToolTip("CapsWatcher")
        self.tray.activated.connect(self.handleMainTrayClick)
        self.lastTrayClickTime = None

        self.capsWatcherTrayName = QAction(f"capsWatcher {".".join(map(str, appVersion))}")
        self.capsWatcherTrayName.setDisabled(True)
        self.configAction = QAction("Configuration")
        self.reloadAction = QAction("Reload watcher")
        self.quitAction = QAction("Quit")
        self.trayMenu.addAction(self.capsWatcherTrayName)
        self.trayMenu.addSeparator()
        self.trayMenu.addAction(self.configAction)
        self.trayMenu.addAction(self.reloadAction)
        self.trayMenu.addSeparator()
        self.trayMenu.addAction(self.quitAction)
        self.trayMenu.setWindowFlags(Qt.Popup)
        self.tray.setContextMenu(self.trayMenu)

        self.reloadAction.triggered.connect(self.reloadElements)
        self.quitAction.triggered.connect(self.overlayQuit)
        self.configAction.triggered.connect(self.handleConfigTrayClick)

    def parsePaths(self):
        if getattr(sys, 'frozen', False) : self.currentDirectory = os.path.dirname(sys.executable)
        else : self.currentDirectory = os.path.dirname(os.path.abspath(__file__))
        self.cfgPath = pathj(os.getenv('APPDATA'), 'capsWatcher')
        self.cfgFilePath = pathj(self.cfgPath, 'capsWatcher.cfg')
        self.themesPath = pathj(self.currentDirectory, 'themes')
        self.reloadFile = pathj(self.currentDirectory, 'reload.d')
        self.terminateFile = pathj(self.currentDirectory, 'terminate.d')
        self.currentDirectory = None

    def handleConfigTrayClick(self):
        subprocess.Popen(os.path.join(self.currentDirectory, 'capsWatcherInterface.exe'), shell=True)
    
    def handleMainTrayClick(self):
        if self.lastTrayClickTime is not None:
            currentTrayClickTime = datetime.now()
            timeDiff = (currentTrayClickTime - self.lastTrayClickTime).total_seconds() * 1000
            if timeDiff < 500 : self.handleConfigTrayClick()
            self.lastTrayClickTime = currentTrayClickTime
        else : self.lastTrayClickTime = datetime.now()
            
    def overlayQuit(self):
        sys.exit(0)

    def overlayScreenPosition(self, pos):
        if pos == 0 : return (5.25, 4)
        elif pos == 1 : return (2, 4)
        elif pos == 2 : return (1.25, 4)
        elif pos == 3 : return (5.25, 1.45)
        elif pos == 4 : return (2, 1.45)
        elif pos == 5 : return (1.25, 1.45)

    def overlayShow(self, key, state):
        if key == 144 and state : self.currentOverlay = self.numLockEnabledOverlay
        elif key == 144 and not state : self.currentOverlay = self.numLockDisabledOverlay
        elif key == 20 and state : self.currentOverlay = self.capsLockEnabledOverlay
        elif key == 20 and not state : self.currentOverlay = self.capsLockDisabledOverlay
        elif key == 145 and state : self.currentOverlay = self.scrollLockEnabledOverlay
        elif key == 145 and not state : self.currentOverlay = self.scrollLockDisabledOverlay
        elif key == 0 and not state : self.currentOverlay = None

        self.overlayFadeIn()
        self.pixmap = QPixmap(self.currentOverlay)
        self.imageOverlay.setPixmap(self.pixmap)
        self.imageOverlay.setGraphicsEffect(self.imageOpacity)

        cursor_pos = QCursor.pos()
        screen_number = QApplication.desktop().screenNumber(cursor_pos)
        screenGeometry = QApplication.desktop().screenGeometry(screen_number)
        self.move(screenGeometry.left(), screenGeometry.top())

        x, y = self.overlayScreenPosition(self.overlayPositionOnScreen)

        centerX = int(screenGeometry.left() + (screenGeometry.width() // x - self.pixmap.width() // 2))
        centerY = int(screenGeometry.top() + (screenGeometry.height() // y - self.pixmap.height() // 2))

        self.setGeometry(centerX, centerY, self.pixmap.width(), self.pixmap.height())

        if not self.isHidden() : self.displayTimer.start(self.overlayDisplayTime)

    def overlayHide(self):
        self.hideTimer.stop()
        self.hide()

    def overlayFadeOut(self):
        self.displayTimer.stop()
        if not self.displayTimer.isActive():
            self.fadeEffect.setStartValue(1)
            self.fadeEffect.setEndValue(0)
            self.fadeEffect.start()
            self.hideTimer.start(100)

    def overlayFadeIn(self):
        self.show()
        self.fadeEffect.setStartValue(0)
        self.fadeEffect.setEndValue(1)
        self.fadeEffect.start()
    
    def treatThemeScheme(self, data, scheme):
        overlayPath = pathj(self.themeFolder, data[scheme]['overlayPath'])
        if data[scheme]['numLockSupport']:
            self.numLockEnabledOverlay = pathj(overlayPath, '1441.png')
            self.numLockDisabledOverlay = pathj(overlayPath, '1440.png')
        if data[scheme]['capsLockSupport']:
            self.capsLockEnabledOverlay = pathj(overlayPath, '201.png')
            self.capsLockDisabledOverlay = pathj(overlayPath, '200.png')
        if data[scheme]['scrollLockSupport']:
            self.scrollLockEnabledOverlay = pathj(overlayPath, '1451.png')
            self.scrollLockDisabledOverlay = pathj(overlayPath, '1450.png')

    def showMessageBox(self, title, message, icon):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setWindowIcon(QIcon(":/capsWatcher/appicon.png"))
        msg_box.setText(message)
        if icon == 'information': msg_box.setIcon(QMessageBox.Information)
        elif icon == 'warning': msg_box.setIcon(QMessageBox.Warning)
        elif icon == 'critical': msg_box.setIcon(QMessageBox.Critical)
        else: msg_box.setIcon(QMessageBox.NoIcon)
        msg_box.exec_()
    
    def appException(self, error, message, configRelated=False):
        self.showMessageBox("capsWatcher", error+'\n'+'ㅤ'*30+'\n'+message, 'critical')
        if configRelated == True : os.unlink(self.cfgFilePath)
        sys.exit(1)

class capsWatcher_KeyState(QThread):
    stateChanged = pyqtSignal(int, bool)

    def __init__(self, keyName:str):
        super(capsWatcher_KeyState, self).__init__()
        self.allowedKeyNames = ["capslock", "numlock", "scrolllock"]
        self.keyName = keyName.lower()

        if self.keyName not in self.allowedKeyNames:
            raise SyntaxError(f'The ({keyName}) is not allowed to watch, current supported keyWatches is ("Capslock", "Numlock", "Scrolllock").')

        if self.keyName == self.allowedKeyNames[0] : self.keyCode = 20
        if self.keyName == self.allowedKeyNames[1] : self.keyCode = 144
        if self.keyName == self.allowedKeyNames[2] : self.keyCode = 145

        self.disableKeyEventValues, self.enableKeyEventValues = [-128, 0], [-127, 1]

        self.currentState = True if GetKeyState(self.keyCode) == 1 else False
        self.handledEvent = False
    
    def run(self):
        self.stateChanged.emit(0, False)
        self.checkState()

    def checkState(self):
        while True:
            currentInLoopState = GetKeyState(self.keyCode)

            if currentInLoopState != self.currentState and not self.handledEvent:
                if currentInLoopState in self.disableKeyEventValues : self.currentState = False
                elif currentInLoopState in self.enableKeyEventValues : self.currentState = True

                self.handledEvent = True
                self.stateChanged.emit(self.keyCode, self.currentState)

            elif currentInLoopState == self.currentState and self.handledEvent : self.handledEvent = False

            self.msleep(25)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    capsWatcher_Overlay().show()
    sys.exit(app.exec_())