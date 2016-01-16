# -*- coding: utf-8 -*-
import sys
import random
import os
from os import environ, listdir, makedirs
from os.path import isfile, isdir, basename, dirname, join, normpath
from platform import machine
from sys import platform
from PyQt4.QtCore import QSettings, QString, QT_VERSION
from PyQt4.QtGui import QMessageBox, QFileDialog, QDesktopServices

if platform == 'win32':
    import ctypes
    CSIDL_LOCAL_APPDATA = 0x001c
    CSIDL_PROGRAM_FILESX86 = 0x002a
    SHGFP_TYPE_CURRENT = 0 	# Current, not default, values

    # _winreg that ships with Python 2 doesn't support unicode, so do this instead
    from ctypes.wintypes import *

    HKEY_CURRENT_USER       = 0x80000001
    HKEY_LOCAL_MACHINE      = 0x80000002
    KEY_READ                = 0x00020019
    REG_SZ    = 1

    RegOpenKeyEx = ctypes.windll.advapi32.RegOpenKeyExW
    RegOpenKeyEx.restype = LONG
    RegOpenKeyEx.argtypes = [HKEY, LPCWSTR, DWORD, DWORD, ctypes.POINTER(HKEY)]

    RegCloseKey = ctypes.windll.advapi32.RegCloseKey
    RegCloseKey.restype = LONG
    RegCloseKey.argtypes = [HKEY]

    RegQueryValueEx = ctypes.windll.advapi32.RegQueryValueExW
    RegQueryValueEx.restype = LONG
    RegQueryValueEx.argtypes = [HKEY, LPCWSTR, LPCVOID, ctypes.POINTER(DWORD), LPCVOID, ctypes.POINTER(DWORD)]

    RegEnumKeyEx = ctypes.windll.advapi32.RegEnumKeyExW
    RegEnumKeyEx.restype = LONG
    RegEnumKeyEx.argtypes = [HKEY, DWORD, LPWSTR, ctypes.POINTER(DWORD), ctypes.POINTER(DWORD), LPWSTR, ctypes.POINTER(DWORD), ctypes.POINTER(FILETIME)]

elif platform == 'darwin':
    from Foundation import NSHomeDirectory, NSSearchPathForDirectoriesInDomains, NSDocumentDirectory, NSApplicationSupportDirectory, NSPicturesDirectory, NSUserDomainMask

appconf = (platform=="darwin" and "AppConfigLocal.xml" or "AppConfig.xml")


