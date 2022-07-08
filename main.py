import subprocess

import PySide2
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import QTableWidgetItem, QListWidgetItem

from form_main import Ui_Form
from form_tracert import Ui_Form as form_tracert
from form_settings import Ui_Form as form_settings


class MyWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.initUi()
        self.initWindows()

        self.initThreads()

    def initWindows(self):
         self.childWindow = Child()
         self.childWindow_2 = Child_2()

    def open_childWindow(self):
        self.childWindow.show()

    def open_childWindow_2(self):
        self.childWindow_2.show()

    def initThreads(self):
        self.tracertThread = TracertThread()
        self.pingThread = PingThread()

        #init threads signals
        self.tracertThread.mySignal.connect(self.tracertThreadSignal)

        self.pingThread.started.connect(self.pingThreadStarted)
        self.pingThread.finished.connect(self.pingThreadFinished)
        self.pingThread.pingSignal.connect(self.pingThreadpingSignal)

    def initUi(self):
        # init widget signals
        self.ui.pushButton_3.clicked.connect(self.OnPBTracerClicked)

        self.ui.pushButton_4.clicked.connect(self.open_childWindow_2)

        self.ui.pushButton.clicked.connect(self.OnPBStartPingClicked)
        self.ui.pushButton_2.clicked.connect(self.OnPBStopPingClicked)

    #slots for tracert

    def OnPBTracerClicked(self) -> None:
        """
        Слот для кнопки потока self.tracertThread
        :return: None
        """
        text, ok = QtWidgets.QInputDialog.getText(self, "IP-address", "Введите IP")
        self.tracertThread.setIP(text)
        if ok:
            self.open_childWindow()
            self.tracertThread.start()

    def tracertThreadSignal(self, values) -> None:
        """
        Слот для обработки сигнала, который шлёт данные из потока self.tracertThread
        :param values: данные, полученные от tracert
        :return: None
        """
        self.childWindow.ui.plainTextEdit.setPlainText(values)

    #slots for ping

    def OnPBStartPingClicked(self):
        """
        Слот для кнопки start потока self.pingThread
        :return: None
        """
        text, ok = QtWidgets.QInputDialog.getText(self, "IP-address", "Введите IP")
        self.pingThread.setIP(text)
        if ok:
            self.pingThread.start()


    def OnPBStopPingClicked(self):
        self.pingThread.status = False

    def pingThreadStarted(self):
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(True)


    def pingThreadFinished(self):
        """
        Слот для сигнала finished потока self.timerThread
        :return: None
        """
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_2.setEnabled(False)

    def pingThreadpingSignal(self, emit_value) -> None:
        """
        Слот для обработки сигнала, который шлёт данные из потока self.pingThread
        :param emit_value: данные, полученные от Ping
        :return: None
        """
        flag = "потеряно = 0"
        i = self.ui.tableWidget.rowCount()
        if flag in str(emit_value):
            i += 1
            self.ui.tableWidget.setItem(i, 1, QTableWidgetItem(self.pingThread.ip))
            self.ui.tableWidget.setItem(i, 2, QTableWidgetItem("Доступен"))
        else:
            self.ui.tableWidget.setItem(i, 1, QTableWidgetItem(self.pingThread.ip))
            self.ui.tableWidget.setItem(i, 2, QTableWidgetItem("Недоступен"))
            self.ui.plainTextEdit.setPlainText(emit_value)


    #Threads

class TracertThread(QtCore.QThread):
    Signal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ip = None
        self.status = None

    def setIP(self, ip):
        """
        Метод для установки ip-адреса
        :param ip: значение ip-адреса
        :return: None
        """
        self.ip = ip

    def run(self):
        self.status = True
        while self.status:
            command = f"tracert {self.ip}"
            pr = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout, stderr = pr.communicate()
            self.Signal.emit(str(stdout.decode("cp866", "ignore")))


class PingThread(QtCore.QThread):
    pingSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = None
        self.ip = None

    def setIP(self, ip):
        """
        Метод для установки ip-адреса
        :param ip: значение ip-адреса
        :return: None
        """
        self.ip = ip

    def run(self):
        self.status = True
        while self.status:
            cmd_command = f"ping {self.ip} -n 1"
            pr = subprocess.Popen(cmd_command.split(" "), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout, stderr = pr.communicate()
            self.pingSignal.emit(str(stdout.decode("cp866", "ignore")))


# Класс, создающий окно для вывода данных из tracert
class Child(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = form_tracert()
        self.ui.setupUi(self)

        self.initUi()

    def initUi(self):
        pass


# Класс, создающий окно settings
class Child_2(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = form_settings()
        self.ui.setupUi(self)

        self.ip_list_settings = QtCore.QSettings("Qt_exam")

        self.initUi()

    def initUi(self): #НЕ РАБОТАЕТ
        ip_list = self.ip_list_settings.value("ip_list", [])  # ошибка EOFError: Ran out of input
        i = 0
        if ip_list:
            self.ui.listWidget.addItem(QListWidgetItem(ip_list[i]))
            i += 1

    def closeEvent(self, event: PySide2.QtGui.QCloseEvent) -> None:
        if self.ui.listWidget.count():
            rows = self.ui.listWidget.count()
            for i in range(0, rows):
                self.ip_list_settings.setValue("ip_list", [self.ui.listWidget.item(i)])


if __name__ == "__main__":
    app = QtWidgets.QApplication()

    win = MyWindow()
    win.show()

    app.exec_()
