from PyQt5.QtWidgets import QMessageBox, QInputDialog
from qgis.core import QgsProject
from qgis.gui import QgsMessageBar
from qgis.utils import iface
from qgis.core import Qgis, NULL
from datetime import datetime
import statistics
import operator

# Se instancia el proyecto
project = QgsProject.instance()

	# CALIDAD TEMPORAL
	# Funcion para la evaluacion de calidad del elemento de calidad temporal
  
def caltemporal(self,capa_cde_temp,nom_cde_temp,ruta):

	iface.messageBar().pushMessage("Calidad Temporal",'En ejecición por favor espere', level=Qgis.Info, duration=10)

	now = datetime.now()
	hoy = now.strftime('%Y/%m/%d %H:%M')
	
	mensaje_exac="<table border=1><tr><td colspan=2></td><td colspan=3><b>Validez Temporal</b></td><td colspan=9><b>Exactitud de una medida de tiempo</b></td></tr>"
	mensaje_exac+="<tr><td><b>Conjunto de Datos</b></td><td><b># Chequeos</b></td><td><b>Sin Fechas</b></td><td><b>Fechas invalidas</b></td>"
	mensaje_exac+="<td><b># Fechas validas</b></td><td><b>Fechas mínima</b></td><td><b>Fechas máxima</b></td><td><b>Fecha Media</b></td>"
	mensaje_exac+="<td><b>Medida 54 (LE68.3)</b></td><td><b>Medida 55 (LE50)</b></td><td><b>Medida 56 (LE90)</b></td><td><b>Medida 57 (LE95)</b></td>"
	mensaje_exac+="<td><b>Medida 58 (LE99)</b></td><td><b>Medida 59 (LE99.8)</b></td></tr>"

	cont=0
	acum_che = 0
	acum_vac = 0
	acum_inv = 0
	ord_min = dict()
	ord_max = dict()
	ord_med = dict()

	cont_nom = 0
	keys= capa_cde_temp.keys()
	for x in keys:
		fecha_min=""
		fecha_max=""
		fecha_des=""
		fecha_med = ""
		le68 = ""
		le50 = ""
		le90 = ""
		le95 = ""
		le99 = ""
		le998 = ""
		fechas_vr = []
		fechas_data = []
		num_fechas_inv = 0

		# Para el calculo de la exactitud de una medida de tiempo
		for m in capa_cde_temp[x].getFeatures():
			ids_f = m.fieldNameIndex('F_ALTA')
			if ids_f!=-1:			
				valor = m.attributes()[ids_f]
				if valor!=NULL:
					try:
						fecha = datetime.strptime(str(valor), '%Y/%m/%d')
						monto = fecha.toordinal()
						fechas_data.append(monto)
						fechas_vr.append(valor)
					except ValueError:
						num_fechas_inv+=1
			else:
				num_fechas_inv = 0

		num_fechas_che = len(capa_cde_temp[x])
		num_fechas_ele = len(fechas_vr)
		num_fechas_vac = num_fechas_che - num_fechas_ele - num_fechas_inv
		if num_fechas_ele>0:
			num_fechas_val = num_fechas_ele
			fecha_min = min(fechas_vr)
			fecha_max = max(fechas_vr)
			if num_fechas_ele>1:
				fecha_des = round(statistics.stdev(fechas_data),2)
				fecha_med = int(statistics.mean(fechas_data))
				fecha_med = datetime.fromordinal(fecha_med)
				fecha_med = '{:%Y}'.format(fecha_med)+"/"+'{:%m}'.format(fecha_med)+"/"+'{:%d}'.format(fecha_med)
				le68 = fecha_des
				le50 = round((fecha_des*0.6745),2)
				le90 = round((fecha_des*1.645),2)
				le95 = round((fecha_des*1.96),2)
				le99 = round((fecha_des*2.576),2)
				le998 = round((fecha_des*3),2)
			else:
				fecha_med = fecha_min
			ord_min[nom_cde_temp[cont_nom]]=fecha_min
			ord_max[nom_cde_temp[cont_nom]]=fecha_max
			ord_med[nom_cde_temp[cont_nom]]=fecha_med	
		else:
			num_fechas_val = 0 

		acum_che += num_fechas_che
		acum_vac += num_fechas_vac
		acum_inv += num_fechas_inv
		
		mensaje_exac+=f"<tr><td>{nom_cde_temp[cont_nom]}</td><td>{num_fechas_che}</td><td>{num_fechas_vac}</td><td>{num_fechas_inv}</td><td>{num_fechas_val}</td>"
		mensaje_exac+=f"<td>{fecha_min}</td><td>{fecha_max}</td><td>{fecha_med}</td><td>{le68}</td><td>{le50}</td><td>{le90}</td>"
		mensaje_exac+=f"<td>{le95}</td><td>{le99}</td><td>{le998}</td></tr>"

		cont+=1
		val = 5 + int(85*cont/len(capa_cde_temp))  
		self.pbr_elem.setValue(val)	
		cont_nom += 1
		# Fin exactitud de una medida de tiempo


	# Validez temporal
	# Elementos sin fecha
	if acum_vac == 0:
		val_vac15 = "Verdadero"
		val_vac16 = 0
		val_vac18 = 0
	else:
		val_vac15 = "Falso"
		val_vac16 = acum_vac 
		val_vac18 = round(acum_vac/(acum_che),2)

	# Validez temporal
	# Elementos sin fecha
	if acum_inv == 0:
		val_inv15 = "Verdadero"
		val_inv16 = 0
		val_inv18 = 0
	else:
		val_inv15 = "Falso"
		val_inv16 = acum_inv 
		val_inv18 = round(acum_inv/(acum_che),2)

	# Orden de los eventos de la consistencia temporal
		# Ordenado por fecha minima
	ord_min_sort = sorted(ord_min.items(), key=operator.itemgetter(1))
	mensaje_cron="<p><b>Orden de los eventos por fecha mínima</b></p>"
	mensaje_cron+="<table border=1><tr><td><b>Conjunto de datos</b></td><td><b>Fecha minima</b></td></tr>"
	for men in enumerate(ord_min_sort):
		mensaje_cron+=f"<tr><td>{men[1][0]}</td><td>{ord_min[men[1][0]]}</td></tr>"
	mensaje_cron += "</table><br>"
			# Ordenado por fecha maxima
	ord_max_sort = sorted(ord_max.items(), key=operator.itemgetter(1))
	mensaje_cron+="<p><b>Orden de los eventos por fecha máxima</b></p>"
	mensaje_cron+="<table border=1><tr><td><b>Conjunto de datos</b></td><td><b>Fecha máxima</b></td></tr>"
	for men in enumerate(ord_max_sort):
		mensaje_cron+=f"<tr><td>{men[1][0]}</td><td>{ord_max[men[1][0]]}</td></tr>"
	mensaje_cron += "</table><br>"
			# Ordenado por fecha maxima
	ord_med_sort = sorted(ord_med.items(), key=operator.itemgetter(1))
	mensaje_cron+="<p><b>Orden de los eventos por fecha media</b></p>"
	mensaje_cron+="<table border=1><tr><td><b>Conjunto de datos</b></td><td><b>Fecha media</b></td></tr>"
	for men in enumerate(ord_med_sort):
		mensaje_cron+=f"<tr><td>{men[1][0]}</td><td>{ord_med[men[1][0]]}</td></tr>"
	mensaje_cron += "</table><br>"

	# Visualizacion de los resultados de la calidad temporal"
	text_for = "<center><h2>Evaluación Calidad Temporal</h2></center>"
	text_for += f"Proyecto: <b>{ruta}</b><p>"
	text_for += f"Fecha: <b>{hoy}</b><p>"
	text_for += "Método de evaluación: <b>Directo Interno</b><p>"
	text_for += "Enfoque de inspeción: <b>Automático / Inspección completa</b><p>"	
	text_for += "<h3>Reporte resultados (Anexo D ISO 19157)</h3>"
	text_for += f"<b>Exactitud de una medida de tiempo (elementos chequeados {acum_che})</b>"
	text_for += "<p>ver reporte detallado</p>"
	text_for +=f"<b>Validez Temporal (elementos chequeados {acum_che})</b><br>"
	text_for +="<table border=1><tr><td></td><td><b>Medida 15</b></td><td><b>Medida 16</b></td><td><b>Medida 18</b></td></tr>"
	text_for +=f"<tr><td><b>Elementos sin fecha</b></td><td>{val_vac15}</td><td>{val_vac16}</td><td>{val_vac18}</td></tr>"
	text_for +=f"<tr><td><b>Elementos con fecha invalida</b></td><td>{val_inv15}</td><td>{val_inv16}</td><td>{val_inv18}</td></tr>"
	text_for +="</table><br><p>"
	text_for += f"<b>Consistencia temporal (elementos chequeados {acum_che})</b>"
	text_for += "<p>ver reporte detallado</p>"
	
	mensaje = "<b>Validez temporal  / Exactitud de una medida de tiempo</b><p>"+mensaje_exac+"</table><p>"
	mensaje += "<b>Consistencia temporal</b> (Medida 159: Indicación de que un evento está ordenado incorrectamente en relación al resto de eventos, el usuario debe definir esta medida)<p>"+mensaje_cron+"<p>"

	resultado = str(ruta)+'/Resultados/Calidad_temporal.html'
	f = open (resultado, 'w')
	f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>Resultado de Evaluación Calidad Temporal</title>\n')
	f.write('<style type="text/css">\nbody {font-family: arial; margin: 5%;}\ntable {border: 2px solid blue; border-collapse: collapse; font-family: arial; width: 80%;}\n')
	f.write('td {padding: 5px;text-align: center;}</style></head>\n<body>\n')
	f.write(text_for)
	f.write('\n<p>\n')
	f.write('<hr><p><h3>Reporte Detallado</h3><p>\n')
	f.write(mensaje)
	f.write('\n</html>')
	f.close()

	self.bt_resultado.setEnabled(True)
	self.bt_resultado.clicked.connect(self.ver_result_temp)

	doc = """<style type='text/css'>
	  table {border-collapse:collapse; border:1px; border-style:solid; border-color:darkblue; padding:3px; vertical-align:middle;} 
	  td {padding: 3px;text-align: center;}</style>"""

	self.rel_val.setHtml(doc+text_for)