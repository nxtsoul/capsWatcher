from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QInputDialog, QMessageBox, QGraphicsOpacityEffect, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from winreg import OpenKey, SetValueEx, QueryValueEx, DeleteValue, REG_SZ, KEY_ALL_ACCESS, HKEY_CURRENT_USER
from datetime import datetime
import capsWatcherResources, sys, os, subprocess, configparser, json, psutil, time, pywinstyles, pathlib, zipfile

appVersion = [1, 0, 1, 9]

class capsWatcher_configInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = capsWatcher_uiElements()
        self.ui.setupUi(self)

        self.cfgPath = os.path.join(os.getenv('APPDATA'), 'capsWatcher')
        self.cfgFilePath = os.path.join(self.cfgPath, 'capsWatcher.cfg')
        self.themesPath = os.path.join(self.cfgPath, 'themes')
        self.languagesPath = os.path.join(self.cfgPath, 'languages')

        self.messageBox = QMessageBox()

        self.currentScheme = None
        self.currentDirectory = None
        self.darkModeSupport = None
        self.lightModeSupport = None
        self.fileModified = None
        self.numLockSupport = ['Num Lock', None]
        self.capsLockSupport = ['Caps Lock', None]
        self.scrollLockSupport = ['Scroll Lock', None]

        self.parseCurrentDirectory()
        self.parseConfig()
        self.parseThemes()
        self.configureInterface()

        self.processWatcherThread = capsWatcher_processWatcher()
        self.processWatcherThread.processData.connect(self.processWatcher)
        self.processWatcherThread.start()

        self.monitorConfigFile = capsWatcher_monitorConfigFile()
        self.monitorConfigFile.needReload.connect(self.handleFileModified)
        self.monitorConfigFile.start()
    
    def parseConfig(self):
        self.configParser = configparser.ConfigParser()

        if not os.path.exists(self.cfgPath): os.mkdir(self.cfgPath)
        if not os.path.exists(self.cfgFilePath):
            self.configParser.add_section('overlay')
            self.configParser.set('overlay', 'displayTime', '1500')
            self.configParser.set('overlay', 'opacity', '95')
            self.configParser.set('overlay', 'fadeEffectTime', '150')
            self.configParser.set('overlay', 'positionOnScreen', '4')
            self.configParser.set('overlay', 'theme', 'elegant')
            self.configParser.set('overlay', 'colorScheme', '2')
            self.configParser.set('overlay', 'keysToWatch', '20,144,145')
            self.configParser.add_section('settings')
            self.configParser.set('settings', 'runAtStartup', '1')
            self.configParser.set('settings', 'trayIcon', '1')
            self.configParser.set('settings', 'language', 'en-US')
            self.configParser.set('settings', 'checkForUpdates', '1')
            with open(self.cfgFilePath, 'w') as f:
                self.configParser.write(f)
                f.close()
            self.handleRunAtStart(2)

        self.configParser.read(self.cfgFilePath)

        self.overlayDisplayTime = int(self.configParser.get('overlay', 'displayTime'))
        self.overlayOpacity = int(self.configParser.get('overlay', 'opacity'))
        self.overlayFadeEffectTime = int(self.configParser.get('overlay', 'fadeEffectTime'))
        self.overlayPositionOnScreen = int(self.configParser.get('overlay', 'positionOnScreen'))
        self.overlayTheme = self.configParser.get('overlay', 'theme')
        self.currentThemeFile = os.path.join(os.path.join(self.themesPath, self.overlayTheme), f"{self.overlayTheme}.json")
        self.currentThemeExists = os.path.exists(self.currentThemeFile)
        self.overlayColorScheme = int(self.configParser.get('overlay', 'colorScheme'))
        self.overlayKeysToWatch = list(map(int, self.configParser.get('overlay', 'keysToWatch').split(',')))
        self.settingsRunAtStartup = bool(int(self.configParser.get('settings', 'runAtStartup')))
        self.settingsTrayIcon = bool(int(self.configParser.get('settings', 'trayIcon')))
        self.settingsLanguage = self.configParser.get('settings', 'language')
        self.currentLanguageFile = os.path.join(self.languagesPath, f"{self.settingsLanguage}.json")
        self.currentLanguageExists = os.path.exists(self.currentLanguageFile)
        self.settingsCheckForUpdates = bool(int(self.configParser.get('settings', 'checkForUpdates')))

        if not 500 <= self.overlayDisplayTime <= 2000 : self.appException("Unable to load configuration file.", "Display Time not in allowed range (500, 2000).", configRelated=True)
        if not 10 <= self.overlayOpacity <= 100 : self.appException("Unable to load configuration file.", "Opacity value not in allowed range (10, 100).", configRelated=True)
        if not 50 <= self.overlayFadeEffectTime <= 500 : self.appException("Unable to load configuration file.", "Fade Time value not in allowed range (50, 500).", configRelated=True)
        if self.overlayPositionOnScreen not in [0, 1, 2, 3, 4, 5] : self.appException("Unable to load configuration file.", "Position on screen value not in allowed options (0, 1, 2, 3, 4, 5).", configRelated=True)
        if not self.overlayTheme or not self.currentThemeExists : self.appException("Unable to load configuration file.", f"The theme file '{self.overlayTheme}.json' is not found or is corrupted.", configRelated=True)
        if self.overlayColorScheme not in [0, 1, 2] : self.appException("Unable to load configuration file.", "Color scheme not in allowed options (0, 1, 2)", configRelated=True)
        if any(item not in [20,144,145] for item in self.overlayKeysToWatch) : self.appException("Unable to load configuration file.", f"Invalid key {[x for x in self.overlayKeysToWatch]} to define to capsWatcher, supported keys is (20, 144, 145)", configRelated=True)
        if not self.settingsLanguage or not self.currentLanguageExists : self.appException("Unable to load configuration file.", f"The language file '{self.settingsLanguage}.json' is not found or is corrupted.", configRelated=True)

        self.parseLanguages()
        self.parseTranslation()

        self.ui.displayTimeBoxSlider.setValue(self.overlayDisplayTime)
        self.ui.displayTimeBoxLabel.setText(f"{self.overlayDisplayTime}ms")
        self.ui.opacityBoxSlider.setValue(self.overlayOpacity)
        self.ui.opacityBoxLabel.setText(f"{self.overlayOpacity}%")
        self.ui.fadeEffectBoxSlider.setValue(self.overlayFadeEffectTime)
        self.ui.fadeEffectBoxLabel.setText(f"{self.overlayFadeEffectTime}ms")
        self.ui.positionScreenComboBox.setCurrentIndex(self.overlayPositionOnScreen)
        self.ui.themeComboBox.setCurrentIndex(self.ui.themeComboBox.findData(self.overlayTheme))
        self.ui.colorSchemeComboBox.setCurrentIndex(self.overlayColorScheme)
        if 144 in self.overlayKeysToWatch : self.ui.numLockCheckBox.setChecked(True)
        if 20 in self.overlayKeysToWatch : self.ui.capsLockCheckBox.setChecked(True)
        if 145 in self.overlayKeysToWatch : self.ui.scrollLockCheckBox.setChecked(True)
        if self.settingsRunAtStartup: self.ui.settingsBoxAtStartupCheckBox.setChecked(True)
        if self.settingsTrayIcon : self.ui.settingsBoxTrayIconCheckBox.setChecked(True)
        if not self.settingsCheckForUpdates : self.ui.neverUpdateCheckbox.setChecked(True)

    def parseThemes(self):
        self.ui.themeComboBox.clear()
        if len(os.listdir(self.themesPath)) < 1: 
                self.appException(self.appLang["UNABLE_TO_LOAD_THEMES"], self.appLang["UNABLE_TO_LOAD_THEMES_TEXT"].format(self.themesPath))
        for folder in os.listdir(self.themesPath):
            themeFolder = os.path.join(self.themesPath, folder)
            themeFile = os.path.join(themeFolder, f"{folder}.json")
            if os.path.exists(themeFile):
                try:
                    data = json.load(open(themeFile, encoding='utf-8'))
                    lightMode = data['lightMode']['isSupported']
                    darkMode = data['darkMode']['isSupported']
                    if darkMode and lightMode : visualName = data['name']
                    elif not darkMode and lightMode: visualName = f'{data["name"]} ({self.appLang["LIGHT_MODE_ONLY"]})'
                    elif darkMode and not lightMode : visualName = f'{data["name"]} ({self.appLang["DARK_MODE_ONLY"]})'
                    elif not darkMode and not lightMode : continue
                    self.ui.themeComboBox.addItem(visualName, userData=data['theme'])
                except ValueError : pass
    
    def parseLanguages(self):
        self.ui.languageBoxComboBox.clear()
        if len(os.listdir(self.languagesPath)) < 1: 
                self.appException('Failed to load language files', f"There are no languages files installed to use capsWatcher, please try again or reinstall the software.")
        for languageFile in os.listdir(self.languagesPath):
            try:
                languageFileStrings = json.load(open(os.path.join(self.languagesPath, languageFile), encoding='utf-8'))
                self.ui.languageBoxComboBox.addItem(languageFileStrings["LANGUAGE_DESCRIPTION"], userData=languageFileStrings["LANGUAGE_SHORTNAME"])
            except ValueError : pass
    
    def parseKeyToWatch(self):
        checkBoxList = [self.ui.numLockCheckBox, self.ui.capsLockCheckBox, self.ui.scrollLockCheckBox]
        keyThemeNonSupport = [key for key in [self.numLockSupport, self.capsLockSupport, self.scrollLockSupport] if key[1] == False]
        if len(keyThemeNonSupport) > 0:
            for x in keyThemeNonSupport:
                for j in checkBoxList:
                    if x[0] == j.text():
                        self.treatCheckBox(j, disabled=True, tooltip=self.appLang["DISABLE_KEY_NON_SUPPORT"])
                        checkBoxList.remove(j)
        else : [self.treatCheckBox(key, disabled=False) for key in checkBoxList] 
        enabledCheckBox = [checkbox for checkbox in checkBoxList if checkbox.isChecked()]
        if len(enabledCheckBox) == 0 and len(keyThemeNonSupport) == 3:
            [self.treatCheckBox(key, disabled=True, tooltip=self.appLang["DISABLE_KEY_NON_SUPPORT"]) for key in enabledCheckBox]
        elif len(enabledCheckBox) == 0 and len(keyThemeNonSupport) < 3:
            checkBoxList[0].setChecked(True)
            self.treatCheckBox(checkBoxList[0], disabled=True, tooltip=self.appLang["DISABLE_KEY_REQUIREMENT"])
        elif len(enabledCheckBox) == 1:
            self.treatCheckBox(enabledCheckBox[0], disabled=True, tooltip=self.appLang["DISABLE_KEY_REQUIREMENT"])
        elif len(enabledCheckBox) > 1:
            [self.treatCheckBox(key, disabled=False) for key in enabledCheckBox]

    def parsePreviewImage(self):
        themeData = json.load(open(self.currentThemeFile, encoding='utf-8'))
        themeFolder = os.path.join(self.themesPath, self.overlayTheme)
        if (self.currentScheme == 1 and not themeData['lightMode']['isSupported']) or (self.currentScheme == 0 and themeData['darkMode']['isSupported']):
            themeSchemeFolder = os.path.join(themeFolder, themeData['darkMode']['overlayPath'])
        elif (self.currentScheme == 0 and not themeData['darkMode']['isSupported']) or (self.currentScheme == 1 and themeData['lightMode']['isSupported']):
            themeSchemeFolder = os.path.join(themeFolder, themeData['lightMode']['overlayPath'])

        previewCandidates = [os.path.join(themeSchemeFolder, '200.png'), os.path.join(themeSchemeFolder, '1440.png'), os.path.join(themeSchemeFolder, '1450.png')]

        for overlayPath in previewCandidates:
            if os.path.exists(overlayPath):
                self.previewImage = overlayPath
                break
            
        overlayPreviewPixmap = QPixmap(self.previewImage)
        self.imageOpacity = QGraphicsOpacityEffect()
        self.ui.previewBoxIconLabel.setPixmap(overlayPreviewPixmap)

    def parseTranslation(self):
        languageComboBoxItem = self.ui.languageBoxComboBox.findData(self.settingsLanguage)
        self.ui.languageBoxComboBox.setCurrentIndex(languageComboBoxItem)
        with open(self.currentLanguageFile, "r", encoding="utf-8") as languageFile:
            self.appLang = json.load(languageFile)
            languageFile.close()
        self.ui.opacityBox.setTitle(self.appLang["OPACITY"])
        self.ui.displayTimeBox.setTitle(self.appLang["DISPLAY_TIME"])
        self.ui.colorSchemeBox.setTitle(self.appLang["COLOR_SCHEME"])
        self.ui.colorSchemeComboBox.setItemText(0, self.appLang["DARK_MODE"])
        self.ui.colorSchemeComboBox.setItemText(1, self.appLang["LIGHT_MODE"])
        self.ui.colorSchemeComboBox.setItemText(2, self.appLang["USE_SYSTEM_SCHEME"])
        self.ui.fadeEffectBox.setTitle(self.appLang["FADE_IN_OUT_EFFECT"])
        self.ui.positionScreenBox.setTitle(self.appLang["POSITION_ON_SCREEN"])
        self.ui.positionScreenComboBox.setItemText(0, self.appLang["TOP_LEFT"])
        self.ui.positionScreenComboBox.setItemText(1, self.appLang["TOP_MIDDLE"])
        self.ui.positionScreenComboBox.setItemText(2, self.appLang["TOP_RIGHT"])
        self.ui.positionScreenComboBox.setItemText(3, self.appLang["BOTTOM_LEFT"])
        self.ui.positionScreenComboBox.setItemText(4, self.appLang["BOTTOM_MIDDLE"])
        self.ui.positionScreenComboBox.setItemText(5, self.appLang["BOTTOM_RIGHT"])
        self.ui.themeBox.setTitle(self.appLang["THEME"])
        self.ui.previewBox.setTitle(self.appLang["PREVIEW"])
        self.ui.keysToWatchBox.setTitle(self.appLang["KEYS_TO_WATCH"])
        self.ui.numLockCheckBox.setText("Num Lock")
        self.ui.capsLockCheckBox.setText("Caps Lock")
        self.ui.scrollLockCheckBox.setText("Scroll Lock")
        self.ui.watcherStatusBox.setTitle(self.appLang["WATCHER_STATUS"])
        self.ui.watcherStatus.setText(self.appLang["LOOKING_FOR_PROCESS"])
        self.ui.watcherStart.setText(self.appLang["START"])
        self.ui.watcherStop.setText(self.appLang["STOP"])
        self.ui.mainTab.setTabText(self.ui.mainTab.indexOf(self.ui.overlayTab), self.appLang["OVERLAY"])
        self.ui.settingsBox.setTitle(self.appLang["SETTINGS"])
        self.ui.settingsBoxAtStartupCheckBox.setText(self.appLang["RUN_AT_STARTUP"])
        self.ui.settingsBoxTrayIconCheckBox.setText(self.appLang["SHOW_ICON_NOTIFICATION"])
        self.ui.languageBox.setTitle(self.appLang["LANGUAGE"])
        self.ui.updateResetBox.setTitle(self.appLang["UPDATE_AND_RESET"])
        self.ui.updateButton.setText(self.appLang["CHECK_UPDATES"])
        self.ui.neverUpdateCheckbox.setText(self.appLang["NEVER_UPDATE"])
        self.ui.resetButton.setText(self.appLang["RESET_SETTINGS"])
        self.ui.resetLabel.setText(f'<p align=\"center\"><span style=\"color:#7c7c00;\">{self.appLang["RESET_WARNING"]}</span></p>')
        self.ui.addThemeBox.setTitle(self.appLang["ADD_THEME"])
        self.ui.addThemeBoxButton.setText(self.appLang["SELECT_FILE"])
        self.ui.addThemeBoxLineEdit.setText(self.appLang["SELECT_FILE_TYPE"])
        self.ui.addThemeBoxHelperLabel.setText(self.appLang["ADD_THEME_HELPER_TEXT"])
        self.ui.about.setText(f'<span style=\"font-size:12pt;font-weight:600;\">{self.appLang["ABOUT"]}</span>')
        self.ui.aboutText.setText(self.appLang["ABOUT_TEXT"])
        self.ui.aboutCopyright.setText(f'<p align=\"right\"><span style=\" font-weight:600;\">v{".".join(map(str, appVersion))} | {self.appLang["COPYRIGHT"]}&nbsp;&nbsp;&nbsp;</span><img width=\"20\" src=\":/capsWatcher/brazil.png\"/>')
        self.ui.mainTab.setTabText(self.ui.mainTab.indexOf(self.ui.settingsTab), self.appLang["SETTINGS"])
        self.ui.exitButton.setText(self.appLang["QUIT"])
        self.ui.applyButton.setText(self.appLang["APPLY_CHANGES"])
    
    def parseCurrentDirectory(self):
        if getattr(sys, 'frozen', False) : self.currentDirectory = os.path.dirname(sys.executable)
        else : self.currentDirectory = os.path.dirname(os.path.abspath(__file__))

    def configureInterface(self):
        self.treatColorScheme(self.overlayColorScheme)

        self.ui.displayTimeBoxLabel.setText(f"{self.ui.displayTimeBoxSlider.value()}ms")
        self.ui.displayTimeBoxSlider.valueChanged.connect(self.handleDisplayTime)
        self.ui.displayTimeBoxLabel.mouseDoubleClickEvent = self.handleDisplayTime

        self.ui.opacityBoxLabel.setText(f"{self.ui.opacityBoxSlider.value()}%")
        self.ui.opacityBoxSlider.valueChanged.connect(self.handleOpacity)
        self.ui.opacityBoxLabel.mouseDoubleClickEvent = self.handleOpacity

        self.ui.fadeEffectBoxLabel.setText(f"{self.ui.fadeEffectBoxSlider.value()}ms")
        self.ui.fadeEffectBoxSlider.valueChanged.connect(self.handleFadeEffect)
        self.ui.fadeEffectBoxLabel.mouseDoubleClickEvent = self.handleFadeEffect

        self.ui.themeComboBox.activated.connect(self.handleTheme)
        self.ui.themeInfo.clicked.connect(self.handleThemeInfo)
        self.ui.positionScreenComboBox.currentIndexChanged.connect(self.handleScreenPosition)
        self.ui.colorSchemeComboBox.activated.connect(self.handleColorScheme)

        self.ui.numLockCheckBox.stateChanged.connect(self.handleKeyToWatch)
        self.ui.capsLockCheckBox.stateChanged.connect(self.handleKeyToWatch)
        self.ui.scrollLockCheckBox.stateChanged.connect(self.handleKeyToWatch)

        self.ui.settingsBoxAtStartupCheckBox.stateChanged.connect(self.handleRunAtStart)
        self.ui.settingsBoxTrayIconCheckBox.stateChanged.connect(self.handleTrayIcon)

        self.ui.addThemeBoxButton.clicked.connect(self.handleThemeAddition)
        self.ui.neverUpdateCheckbox.stateChanged.connect(self.handleUpdateCheck)

        self.ui.languageBoxComboBox.currentIndexChanged.connect(self.handleLanguage)
        
        self.ui.resetButton.clicked.connect(self.handleReset)

        self.ui.exitButton.clicked.connect(self.handleQuit)

        self.ui.watcherStart.clicked.connect(self.handleStartProcess)
        self.ui.watcherStop.clicked.connect(self.handleStopProcess)
        self.ui.applyButton.clicked.connect(self.handleApply)

        self.parseKeyToWatch()
        self.handlePreviewIconOpacity()

    def handleTheme(self, event=None):
        currentData = self.ui.themeComboBox.currentData()
        if self.overlayTheme != currentData:
            self.overlayTheme = currentData
            self.currentThemeFile = os.path.join(os.path.join(self.themesPath, self.overlayTheme), f"{self.overlayTheme}.json")
            self.currentThemeExists = os.path.exists(self.currentThemeFile)
            self.handleColorScheme()
            self.modifyConfig('overlay', 'theme', str(currentData))
    
    def handleThemeInfo(self, event=None):
        themeData = json.load(open(self.currentThemeFile, encoding='utf-8'))
        darkModeKeys = self.treatKeyWatchBasedOnTheme('darkMode', listKeys=True)
        lightModeKeys = self.treatKeyWatchBasedOnTheme('lightMode', listKeys=True)
        createdDate = datetime.strptime(themeData['creation_date'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y at %I:%M:%S%p')
        infoString = f"""
            <span style="font-size:20px;">
                {themeData['name']} {self.appLang["BY"]} {themeData['creator']}
            </span>
            <br />
            <span style="font-size:16px;">
                {themeData['description']}
            </span>
            <br />
            <br />
            <b>
                {self.appLang["CREATOR_GITHUB_PROFILE"]}
            </b>
            <br />
            <a style="color:#00a2ff;" href="https://github.com/{themeData['github_user']}">
                https://github.com/{themeData['github_user']}
            </a>
            <br />
            <br />
            {f'<b>{self.appLang["DARK_MODE_KEYS_SUPPORTED"]}</b><br />'+", ".join(darkModeKeys)+"<br /><br />" if len(darkModeKeys) > 0 else ""}
            {f'<b>{self.appLang["LIGHT_MODE_KEYS_SUPPORTED"]}</b><br />'+", ".join(lightModeKeys)+"<br /><br />" if len(lightModeKeys) > 0 else ""}
            <b>{self.appLang["CREATED_AT"]}</b><br />
            {createdDate}<br />
            """+"&nbsp;"*150
        self.showMessageBox(f'{themeData["name"]} {self.appLang["BY"]} {themeData["creator"]}', infoString, 'information')
    
    def handleColorScheme(self, event=None):
        currentIndex = self.ui.colorSchemeComboBox.currentIndex()
        self.treatColorScheme(currentIndex)
        self.overlayColorScheme = currentIndex
        self.modifyConfig('overlay', 'colorScheme', str(currentIndex))

    def handleScreenPosition(self, event=None):
        currentIndex = self.ui.positionScreenComboBox.currentIndex()
        if self.overlayPositionOnScreen != currentIndex:
            self.overlayPositionOnScreen = currentIndex
            self.modifyConfig('overlay', 'positionOnScreen', str(currentIndex))
    
    def handleDisplayTime(self, event=None):
        currentValue = self.ui.displayTimeBoxSlider.value()
        cs = self.overlayColorScheme
        self.ui.displayTimeBoxLabel.setText(f"{currentValue}ms")
        if not type(event) == int:
            if event.button() == Qt.LeftButton and event.type() == event.MouseButtonDblClick:
                dialog = QInputDialog(self)
                if cs == 0 or (cs == 2 and self.getSystemScheme() == 0):
                    dialog.setStyleSheet(self.ui.darkSpinBox)
                    pywinstyles.apply_style(dialog,"dark")
                if cs == 1 or (cs == 2 and self.getSystemScheme() == 1):
                    dialog.setStyleSheet(self.ui.lightSpinBox)
                    pywinstyles.apply_style(dialog,"light")
                dialog.setWindowTitle(self.appLang["SET_DISPLAY_TIME_MS"])
                dialog.setLabelText(self.appLang["DISPLAY_TIME_MS"])
                dialog.setInputMode(QInputDialog.IntInput)
                dialog.setIntMinimum(500)
                dialog.setIntMaximum(2000)
                dialog.setIntValue(int(self.ui.displayTimeBoxLabel.text().replace("ms", "")))
                dialog.setFixedSize(280, 200)
                dialog.exec_()
                self.ui.displayTimeBoxSlider.setValue(dialog.intValue())
                currentValue = dialog.intValue()
        self.ui.displayTimeBoxLabel.setText(f"{currentValue}ms")
        if self.overlayDisplayTime != currentValue:
            self.overlayDisplayTime = currentValue
            self.modifyConfig('overlay', 'displayTime', str(currentValue))

    def handleOpacity(self, event=None):
        currentValue = self.ui.opacityBoxSlider.value()
        cs = self.overlayColorScheme
        if not type(event) == int:
            if event.button() == Qt.LeftButton and event.type() == event.MouseButtonDblClick:
                dialog = QInputDialog(self)
                if cs == 0 or (cs == 2 and self.getSystemScheme() == 0):
                    dialog.setStyleSheet(self.ui.darkSpinBox)
                    pywinstyles.apply_style(dialog,"dark")
                if cs == 1 or (cs == 2 and self.getSystemScheme() == 1):
                    dialog.setStyleSheet(self.ui.lightSpinBox)
                    pywinstyles.apply_style(dialog,"light")
                dialog.setWindowTitle(self.appLang["SET_OPACITY_PERCENTAGE"])
                dialog.setLabelText(self.appLang["OPACITY_PERCENTAGE"])
                dialog.setInputMode(QInputDialog.IntInput)
                dialog.setIntMinimum(10)
                dialog.setIntMaximum(100)
                dialog.setIntValue(int(self.ui.opacityBoxLabel.text().replace("%", "")))
                dialog.setFixedSize(300, 200)
                dialog.exec_()
                self.ui.opacityBoxSlider.setValue(dialog.intValue())
                currentValue = dialog.intValue()
        self.ui.opacityBoxLabel.setText(f"{currentValue}%")
        if self.overlayOpacity != currentValue:
            self.overlayOpacity = currentValue
            self.modifyConfig('overlay', 'opacity', str(currentValue))
        self.handlePreviewIconOpacity()

    def handleFadeEffect(self, event=None):
        currentValue = self.ui.fadeEffectBoxSlider.value()
        cs = self.overlayColorScheme
        if not type(event) == int:
            if event.button() == Qt.LeftButton and event.type() == event.MouseButtonDblClick:
                dialog = QInputDialog(self)
                if cs == 0 or (cs == 2 and self.getSystemScheme() == 0):
                    dialog.setStyleSheet(self.ui.darkSpinBox)
                    pywinstyles.apply_style(dialog,"dark")
                if cs == 1 or (cs == 2 and self.getSystemScheme() == 1):
                    dialog.setStyleSheet(self.ui.lightSpinBox)
                    pywinstyles.apply_style(dialog,"light")
                dialog.setWindowTitle(self.appLang["FADE_EFFECT_DURATION_MS"])
                dialog.setLabelText(self.appLang["FADE_DURATION_MS"])
                dialog.setInputMode(QInputDialog.IntInput)
                dialog.setIntMinimum(50)
                dialog.setIntMaximum(500)
                dialog.setIntValue(int(self.ui.fadeEffectBoxLabel.text().replace("ms", "")))
                dialog.setFixedSize(300, 200)
                dialog.exec_()
                self.ui.fadeEffectBoxSlider.setValue(dialog.intValue())
                currentValue = dialog.intValue()
        self.ui.fadeEffectBoxLabel.setText(f"{currentValue}ms")
        if self.overlayFadeEffectTime != currentValue:
            self.overlayFadeEffectTime = currentValue
            self.modifyConfig('overlay', 'fadeEffectTime', str(currentValue))

    def handleStartProcess(self, event=None):
        self.processWatcherThread.terminate()
        self.ui.watcherStart.setDisabled(True)
        self.ui.watcherStart.setIcon(self.ui.startIconDisabled)
        self.ui.watcherStatus.setStyleSheet(self.ui.yellowLabel)
        self.ui.watcherStatus.setText(self.appLang["STARTING_CAPSWATCHER"])
        subprocess.Popen(os.path.join(self.currentDirectory, 'capsWatcher.exe'), shell=True)
        self.processWatcherThread.start()
    
    def handleStopProcess(self, event=None):
        self.ui.watcherStop.setDisabled(True)
        self.ui.watcherStop.setIcon(self.ui.stopIconDisabled)
        self.processWatcherThread.terminate()
        self.ui.watcherStatus.setStyleSheet(self.ui.yellowLabel)
        self.ui.watcherStatus.setText(self.appLang["STOPPING_CAPSWATCHER"])
        open(os.path.join(self.cfgPath, 'terminate.d'), 'w').close()
        self.processWatcherThread.start()

    def handleReset(self, event=None):
        if self.showMessageBox(self.appLang["RESET_SETTINGS"], self.appLang["RESET_TEXT"]+"<br />"+self.appLang["RESET_WARNING"], "question") != QMessageBox.Yes: return
        self.monitorConfigFile.terminate()
        os.unlink(self.cfgFilePath)
        self.parseConfig()
        self.treatColorScheme(self.overlayColorScheme)
        self.parseKeyToWatch()
        self.handlePreviewIconOpacity()
        open(os.path.join(self.cfgPath, 'reload.d'), 'w').close()
        self.monitorConfigFile.start()
    
    def handleApply(self, event=None):
        self.handleFileModified(modified=False)

    def handleThemeAddition(self, event=None):
        selectedFile = QFileDialog.getOpenFileName(self, self.appLang["SELECT_TITLE"], os.path.join(os.getenv('USERPROFILE'), 'Downloads'), self.appLang["SELECT_FILE_TYPE"])
        if len(selectedFile[0]) == 0 : return
        if not pathlib.Path(selectedFile[0]).suffix == '.zip' or (os.path.getsize(selectedFile[0])/(1024 * 1024)) > 5:
            self.showMessageBox(self.appLang["SELECT_FAILED_TITLE"], self.appLang["SELECT_FAILED_TEXT"], "critical")
            return
        self.ui.addThemeBoxLineEdit.setText(selectedFile[0])
        with zipfile.ZipFile(selectedFile[0], 'r') as zipTheme:
            zipTheme.extractall(self.themesPath)
            zipTheme.close()
        self.parseThemes()
        self.showMessageBox(self.appLang["THEME_INSTALLED_TITLE"], self.appLang["THEME_INSTALLED_TEXT"], "information") 
    
    def handleFileModified(self, modified=True):
        if modified == True:
            self.fileModified = True
            self.ui.applyButton.setEnabled(True)
            currentIcon = self.ui.lightApplyIcon if self.currentScheme == 1 else self.ui.darkApplyIcon
            self.ui.applyButton.setIcon(currentIcon)
            self.ui.infoLabel.setText(self.appLang["PENDING_CHANGES_TO_APPLY"])
        elif modified == False:
            self.fileModified = False
            self.ui.applyButton.setEnabled(False)
            self.ui.applyButton.setIcon(self.ui.applyIconDisabled)
            open(os.path.join(self.cfgPath, 'reload.d'), 'w').close()
            self.ui.infoLabel.setText("")
            self.monitorConfigFile.start()

    def handleQuit(self):
        sys.exit(0)

    def handleKeyToWatch(self, state):
        self.parseKeyToWatch()
        senderName = self.sender().text().replace(" ", "").lower()
        if senderName == "numlock" : key = 144
        elif senderName == "capslock" : key = 20
        elif senderName == "scrolllock" : key = 145
        if state == 0 and key in self.overlayKeysToWatch : self.overlayKeysToWatch.remove(key)
        elif state == 2 and key not in self.overlayKeysToWatch : self.overlayKeysToWatch.append(key)
        self.overlayKeysToWatch.sort()
        self.modifyConfig('overlay', 'keysToWatch', ",".join(map(str, self.overlayKeysToWatch)))

    def handleLanguage(self):
        currentData = self.ui.languageBoxComboBox.currentData()
        if self.settingsLanguage != currentData:
            self.settingsLanguage = currentData
            self.currentLanguageFile = os.path.join(self.languagesPath, f"{currentData}.json")
            self.currentLanguageExists = os.path.exists(self.currentLanguageFile)
            self.parseTranslation()
            self.modifyConfig('settings', 'language', str(currentData))

    def treatKeyWatchBasedOnTheme(self, colorMode, listKeys=False):
        themeData = json.load(open(self.currentThemeFile, encoding='utf-8'))
        darkModeSupport = themeData['darkMode']['isSupported']
        lightModeSupported = themeData['lightMode']['isSupported']

        supportedMode = None
        if not listKeys:
            if self.currentScheme == 0 and not darkModeSupport : supportedMode = False
            elif self.currentScheme == 1 and not lightModeSupported : supportedMode = False
        else : supportedMode = False if not themeData[colorMode]['isSupported'] else None
            
        self.numLockSupport[1] = themeData[colorMode]['numLockSupport'] if supportedMode is None else supportedMode
        self.capsLockSupport[1] = themeData[colorMode]['capsLockSupport'] if supportedMode is None else supportedMode
        self.scrollLockSupport[1] = themeData[colorMode]['scrollLockSupport'] if supportedMode is None else supportedMode

        if not listKeys : self.parseKeyToWatch()
        else : return [keySup[0] for keySup in [self.numLockSupport, self.capsLockSupport, self.scrollLockSupport] if keySup[1]]

    def treatCheckBox(self, element, disabled=False, tooltip=""):
        element.setDisabled(disabled)
        element.setToolTip(tooltip)

    def treatColorScheme(self, comparative):
        if comparative == 0 or (comparative == 2 and self.getSystemScheme() == 0):
            self.currentScheme = 0
            self.ui.setDarkMode(self)
            self.messageBox.setStyleSheet(self.ui.darkMessageBox)
            pywinstyles.apply_style(self,"dark")
            pywinstyles.apply_style(self.messageBox,"dark")
            self.treatKeyWatchBasedOnTheme('darkMode')
            if self.fileModified : self.ui.applyButton.setIcon(self.ui.darkApplyIcon)
            self.parsePreviewImage()
        elif comparative == 1 or (comparative == 2 and self.getSystemScheme() == 1): 
            self.currentScheme = 1
            self.ui.setLightMode(self)
            self.messageBox.setStyleSheet("")
            pywinstyles.apply_style(self,"light")
            pywinstyles.apply_style(self.messageBox,"light")
            self.treatKeyWatchBasedOnTheme('lightMode')
            if self.fileModified : self.ui.applyButton.setIcon(self.ui.lightApplyIcon)
            self.parsePreviewImage()

    def handleRunAtStart(self, state):
        regKey = OpenKey(HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, KEY_ALL_ACCESS)
        regKeyName = "capsWatcher"
        config = str(int(False))
        try:
            QueryValueEx(regKey, regKeyName)[0]
            regKeyExists = True
        except:
            regKeyExists = False
        if state == 2:
            if not regKeyExists:
                SetValueEx(regKey, regKeyName, 0, REG_SZ, 'C:\\Program Files (x86)\\capsWatcher\\capsWatcher.exe')
                config = str(int(True))
        elif state == 0:
            if regKeyExists:
                DeleteValue(regKey, regKeyName)
                config = str(int(False))
        self.modifyConfig('settings', 'runatstartup', config)
    
    def handleTrayIcon(self, state):
        if state == 0 : self.modifyConfig('settings', 'trayicon', '0')
        elif state == 2 : self.modifyConfig('settings', 'trayicon', '1')

    def handleUpdateCheck(self, state):
        if state == 0 : self.modifyConfig('settings', 'checkforupdates', '1')
        elif state == 2 : self.modifyConfig('settings', 'checkforupdates', '0')

    def handlePreviewIconOpacity(self):
        self.imageOpacity.setOpacity(self.overlayOpacity/100)
        self.ui.previewBoxIconLabel.setGraphicsEffect(self.imageOpacity)
        
    def processWatcher(self, state, pid):
        if state:
            self.ui.watcherStatus.setStyleSheet(self.ui.greenLabel)
            self.ui.watcherStatus.setText(self.appLang["RUNNING_PROCESS"].format(pid))
            self.ui.watcherStart.setDisabled(True)
            self.ui.watcherStop.setDisabled(False)
            if self.currentScheme == 0:
                self.ui.watcherStart.setIcon(self.ui.startIconDisabled)
                self.ui.watcherStop.setIcon(self.ui.darkStopIcon)
            elif self.currentScheme == 1:
                self.ui.watcherStart.setIcon(self.ui.startIconDisabled)
                self.ui.watcherStop.setIcon(self.ui.lightStopIcon)
        else:
            self.ui.watcherStatus.setStyleSheet(self.ui.redLabel)
            self.ui.watcherStatus.setText(self.appLang["NOT_RUNNING_PROCESS"])
            self.ui.watcherStart.setDisabled(False)
            self.ui.watcherStop.setDisabled(True)
            if self.currentScheme == 0:
                self.ui.watcherStart.setIcon(self.ui.darkStartIcon)
                self.ui.watcherStop.setIcon(self.ui.stopIconDisabled)
            elif self.currentScheme == 1:
                self.ui.watcherStart.setIcon(self.ui.lightStartIcon)
                self.ui.watcherStop.setIcon(self.ui.stopIconDisabled)

    def getSystemScheme(self):
        try: return 0 if QueryValueEx(OpenKey(HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'), 'AppsUseLightTheme')[0] == 0 else 1
        except Exception as e : return f"Error: {e}"

    def modifyConfig(self, section, key, value):
        self.configParser.set(section, key, value)
        f = open(self.cfgFilePath, 'w')
        self.configParser.write(f)
        f.close()

    def showMessageBox(self, title, message, icon):
        self.messageBox.setWindowTitle(title)
        self.messageBox.setWindowIcon(QIcon(":/capsWatcher/appicon.png"))
        self.messageBox.setTextFormat(Qt.RichText)
        self.messageBox.setText(message)
        self.messageBox.setStandardButtons(QMessageBox.Ok)
        if icon == 'information' : self.messageBox.setIcon(QMessageBox.Information)
        elif icon == 'warning' : self.messageBox.setIcon(QMessageBox.Warning)
        elif icon == 'critical' : self.messageBox.setIcon(QMessageBox.Critical)
        elif icon == 'question':
            self.messageBox.setIcon(QMessageBox.Question)
            self.messageBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            yesButton = self.messageBox.button(QMessageBox.Yes)
            yesButton.setText(self.appLang["YES"])
            noButton = self.messageBox.button(QMessageBox.No)
            noButton.setText(self.appLang["NO"])
        else: self.messageBox.setIcon(QMessageBox.NoIcon)
        return self.messageBox.exec_()
    
    def appException(self, error, message, configRelated=False):
        self.showMessageBox("capsWatcher", error+'\n'+'ㅤ'*30+'\n'+message, 'critical')
        if configRelated == True : os.unlink(self.cfgFilePath)
        sys.exit(1)

class capsWatcher_processWatcher(QThread):
    processData = pyqtSignal(bool, str)

    def run(self):
        foundProcess = False
        processInfo = ['capsWatcher.exe', None]
        time.sleep(1)
        while not foundProcess:
            time.sleep(1)
            for process in psutil.process_iter(['name']):
                self.msleep(1)
                if process.info['name'] == processInfo[0]:
                    foundProcess = True
                    processInfo[1] = process.pid
                    break
            if not foundProcess : self.processData.emit(False, "")

        while True:
            try:
                process = psutil.Process(processInfo[1])
                if process.is_running() and process.name() == processInfo[0] : self.processData.emit(foundProcess, str(processInfo[1]))
                else : self.processData.emit(False, "")
            except psutil.NoSuchProcess:
                foundProcess = False
                self.processData.emit(False, "")
                break

            self.msleep(1)     

class capsWatcher_monitorConfigFile(QThread):
    needReload = pyqtSignal(bool)
    def run(self):
        self.cfgFilePath = os.path.join(os.path.join(os.getenv('APPDATA'), 'capsWatcher'), 'capsWatcher.cfg')
        self.cachedStamp = os.stat(self.cfgFilePath).st_mtime
        while True:
            currentStamp = os.stat(self.cfgFilePath).st_mtime
            if currentStamp != self.cachedStamp:
                self.cachedStamp = currentStamp
                self.needReload.emit(True)
                break
            self.msleep(50)

class capsWatcher_uiElements(object):
    def setupUi(self, capsWatcher):
        capsWatcher.setObjectName("capsWatcher")
        capsWatcher.resize(621, 606)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(capsWatcher.sizePolicy().hasHeightForWidth())
        capsWatcher.setSizePolicy(sizePolicy)
        capsWatcher.setMinimumSize(QtCore.QSize(621, 606))
        capsWatcher.setMaximumSize(QtCore.QSize(621, 606))
        capsWatcher.setWindowIcon(QtGui.QIcon(':/capsWatcher/appicon.png'))
        capsWatcher.setWindowTitle("capsWatcher")
        segoeFont = QtGui.QFont()
        segoeFont.setFamily("Segoe UI")
        segoeFont.setPointSize(9)
        normalFont = QtGui.QFont()
        normalFont.setWeight(50)
        normalFont.setFamily("Segoe UI")
        normalFont.setPointSize(9)
        boldNormalFont = QtGui.QFont()
        boldNormalFont.setBold(True)
        boldNormalFont.setWeight(75)
        self.centralwidget = QtWidgets.QWidget(capsWatcher)
        self.centralwidget.setObjectName("centralwidget")
        self.capsWatcher_logo = QtWidgets.QLabel(self.centralwidget)
        self.capsWatcher_logo.setGeometry(QtCore.QRect(20, 10, 581, 111))
        self.capsWatcher_logo.setObjectName("capsWatcher_logo")
        self.mainTab = QtWidgets.QTabWidget(self.centralwidget)
        self.mainTab.setGeometry(QtCore.QRect(20, 110, 581, 446))
        self.mainTab.setFont(segoeFont)
        self.mainTab.setObjectName("mainTab")
        self.overlayTab = QtWidgets.QWidget()
        self.overlayTab.setObjectName("overlayTab")
        self.opacityBox = QtWidgets.QGroupBox(self.overlayTab)
        self.opacityBox.setGeometry(QtCore.QRect(305, 9, 261, 61))
        self.opacityBox.setFont(normalFont)
        self.opacityBox.setObjectName("opacityBox")
        self.layoutWidget_4 = QtWidgets.QWidget(self.opacityBox)
        self.layoutWidget_4.setGeometry(QtCore.QRect(12, 20, 241, 31))
        self.layoutWidget_4.setObjectName("layoutWidget_4")
        self.opacityBoxLayout = QtWidgets.QHBoxLayout(self.layoutWidget_4)
        self.opacityBoxLayout.setContentsMargins(10, 0, 0, 0)
        self.opacityBoxLayout.setSpacing(16)
        self.opacityBoxLayout.setObjectName("opacityBoxLayout")
        self.opacityBoxSlider = QtWidgets.QSlider(self.layoutWidget_4)
        self.opacityBoxSlider.setMaximumSize(QtCore.QSize(175, 16777215))
        self.opacityBoxSlider.setOrientation(QtCore.Qt.Horizontal)
        self.opacityBoxSlider.setObjectName("opacityBoxSlider")
        self.opacityBoxSlider.setMinimum(10)
        self.opacityBoxSlider.setMaximum(100)
        self.opacityBoxSlider.setValue(85)
        self.opacityBoxLayout.addWidget(self.opacityBoxSlider)
        self.opacityBoxLabel = QtWidgets.QLabel(self.layoutWidget_4)
        self.opacityBoxLabel.setFont(segoeFont)
        self.opacityBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.opacityBoxLabel.setObjectName("opacityBoxLabel")
        self.opacityBoxLayout.addWidget(self.opacityBoxLabel)
        self.displayTimeBox = QtWidgets.QGroupBox(self.overlayTab)
        self.displayTimeBox.setGeometry(QtCore.QRect(15, 10, 261, 61))
        self.displayTimeBox.setFont(normalFont)
        self.displayTimeBox.setObjectName("displayTimeBox")
        self.layoutWidget_3 = QtWidgets.QWidget(self.displayTimeBox)
        self.layoutWidget_3.setGeometry(QtCore.QRect(12, 20, 241, 31))
        self.layoutWidget_3.setObjectName("layoutWidget_3")
        self.displayTimeBoxLayout = QtWidgets.QHBoxLayout(self.layoutWidget_3)
        self.displayTimeBoxLayout.setContentsMargins(10, 0, 0, 0)
        self.displayTimeBoxLayout.setSpacing(16)
        self.displayTimeBoxLayout.setObjectName("displayTimeBoxLayout")
        self.displayTimeBoxSlider = QtWidgets.QSlider(self.layoutWidget_3)
        self.displayTimeBoxSlider.setMaximumSize(QtCore.QSize(175, 16777215))
        self.displayTimeBoxSlider.setOrientation(QtCore.Qt.Horizontal)
        self.displayTimeBoxSlider.setObjectName("displayTimeBoxSlider")
        self.displayTimeBoxSlider.setMinimum(500)
        self.displayTimeBoxSlider.setMaximum(2000)
        self.displayTimeBoxSlider.setValue(500)
        self.displayTimeBoxLayout.addWidget(self.displayTimeBoxSlider)
        self.displayTimeBoxLabel = QtWidgets.QLabel(self.layoutWidget_3)
        self.displayTimeBoxLabel.setFont(segoeFont)
        self.displayTimeBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.displayTimeBoxLabel.setObjectName("displayTimeBoxLabel")
        self.displayTimeBoxLayout.addWidget(self.displayTimeBoxLabel)
        self.colorSchemeBox = QtWidgets.QGroupBox(self.overlayTab)
        self.colorSchemeBox.setGeometry(QtCore.QRect(305, 149, 261, 71))
        self.colorSchemeBox.setFont(normalFont)
        self.colorSchemeBox.setObjectName("colorSchemeBox")
        self.layoutWidget_12 = QtWidgets.QWidget(self.colorSchemeBox)
        self.layoutWidget_12.setGeometry(QtCore.QRect(10, 24, 241, 31))
        self.layoutWidget_12.setObjectName("layoutWidget_12")
        self.colorSchemeLayout = QtWidgets.QVBoxLayout(self.layoutWidget_12)
        self.colorSchemeLayout.setContentsMargins(6, 0, 6, 0)
        self.colorSchemeLayout.setObjectName("colorSchemeLayout")
        self.colorSchemeComboBox = QtWidgets.QComboBox(self.layoutWidget_12)
        self.colorSchemeComboBox.setFont(segoeFont)
        self.colorSchemeComboBox.setObjectName("colorSchemeComboBox")
        self.colorSchemeComboBox.addItem("")
        self.colorSchemeComboBox.addItem("")
        self.colorSchemeComboBox.addItem("")
        self.colorSchemeLayout.addWidget(self.colorSchemeComboBox)
        self.fadeEffectBox = QtWidgets.QGroupBox(self.overlayTab)
        self.fadeEffectBox.setGeometry(QtCore.QRect(15, 79, 261, 61))
        self.fadeEffectBox.setFont(normalFont)
        self.fadeEffectBox.setObjectName("fadeEffectBox")
        self.layoutWidget_7 = QtWidgets.QWidget(self.fadeEffectBox)
        self.layoutWidget_7.setGeometry(QtCore.QRect(12, 20, 241, 31))
        self.layoutWidget_7.setObjectName("layoutWidget_7")
        self.fadeEffectBoxLayout = QtWidgets.QHBoxLayout(self.layoutWidget_7)
        self.fadeEffectBoxLayout.setContentsMargins(10, 0, 0, 0)
        self.fadeEffectBoxLayout.setSpacing(16)
        self.fadeEffectBoxLayout.setObjectName("fadeEffectBoxLayout")
        self.fadeEffectBoxSlider = QtWidgets.QSlider(self.layoutWidget_7)
        self.fadeEffectBoxSlider.setMaximumSize(QtCore.QSize(175, 16777215))
        self.fadeEffectBoxSlider.setOrientation(QtCore.Qt.Horizontal)
        self.fadeEffectBoxSlider.setObjectName("fadeEffectBoxSlider")
        self.fadeEffectBoxSlider.setMinimum(50)
        self.fadeEffectBoxSlider.setMaximum(500)
        self.fadeEffectBoxSlider.setValue(150)
        self.fadeEffectBoxLayout.addWidget(self.fadeEffectBoxSlider)
        self.fadeEffectBoxLabel = QtWidgets.QLabel(self.layoutWidget_7)
        self.fadeEffectBoxLabel.setFont(segoeFont)
        self.fadeEffectBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.fadeEffectBoxLabel.setObjectName("fadeEffectBoxLabel")
        self.fadeEffectBoxLayout.addWidget(self.fadeEffectBoxLabel)
        self.positionScreenBox = QtWidgets.QGroupBox(self.overlayTab)
        self.positionScreenBox.setGeometry(QtCore.QRect(305, 79, 261, 61))
        self.positionScreenBox.setFont(normalFont)
        self.positionScreenBox.setObjectName("positionScreenBox")
        self.layoutWidget_14 = QtWidgets.QWidget(self.positionScreenBox)
        self.layoutWidget_14.setGeometry(QtCore.QRect(10, 20, 241, 31))
        self.layoutWidget_14.setObjectName("layoutWidget_14")
        self.positionScreenLayout = QtWidgets.QVBoxLayout(self.layoutWidget_14)
        self.positionScreenLayout.setContentsMargins(6, 0, 6, 0)
        self.positionScreenLayout.setObjectName("positionScreenLayout")
        self.positionScreenComboBox = QtWidgets.QComboBox(self.layoutWidget_14)
        self.positionScreenComboBox.setFont(segoeFont)
        self.positionScreenComboBox.setObjectName("positionScreenComboBox")
        self.positionScreenComboBox.addItem("")
        self.positionScreenComboBox.addItem("")
        self.positionScreenComboBox.addItem("")
        self.positionScreenComboBox.addItem("")
        self.positionScreenComboBox.addItem("")
        self.positionScreenComboBox.addItem("")
        self.positionScreenLayout.addWidget(self.positionScreenComboBox)
        self.themeBox = QtWidgets.QGroupBox(self.overlayTab)
        self.themeBox.setGeometry(QtCore.QRect(15, 149, 261, 71))
        self.themeBox.setFont(normalFont)
        self.themeBox.setObjectName("themeBox")
        self.layoutWidget = QtWidgets.QWidget(self.themeBox)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 24, 241, 31))
        self.layoutWidget.setObjectName("layoutWidget")
        self.themeBoxLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.themeBoxLayout.setContentsMargins(6, 0, 6, 0)
        self.themeBoxLayout.setObjectName("themeBoxLayout")
        self.themeComboBox = QtWidgets.QComboBox(self.layoutWidget)
        self.themeComboBox.setFont(segoeFont)
        self.themeComboBox.setObjectName("themeComboBox")
        self.themeBoxLayout.addWidget(self.themeComboBox)
        self.themeInfo = QtWidgets.QPushButton(self.layoutWidget)
        self.themeInfo.setMaximumSize(QtCore.QSize(24, 21))
        self.themeInfo.setObjectName("themeInfo")
        self.themeBoxLayout.addWidget(self.themeInfo)
        self.previewBox = QtWidgets.QGroupBox(self.overlayTab)
        self.previewBox.setGeometry(QtCore.QRect(15, 230, 261, 171))
        self.previewBox.setFont(normalFont)
        self.previewBox.setObjectName("previewBox")
        self.previewBoxBackgroundLabel = QtWidgets.QLabel(self.previewBox)
        self.previewBoxBackgroundLabel.setGeometry(QtCore.QRect(4, 21, 253, 146))
        self.previewBoxBackgroundLabel.setText("")
        self.previewBoxBackgroundLabel.setObjectName("previewBoxBackgroundLabel")
        self.previewBoxIconLabel = QtWidgets.QLabel(self.previewBox)
        self.previewBoxIconLabel.setGeometry(QtCore.QRect(65, 32, 128, 128))
        self.previewBoxIconLabel.setText("")
        self.previewBoxIconLabel.setObjectName("previewBoxIconLabel")
        self.keysToWatchBox = QtWidgets.QGroupBox(self.overlayTab)
        self.keysToWatchBox.setGeometry(QtCore.QRect(305, 230, 261, 61))
        self.keysToWatchBox.setFont(normalFont)
        self.keysToWatchBox.setCheckable(False)
        self.keysToWatchBox.setObjectName("keysToWatchBox")
        self.layoutWidget1 = QtWidgets.QWidget(self.keysToWatchBox)
        self.layoutWidget1.setGeometry(QtCore.QRect(11, 21, 247, 31))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.keysToWatchLayout = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.keysToWatchLayout.setContentsMargins(3, 0, 3, 0)
        self.keysToWatchLayout.setSpacing(3)
        self.keysToWatchLayout.setObjectName("keysToWatchLayout")
        self.numLockCheckBox = QtWidgets.QCheckBox(self.layoutWidget1)
        self.numLockCheckBox.setFont(segoeFont)
        self.numLockCheckBox.setObjectName("numLockCheckBox")
        self.keysToWatchLayout.addWidget(self.numLockCheckBox)
        self.capsLockCheckBox = QtWidgets.QCheckBox(self.layoutWidget1)
        self.capsLockCheckBox.setFont(segoeFont)
        self.capsLockCheckBox.setObjectName("capsLockCheckBox")
        self.keysToWatchLayout.addWidget(self.capsLockCheckBox)
        self.scrollLockCheckBox = QtWidgets.QCheckBox(self.layoutWidget1)
        self.scrollLockCheckBox.setFont(segoeFont)
        self.scrollLockCheckBox.setObjectName("scrollLockCheckBox")
        self.keysToWatchLayout.addWidget(self.scrollLockCheckBox)
        self.watcherStatusBox = QtWidgets.QGroupBox(self.overlayTab)
        self.watcherStatusBox.setGeometry(QtCore.QRect(305, 300, 261, 101))
        self.watcherStatusBox.setFont(normalFont)
        self.watcherStatusBox.setCheckable(False)
        self.watcherStatusBox.setObjectName("watcherStatusBox")
        self.layoutWidget2 = QtWidgets.QWidget(self.watcherStatusBox)
        self.layoutWidget2.setGeometry(QtCore.QRect(10, 20, 241, 65))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.watcherStatusLayout = QtWidgets.QVBoxLayout(self.layoutWidget2)
        self.watcherStatusLayout.setContentsMargins(0, 0, 0, 0)
        self.watcherStatusLayout.setObjectName("watcherStatusLayout")
        self.watcherStatus = QtWidgets.QLabel(self.layoutWidget2)
        self.watcherStatus.setAlignment(QtCore.Qt.AlignCenter)
        self.watcherStatus.setObjectName("watcherStatus")
        self.watcherStatusLayout.addWidget(self.watcherStatus)
        self.watcherButtonsLayout = QtWidgets.QHBoxLayout()
        self.watcherButtonsLayout.setObjectName("watcherButtonsLayout")
        self.watcherStart = QtWidgets.QPushButton(self.layoutWidget2)
        self.watcherStart.setObjectName("watcherStart")
        self.watcherButtonsLayout.addWidget(self.watcherStart)
        self.watcherStop = QtWidgets.QPushButton(self.layoutWidget2)
        self.watcherStop.setObjectName("watcherStop")
        self.watcherButtonsLayout.addWidget(self.watcherStop)
        self.watcherStatusLayout.addLayout(self.watcherButtonsLayout)
        self.mainTab.addTab(self.overlayTab, "")
        self.settingsTab = QtWidgets.QWidget()
        self.settingsTab.setObjectName("settingsTab")
        self.settingsBox = QtWidgets.QGroupBox(self.settingsTab)
        self.settingsBox.setGeometry(QtCore.QRect(15, 10, 261, 71))
        self.settingsBox.setFont(normalFont)
        self.settingsBox.setCheckable(False)
        self.settingsBox.setObjectName("settingsBox")
        self.layoutWidget_9 = QtWidgets.QWidget(self.settingsBox)
        self.layoutWidget_9.setGeometry(QtCore.QRect(10, 20, 241, 46))
        self.layoutWidget_9.setObjectName("layoutWidget_9")
        self.settingsBoxLayout = QtWidgets.QVBoxLayout(self.layoutWidget_9)
        self.settingsBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.settingsBoxLayout.setSpacing(3)
        self.settingsBoxLayout.setObjectName("settingsBoxLayout")
        self.settingsBoxAtStartupCheckBox = QtWidgets.QCheckBox(self.layoutWidget_9)
        self.settingsBoxAtStartupCheckBox.setFont(segoeFont)
        self.settingsBoxAtStartupCheckBox.setObjectName("settingsBoxAtStartupCheckBox")
        self.settingsBoxLayout.addWidget(self.settingsBoxAtStartupCheckBox)
        self.settingsBoxTrayIconCheckBox = QtWidgets.QCheckBox(self.layoutWidget_9)
        self.settingsBoxTrayIconCheckBox.setFont(segoeFont)
        self.settingsBoxTrayIconCheckBox.setObjectName("settingsBoxTrayIconCheckBox")
        self.settingsBoxLayout.addWidget(self.settingsBoxTrayIconCheckBox)
        self.languageBox = QtWidgets.QGroupBox(self.settingsTab)
        self.languageBox.setGeometry(QtCore.QRect(305, 10, 261, 71))
        self.languageBox.setFont(normalFont)
        self.languageBox.setObjectName("languageBox")
        self.layoutWidget_13 = QtWidgets.QWidget(self.languageBox)
        self.layoutWidget_13.setGeometry(QtCore.QRect(10, 24, 241, 31))
        self.layoutWidget_13.setObjectName("layoutWidget_13")
        self.languageBoxLayout = QtWidgets.QVBoxLayout(self.layoutWidget_13)
        self.languageBoxLayout.setContentsMargins(6, 0, 6, 0)
        self.languageBoxLayout.setObjectName("languageBoxLayout")
        self.languageBoxComboBox = QtWidgets.QComboBox(self.layoutWidget_13)
        self.languageBoxComboBox.setFont(segoeFont)
        self.languageBoxComboBox.setObjectName("languageBoxComboBox")
        self.languageBoxLayout.addWidget(self.languageBoxComboBox)
        self.updateResetBox = QtWidgets.QGroupBox(self.settingsTab)
        self.updateResetBox.setGeometry(QtCore.QRect(15, 190, 551, 81))
        self.updateResetBox.setFont(normalFont)
        self.updateResetBox.setObjectName("updateResetBox")
        self.layoutWidget1 = QtWidgets.QWidget(self.updateResetBox)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 19, 531, 51))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.updateResetLayout = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.updateResetLayout.setContentsMargins(0, 0, 0, 0)
        self.updateResetLayout.setSpacing(48)
        self.updateResetLayout.setObjectName("updateResetLayout")
        self.updateLayout = QtWidgets.QVBoxLayout()
        self.updateLayout.setContentsMargins(6, -1, 6, -1)
        self.updateLayout.setSpacing(0)
        self.updateLayout.setObjectName("updateLayout")
        self.updateButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.updateButton.setFont(segoeFont)
        self.updateButton.setObjectName("updateButton")
        self.updateLayout.addWidget(self.updateButton)
        self.neverUpdateCheckbox = QtWidgets.QCheckBox(self.layoutWidget1)
        self.neverUpdateCheckbox.setFont(segoeFont)
        self.neverUpdateCheckbox.setObjectName("neverUpdateCheckbox")
        self.updateLayout.addWidget(self.neverUpdateCheckbox)
        self.updateResetLayout.addLayout(self.updateLayout)
        self.resetLayout = QtWidgets.QVBoxLayout()
        self.resetLayout.setContentsMargins(6, 0, 6, -1)
        self.resetLayout.setSpacing(0)
        self.resetLayout.setObjectName("resetLayout")
        self.resetButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.resetButton.setFont(segoeFont)
        self.resetButton.setObjectName("resetButton")
        self.resetLayout.addWidget(self.resetButton)
        self.resetLabel = QtWidgets.QLabel(self.layoutWidget1)
        self.resetLabel.setMaximumSize(QtCore.QSize(16777215, 15))
        self.resetLabel.setFont(segoeFont)
        self.resetLabel.setObjectName("resetLabel")
        self.resetLayout.addWidget(self.resetLabel)
        self.updateResetLayout.addLayout(self.resetLayout)
        self.addThemeBox = QtWidgets.QGroupBox(self.settingsTab)
        self.addThemeBox.setGeometry(QtCore.QRect(15, 90, 551, 91))
        self.addThemeBox.setFont(normalFont)
        self.addThemeBox.setObjectName("addThemeBox")
        self.layoutWidget_11 = QtWidgets.QWidget(self.addThemeBox)
        self.layoutWidget_11.setGeometry(QtCore.QRect(10, 50, 531, 31))
        self.layoutWidget_11.setObjectName("layoutWidget_11")
        self.addThemeBoxLayout = QtWidgets.QHBoxLayout(self.layoutWidget_11)
        self.addThemeBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.addThemeBoxLayout.setSpacing(8)
        self.addThemeBoxLayout.setObjectName("addThemeBoxLayout")
        self.addThemeBoxLineEdit = QtWidgets.QLineEdit(self.layoutWidget_11)
        self.addThemeBoxLineEdit.setEnabled(False)
        self.addThemeBoxLineEdit.setMinimumSize(QtCore.QSize(0, 20))
        self.addThemeBoxLineEdit.setMaximumSize(QtCore.QSize(400, 16777215))
        self.addThemeBoxLineEdit.setFont(segoeFont)
        self.addThemeBoxLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.addThemeBoxLineEdit.setObjectName("addThemeBoxLineEdit")
        self.addThemeBoxLayout.addWidget(self.addThemeBoxLineEdit)
        self.addThemeBoxButton = QtWidgets.QPushButton(self.layoutWidget_11)
        self.addThemeBoxButton.setMinimumSize(QtCore.QSize(0, 20))
        self.addThemeBoxButton.setFont(segoeFont)
        self.addThemeBoxButton.setCheckable(False)
        self.addThemeBoxButton.setObjectName("addThemeBoxButton")
        self.addThemeBoxLayout.addWidget(self.addThemeBoxButton)
        self.addThemeBoxHelperLabel = QtWidgets.QLabel(self.addThemeBox)
        self.addThemeBoxHelperLabel.setGeometry(QtCore.QRect(10, 18, 531, 31))
        self.addThemeBoxHelperLabel.setFont(segoeFont)
        self.addThemeBoxHelperLabel.setWordWrap(True)
        self.addThemeBoxHelperLabel.setOpenExternalLinks(True)
        self.addThemeBoxHelperLabel.setObjectName("addThemeBoxHelperLabel")
        self.layoutWidget2 = QtWidgets.QWidget(self.settingsTab)
        self.layoutWidget2.setGeometry(QtCore.QRect(15, 280, 551, 131))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.aboutLayout = QtWidgets.QVBoxLayout(self.layoutWidget2)
        self.aboutLayout.setContentsMargins(0, 0, 0, 0)
        self.aboutLayout.setSpacing(0)
        self.aboutLayout.setObjectName("aboutLayout")
        self.about = QtWidgets.QLabel(self.layoutWidget2)
        self.about.setMaximumSize(QtCore.QSize(16777215, 25))
        self.about.setFont(segoeFont)
        self.about.setObjectName("about")
        self.aboutLayout.addWidget(self.about)
        self.aboutText = QtWidgets.QLabel(self.layoutWidget2)
        self.aboutText.setWordWrap(True)
        self.aboutText.setObjectName("aboutText")
        self.aboutLayout.addWidget(self.aboutText)
        self.aboutCopyright = QtWidgets.QLabel(self.layoutWidget2)
        self.aboutCopyright.setFont(segoeFont)
        self.aboutCopyright.setObjectName("aboutCopyright")
        self.aboutLayout.addWidget(self.aboutCopyright)
        self.mainTab.addTab(self.settingsTab, "")
        self.layoutWidget3 = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget3.setGeometry(QtCore.QRect(20, 564, 581, 27))
        self.layoutWidget3.setObjectName("layoutWidget3")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget3)
        self.horizontalLayout.setContentsMargins(6, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.infoLabel = QtWidgets.QLabel(self.layoutWidget3)
        self.infoLabel.setFont(segoeFont)
        self.infoLabel.setObjectName("versionLabel")
        self.horizontalLayout.addWidget(self.infoLabel)
        self.mainGroupButtons = QtWidgets.QHBoxLayout()
        self.mainGroupButtons.setContentsMargins(-1, 0, -1, -1)
        self.mainGroupButtons.setSpacing(6)
        self.mainGroupButtons.setObjectName("mainGroupButtons")
        self.exitButton = QtWidgets.QPushButton(self.layoutWidget3)
        self.exitButton.setMaximumSize(131, 23)
        self.exitButton.setFont(segoeFont)
        self.exitButton.setObjectName("exitButton")
        self.mainGroupButtons.addWidget(self.exitButton)
        self.applyButton = QtWidgets.QPushButton(self.layoutWidget3)
        self.applyButton.setFont(segoeFont)
        self.applyButton.setStyleSheet("")
        self.applyButton.setObjectName("applyButton")
        self.mainGroupButtons.addWidget(self.applyButton)
        self.horizontalLayout.addLayout(self.mainGroupButtons)
        self.mainTab.setCurrentIndex(0)
        self.darkLabel = ("QLabel{\n"
"    color: white;\n"
"}")
        self.darkGroupBox = ("""QGroupBox {
	color:white;
	font-size:12px;
	border: 1px solid rgb(78, 78, 78);
	border-radius:5px;
}
QGroupBox::title {
	padding-left: 6px;
	padding-right: 10px;
	padding-bottom: 6px;
}
""")
        self.darkComboBox = ("QComboBox {\n"
"        border: 1px solid rgb(78, 78, 78);\n"
"        border-radius: 3px;\n"
"        padding: 1px 18px 1px 3px;\n"
"        background-color: #333333;\n"
"        color: white;\n"
"        selection-background-color: darkgray;\n"
"    }\n"
"\n"
"    QComboBox:hover {\n"
"        background-color: #444444;\n"
"    }\n"
"\n"
"    QComboBox:!editable, QComboBox::drop-down:editable {\n"
"        background: #333333;\n"
"    }\n"
"\n"
"    QComboBox::drop-down {\n"
"        subcontrol-origin: padding;\n"
"        subcontrol-position: right;\n"
"        width: 20px;\n"
"        border-left-width: 1px;\n"
"        border-left-color: rgb(78, 78, 78);\n"
"        border-left-style: solid;\n"
"        border-top-right-radius: 2px;\n"
"        border-bottom-right-radius: 2px;\n"
"        background-color: #666666;\n"
"    }\n"
"\n"
"    QComboBox::down-arrow {\n"
"        image: url(:/capsWatcher/white-down-arrow.png);\n"
"        width: 10px;\n"
"        height: 10px;\n"
"    }\n"
"    \n"
"    QComboBox QAbstractItemView {\n"
"        border: 1px solid rgb(78, 78, 78);\n"
"        background-color: #333333;\n"
"        selection-background-color: #666666;\n"
"        border-bottom-left-radius: 3px;\n"
"        border-bottom-right-radius: 3px;\n"
"        color: white;\n"
"        outline: none;\n"
"    }")
        self.darkCheckBox = ("QCheckBox {\n"
"        color: #FFFFFF;\n"
"    }\n"
"    \n"
"    QCheckBox:disabled {\n"
"        color: #777777;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked {\n"
"        border: 1px solid #CCCCCC;\n"
"        background-color: #333333;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"        background-color: #444444;\n"
"        border: 1px solid #BBBBBB;\n"
"    }\n"
"   ")
        self.darkPushButton = ("QPushButton {\n"
"        background-color: #333333;\n"
"        color: #FFFFFF;\n"
"        border: 1px solid rgb(78, 78, 78);\n"
"        border-radius: 4px;\n"
"        padding: 3px 16px;\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: #333333;\n"
"        color: #777777;\n"
"        border: 1px solid #777777;\n"
"        border-radius: 4px;\n"
"        padding: 3px 16px;\n"
"    }\n"
"    \n"
"    QPushButton:hover {\n"
"        background-color: #444444;\n"
"        border: 1px solid #BBBBBB;\n"
"    }\n"
"    \n"
"    QPushButton:pressed {\n"
"        background-color: #222222;\n"
"        border: 1px solid #888888;\n"
"    }")
        self.darkMessageBox = ("""QMessageBox {
    background-color:rgb(40, 40, 40);
}
QMessageBox QLabel {
    color:white;
    text-align:left;
}
"""+self.darkPushButton)
        self.darkSpinBox = ("""
    QInputDialog {
        background-color:rgb(40, 40, 40);
    }

    QInputDialog QLabel {
        color:white;
        font-size:14px;
    }

    QInputDialog QSpinBox {
        font-size:18px;
        border: 1px solid gray;
        border-radius: 3px;
        padding: 2px 18px 2px 3px;
        background-color: #333333;
        color: white;
        selection-background-color: darkgray;
    }

    QSpinBox::up-button {
        subcontrol-origin: padding;
        subcontrol-position: right;
        width: 0px;
    }

    QSpinBox::down-button {
        subcontrol-origin: padding;
        subcontrol-position: right;
        width: 0px;
    }
"""+self.darkPushButton)
        self.lightGroupBox = ("""QGroupBox {
	font-size:12px;
	border: 1px solid rgb(210, 210, 210);
	border-radius:5px;
}
QGroupBox::title {
	padding-left: 6px;
	padding-right: 10px;
	padding-bottom: 6px;
}
""")
        self.lightSpinBox = ("""
    QInputDialog {
        background-color:white;
    }

    QInputDialog QLabel {
        font-size:14px;
    }

    QInputDialog QSpinBox {
        font-size:18px;
        padding: 2px 18px 2px 3px;
    }

    QSpinBox::up-button {
        subcontrol-origin: padding;
        subcontrol-position: right;
        width: 0px;
    }

    QSpinBox::down-button {
        subcontrol-origin: padding;
        subcontrol-position: right;
        width: 0px;
    }
""")
        self.lightComboBox = ("""
QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: right;
        width: 20px;
        border-left-width: 1px;
        border-left-style: solid;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
QComboBox::down-arrow {
        image: url(:/capsWatcher/grey-down-arrow.png);
        width: 10px;
        height: 10px;
    }
QComboBox QAbstractItemView {
		border: 1px solid #828790;
		outline: none;
    }
""")
        
        capsWatcher.setTabOrder(self.mainTab, self.displayTimeBoxSlider)
        capsWatcher.setTabOrder(self.displayTimeBoxSlider, self.opacityBoxSlider)
        capsWatcher.setTabOrder(self.opacityBoxSlider, self.fadeEffectBoxSlider)
        capsWatcher.setTabOrder(self.fadeEffectBoxSlider, self.positionScreenComboBox)
        capsWatcher.setTabOrder(self.positionScreenComboBox, self.themeComboBox)
        capsWatcher.setTabOrder(self.themeComboBox, self.themeInfo)
        capsWatcher.setTabOrder(self.themeInfo, self.colorSchemeComboBox)
        capsWatcher.setTabOrder(self.colorSchemeComboBox, self.numLockCheckBox)
        capsWatcher.setTabOrder(self.numLockCheckBox, self.capsLockCheckBox)
        capsWatcher.setTabOrder(self.capsLockCheckBox, self.scrollLockCheckBox)
        capsWatcher.setTabOrder(self.scrollLockCheckBox, self.watcherStart)
        capsWatcher.setTabOrder(self.watcherStart, self.watcherStop)
        
        capsWatcher.setTabOrder(self.settingsTab, self.settingsBoxAtStartupCheckBox)
        capsWatcher.setTabOrder(self.settingsBoxAtStartupCheckBox, self.settingsBoxTrayIconCheckBox)
        capsWatcher.setTabOrder(self.settingsBoxTrayIconCheckBox, self.languageBoxComboBox)
        capsWatcher.setTabOrder(self.languageBoxComboBox, self.addThemeBoxButton)
        capsWatcher.setTabOrder(self.addThemeBoxButton, self.updateButton)
        capsWatcher.setTabOrder(self.updateButton, self.neverUpdateCheckbox)
        capsWatcher.setTabOrder(self.neverUpdateCheckbox, self.resetButton)

        self.darkQuitIcon = QtGui.QIcon(":/capsWatcher/exit_light.png")
        self.darkSelectIcon = QtGui.QIcon(":/capsWatcher/source_light.png")
        self.darkResetIcon = QtGui.QIcon(":/capsWatcher/restart_light.png")
        self.darkStartIcon = QtGui.QIcon(":/capsWatcher/play_light.png")
        self.darkUpdateIcon = QtGui.QIcon(":/capsWatcher/update_light.png")
        self.darkStopIcon = QtGui.QIcon(":/capsWatcher/stop_light.png")
        self.darkApplyIcon = QtGui.QIcon(":/capsWatcher/apply_light.png")
        self.darkInfoIcon = QtGui.QIcon(":/capsWatcher/info_light.png")

        self.lightQuitIcon = QtGui.QIcon(":/capsWatcher/exit_dark.png")
        self.lightSelectIcon = QtGui.QIcon(":/capsWatcher/source_dark.png")
        self.lightResetIcon = QtGui.QIcon(":/capsWatcher/restart_dark.png")
        self.lightStartIcon = QtGui.QIcon(":/capsWatcher/play_dark.png")
        self.lightUpdateIcon = QtGui.QIcon(":/capsWatcher/update_dark.png")
        self.lightStopIcon = QtGui.QIcon(":/capsWatcher/stop_dark.png")
        self.lightApplyIcon = QtGui.QIcon(":/capsWatcher/apply_dark.png")
        self.lightInfoIcon = QtGui.QIcon(":/capsWatcher/info_dark.png")

        self.startIconDisabled = QtGui.QIcon(":/capsWatcher/play_light_disabled.png")
        self.stopIconDisabled = QtGui.QIcon(":/capsWatcher/stop_light_disabled.png")
        self.applyIconDisabled = QtGui.QIcon(":/capsWatcher/apply_light_disabled.png")

        self.watcherStart.setDisabled(True)
        self.watcherStop.setDisabled(True)
        self.applyButton.setDisabled(True)
        capsWatcher.setCentralWidget(self.centralwidget)

        QtCore.QMetaObject.connectSlotsByName(capsWatcher)
    
    def setLightMode(self, capsWatcher):
        self.capsWatcher_logo.setText("<html><head/><body><p align=\"center\"><img src=\":/capsWatcher/capsWatcher_light.png\"/></p></body></html>")
        self.previewBoxBackgroundLabel.setStyleSheet("background:url(:/capsWatcher/previewLightMode.png);border-radius:4px")
        self.opacityBoxLabel.setStyleSheet("")
        self.displayTimeBoxLabel.setStyleSheet("")
        self.colorSchemeComboBox.setStyleSheet(self.lightComboBox)
        self.fadeEffectBoxLabel.setStyleSheet("")
        self.positionScreenComboBox.setStyleSheet(self.lightComboBox)
        self.themeComboBox.setStyleSheet(self.lightComboBox)
        self.settingsBoxAtStartupCheckBox.setStyleSheet("")
        self.settingsBoxTrayIconCheckBox.setStyleSheet("")
        self.languageBoxComboBox.setStyleSheet(self.lightComboBox)
        self.updateButton.setStyleSheet("")
        self.applyButton.setStyleSheet("")
        self.neverUpdateCheckbox.setStyleSheet("")
        self.resetButton.setStyleSheet("")
        self.resetLabel.setStyleSheet("")
        self.addThemeBoxButton.setStyleSheet("")
        self.addThemeBoxHelperLabel.setStyleSheet("")
        self.about.setStyleSheet("")
        self.aboutText.setStyleSheet("")
        self.aboutCopyright.setStyleSheet("")
        self.exitButton.setStyleSheet("")
        self.numLockCheckBox.setStyleSheet("")
        self.scrollLockCheckBox.setStyleSheet("")
        self.capsLockCheckBox.setStyleSheet("")
        self.watcherStatus.setStyleSheet("")
        self.watcherStart.setStyleSheet("")
        self.watcherStop.setStyleSheet("")
        self.infoLabel.setStyleSheet("")
        self.themeInfo.setStyleSheet("")
        self.greenLabel = ("""QLabel {
    color:#1E961E;
}
""")
        self.redLabel = ("""QLabel {
    color:#961E1E;
}
""")
        self.yellowLabel = ("""QLabel {
    color:#96961E;
}
""")
        self.addThemeBoxLineEdit.setStyleSheet("QLineEdit::disabled {\n"
"    padding: 1px 18px 1px 3px;\n"
"    color: #9B9B9B;\n"
"    border-radius:3px;\n"
"    border: 1px solid #D0D0D0;\n"
"    background-color: #F9F9F9;\n"
"}")
        self.addThemeBox.setStyleSheet(self.lightGroupBox)
        capsWatcher.setStyleSheet("QMainWindow {\n"
"    background-color:white;\n"
"}")
        self.mainTab.setStyleSheet("QTabWidget::tab-bar {\n"
"   border: 1px solid white;\n"
"   padding: 10px;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"  margin-left: 15px;\n"
"  padding:10px 14px;\n"
"  border-top-left-radius: 3px;\n"
"  border-top-right-radius: 3px;\n"
"  border-bottom: 2px solid rgb(221,221,221);\n"
"  color: rgb(150, 150, 150);\n"
" }\n"
"\n"
"QTabBar::tab:hover {\n"
"  background: rgb(230,230,230);\n"
"  color: rgb(50,50,50);\n"
" }\n"
"\n"
" QTabBar::tab:selected {\n"
"  background: rgb(215, 215, 215);\n"
"  padding:8px 14px;\n"
"  border-bottom: 2px solid rgb(51,51,51);\n"
"  color: black;\n"
" }\n"
"\n"
"QTabWidget::pane{\n"
"    border: 1px;\n"
"}")
        self.opacityBox.setStyleSheet(self.lightGroupBox)
        self.displayTimeBox.setStyleSheet(self.lightGroupBox)
        self.colorSchemeBox.setStyleSheet(self.lightGroupBox)
        self.fadeEffectBox.setStyleSheet(self.lightGroupBox)
        self.positionScreenBox.setStyleSheet(self.lightGroupBox)
        self.themeBox.setStyleSheet(self.lightGroupBox)
        self.previewBox.setStyleSheet(self.lightGroupBox)
        self.settingsBox.setStyleSheet(self.lightGroupBox)
        self.languageBox.setStyleSheet(self.lightGroupBox)
        self.updateResetBox.setStyleSheet(self.lightGroupBox)
        self.keysToWatchBox.setStyleSheet(self.lightGroupBox)
        self.watcherStatusBox.setStyleSheet(self.lightGroupBox)
        self.previewBox.setStyleSheet(self.lightGroupBox)
        self.themeInfo.setIcon(self.lightInfoIcon)
        self.themeInfo.setIconSize(QtCore.QSize(13, 13))
        self.applyButton.setIcon(self.lightApplyIcon)
        self.exitButton.setIcon(self.lightQuitIcon)
        self.watcherStart.setIcon(self.lightStartIcon)
        self.watcherStop.setIcon(self.lightStopIcon)
        self.addThemeBoxButton.setIcon(self.lightSelectIcon)
        self.updateButton.setIcon(self.lightUpdateIcon)
        self.resetButton.setIcon(self.lightResetIcon)
        self.watcherStatus.setStyleSheet(self.yellowLabel)
 
    def setDarkMode(self, capsWatcher):
        self.capsWatcher_logo.setText("<html><head/><body><p align=\"center\"><img src=\":/capsWatcher/capsWatcher_dark.png\"/></p></body></html>")
        capsWatcher.setStyleSheet("QMainWindow {\n"
"    background-color:rgb(40, 40, 40);\n"
"}")
        self.previewBoxBackgroundLabel.setStyleSheet("background:url(:/capsWatcher/previewDarkMode.png);border-radius:4px")
        self.mainTab.setStyleSheet("QTabWidget::tab-bar {\n"
"   border: 1px solid white;\n"
"   padding: 10px;\n"
"}\n"
"QTabBar::tab {\n"
"  margin-left: 15px;\n"
"  border-top-left-radius: 3px;\n"
"  border-top-right-radius: 3px;\n"
"  color: rgb(131, 131, 131);\n"
"  padding:10px 14px;\n"
"  border-bottom: 2px solid rgb(60, 60, 60);"
" }\n"
"\n"
"QTabBar::tab:hover {\n"
"  background: rgb(30,30,30);\n"
"  color: rgb(220,220,220);\n"
" }\n"
"\n"
" QTabBar::tab:selected {\n"
"  background: rgb(70,70,70);\n"
"  padding:8px 14px;\n"
"  border-bottom: 2px solid rgb(221, 221, 221);\n"
"  color: white;\n"
" }\n"
"\n"
"QTabWidget::pane { \n"
"    border: 1px;\n"
"}")
        self.greenLabel = ("""QLabel {
    color:#88ff88;
}
""")
        self.redLabel = ("""QLabel {
    color:#ff8888;
}
""")
        self.yellowLabel = ("""QLabel {
    color:#fffc88;
}
""")
        self.opacityBox.setStyleSheet(self.darkGroupBox)
        self.opacityBoxLabel.setStyleSheet(self.darkLabel)
        self.displayTimeBox.setStyleSheet(self.darkGroupBox)
        self.displayTimeBoxLabel.setStyleSheet(self.darkLabel)
        self.colorSchemeBox.setStyleSheet(self.darkGroupBox)
        self.colorSchemeComboBox.setStyleSheet(self.darkComboBox)
        self.fadeEffectBox.setStyleSheet(self.darkGroupBox)
        self.fadeEffectBoxLabel.setStyleSheet(self.darkLabel)
        self.positionScreenBox.setStyleSheet(self.darkGroupBox)
        self.positionScreenComboBox.setStyleSheet(self.darkComboBox)
        self.keysToWatchBox.setStyleSheet(self.darkGroupBox)
        self.themeBox.setStyleSheet(self.darkGroupBox)
        self.themeComboBox.setStyleSheet(self.darkComboBox)
        self.themeInfo.setStyleSheet(self.darkPushButton)
        self.previewBox.setStyleSheet(self.darkGroupBox)
        self.numLockCheckBox.setStyleSheet(self.darkCheckBox)
        self.scrollLockCheckBox.setStyleSheet(self.darkCheckBox)
        self.capsLockCheckBox.setStyleSheet(self.darkCheckBox)
        self.settingsBox.setStyleSheet(self.darkGroupBox)
        self.settingsBoxAtStartupCheckBox.setStyleSheet(self.darkCheckBox)
        self.settingsBoxTrayIconCheckBox.setStyleSheet(self.darkCheckBox)
        self.languageBox.setStyleSheet(self.darkGroupBox)
        self.languageBoxComboBox.setStyleSheet(self.darkComboBox)
        self.updateResetBox.setStyleSheet(self.darkGroupBox)
        self.updateButton.setStyleSheet(self.darkPushButton)
        self.applyButton.setStyleSheet(self.darkPushButton)
        self.neverUpdateCheckbox.setStyleSheet(self.darkCheckBox)
        self.resetButton.setStyleSheet(self.darkPushButton)
        self.resetLabel.setStyleSheet(self.darkLabel)
        self.addThemeBox.setStyleSheet(self.darkGroupBox)
        self.addThemeBoxLineEdit.setStyleSheet("QLineEdit::disabled {\n"
"    border: 1px solid gray;\n"
"    border-radius: 3px;\n"
"    padding: 2px 18px 2px 3px;\n"
"    background-color: #333333;\n"
"    color: rgb(173, 173, 173);\n"
"    selection-background-color: darkgray;\n"
"}")
        self.addThemeBoxButton.setStyleSheet(self.darkPushButton)
        self.addThemeBoxHelperLabel.setStyleSheet(self.darkLabel)
        self.about.setStyleSheet(self.darkLabel)
        self.aboutText.setStyleSheet(self.darkLabel)
        self.aboutCopyright.setStyleSheet(self.darkLabel)
        self.infoLabel.setStyleSheet(self.darkLabel)
        self.exitButton.setStyleSheet(self.darkPushButton)
        self.watcherStatusBox.setStyleSheet(self.darkGroupBox)
        self.watcherStatus.setStyleSheet(self.darkLabel)
        self.watcherStart.setStyleSheet(self.darkPushButton)
        self.watcherStop.setStyleSheet(self.darkPushButton)
        self.previewBox.setStyleSheet(self.darkGroupBox)
        self.themeInfo.setIcon(self.darkInfoIcon)
        self.themeInfo.setIconSize(QtCore.QSize(13, 13))
        self.applyButton.setIcon(self.applyIconDisabled)
        self.exitButton.setIcon(self.darkQuitIcon)
        self.watcherStart.setIcon(self.startIconDisabled)
        self.watcherStop.setIcon(self.stopIconDisabled)
        self.addThemeBoxButton.setIcon(self.darkSelectIcon)
        self.updateButton.setIcon(self.darkUpdateIcon)
        self.resetButton.setIcon(self.darkResetIcon)
        self.watcherStatus.setStyleSheet(self.yellowLabel)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    capsWatcher_configInterface().show()
    sys.exit(app.exec_())