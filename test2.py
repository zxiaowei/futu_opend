# encoding: utf-8

import sys
import traceback

from qtpy.QtWidgets import QLabel, QLineEdit, QGridLayout, QPushButton, QMainWindow, QApplication, QWidget
from threading import Thread
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        center = QWidget()
        self.setCentralWidget(center)
        self.l1 = QLineEdit()
        self.l2 = QLineEdit()
        self.l3 = QLineEdit()

        self.lb1 = QLabel()
        self.lb2 = QLabel()
        self.lb3 = QLabel()

        layout = QGridLayout()
        layout.addWidget(self.l1,0,0)
        layout.addWidget(self.l2,1,0)
        layout.addWidget(self.l3, 2,0)

        layout.addWidget(self.lb1,3,0)
        layout.addWidget(self.lb2,4,0)
        layout.addWidget(self.lb3,5,0)
        center.setLayout(layout)

def run():
    time.sleep(5)
    for i in range(1000000):
        mw.l1.setText("aaaa%s"%i)
        mw.l2.setText("bbbb%s" % i)
        mw.l3.setText("cccc%s" % i)

        mw.lb1.setText("aaaa%s"%i)
        mw.lb2.setText("bbbb%s" % i)
        mw.lb3.setText("cccc%s" % i)
        time.sleep(1)

qApp = QApplication([])
mw = MainWindow()

mw.show()

t1 = Thread(target=run)
t1.start()

sys.exit(qApp.exec_())