class Settings():
    def __init__(self, parent=None):
        self.parent = parent
        self.app_path = self.getPathToSelf()
        self.storage_path = self.getPathToStorage()
        self.values = {}
        self.reg = QSettings()	# uses QCoreApplication.organizationName and applicationName
        self.userprofile = self.getUserProfile()
        if self.reg.contains('settings_version'):
            if float(self.reg.value('settings_version', type=QString)) < 1.6:
                self.cleanReg()
                self.setAllDefaults()
                self.reg.sync()
                self.values = self.loadSettings()
            else:
                self.values = self.loadSettings()
                self.values['create_nn_images'] = False
        else:
            self.cleanReg()
            self.setAllDefaults()
            self.reg.sync()
            self.values = self.loadSettings()
    
    def __getitem__(self, key):
        if key in self.values:
            return self.values[key]
        else:
            raise KeyError("Key "+unicode(key)+" not found in settings.")
            
    def setValue(self, key, value):
        self.reg.setValue(key, value)
        
    def sync(self):
        """Save changes and reload settings"""
        self.reg.sync()
        self.values = self.loadSettings()
        
    def cleanReg(self):
        """Clean all registry entries (for old version or version not set)"""
        keys = self.reg.allKeys()
        for key in keys:
            self.reg.remove(key)

    def loadSettings(self):
        """Load all settings to a dict"""
        set = {'first_run': self.reg.value('first_run', True, type=bool),
               'screenshot_dir': self.reg.value('screenshot_dir', type=QString),
               'export_dir': self.reg.value('export_dir', type=QString),
               'horizontal_exp': self.reg.value('horizontal_exp', False, type=bool),
               'gray_preview': self.reg.value('gray_preview', False, type=bool),
               'last_export_format': self.reg.value('last_export_format', "csv", type=QString),
               'log_dir': self.reg.value('log_dir', type=QString),
               'auto_fill': self.reg.value('auto_fill', type=bool),
               'remove_dupli': self.reg.value('remove_dupli', type=bool),
               'userID': self.reg.value('userID', type=QString),
               'ui_language': self.reg.value('ui_language', type=QString),
               'ocr_language': self.reg.value('ocr_language', type=QString),
               'delete_files': self.reg.value('delete_files', type=bool),
               'translate_results': self.reg.value('translate_results', type=bool),
               'pause_at_end': self.reg.value('pause_at_end', type=bool),
               'public_mode': self.reg.value('public_mode', type=bool),
               'native_dialog': self.reg.value('native_dialog', type=bool),
               'create_nn_images': self.reg.value('create_nn_images', type=bool),
               'zoom_factor': self.reg.value('zoom_factor', 1.0, type=float),
               'info_accepted': self.reg.value('info_accepted', False, type=bool),
               'theme': self.reg.value('theme', 'default', type=QString),
               'input_size': self.reg.value('input_size', 30, type=int),
               'snippet_size': self.reg.value('snippet_size', 30, type=int),
               'label_color': self.reg.value('label_color', '#ff7f0f', type=QString),
               'input_color': self.reg.value('input_color', '#ffffff', type=QString),
               'button_color': self.reg.value('button_color', '#ff7f0f', type=QString),
               'button_border_color': self.reg.value('button_border_color', '#af4f0f', type=QString),
               'border_color': self.reg.value('border_color', '#af4f0f', type=QString),
               'background_color': self.reg.value('background_color', '#000000', type=QString),
               'color1': self.reg.value('color1', '#ffffff', type=QString),
               'color2': self.reg.value('color2', '#ffffff', type=QString),
               'color3': self.reg.value('color3', '#ffffff', type=QString),
               'color4': self.reg.value('color4', '#ffffff', type=QString),
               'color5': self.reg.value('color5', '#ffffff', type=QString),
               'contrast': self.reg.value('contrast', 85.0, type=float)}
        return set
        
    def setAllDefaults(self):
        """Set all settings to default values"""
        self.setDefaultAutoFill()
        self.setDefaultRemoveDupli()
        self.setDefaultCreateNNImg()
        self.setDefaultDelete()
        self.setDefaultTranslateResults()
        self.setDefaultPause()
        self.setDefaultPublicMode()
        self.setDefaultNativeDialog()
        self.setDefaultScreenshotDir()
        self.setDefaultLogDir()
        self.setDefaultExportDir()
        self.setDefaultLanguage()
        self.setUserID()
        self.setSettingsVersion()
        
    def setSettingsVersion(self):
        self.reg.setValue('settings_version', "1.6")
        
    def setUserID(self):
        self.reg.setValue('userID', "EO"+''.join(random.choice('0123456789abcdef') for i in range(8)))
        
    def setDefaultExportOptions(self):
        self.setValue('horizontal_exp', False)
        self.setValue('last_export_format', 'xlsx')
    
    def setDefaultAutoFill(self):
        self.reg.setValue('auto_fill', False)
        
    def setDefaultRemoveDupli(self):
        self.reg.setValue('remove_dupli', True)
    
    def setDefaultLanguage(self):
        self.reg.setValue('ui_language', "en")
        self.reg.setValue('ocr_language', "eng")
        
    def setDefaultCreateNNImg(self):
        self.reg.setValue('create_nn_images', False)
        
    def setDefaultDelete(self):
        self.reg.setValue('delete_files', False)
        
    def setDefaultTranslateResults(self):
        self.reg.setValue('translate_results', False)
    
    def setDefaultPause(self):
        self.reg.setValue('pause_at_end', True)
        
    def setDefaultPublicMode(self):
        self.reg.setValue('public_mode', True)
    
    def setDefaultNativeDialog(self):
        # Native save dialogs bugged on 4.8.6 on OSX - https://codereview.qt-project.org/#/c/94980/
        self.reg.setValue('native_dialog', platform=="darwin" and QT_VERSION>=0x40807)
        
    def setDefaultScreenshotDir(self):
        path = join(unicode(QDesktopServices.storageLocation(QDesktopServices.PicturesLocation)), "Frontier Developments", "Elite Dangerous")
        self.reg.setValue('screenshot_dir', isdir(path) and path or self.userprofile)
        
    def setDefaultLogDir(self):
        self.reg.setValue('log_dir', self.getLogDir() or self.userprofile)

    def getLogDir(self):
        if platform == 'win32':
            # https://support.elitedangerous.com/kb/faq.php?id=108
            candidates = []

            # Steam and Steam libraries
            key = HKEY()
            if not RegOpenKeyEx(HKEY_CURRENT_USER, r'Software\Valve\Steam', 0, KEY_READ, ctypes.byref(key)):
                valtype = DWORD()
                valsize = DWORD()
                if not RegQueryValueEx(key, 'SteamPath', 0, ctypes.byref(valtype), None, ctypes.byref(valsize)) and valtype.value == REG_SZ:
                    buf = ctypes.create_unicode_buffer(valsize.value / 2)
                    if not RegQueryValueEx(key, 'SteamPath', 0, ctypes.byref(valtype), buf, ctypes.byref(valsize)):
                        steampath = buf.value.replace('/', '\\')	# For some reason uses POSIX seperators
                        steamlibs = [steampath]
                        try:
                            # Simple-minded Valve VDF parser
                            with open(join(steampath, 'config', 'config.vdf'), 'rU') as h:
                                for line in h:
                                    vals = line.split()
                                    if vals and vals[0].startswith('"BaseInstallFolder_'):
                                        steamlibs.append(vals[1].strip('"').replace('\\\\', '\\'))
                        except:
                            pass
                        for lib in steamlibs:
                            candidates.append(join(lib, 'steamapps', 'common', 'Elite Dangerous Horizons', 'Products'))
                            candidates.append(join(lib, 'steamapps', 'common', 'Elite Dangerous', 'Products'))
                RegCloseKey(key)

            # Next try custom installation under the Launcher
            candidates.append(self.getCustomLogDir() or '')

            # Standard non-Steam locations
            programs = ctypes.create_unicode_buffer(MAX_PATH)
            ctypes.windll.shell32.SHGetSpecialFolderPathW(0, programs, CSIDL_PROGRAM_FILESX86, 0)
            candidates.append(join(programs.value, 'Frontier', 'Products')),

            applocal = ctypes.create_unicode_buffer(MAX_PATH)
            ctypes.windll.shell32.SHGetSpecialFolderPathW(0, applocal, CSIDL_LOCAL_APPDATA, 0)
            candidates.append(join(applocal.value, 'Frontier_Developments', 'Products'))

            for game in ['elite-dangerous-64', 'FORC-FDEV-D-1']:	# Look for Horizons in all candidate places first
                for base in candidates:
                    if isdir(base):
                        for d in listdir(base):
                            if d.startswith(game) and isfile(join(base, d, 'AppConfig.xml')) and isdir(join(base, d, 'Logs')):
                                return join(base, d, 'Logs')

        elif platform == 'darwin':
            # https://support.frontier.co.uk/kb/faq.php?id=97
            suffix = join("Frontier Developments", "Elite Dangerous", "Logs")
            paths = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, True)
            if len(paths) and isdir(join(paths[0], suffix)):
                return join(paths[0], suffix)

        return None	# not found in standard places

    def getCustomLogDir(self):
        if platform == 'win32':
            key = HKEY()
            if not RegOpenKeyEx(HKEY_LOCAL_MACHINE,
                                machine().endswith('64') and
                                r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall' or	# Assumes that the launcher is a 32bit process
                                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                                0, KEY_READ, ctypes.byref(key)):
                buf = ctypes.create_unicode_buffer(MAX_PATH)
                i = 0
                while True:
                    size = DWORD(MAX_PATH)
                    if RegEnumKeyEx(key, i, buf, ctypes.byref(size), None, None, None, None):
                        break

                    subkey = HKEY()
                    if not RegOpenKeyEx(key, buf, 0, KEY_READ, ctypes.byref(subkey)):
                        valtype = DWORD()
                        valsize = DWORD((len('Frontier Developments')+1)*2)
                        valbuf = ctypes.create_unicode_buffer(valsize.value / 2)
                        if not RegQueryValueEx(subkey, 'Publisher', 0, ctypes.byref(valtype), valbuf, ctypes.byref(valsize)) and valtype.value == REG_SZ and valbuf.value == 'Frontier Developments':
                            if not RegQueryValueEx(subkey, 'InstallLocation', 0, ctypes.byref(valtype), None, ctypes.byref(valsize)) and valtype.value == REG_SZ:
                                valbuf = ctypes.create_unicode_buffer(valsize.value / 2)
                                if not RegQueryValueEx(subkey, 'InstallLocation', 0, ctypes.byref(valtype), valbuf, ctypes.byref(valsize)):
                                    return(join(valbuf.value, 'Products'))
                        RegCloseKey(subkey)
                    i += 1
                RegCloseKey(key)
        return None

    def setDefaultExportDir(self):
        path = unicode(QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation))
        self.reg.setValue('export_dir', isdir(path) and path or self.userprofile)

    def getUserProfile(self):
        path = unicode(QDesktopServices.storageLocation(QDesktopServices.HomeLocation))
        return isdir(path) and path or u"."

    def getPathToSelf(self):
        """Return the path to our supporting files"""
        if getattr(sys, 'frozen', False):
            if platform=='darwin':
                application_path = normpath(join(dirname(sys.executable), os.pardir, 'Resources'))
            else:
                application_path = dirname(sys.executable).decode(sys.getfilesystemencoding())
        elif __file__:
            application_path = dirname(__file__).decode(sys.getfilesystemencoding())
        else:
            application_path = u"."
        return application_path

    def getPathToStorage(self):
        """Return the path to a place for writing supporting files"""
        if platform=='win32':
            path = join(self.getPathToSelf(), "trainingdata")	# Store writable data alongside executable
        else:
            path = unicode(QDesktopServices.storageLocation(QDesktopServices.DataLocation))
        if not isdir(path):
            makedirs(path)
        return path


