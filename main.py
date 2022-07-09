import subprocess
from time import ctime

import PySide2
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import QTableWidgetItem

from form_main import Ui_Form
from form_tracert import Ui_Form as form_tracert
from form_settings import Ui_Form as form_settings


class MyWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ip_list_settings = QtCore.QSettings("Qt_exam")

        self.initUi()
        self.initWindows()

        self.initThreads()

        self.loadIPList()

    def initWindows(self):
        self.tracertWindow = tracertWindow()
        self.settingsWindow = settingsWindow()

        self.settingsWindow.signal_ip_list.connect(self.load_ip_list_from_settings)

    def open_tracertWindow(self):
        self.tracertWindow.show()

    def open_settingsWindow(self):
        self.settingsWindow.show()

    def initThreads(self):
        self.tracertThread = TracertThread()
        self.pingThread = PingThread()

        # init threads signals
        self.tracertThread.mySignal.connect(self.tracertThreadSignal)

        self.pingThread.started.connect(self.pingThreadStarted)
        self.pingThread.finished.connect(self.pingThreadFinished)
        self.pingThread.pingSignal.connect(self.pingThreadpingSignal)

    def initUi(self):
        # init widget signals
        self.ui.pushButton_3.clicked.connect(self.OnPBTracerClicked)

        self.ui.pushButton_4.clicked.connect(self.open_settingsWindow)

        self.ui.pushButton.clicked.connect(self.OnPBStartPingClicked)
        self.ui.pushButton_2.clicked.connect(self.OnPBStopPingClicked)

    def loadIPList(self):
        ip_list = self.ip_list_settings.value("ip_list", [])
        if ip_list:
            self.load_ip_list_from_settings(ip_list)

    # slots for tracert

    def OnPBTracerClicked(self) -> None:
        """
        Слот для кнопки потока self.tracertThread
        :return: None
        """
        text, ok = QtWidgets.QInputDialog.getText(self, "IP-address", "Введите IP")
        self.tracertThread.setIP(text)
        if ok:
            self.open_tracertWindow()
            self.tracertThread.start()

    def tracertThreadSignal(self, values) -> None:
        """
        Слот для обработки сигнала, который шлёт данные из потока self.tracertThread
        :param values: данные, полученные от tracert
        :return: None
        """
        self.tracertWindow.ui.plainTextEdit.setPlainText(values)

    # slots for ping

    def OnPBStartPingClicked(self):
        """
        Слот для кнопки start потока self.pingThread
        :return: None
        """
        rows = self.ui.tableWidget.rowCount()
        for row in range(rows):
            ip_addr = self.ui.tableWidget.item(row, 0).text()
            self.pingThread.ip = ip_addr

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
        for row in range(self.ui.tableWidget.rowCount()):
            if flag in str(emit_value):
                self.ui.tableWidget.setItem(row, 1, QTableWidgetItem("Доступен"))
            else:
                self.ui.tableWidget.setItem(row, 1, QTableWidgetItem("Недоступен"))
                self.ui.plainTextEdit.setPlainText(f"Ip-адрес {self.ui.tableWidget.item(row, 0).text()} недоступен. Время потери доступа: {ctime()}")

    def load_ip_list_from_settings(self, emit_value):
        self.ui.tableWidget.clear()

        self.ui.tableWidget.setRowCount(len(emit_value))

        for row, elem in enumerate(emit_value):
            self.ui.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(elem))

    # Threads


class TracertThread(QtCore.QThread):
    mySignal = QtCore.Signal(str)

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
            self.mySignal.emit(str(stdout.decode("cp866", "ignore")))


class PingThread(QtCore.QThread):
    pingSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = None
        self.ip = None

    def run(self):
        self.status = True
        while self.status:
            cmd_command = f"ping {self.ip} -n 1"
            pr = subprocess.Popen(cmd_command.split(" "), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout, stderr = pr.communicate()
            self.pingSignal.emit(str(stdout.decode("cp866", "ignore")))


# Класс, создающий окно для вывода данных из tracert
class tracertWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = form_tracert()
        self.ui.setupUi(self)

        self.initUi()

    def initUi(self):
        pass


# Класс, создающий окно settings
class settingsWindow(QtWidgets.QWidget):
    signal_ip_list = QtCore.Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = form_settings()
        self.ui.setupUi(self)

        self.ip_list_settings = QtCore.QSettings("Qt_exam")

        self.initUi()

        self.load_ip()

    def initUi(self):
        self.ui.pushButton.clicked.connect(self.add_ip)
        self.ui.pushButton_2.clicked.connect(self.delete_ip)

    def add_ip(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "ip", "ip")

        if not ok:
            return
        for symbol in text:
            if symbol.isalpha():
                QtWidgets.QMessageBox.critical(self, "Ошибка!!!", "Неверный ip-адрес!", QtWidgets.QMessageBox.Ok)
                return

        self.ui.listWidget.addItem(text)

    def delete_ip(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "ip", "удалить ip-адрес")

        if not ok:
            return

        for row in range(self.ui.listWidget.count()):
            if text == self.ui.listWidget.item(row).text():
                self.ui.listWidget.takeItem(row)

    def load_ip(self):
        ip_list = self.ip_list_settings.value("ip_list", [])
        if ip_list:
            for ip_addr in ip_list:
                self.ui.listWidget.addItem(ip_addr)

    def get_ip_list(self):
        result = []

        for i in range(self.ui.listWidget.count()):
            result.append(self.ui.listWidget.item(i).text())

        return result

    def closeEvent(self, event: PySide2.QtGui.QCloseEvent) -> None:

        ip_list = self.get_ip_list()
        self.signal_ip_list.emit(ip_list)
        self.ip_list_settings.setValue("ip_list", ip_list)


if __name__ == "__main__":
    app = QtWidgets.QApplication()

    win = MyWindow()
    win.show()

    app.exec_()
