#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  main.py
#  
#  Copyright 2017 Patrice <patrice.chirouze@free.fr>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
# 
# 
import json
import sys
import time
# --- importation du fichier de description GUI ---
from PyQt4.QtGui import *
from PyQt4.QtCore import * # inclut QTimer..

from HDMI_Chauffage import *
import paho.mqtt.client as mqtt

# DEBUG = True
DEBUG = False
MQTT_SERVER = 'm23.cloudmqtt.com'
MQTT_PORT = 1883

# Variables globales
data_chauffage={}
data_solaire = {}
new_mes_chauffe = False
new_mes_solaire = False
connected = False

# Utiliser par SetStyleSheet (fonction avec callback si erreur)
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
       
def on_connect(client, userdata,rc):
    global connected
    connected = True
    print('Connecté')
    
    
def on_message(client, userdata, msg):
    global data_chauffage, data_solaire, new_mes_chauffe, new_mes_solaire
    if DEBUG: print(msg.topic, msg.payload)
    if msg.topic == '/regchauf/mesur':
        data_chauffage = json.loads(msg.payload)
        new_mes_chauffe = True
    if msg.topic == '/regsol/mesur':
        data_solaire = json.loads(msg.payload)
        new_mes_solaire = True

class myApp(QTabWidget, Ui_Dialog):
    
    def __init__(self, parent=None):
        global connected

        Ui_Dialog.__init__(self) # initialise le Qwidget principal
        QTabWidget.__init__(self)
        self.setupUi(parent) # Obligatoire
        self.clientmqtt = mqtt.Client()
        self.clientmqtt.on_connect = on_connect
        self.clientmqtt.on_message = on_message
        try:
            self.clientmqtt.connect(MQTT_SERVER, MQTT_PORT, 120) # Fonction bloquante
            self.clientmqtt.subscribe('/regchauf/mesur', 0)
            self.clientmqtt.subscribe('/regsol/mesur', 0)
        except:
            print('Pas de reseau')
            self.label_29.setText("Pas de connexion réseau")

        self.lineEdit.clearFocus()

        self.pushButton.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);"))
        self.counter = 0
        self.timer = QTimer()
        self.timer.start(300)
        self.connect(self.timer, SIGNAL("timeout()"), self.timerEvent)
        self.connect(self.pushButton, SIGNAL("clicked()"), self.pushbuttonclicked)
        self.connect(self.lineEdit, SIGNAL("returnPressed()"), self.setpointChanged)
        self.connect(self.pushButton_quit, SIGNAL("clicked()"), self.closeAppli)
        self.setTabEnabled(0, True)
        self.flagtimer = False
        self.once_time = False
        self.van_tm1 = 0
        self.label_29.setStyleSheet(_fromUtf8("color: rgb(255, 0, 180);"))
      
    def pushbuttonclicked(self):
        if data_chauffage['FNCT'][1] == 0:
            print('Cde start')
            self.clientmqtt.publish('/regchauf/cde', '1')
        else:
            print('Cde stop')
            self.clientmqtt.publish('/regchauf/cde', '0')
        self.pushButton.setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
        self.pushButton.clearFocus()
  
    def setpointChanged(self):
        self.clientmqtt.publish('/regchauf/cons', str(self.lineEdit.text()))
        self.lineEdit.clearFocus()
    
    def closeAppli(self):
        self.clientmqtt.publish('/regchauf/send', 'stop')
        self.clientmqtt.publish('/regsol/send', 'stop')
        time.sleep(1)
        self.clientmqtt.disconnect()
        exit()
        
    def timerEvent(self):
        global connected, new_mes_chauffe, new_mes_solaire

        self.clientmqtt.loop()
        if connected:
            self.label_29.setText(_fromUtf8("Connecté à " + MQTT_SERVER))
            if self.once_time is False:
                self.clientmqtt.publish('/regchauf/send', 'start')
                self.clientmqtt.publish('/regsol/send', 'start')
                self.once_time = True
            if new_mes_chauffe is True: 
