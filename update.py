import os
from os.path import dirname, join
import sys

from PyQt4.QtCore import QCoreApplication, QEvent


if not getattr(sys, 'frozen', False):

    class Updater():

        QUIT_EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

        def __init__(self, window):
            pass

        def checkForUpdates(self):
            pass

        def close(self):
            pass


elif sys.platform=='darwin':

    import objc

    class Updater():

        QUIT_EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

        # http://sparkle-project.org/documentation/customization/

        def __init__(self, window):
            try:
                objc.loadBundle('Sparkle', globals(), join(dirname(sys.executable), os.pardir, 'Frameworks', 'Sparkle.framework'))
                self.updater = SUUpdater.sharedUpdater()
            except:
                # can't load framework - not frozen or not included in app bundle?
                self.updater = None

        def checkForUpdates(self):
            if self.updater:
                self.updater.checkForUpdates_(None)

        def close(self):
            self.updater = None


elif sys.platform=='win32':

    import ctypes

    # https://github.com/vslavik/winsparkle/blob/master/include/winsparkle.h#L272

    mainwindow = None

    def shutdown_request():
        QCoreApplication.postEvent(mainwindow, QEvent(Updater.QUIT_EVENT_TYPE))


    class Updater():

        QUIT_EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

        # https://github.com/vslavik/winsparkle/wiki/Basic-Setup

        def __init__(self, window):
            try:
                sys.frozen	# don't want to try updating python.exe
                self.updater = ctypes.cdll.WinSparkle
                self.updater.win_sparkle_set_appcast_url('http://eliteocr.sourceforge.net/appcast.xml')	# py2exe won't let us embed this in resources
                self.updater.win_sparkle_set_automatic_check_for_updates(1)
                self.updater.win_sparkle_set_update_check_interval(47*60*60)

                # set up shutdown callback
                global mainwindow
                mainwindow = window
                self.callback_t = ctypes.CFUNCTYPE(None)	# keep reference
                self.callback_fn = self.callback_t(shutdown_request)
                self.updater.win_sparkle_set_shutdown_request_callback(self.callback_fn)

                self.updater.win_sparkle_init()

            except:
                from traceback import print_exc
                print_exc()
                self.updater = None

        def checkForUpdates(self):
            if self.updater:
                self.updater.win_sparkle_check_update_with_ui()

        def close(self):
            if self.updater:
                self.updater.win_sparkle_cleanup()
            self.updater = None
