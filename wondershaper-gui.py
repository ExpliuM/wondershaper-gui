#!/usr/bin/env python

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
                             QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
                             QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
                             QVBoxLayout, QWidget, QMessageBox)

from subprocess import Popen, PIPE
from shlex import split
from typing import Union
from glob import glob

import os
import signal
import sys
import time
import threading

runWondershaperThread = False


def getNicList():
    # Full bash command: ifconfig -s -a | cut -d " " -f 1 | sed '1d;$d'
    p1 = Popen(split("ifconfig -s -a"), stdout=PIPE, stderr=PIPE)
    p2 = Popen(split('cut -d " " -f 1'), stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
    p3 = Popen(split("sed '1d;$d'"), stdin=p2.stdout, stdout=PIPE, stderr=PIPE)
    outs, errs = p3.communicate(timeout=15)
    return str(outs.decode('UTF-8').strip()).split("\n")


def wondershaperLimitScript(nic, downlinkLimit, uplinkLimit):
    downlinkLimitCommandPart = ""
    uplinkLimitCommandPart = ""

    if (downlinkLimit is not None):
        downlinkLimitCommandPart = " -d " + str(downlinkLimit) + " "

    if (uplinkLimit is not None):
        uplinkLimitCommandPart = "-u " + str(uplinkLimit)

    # Full bash command: sudo wondershaper -a nic -d downlinklimit -u uplinklimit
    print("sudo wondershaper -a " + nic +
          downlinkLimitCommandPart + uplinkLimitCommandPart)
    p1 = Popen(split("sudo wondershaper -a " + nic +
                     downlinkLimitCommandPart + uplinkLimitCommandPart))
    p1.communicate(timeout=15)


def wondershaperStopLimits(nic):
    print("sudo wondershaper -c -a " + str(nic))
    p1 = Popen(split("sudo wondershaper -c -a " + str(nic)))
    p1.communicate(timeout=15)


def automaticWondershaperThreadFunction():
    global app

    while (runWondershaperThread):
        app.wondershaperGroupBox.runWondershaper()

        time_to_end = time.time() + int(app.wondershaperGroupBox.limitTimeLineEdit.text())
        current_time = time.time()

        while (current_time < time_to_end and runWondershaperThread):
            current_time = time.time()

        app.wondershaperGroupBox.stopWondershaper()

        time_to_end = time.time() + int(app.wondershaperGroupBox.noLimitTimeLineEdit.text())
        current_time = time.time()
        while (current_time < time_to_end and runWondershaperThread):
            current_time = time.time()


class WondershaperGroupBox(QGroupBox):
    runStopPushButton = None
    runStopAutomaticPushButton = None

    nicComboBox = None

    downlinkLimitCheckBox = None
    downlinkLimitLineEdit = None

    uplinkLimitCheckBox = None
    uplinkLimitLineEdit = None

    limitTimeLineEdit = None
    noLimitTimeLineEdit = None

    automaticWondershaperThread = None

    def __init__(self, parent=None):
        super(WondershaperGroupBox, self).__init__("Wondershaper")

        nicLabel = QLabel("NIC:")
        self.nicComboBox = QComboBox()

        self.downlinkLimitCheckBox = QCheckBox('', self)
        self.downlinkLimitCheckBox.stateChanged.connect(
            self.updateDownlinkLimitCheckBox)

        downlinkLimitLable = QLabel("downlink limit(Kbps)")
        self.downlinkLimitLineEdit = QLineEdit("1200")

        self.uplinkLimitCheckBox = QCheckBox('', self)
        self.uplinkLimitCheckBox.stateChanged.connect(
            self.updateUplinkLimitCheckBox)

        uplinkLimiLable = QLabel("uplink limit(Kbps)")
        self.uplinkLimitLineEdit = QLineEdit("")

        limitTimeLable = QLabel("limit time(sec)")
        self.limitTimeLineEdit = QLineEdit("30")

        noLimitTimeLable = QLabel("no limit time(sec)")
        self.noLimitTimeLineEdit = QLineEdit("30")

        self.runStopPushButton = QPushButton("Run Wondershaper")
        self.runStopPushButton.setDefault(True)
        self.runStopPushButton.clicked.connect(
            self.On_Click_RunStopPushButton)

        self.runStopAutomaticPushButton = QPushButton(
            "Run automatic Wondershaper")
        self.runStopAutomaticPushButton.setDefault(True)
        self.runStopAutomaticPushButton.clicked.connect(
            self.On_Click_RunStopAutoPushButton)

        self.downlinkLimitLineEdit.setDisabled(True)
        self.uplinkLimitLineEdit.setDisabled(True)

        self.updateNicComboBox()

        layout = QGridLayout()
        layout.addWidget(nicLabel, 0, 0)
        layout.addWidget(self.nicComboBox, 0, 1)
        layout.addWidget(self.downlinkLimitCheckBox, 0, 2)
        layout.addWidget(downlinkLimitLable, 0, 3)
        layout.addWidget(self.downlinkLimitLineEdit, 0, 4)
        layout.addWidget(self.uplinkLimitCheckBox, 0, 5)
        layout.addWidget(uplinkLimiLable, 0, 6)
        layout.addWidget(self.uplinkLimitLineEdit, 0, 7)
        layout.addWidget(limitTimeLable, 0, 8)
        layout.addWidget(self.limitTimeLineEdit, 0, 9)
        layout.addWidget(noLimitTimeLable, 0, 10)
        layout.addWidget(self.noLimitTimeLineEdit, 0, 11)
        layout.addWidget(self.runStopPushButton, 1, 0, 1, 12)
        layout.addWidget(self.runStopAutomaticPushButton, 2, 0, 1, 12)
        self.setLayout(layout)

    def updateDownlinkLimitCheckBox(self, state):
        if state == Qt.Checked:
            self.downlinkLimitLineEdit.setDisabled(False)
        else:
            self.downlinkLimitLineEdit.setDisabled(True)

    def updateUplinkLimitCheckBox(self, state):
        if state == Qt.Checked:
            self.uplinkLimitLineEdit.setDisabled(False)
        else:
            self.uplinkLimitLineEdit.setDisabled(True)

    def On_Click_RunStopPushButton(self, styleName):
        if self.runStopPushButton.text() == "Run Wondershaper":
            self.runStopPushButton.setText("Stop Wondershaper")
            self.setChangableDisabled(True)
            self.runStopAutomaticPushButton.setDisabled(True)

            self.runWondershaper()

        else:
            self.runStopPushButton.setText("Run Wondershaper")

            self.stopWondershaper()

            self.setChangableDisabled(False)
            self.runStopAutomaticPushButton.setDisabled(False)

    def On_Click_RunStopAutoPushButton(self, styleName):
        if self.runStopAutomaticPushButton.text() == "Run automatic Wondershaper":
            self.runStopAutomaticPushButton.setText(
                "Stop automatic Wondershaper")
            self.setChangableDisabled(True)
            self.runStopPushButton.setDisabled(True)

            self.runAutomaticWondershaper()
        else:
            self.runStopAutomaticPushButton.setText(
                "Run automatic Wondershaper")
            self.stopAutomaticWondershaper()

            self.setChangableDisabled(False)
            self.runStopPushButton.setDisabled(False)

    def updateNicComboBox(self):
        nicList = getNicList()

        for i in range(self.nicComboBox.count()):
            self.nicComboBox.removeItem(0)

        nicList = getNicList()

        self.nicComboBox.addItems(nicList)

    def runWondershaper(self):
        nic = self.nicComboBox.currentText()

        downlinkLimit = None
        uplinkLimit = None

        if (self.downlinkLimitCheckBox.isChecked()):
            downlinkLimit = self.downlinkLimitLineEdit.text()

        if (self.uplinkLimitCheckBox.isChecked()):
            uplinkLimit = self.uplinkLimitLineEdit.text()

        wondershaperLimitScript(nic, downlinkLimit, uplinkLimit)

    def stopWondershaper(self):
        for i in range(self.nicComboBox.count()):
            nic = self.nicComboBox.itemText(i)
            wondershaperStopLimits(nic)

    def runAutomaticWondershaper(self):
        global runWondershaperThread
        runWondershaperThread = True

        self.automaticWondershaperThread = threading.Thread(
            target=automaticWondershaperThreadFunction)

        self.automaticWondershaperThread.start()

    def stopAutomaticWondershaper(self):
        global runWondershaperThread
        runWondershaperThread = False

        self.automaticWondershaperThread.join()

        self.stopWondershaper()

    def setChangableDisabled(self, flag):
        self.nicComboBox.setDisabled(flag)
        self.downlinkLimitCheckBox.setDisabled(flag)
        self.downlinkLimitLineEdit.setDisabled(flag)
        self.uplinkLimitCheckBox.setDisabled(flag)
        self.uplinkLimitLineEdit.setDisabled(flag)
        self.limitTimeLineEdit.setDisabled(flag)
        self.noLimitTimeLineEdit.setDisabled(flag)


class App(QDialog):
    wondershaperGroupBox = None

    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setWindowTitle("Wondershaper app")

        self.wondershaperGroupBox = WondershaperGroupBox()

        self.changeStyle('Fusion')

        layout = QGridLayout()
        layout.addWidget(self.wondershaperGroupBox, 0, 0)
        self.setLayout(layout)

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())


if __name__ == '__main__':
    appctxt = ApplicationContext()
    global app
    app = App()
    app.show()
    appctxt.app.exec_()
