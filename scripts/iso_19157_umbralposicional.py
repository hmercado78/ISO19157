from qgis.utils import iface
from qgis.core import QgsProject
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtWidgets import *
import sys
from collections import OrderedDict
#from datetime import datetime
#from qgis.core import (Qgis, QgsVectorLayer, QgsField, QgsFeatureRequest, QgsProcessingFeatureSourceDefinition, 
#	QgsSingleSymbolRenderer, QgsLineSymbol, QgsLayerTreeLayer)
#import math
#from qgis.PyQt.QtCore import QVariant
#from qgis import processing
#from processing.tools import dataobjects

# Se instancia el proyecto
project = QgsProject.instance()

# Función escribir numero romano tomado de https://www.it-swarm-es.com/es/python/programa-basico-para-convertir-enteros-numeros-romanos/1050857259/
def write_roman(num):
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"
    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break
    return "".join([a for a in roman_num(num)])
# ----

	# COMPLECION
	# Funcion para la evaluacion de calidad del elemento de calidad de complecion

def umbral(self):
	modulos = ['1.000','5.000','10.000','25.000','50.000','100.000','200.000','500.000','1.250.000','2.000.000']
	ok=""
	while ok=="" or ok==False:
		escala, ok = QInputDialog.getItem(self, "Escala del Conjunto de datos", "Seleccione el modulo de la escala 1:", modulos, 3, False)

	modulo = int(escala.replace('.', ''))
	# Limite de percepcion visual
	lpv = 0.0002*1.25*modulo

	# Error posicionamiento de contornos - EPC
	epc_p = 0.0005*modulo 
	epc_q = 0.0007*modulo

	# Estándar de Precisión ASPRS
	clase = ""

	# Selección del usuario del Umbral o tolerancia.
	t_lpv = "Limite de percepción visual: "+str(lpv)+ " m"
	t_epc_p = "Error de posicionamiento de contornos (zona plana): "+str(epc_p)+ " m"
	t_epc_q = "Error de posicionamiento de contornos (zona alta pendiente): "+str(epc_q)+ " m"

	opciones = [t_lpv,t_epc_p,t_epc_q,"Estándar de precisión para datos geoespaciales digitales (ASPRS)","Asignado por el usuario"]
	ok=""
	while ok=="" or ok==False:
		opc_umb, ok = QInputDialog.getItem(self, "Umbral o Tolerancia", "Seleccione el umbral o tolerancia para esta evaluación:", opciones, 0, False)

	if opc_umb=="Asignado por el usuario":
		ok=""
		while ok=="" or ok==False:
			tolerancia, ok = QInputDialog.getDouble(self,"Umbral o Tolerancia del Usario", "Ingrese valor del umbral o tolerancia (metros):",0,0,10000,2)
	elif opc_umb=="Estándar de precisión para datos geoespaciales digitales (ASPRS)":
		ok=""
		while ok=="" or ok==False:
			tolerancia, ok = QInputDialog.getDouble(self,"Umbral o Tolerancia estandar ASPRS", "Defina la Clase para la precisión horizontal (ASPRS):",1,0,100,0)
		clase = write_roman(int(tolerancia))
		tolerancia = (tolerancia*0.0125*modulo)/100
		tolerancia = (2*(tolerancia**2))**0.5
		tolerancia = tolerancia*1.7308
	elif opc_umb==t_lpv:
		tolerancia=lpv
	elif opc_umb==t_epc_p:
		tolerancia=epc_p
	elif opc_umb==t_epc_q:
		tolerancia=epc_q

	if opc_umb==t_lpv or opc_umb==t_epc_p or opc_umb==t_epc_q:
		indice = (opc_umb.rfind(':'))
		opc_umb = opc_umb[:indice]
	return escala, tolerancia, opc_umb, clase 