# AppConfig helpers

def isValidLogPath(logpath):
    return isfile(join(logpath, os.pardir, (platform=="darwin" and "AppNetCfg.xml" or "AppConfig.xml")))

def hasAppConf(logpath):
    return isfile(join(logpath, os.pardir, appconf))

def hasVerboseLogging(logpath):
    path = join(logpath, os.pardir, appconf)
    if isfile(path):
        file = open(path, 'rt')
        file_content = file.read()
        file.close()
        start = file_content.find("<Network")
        end = file_content.find("</Network>")
        return file_content.lower().find('verboselogging="1"', start, end) >= 0
    return False

def enableVerboseLogging(logpath):
    path = join(logpath, os.pardir, appconf)
    if not isValidLogPath(logpath) or hasVerboseLogging(logpath):
        return False
    elif not hasAppConf(logpath):
        if platform=="darwin":
            # Create new file
            f = open(path, 'wt')
            f.write('<AppConfig>\n\t<Network\n\t\tVerboseLogging="1"\n\t>\n\t</Network>\n</AppConfig>\n')
            f.close()
            return True
        else:
            return False	# Can't amend file that doesn't exist

    f = open(path, 'rt')
    file_content = f.read()
    f.close()

    f = open(path[:-4] + "_backup.xml", 'wt')
    f.write(file_content)
    f.close()

    f = open(path, 'wt')
    start = file_content.find("<Network")
    if start >= 0:
        f.write(file_content[:start+8] + '\n\t\tVerboseLogging="1"' + file_content[start+8:])
    else:
        start = file_content.find("</AppConfig>")
        if start >= 0:
            f.write(file_content[:start] + '\t<Network\n\t\tVerboseLogging="1"\n\t>\n\t</Network>\n' + file_content[start:])
        else:
            f.write(file_content)	# eh ?
    f.close()

    return True