# Traitement raffraichissement données Qt4 page Controle / Commande
                self.label_53.setStyleSheet(_fromUtf8("background-color: rgb(0, 100, 255);"))
                if data_chauffage['CIRC'] == 0:
                    self.label_10.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);"))
                    self.label_10.setText("A")
                else:
                    self.label_10.setStyleSheet(_fromUtf8("background-color: rgb(0, 255, 0);"))
                    self.label_10.setText('M')
                if data_chauffage['FNCT'][1] == 0:
                    self.pushButton.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);"))
                    self.pushButton.setText('START')
                else:
                    self.pushButton.setStyleSheet(_fromUtf8("background-color: rgb(0, 255, 0);"))
                    self.pushButton.setText('STOP')
                if data_chauffage['ELEC']['PW'] == 0 :
                    self.label_27.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);"))
                    self.label_27.setText("A")   
                else :
                    self.label_27.setStyleSheet(_fromUtf8("background-color: rgb(0, 255, 0);"))
                    self.label_27.setText('M')                 
                    
                self.lcdNumber_2.setProperty("value", data_chauffage['TEMP']['Text'])
                self.lcdNumber_3.setProperty("value", data_chauffage['TEMP']['Tint'])
                self.lcdNumber_4.setProperty("value", data_chauffage['TEMP']['Tcuv'])
                self.progressBar.setProperty("value", data_chauffage['VANN'])
                self.progressBar_2.setProperty("value", data_chauffage['ELEC']['PW'])
                self.lcdNumber_12.setProperty("value", data_chauffage['ELEC']['CHC'])
                self.lcdNumber_13.setProperty("value", data_chauffage['ELEC']['CHP'])
                self.lcdNumber_14.setProperty('value', data_chauffage['TEMP']['Tcuv'])      

                if self.lineEdit.hasFocus() == False:
                    self.lineEdit.setProperty('text', data_chauffage['FNCT'][0])
# Rafraichissement données page 'EDF'
                if len(data_chauffage['EDF']) > 0:
                    self.lcdNumber.setProperty('intValue', data_chauffage['EDF']['HCHC'])
                    self.lcdNumber_5.setProperty('intValue', data_chauffage['EDF']['HCHP'])
                    self.lcdNumber_7.setProperty('intValue', data_chauffage['EDF']['PAPP'])
                    self.lcdNumber_6.setProperty('intValue', data_chauffage['EDF']['IINST'])
                    if data_chauffage['EDF']['PTEC'] == 'HC..':
                        self.label_35.setText("Creuses")
                        self.label_35.setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
                    else:
                        self.label_35.setText("Pleines")
                        self.label_35.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);"))                        
                else:
                    self.label_35.setText("Er.EDF")
# Rafraichissement données page Regulation
                self.lcdNumber_8.setProperty('value', data_chauffage['CONS'])
                self.lcdNumber_11.setProperty("value", data_chauffage['TEMP']['Tv3v'])
                self.lcdNumber_9.setProperty("value", data_chauffage['TEMP']['Tcuv'])
                self.progressBar_2.setProperty("value", data_chauffage['ELEC']['PW'])
                self.progressBar_3.setProperty("value", data_chauffage['VANN'])
                new_mes_chauffe = False
            else:
                self.label_53.setStyleSheet(_fromUtf8("background-color: rgb(233, 225, 255);"))
# Refresh données solaire
            if new_mes_solaire:
                self.label_59.setStyleSheet(_fromUtf8("background-color: rgb(0, 100, 255);"))
                self.lcdNumber_19.setProperty('value', data_solaire['Tcap'])
                self.lcdNumber_15.setProperty('value', data_solaire['Taec'])
                self.lcdNumber_18.setProperty('value', data_solaire['Trec'])
                self.lcdNumber_17.setProperty('value', data_solaire['Tcuh'])
                self.lcdNumber_16.setProperty('value', data_solaire['Tcub'])
                self.lcdNumber_22.setProperty('value', data_solaire['Q'])
                self.lcdNumber_20.setProperty('value', data_solaire['PWR'])
                self.lcdNumber_23.setProperty('value', data_solaire['ENR'])
                if data_solaire['PMP'] == 0:
                    self.label_36.setStyleSheet(_fromUtf8("background-color: rgb(180, 0, 0);"))
                    self.label_36.setText("A")
                else:
                    self.label_36.setStyleSheet(_fromUtf8("background-color: rgb(0, 255, 0);"))
                    self.label_36.setText("M")
                new_mes_solaire = False
            else:
                self.label_59.setStyleSheet(_fromUtf8("background-color: rgb(233, 225, 255);"))                
        else:
            self.label_29.setText(_fromUtf8("Attente connexion à " + MQTT_SERVER))
            if DEBUG: print('Attente connexion à ' + MQTT_SERVER)

def main(args):
    app = QApplication(args) # crée l'objet application
    window = QDialog() # crée le Widget racine
    c = myApp(window) # Crée instance de la classe contenant le code de l'application
    window.show() # affiche la fenêtre QWidget
    ret = app.exec_() # lance l'exécution de l'application

if __name__ == '__main__':
#    sys.exit(main(sys.argv))
    main(sys.argv)
    
