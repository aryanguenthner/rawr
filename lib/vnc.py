import sys
import rdpy.core.log as log

from PyQt4 import QtCore, QtGui
from rdpy.protocol.rfb import rfb
from rdpy.ui.qt4 import qtImageFormatFromRFBPixelFormat

#set log level
log._LOG_LEVEL = log.Level.INFO

class RFBScreenShotFactory(rfb.ClientFactory):

    """
    @summary: Factory for screenshot exemple
    """
    __INSTANCE__ = 0

    def __init__(self, path, reactor, app):
        """
        @param password: password for VNC authentication
        @param path: path of output screenshot
        """
        RFBScreenShotFactory.__INSTANCE__ += 1
        self._path = path
        self._password = ''
        self._reactor = reactor
        self._app = app

    def clientConnectionLost(self, connector, reason):
        """
        @summary: Connection lost event
        @param connector: twisted connector use for rfb connection (use reconnect to restart connection)
        @param reason: str use to advertise reason of lost connection
        """
        RFBScreenShotFactory.__INSTANCE__ -= 1
        if(RFBScreenShotFactory.__INSTANCE__ == 0):
            try:
                self._reactor.stop()
            except:
                pass
            self._app.exit()

    def clientConnectionFailed(self, connector, reason):
        """
        @summary: Connection failed event
        @param connector: twisted connector use for rfb connection (use reconnect to restart connection)
        @param reason: str use to advertise reason of lost connection
        """
        RFBScreenShotFactory.__INSTANCE__ -= 1
        if(RFBScreenShotFactory.__INSTANCE__ == 0):
            try:
                self._reactor.stop()
            except:
                pass
            self._app.exit()

    def buildObserver(self, controller, addr):
        """
        @summary: build ScreenShot observer
        @param controller: RFBClientController
        @param addr: address of target
        """
        class ScreenShotObserver(rfb.RFBClientObserver):

            """
            @summary: observer that connect, cache every image received and save at deconnection
            """

            def __init__(self, controller, path):
                """
                @param controller: RFBClientController
                @param path: path of output screenshot
                """
                rfb.RFBClientObserver.__init__(self, controller)
                self._path = path
                self._buffer = None
                self._complete = False

            def onUpdate(self, width, height, x, y, pixelFormat, encoding, data):
                """
                Implement RFBClientObserver interface
                @param width: width of new image
                @param height: height of new image
                @param x: x position of new image
                @param y: y position of new image
                @param pixelFormat: pixefFormat structure in rfb.message.PixelFormat
                @param encoding: encoding type rfb.message.Encoding
                @param data: image data in accordance with pixel format and encoding
                """
                imageFormat = qtImageFormatFromRFBPixelFormat(pixelFormat)
                if imageFormat is None:
                    log.error("Receive image in bad format")
                    return
                image = QtGui.QImage(data, width, height, imageFormat)

                with QtGui.QPainter(self._buffer) as qp:
                    qp.drawImage(x, y, image, 0, 0, width, height)
                    self._complete = True

                self._controller.close()

            def onReady(self):
                """
                @summary: callback use when RDP stack is connected (just before received bitmap)
                """
                width, height = self._controller.getScreen()
                self._buffer = QtGui.QImage(
                    width, height, QtGui.QImage.Format_RGB32)

            def onClose(self):
                """
                @summary: callback use when RDP stack is closed
                """
                if self._complete:
                    self._buffer.save(self._path)

        controller.setPassword(self._password)
        return ScreenShotObserver(controller, self._path)
        

def get_screenshot(ip, port, logdir):
    log._LOG_LEVEL = log.Level.ERROR
    app = QtGui.QApplication(sys.argv)

    import qt4reactor
    try: qt4reactor.install()
    except: pass
    from twisted.internet import reactor

    try: os.mkdirs(logdir + "5_Reporting/images/")
    except: pass

    path = "%s/5_Reporting/images/vnc_%s_%s.jpg" % (logdir, ip, port)
    reactor.connectTCP(ip, int(port), RFBScreenShotFactory(path, reactor, app))

    try: reactor.runReturn(installSignalHandlers=0)
    except: pass
    app.exec_()

    return "%s/5_Reporting/images/vnc_%s_%s.jpg" % (logdir, ip, port)
