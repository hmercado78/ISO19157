from qgis.utils import iface
from qgis.core import QgsProject
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from datetime import datetime
from qgis.core import (Qgis, QgsVectorLayer, QgsField, QgsFeatureRequest, QgsProcessingFeatureSourceDefinition, 
	QgsSingleSymbolRenderer, QgsLineSymbol, QgsLayerTreeLayer, QgsRasterLayer, NULL, QgsProcessingFeedback,
	QgsCoordinateReferenceSystem)
import math
from qgis.PyQt.QtCore import QVariant, QFileInfo
from qgis import processing
from processing.tools import dataobjects
from iso_19157.scripts.iso_19157_umbralposicional import umbral
import statistics
import numpy as np
import os
import scipy.stats

# Se instancia el proyecto
project = QgsProject.instance()
	
	# EXACTUTUD POSICIONAL
	# Funcion para la evaluacion de calidad de la Exactitud posicional

  
def posicional(self,capa_cde_posi,capa_cdr_posi,nom_cde_posi,nom_cdr_posi,ruta,lista_cde_posi,lista_cdr_posi):
	self.rel_val.setHtml("")
	root = project.layerTreeRoot()

	def progress_changed(progress):
		self.pbr_elem.setValue(progress)
	feed = QgsProcessingFeedback()
	feed.progressChanged.connect(progress_changed)

	# En caso de existir el grupo "Calidad Posicional" se elimina
	grupo = "Calidad_Posicional"
	migrupo = root.findGroup(grupo) 
	if migrupo!=None:
		root.removeChildNode(migrupo)  

	iface.messageBar().pushMessage("Calidad Posicional",'En ejecición por favor espere', level=Qgis.Info, duration=10)
	now = datetime.now()
	hoy = now.strftime('%Y/%m/%d %H:%M')

	# Se configura el contexto para utilziarlo en los geoprocesos que requieran trabajar con geometrias invalidas
	context = dataobjects.createContext()
	context.setInvalidGeometryCheck(QgsFeatureRequest.GeometryNoCheck)

	items = ("Cobertura Compartida", "Extensión CDE", "Extensión CDR")
	cob, ok = QInputDialog.getItem(self, "Extensión espacial de la evaluación", "Seleccione:", items, 0, False)

	curvas = ""
	indice_c = ""
	texto_adv = ""
	indice=0
	if ok==True: 
		if ok and cob:
			if cob=="Cobertura Compartida":
				ext = project.mapLayersByName('Cobertura_compartida')[0]
				ext_comp = project.mapLayersByName('Extension_CDE')[0]
				for feat in ext.getFeatures():
					area_ext = feat.geometry().area()
				for feat in ext_comp.getFeatures():
					area_ext_comp = feat.geometry().area()
				area_cob = f"({round((area_ext/area_ext_comp)*100,1)} % de la extensión del CDE"  
			if cob=="Extensión CDE":
				ext = project.mapLayersByName('Extension_CDE')[0]
				ext_comp = project.mapLayersByName('Cobertura_compartida')[0]
				for feat in ext.getFeatures():
					area_ext = feat.geometry().area()
				for feat in ext_comp.getFeatures():
					area_ext_comp = feat.geometry().area()
				area_cob = f"({round((area_ext_comp/area_ext)*100,1)} % de extensión del CDE esta compartida con el CDR"
			if cob=="Extensión CDR":
				ext = project.mapLayersByName('Extension_CDR')[0]
				ext_comp = project.mapLayersByName('Cobertura_compartida')[0]
				for feat in ext.getFeatures():
					area_ext = feat.geometry().area()
				for feat in ext_comp.getFeatures():
					area_ext_comp = feat.geometry().area()
				area_cob = f"({round((area_ext_comp/area_ext)*100,1)} % de extensión del CDR esta compartida con el CDE"

		# Para saber cuantos elementos existen en el CD y determinar el maximo muestreo
		cont=0
		max_muestreo = 0
		entidades = 0
		for n in capa_cde_posi:
			if capa_cde_posi[n].geometryType()==0 or capa_cde_posi[n].geometryType()==2:
				processing.run("native:selectbylocation", {'INPUT':capa_cde_posi[n],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
				sel = capa_cde_posi[n].selectedFeatures()
				max_muestreo += len(sel)
				entidades += len(sel)
				capa_cde_posi[n].removeSelection()
				cont += 1
				cont_201=0
			if capa_cde_posi[n].geometryType()==1:
				processing.run("native:selectbylocation", {'INPUT':capa_cde_posi[n],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
				sel = capa_cde_posi[n].selectedFeatures()
				if not "201L" in nom_cde_posi[cont]:
					max_muestreo += int((len(sel)))
					entidades += int((len(sel)))
					cont_201=0
				else:
					cont_201=cont
				capa_cde_posi[n].removeSelection()
				cont += 1

		if max_muestreo>=25:
			text_mens=f"Entre el número de puntos a evaluar entre 25 y {max_muestreo})"
			num_pt, ok = QInputDialog.getInt(self,"Calidad Posicional", text_mens,25,25,max_muestreo,1)
		else:
			num_pt=0
			ok=False

		if ok and num_pt>=25:
			# Se ejecuta la funcion umbral para que el usuario defina las tolerancias y el umbral.
			escala, tolerancia, opc_umb, clase = umbral(self)

			if "201L" in nom_cde_posi[cont_201]:
				titulo = "Incertidumbre posicionales verticales"
				mens_b = "En el CDE existe informacion de curvas de nivel ¿Desea evaluar incertidumbre posicional vertical en este CD?"
				msgBox = QMessageBox().question(self,titulo, mens_b, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
			else:
				msgBox = QMessageBox.No

			capa_cdr_c = capa_cdr_posi.copy()

			if msgBox == QMessageBox.Yes:
				str_match = [s for s in nom_cde_posi if "201L" in s]
				if len(str_match)>0:
					indice = nom_cde_posi.index(str_match[0])
					if indice in capa_cdr_posi.keys():
						del capa_cdr_c[indice]
						curvas = "si"
						indice_c = indice
						texto_adv = f"La capa <b>{nom_cde_posi[indice]}</b> no se utilizará para determinar la incertidumbre posicional horizontal"
						self.rel_val.setHtml(texto_adv)

				if len(capa_cdr_c)>0 or curvas=="si":
					# Creación de MDE desde la capa CDE.	
					self.pbr_elem.setValue(20)
					ext_ext = ext.extent()
					capa_ent = lista_cde_posi[indice]+'::~::1::~::-1::~::0'
					mde_cde = processing.run("qgis:tininterpolation", {'INTERPOLATION_DATA':capa_ent,'METHOD':0,'EXTENT':ext_ext,'PIXEL_SIZE':1,'OUTPUT':'TEMPORARY_OUTPUT'}, feedback=feed)
					fileName = mde_cde['OUTPUT']
					fileInfo = QFileInfo(fileName)
					baseName = fileInfo.baseName()
					rlayer_cde = QgsRasterLayer(fileName, baseName)

					# Creación de MDE desde la capa CDR.
					self.pbr_elem.setValue(40)
					capa_ent = lista_cdr_posi[indice]+'::~::1::~::-1::~::0'
					mde_cdr = processing.run("qgis:tininterpolation", {'INTERPOLATION_DATA':capa_ent,'METHOD':0,'EXTENT':ext_ext,'PIXEL_SIZE':1,'OUTPUT':'TEMPORARY_OUTPUT'}, feedback=feed)
					fileName = mde_cdr['OUTPUT']
					fileInfo = QFileInfo(fileName)
					baseName = fileInfo.baseName()
					rlayer_cdr = QgsRasterLayer(fileName, baseName)

			else:
				str_match = [s for s in nom_cde_posi if "201L" in s]
				if len(str_match)>0:
					indice = nom_cde_posi.index(str_match[0])
					if indice in capa_cdr_posi.keys():
						del capa_cdr_c[indice]				

			keys= capa_cde_posi.keys()
			for x in keys:
				p=x
			epsg=capa_cde_posi[p].crs().toWkt()
			pts_cde_sel = QgsVectorLayer("Point?crs="+ epsg, "temp", "Memory")
			pts_cde_sel.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
			pts_cde_sel.updateFields()
			capa_posi = QgsVectorLayer("Linestring?crs="+ epsg, "temp", "Memory")
			capa_posi.dataProvider().addAttributes([QgsField("ID_CDE", QVariant.String)])
			capa_posi.dataProvider().addAttributes([QgsField("ID_CDR", QVariant.String)])
			capa_posi.dataProvider().addAttributes([QgsField("Dist", QVariant.Double)])
			capa_posi.dataProvider().addAttributes([QgsField("Datos", QVariant.String)])
			capa_posi.updateFields()

			conteo= 0
			# Sumatoria de los sesgos para la medidad 128
			ax_sum = 0
			ay_sum = 0
			# ----

			# Valor medio de las incertidumbres posicionales excluyendo atípicos
			axe_sum = 0
			aye_sum = 0
			excluidos = 0
			# ----

			# Vectores de error 
			vec_ex = []
			vec_ey = []
			vec_coor = []

			cont_nom = 0
			if len(capa_cdr_c)>0:
				llaves = capa_cde_posi.keys()
				for x in llaves:
					if x in capa_cdr_c.keys():
						pts_cde_opc = QgsVectorLayer("Point?crs="+ epsg, "temp", "Memory")
						pts_cde_opc.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
						pts_cde_opc.updateFields()
						num_capas = len(capa_cdr_c)
						capa_cde_posi[x].removeSelection()

						# Para definir cuantos elementos se seleccionan segun el muestreo
						processing.run("native:selectbylocation", {'INPUT':capa_cde_posi[x],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
						sel = capa_cde_posi[x].selectedFeatures()
						sele_muestreo = len(sel)
						capa_cde_posi[x].removeSelection()
						num_sel = math.ceil(sele_muestreo*(num_pt/max_muestreo))
						conteo += 1
						if len(capa_cdr_c)==conteo:
							num_sel = num_pt-len(pts_cde_sel)
						# ----

						if capa_cde_posi[x].geometryType()==0: # si la capa es  ######## PUNTO ######
							capa_cde_posi[x].removeSelection()
							processing.run("native:selectbylocation", {'INPUT':capa_cde_posi[x],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
							sel = capa_cde_posi[x].selectedFeatures()
							pts_cde_opc.dataProvider().addFeatures(sel)
							capa_cde_posi[x].removeSelection()

							processing.run("qgis:randomselection", {'INPUT':pts_cde_opc,'METHOD':0,'NUMBER':num_sel})
							sel = pts_cde_opc.selectedFeatures()
							for f in sel:
								item = len(pts_cde_sel)+1
								f.setAttribute(0,item)
								pts_cde_sel.dataProvider().addFeatures([f])

							prop_cde = processing.run("native:saveselectedfeatures", {'INPUT': pts_cde_opc, 'OUTPUT': 'memory:'})

							processing.run("native:selectbylocation", {'INPUT':capa_cdr_posi[x],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
							sel = capa_cdr_posi[x].selectedFeatures()
							prop_cdr = processing.run("native:saveselectedfeatures", {'INPUT': capa_cdr_posi[x], 'OUTPUT': 'memory:'})
							capa_cdr_posi[x].removeSelection()

							dist = processing.run("qgis:distancetonearesthublinetohub", {'INPUT':prop_cde['OUTPUT'],'HUBS':prop_cdr['OUTPUT'],'FIELD':'ID','UNIT':0,'OUTPUT':'TEMPORARY_OUTPUT'})
							project.addMapLayer(dist['OUTPUT'], False)
							dist['OUTPUT'].dataProvider().addAttributes([QgsField("Datos", QVariant.String)])
							for n in  dist['OUTPUT'].getFeatures():
								n.setAttribute(3,str(nom_cde_posi[cont_nom]))
								capa_posi.dataProvider().addFeatures([n])

							project.addMapLayer(pts_cde_opc, True)
							project.removeMapLayer(pts_cde_opc.id())

						
						if capa_cde_posi[x].geometryType()==1: # si la capa es  ######## LINEA ######
							capa_cde_posi[x].removeSelection()
							ver = processing.run("native:extractspecificvertices", {'INPUT':capa_cde_posi[x],'VERTICES':'0,-1','OUTPUT':'TEMPORARY_OUTPUT'}, context=context)
							project.addMapLayer(ver['OUTPUT'], False)

							processing.run("native:selectbylocation", {'INPUT':ver['OUTPUT'],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
							sel = ver['OUTPUT'].selectedFeatures()
							pts_cde_opc.dataProvider().addFeatures(sel)
							ver['OUTPUT'].removeSelection()

							processing.run("qgis:randomselection", {'INPUT':pts_cde_opc,'METHOD':0,'NUMBER':num_sel})
							sel = pts_cde_opc.selectedFeatures()
							for f in sel:
								item = len(pts_cde_sel)+1
								f.setAttribute(0,item)
								pts_cde_sel.dataProvider().addFeatures([f])

							prop_cde = processing.run("native:saveselectedfeatures", {'INPUT': pts_cde_opc, 'OUTPUT': 'memory:'})

							ver = processing.run("native:extractspecificvertices", {'INPUT':capa_cdr_posi[x],'VERTICES':'0,-1','OUTPUT':'TEMPORARY_OUTPUT'}, context=context)
							processing.run("native:selectbylocation", {'INPUT':ver['OUTPUT'],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
							sel = ver['OUTPUT'].selectedFeatures()
							prop_cdr = processing.run("native:saveselectedfeatures", {'INPUT': ver['OUTPUT'], 'OUTPUT': 'memory:'})
							ver['OUTPUT'].removeSelection()


							dist = processing.run("qgis:distancetonearesthublinetohub", {'INPUT':prop_cde['OUTPUT'],'HUBS':prop_cdr['OUTPUT'],'FIELD':'ID','UNIT':0,'OUTPUT':'TEMPORARY_OUTPUT'})
							project.addMapLayer(dist['OUTPUT'], False)
							dist['OUTPUT'].dataProvider().addAttributes([QgsField("Datos", QVariant.String)])
							for n in  dist['OUTPUT'].getFeatures():
								n.setAttribute(3,str(nom_cde_posi[cont_nom]))
								capa_posi.dataProvider().addFeatures([n])
								
							project.addMapLayer(pts_cde_opc, True)
							project.removeMapLayer(pts_cde_opc.id())

						if capa_cde_posi[x].geometryType()==2: # si la capa es  ######## POLIGONO ######
							capa_cde_posi[x].removeSelection()
							cen = processing.run("native:centroids", {'INPUT':capa_cde_posi[x],'ALL_PARTS':False,'OUTPUT':'TEMPORARY_OUTPUT'}, context=context)					
							project.addMapLayer(cen['OUTPUT'], False)

							processing.run("native:selectbylocation", {'INPUT':cen['OUTPUT'],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
							sel = cen['OUTPUT'].selectedFeatures()
							pts_cde_opc.dataProvider().addFeatures(sel)
							cen['OUTPUT'].removeSelection()

							processing.run("qgis:randomselection", {'INPUT':pts_cde_opc,'METHOD':0,'NUMBER':num_sel})
							sel = pts_cde_opc.selectedFeatures()
							for f in sel:
								item = len(pts_cde_sel)+1
								f.setAttribute(0,item)
								pts_cde_sel.dataProvider().addFeatures([f])

							prop_cde = processing.run("native:saveselectedfeatures", {'INPUT': pts_cde_opc, 'OUTPUT': 'memory:'})

							cen = processing.run("native:centroids", {'INPUT':capa_cdr_posi[x],'ALL_PARTS':False,'OUTPUT':'TEMPORARY_OUTPUT'}, context=context)	
							processing.run("native:selectbylocation", {'INPUT':cen['OUTPUT'],'PREDICATE':[6],'INTERSECT':ext,'METHOD':0})
							sel = cen['OUTPUT'].selectedFeatures()
							prop_cdr = processing.run("native:saveselectedfeatures", {'INPUT': cen['OUTPUT'], 'OUTPUT': 'memory:'})
							cen['OUTPUT'].removeSelection()

							dist = processing.run("qgis:distancetonearesthublinetohub", {'INPUT':prop_cde['OUTPUT'],'HUBS':prop_cdr['OUTPUT'],'FIELD':'ID','UNIT':0,'OUTPUT':'TEMPORARY_OUTPUT'})
							project.addMapLayer(dist['OUTPUT'], False)
							dist['OUTPUT'].dataProvider().addAttributes([QgsField("Datos", QVariant.String)])
							for n in  dist['OUTPUT'].getFeatures():
								n.setAttribute(3,str(nom_cde_posi[cont_nom]))
								capa_posi.dataProvider().addFeatures([n])

							project.addMapLayer(pts_cde_opc, True)
							project.removeMapLayer(pts_cde_opc.id())
					cont_nom +=1

				# Visualizar la capa con las distancias
				processing.run("native:renamelayer", {'INPUT': capa_posi,'NAME': 'Distancia_CDE_CDR'})
				symbol =QgsLineSymbol.createSimple ({'color':'red', 'width':'1.2', 'line_style':'solid'})    
				simb = QgsSingleSymbolRenderer(symbol)    
				capa_posi.setRenderer(simb)   
				project.addMapLayer(capa_posi, False)
				root.insertGroup(0, grupo)
				migrupo = root.findGroup(grupo) 
				migrupo.insertChildNode(-1, QgsLayerTreeLayer(capa_posi))
			else:
				self.rel_val.setHtml("No se cuenta con CD que permitan al evaluación de la incertidumbre posicional horizontal")
				root.insertGroup(0, grupo)
				migrupo = root.findGroup(grupo) 


			if len(capa_cdr_c)>0:
				# Deteccion de errores groseros mediante outliers detection NATO.
				# Desviacion tipica 
				sum_dist = 0
				for m in capa_posi.getFeatures():
					sum_dist +=m.attributes()[2]
					xm = n.geometry().vertexAt(0).x()
					ym = n.geometry().vertexAt(0).y()
					xt = n.geometry().vertexAt(1).x()
					yt = n.geometry().vertexAt(1).y()
					ex = xm - xt
					ey = ym - yt
					ax_sum += ex
					ay_sum += ey
					vec_ex.append(ex)
					vec_ey.append(ey)
					vec_coor.append([xm,ym,xt,yt])
				emh = sum_dist/num_pt #Error medio horizontal
				sum_desv = 0
				for m in capa_posi.getFeatures():
					sum_desv +=(m.attributes()[2]-emh)**2
				desv_tiph_p = (sum_desv/(num_pt))**0.5 # Desviacion tipica poblacional horizontal

				# Errores groseros circular
				error_gro_c = (2.5055+(4.6052*math.log10(num_pt-1)))**0.5
				m2_desv = error_gro_c*desv_tiph_p
				gros_c = 0
				n = len(vec_ex)
				med_dif_x = statistics.mean(vec_ex)
				med_dif_y = statistics.mean(vec_ey)
				gros_c_e=0
				for m in capa_posi.getFeatures():
					xm = m.geometry().vertexAt(0).x()
					ym = m.geometry().vertexAt(0).y()
					xt = m.geometry().vertexAt(1).x()
					yt = m.geometry().vertexAt(1).y()
					ex = xm - xt
					ey = ym - yt
					residual = ((ex-med_dif_x)**2+(ey-med_dif_y)**2)**0.5
					if abs(residual)>m2_desv:
						capa_posi.removeSelection()
						gros_c += 1
						ids = m.id()
						capa_posi.select(ids)
						iface.mapCanvas().zoomToSelected(capa_posi)
						canvas = iface.mapCanvas()
						canvas.zoomOut()
						canvas.zoomOut()
						titulo = "Errores groseros horizontales detectados"
						mens_b = f"El valor absoluto del residual {residual:.2f} es mayor a {m2_desv:.2f} del test circular (NATO) ¿Desea eliminar este punto del muestreo?"
						msgBox_e = QMessageBox().question(self,titulo, mens_b, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
						if msgBox_e == QMessageBox.Yes:
							capa_posi.dataProvider().deleteFeatures([ids])
							gros_c_e+=1
						capa_posi.removeSelection()
				ext.selectAll()
				iface.mapCanvas().zoomToSelected(ext)
				ext.removeSelection()

				if len(capa_posi)>=20:
					# Calculo de las diferencia y desviaciones del muestreo sin errores groseros
					vec_ex=[]
					vec_ey=[]
					vec_coor=[]
					sum_dist=0
					for n in capa_posi.getFeatures():
						sum_dist +=m.attributes()[2]
						# Evaluación de exactitud posicional (sesgo - medida 128)
						xm = n.geometry().vertexAt(0).x()
						ym = n.geometry().vertexAt(0).y()
						xt = n.geometry().vertexAt(1).x()
						yt = n.geometry().vertexAt(1).y()
						ex = xm - xt
						ey = ym - yt
						ax_sum += ex
						ay_sum += ey
						# ---- 
						vec_ex.append(ex)
						vec_ey.append(ey)
						vec_coor.append([xm,ym,xt,yt])

						# Valor medio de las incertidumbres posicionales excluyendo atípicos
						if abs(ex)<=tolerancia and abs(ey)<=tolerancia:
							axe_sum += ex
							aye_sum += ey
						else:
							excluidos += 1

					# Calculo de desviaciones estandar sin errores groseros
					desv_ex = statistics.pstdev(vec_ex)
					desv_ey = statistics.pstdev(vec_ey)

					# Calculo de la diferencia media sin errores groseros
					med_dif_x = statistics.mean(vec_ex)
					med_dif_y = statistics.mean(vec_ey)

					# Prueba para errores sistematicos (sesgo) NATO
					num_pt_r = num_pt-gros_c_e
					t10_h = scipy.stats.t.ppf(1-(0.10/2), ((num_pt_r)-1))
					desv_med_x = desv_ex/(num_pt_r)**0.5
					bajo_x = med_dif_x-t10_h*desv_med_x
					alto_x = med_dif_x+t10_h*desv_med_x

					if bajo_x<=0 and alto_x>=0:
						mens_sesgo_x = "Se considera que <b>no existe</b> sesgo significativo en la posición <b>este</b> con un nivel de confianza del 90%."
					else:
						mens_sesgo_x = "Se considera que <b>existe</b> sesgo significativo en la posición <b>este</b> con un nivel de confianza del 90%"

					desv_med_y = desv_ey/(num_pt_r)**0.5
					bajo_y = med_dif_y-t10_h*desv_med_y
					alto_y = med_dif_y+t10_h*desv_med_y

					if bajo_y<=0 and alto_y>=0:
						mens_sesgo_y = "Se considera que <b>no existe</b> sesgo significativo en la posición <b>norte</b> con un nivel de confianza del 90%."
					else:
						mens_sesgo_y = "Se considera que <b>existe</b> sesgo significativo en la posición <b>norte</b> con un nivel de confianza del 90%"


					# Evaluacion de la incertidumbre en la posicional vertical (capa 201L)
					# Creación de puntos aleatorios en las lineas de error.
					vector_z = []
					if msgBox == QMessageBox.Yes:
						muestreo_vert = processing.run("native:randompointsonlines", {'INPUT':capa_posi,'POINTS_NUMBER':1,'MIN_DISTANCE':None,'MIN_DISTANCE_GLOBAL':None,'MAX_TRIES_PER_POINT':None,'SEED':None,'INCLUDE_LINE_ATTRIBUTES':True,'OUTPUT':'TEMPORARY_OUTPUT'}, context=context)
						muestreo_vert['OUTPUT'].dataProvider().deleteAttributes([0,3,4])
						muestreo_vert['OUTPUT'].updateFields()
						muestreo_cde = processing.run("native:rastersampling", {'INPUT':muestreo_vert['OUTPUT'],'RASTERCOPY':rlayer_cde,'COLUMN_PREFIX':'Z_CDE','OUTPUT':'TEMPORARY_OUTPUT'})
						muestreo_cdr = processing.run("native:rastersampling", {'INPUT':muestreo_cde['OUTPUT'],'RASTERCOPY':rlayer_cdr,'COLUMN_PREFIX':'Z_CDR','OUTPUT':'TEMPORARY_OUTPUT'})
						processing.run("native:renamelayer", {'INPUT': muestreo_cdr['OUTPUT'],'NAME': 'Muestreo Alturas'})
						project.addMapLayer(muestreo_cdr['OUTPUT'], False)
						migrupo.addLayer(muestreo_cdr['OUTPUT'])
						vr_des_z = []
						sum_z = 0
						sum_z_40 = 0
						sum_z_40r = 0
						cont = 0
						for m in muestreo_cdr['OUTPUT'].getFeatures():
							vector_z.append([m.attributes()[0],m.attributes()[1],m.attributes()[2],m.attributes()[3]])
							if m.attributes()[2]!=None and m.attributes()[3]!=None:
								des_z = m.attributes()[2]-m.attributes()[3]
								sum_z += (m.attributes()[2]-m.attributes()[3])**2
								sum_z_40 += m.attributes()[2]-m.attributes()[3]
								sum_z_40r += (m.attributes()[2]-m.attributes()[3])**2
								cont +=1
								vr_des_z.append(des_z)
						cont_z = cont
						if len(vr_des_z)>1:
							desv_z = statistics.stdev(vr_des_z)
							desv_z_p = statistics.pstdev(vr_des_z)
						else:
							desv_z = 0

						# Errores groseros vertical
						error_gro_l = 1.9423+(0.5604*math.log10(cont_z-1))
						m1_desv = error_gro_l*desv_z_p
						gros_v = 0
						gros_v_e = 0
						for m in muestreo_cdr['OUTPUT'].getFeatures():
							if m.attributes()[2]!=None and m.attributes()[3]!=None:
								des_z = m.attributes()[2]-m.attributes()[3]
								residual = des_z-(statistics.mean(vr_des_z))
								if abs(residual)>m1_desv:
									gros_v += 1
									titulo = "Errores groseros verticales detectados"
									mens_b = f"El valor absoluto del residual {residual:.2f} es mayor a {m1_desv:.2f} del test lineal (NATO) ¿Desea eliminar este punto del muestreo vertical?"
									msgBox_e = QMessageBox().question(self,titulo, mens_b, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
									if msgBox_e == QMessageBox.Yes:
										ids = m.id()
										muestreo_cdr['OUTPUT'].dataProvider().deleteFeatures([ids])
										gros_v_e+=1

						# Prueba para errores sistematicos (sesgo)
						t10_v = scipy.stats.t.ppf(1-(0.10/2), (cont_z-1))
						desv_med_z = desv_z_p/(cont_z)**0.5
						bajo_z = (statistics.mean(vr_des_z))-t10_v*desv_med_z
						alto_z = (statistics.mean(vr_des_z))+t10_v*desv_med_z

						if bajo_z<=0 and alto_z>=0:
							mens_sesgo_z = "Se considera que <b>no existe</b> sesgo significativo en la posición <b>Z</b> con un nivel de confianza del 90%."
						else:
							mens_sesgo_z = "Se considera que <b>existe</b> sesgo significativo en la posición <b>Z</b> con un nivel de confianza del 90%"


						# Medidas de calidad Norma ISO 19157 para incertidumbre vertical
						le50 = desv_z*0.6745  # Medida 33
						le683 = desv_z*1 # Medida 34
						le90 =  desv_z*1.6449 # Mediada 35 (Bias-free Estimate of LMAS)
						le95 =  desv_z*1.960 # Medida 36
						le99 =  desv_z*2.576 # Medida 37
						le998 = desv_z*3 # Medida 38
						ecm_z = (sum_z/cont)**0.5 # Medida 39 
						# medida 40
						val_abs_40 = abs(sum_z_40/cont)
						desv_zr = (sum_z_40r/cont)**0.5 
						desv_v = (ecm_z**2 + desv_zr**2)**0.5				
						# Se requiere conocer la desviacion estandar lineal del error en la CDR. 

						#ratio_z = abs(val_abs_40)/desv_v
						#if ratio_z>1.4:
						#	lmas_z = desv_v*(1.282+ratio_z)
						#else:
							#lmas_z = desv_v*(1.6435+(0.92*ratio_z**2)-(0.28*ratio_z**2))
						
						# Medida 41
						try:
							ratio_z = abs(val_abs_40)/ecm_z
						except ZeroDivisionError:
							ratio_z = 0

						if ratio_z>1.4:
							k=1.2815
						else:
							k = 1.6435-(0.999556*ratio_z)+(0.923237*ratio_z**2)-(0.282533*ratio_z**3)
						ale_z= abs(val_abs_40)+(k*ecm_z)
						# --------

					# Calculo de las medidas de calidad ISO 19157
						# Valor medio de la incertidumbre posicional medida 28
					vmip = 0
					vmip_sum = 0

						# Sesgo de las pósiciones
					ax = ax_sum / num_pt_r # Error medio horizontal
					ay = ay_sum / num_pt_r # Error medio horizontal
					ap  = (ax**2+ay**2)**0.5 # Error del vector medio (bias)

						# Valor medio de las incertidumbres posicionales excluyendo atípicos
					if num_pt_r>excluidos:
						axe = axe_sum / (num_pt_r-excluidos)
						aye = aye_sum / (num_pt_r-excluidos)
						ape  = (axe**2+aye**2)**0.5
						exc = f">{tolerancia} m"
					else:
						axe = 999999
						aye = 999999
						ape = 999999
						exc = f"Se excluyen los {excluidos} puntos muestreados"

					# Incertidumbres poscionales horizontales
					# Error circular
					desv_ex = statistics.pstdev(vec_ex)
					desv_ey = statistics.pstdev(vec_ey)
					
					# Error cuadratico medio
					n = len(vec_ex)
					suma = 0
					for x in range(n):
						suma += vec_ex[x]**2+vec_ey[x]**2
					ecmp = (suma/n)**0.5 # Medida 47

					ce394 = (1/(2**0.5))*((desv_ex**2)+(desv_ey**2))**0.5 # Medida 42
					ce50 = (1.1774/(2**0.5))*((desv_ex**2)+(desv_ey**2))**0.5 # Medida 43
					ce90 = (2.146/(2**0.5))*((desv_ex**2)+(desv_ey**2))**0.5 # Mediada 44
					ce95 = (2.4477/(2**0.5))*((desv_ex**2)+(desv_ey**2))**0.5 # Medida 45
					ce998 = (3.5/(2**0.5))*((desv_ex**2)+(desv_ey**2))**0.5 # Medida 46

					# Error circular absoluto al 90% Nato Stanag 2215
					px = sum([(n-ax)**2 for n in vec_ex])
					py = sum([(n-ay)**2 for n in vec_ey])
					dtp = ((1/(2*(num_pt_r-1)))*(px+py))**0.5 # Desviacion tipica (cm)
					# dtc = (dtp**2+ce394**2)**0.5 # Desviacion tipica circular
					# eca = dtc*((1.2943)+(((ax**2+ay**2)/dtc)+0.7254)**0.5) # Error circular absoluto Medida 48

					# Error circular absoluto al 90% ACE
					sum_dist = 0
					for m in capa_posi.getFeatures():
						sum_dist +=m.attributes()[2]
					emh = sum_dist/num_pt_r #Error medio horizontal
					sum_desv = 0
					for m in capa_posi.getFeatures():
						sum_desv +=(m.attributes()[2]-emh)**2
					desv_tiph = (sum_desv/(num_pt_r-1))**0.5 # Desviacion tipica horizontal
					ratio = abs(emh)/desv_tiph # ratio
					if ratio > 1.4:
						k=1.2815
					else:
						k=1.6435-(0.999556*ratio)+(0.923237*ratio**2)-(0.282533*ratio**3)
					ce90_m49 = abs(emh)+(k*desv_tiph) # Medida 49

					# Exactitud relativa o interna
					# Exactiud relativa horizontal
					comb = (math.factorial(num_pt_r))/(math.factorial(num_pt_r - 2)*math.factorial(2))

					sum_x  = 0
					for n in range(len(vec_ex)-1):
						m = n + 1
						for t in range(m,len(vec_ex)):
							sum_x += (vec_ex[n]-vec_ex[t])
					error_rel_e = ((sum_x**2)/(comb-1))**0.5

					sum_y  = 0
					for n in range(len(vec_ey)-1):
						m = n + 1
						for t in range(m,len(vec_ey)):
							sum_y += (vec_ey[n]-vec_ey[t])
					error_rel_n = ((sum_y**2)/(comb-1))**0.5

					error_rel_h = ((error_rel_e**2+error_rel_n**2)/2)**0.5
					er_ce90 = 2.146*error_rel_h # Medida 53

					if msgBox == QMessageBox.Yes:
						comb_z = (math.factorial(cont_z))/(math.factorial(cont_z - 2)*math.factorial(2))
						sum_z  = 0
						for n in range(len(vr_des_z)-1):
							m = n + 1
							for t in range(m,len(vr_des_z)):
								sum_z += (vr_des_z[n]-vr_des_z[t])
						error_rel_z = ((sum_z**2)/(comb_z-1))**0.5

						er_le90 = 1.645*error_rel_z # Medida 52


					# Reporte de la evaluación
					text_for = "<center><h2>Evaluación Exactitud Posicional</h2></center>"
					text_for += f"Proyecto: <b>{ruta}</b><p>"
					text_for += f"La evaluación se realiza sobre: <b>{cob}</b> {area_cob} <p>"
					text_for += f"Fecha: <b>{hoy}</b><p>"
					text_for += "Método de evaluación: <b>Directo Externo</b><p>"
					por_muestreo = round((num_pt_r/entidades)*100,1)
					text_for += f"Enfoque de inspeción: <b>Automático / Muestreo ({por_muestreo} %)</b><p>"
					text_for += f"Puntos muestreo inicial {num_pt} puntos<br>"

					# Detallado en incertidumbre (errores groseros)
					text_for += "<h3>Detección de errores groseros (Outlier)</h3><p>"
					text_for += "<h4>Posiciones horizontales</h4>"
					text_for += "<b>Test Circular</b><p>"
					text_for += f"Grados de libertad {num_pt-1} <p>"
					text_for += f"Potencial errores groseros (>): {m2_desv:.2f} m<p>"
					text_for += f"Errores groseros horizontales encontrados: <b>{gros_c}</b><p>"
					text_for += f"Errores groseros horizontales eliminados: <b>{gros_c_e}</b><p>"		

					if msgBox == QMessageBox.Yes:	
						text_for += "<h4>Posiciones vertical</h4>"
						text_for += "<b>Test lineal</b><p>"
						text_for += f"Grados de libertad {cont_z-1} <p>"
						text_for += f"Potencial errores groseros (>): {m1_desv:.2f} m<p>"
						text_for += f"Errores groseros verticales encontrados: {gros_v}<p>"
						text_for += f"Errores groseros verticales eliminados: {gros_v_e}<p>"													

					# Test sistematico
					text_for += "<h3>Test de significancia del sesgo calculado</h3><p>"
					text_for += f"Rango posiciones en <b>este: ({bajo_x:.4f} : {alto_x:.4f})</b><p>"
					text_for += f"<p>{mens_sesgo_x}</p>"
					text_for += f"Rango posiciones en <b>norte: ({bajo_y:.4f} : {alto_y:.4f})</b><p>"
					text_for += f"<p>{mens_sesgo_y}</p>"

					if msgBox == QMessageBox.Yes:	
						# Test sistematico
						text_for += f"Rango posiciones en <b>altura (Z): ({bajo_z:.4f} : {alto_z:.4f})</b><p>"
						text_for += f"<p>{mens_sesgo_z}</p><br><br>"


					text_for +="<table border=1><tr><td><b>Muestra</b></td><td><b>ID CDE</b></td><td><b>ID CDR</b></td><td><b>Distancia (metros)</b></td><td><b>Fuente</b></td></tr>"
					
					muestra = 1
					z_cde = []
					z_cdr = []
					for m in capa_posi.getFeatures():
						for n in vector_z:
							if m.attributes()[0]==n[0] and m.attributes()[1]==n[1]:
								if n[2]==None:
									z_cde.append("")
								else:
									z_cde.append(n[2])
								if n[3]==None:
									z_cdr.append("")
								else:
									z_cdr.append(n[3])
						text_for +=f"<tr><td><b>{muestra}</b></td><td>{m.attributes()[0]}</td><td>{m.attributes()[1]}</td><td>{m.attributes()[2]:.2f}</td><td>{m.attributes()[3]}</td></tr>"
						muestra += 1
					# Valor medio de la incertidumbre posicional medida 28	
					vmip = emh
					# ---

					text_for += "</table><p>"
					text_for += """<h4>Criterios:</h4> 
						<p>El usuario debe asegurarse que la exactitud del <b>CDR</b> debe ser, como mínimo, tres veces mayor que la exactitud del <b>CDE</b>. Se recomienda consultar 
						el método de creación y las especificaciones del CDE para diseñar y ejecutar un método de captura del CDR que asegure este requisito.</p>
						<p>Para los CDE tipo punto la evaluación se realiza buscando el punto homologo en el CDR mas cercano al punto muestreado, 
						para los CDE y CDR tipo Linea, se extraen el primer y ultimo vertice de cada entidad, se realiza la evaluación muestreando los puntos homologos mas cercados 
						y en el de los CDE y CDR tipo poligono, se extrae el centroide de cada entidad, se realiza la evaluación muestreando los puntos homologos mas cercados</p><br>"""
					text_for += f"<b>Escala </b>1:{escala}<br>"
					if clase == "":
						text_for += f"Tolerancia <b>{opc_umb}</b> con un valor de: <b>{tolerancia} m</b><br><br>"
					else:
						text_for += f"Tolerancia <b>{opc_umb}</b> selecionado clase <b>{clase} </b><br>"
						text_for += f" con RMSEx o RMSEy: <b>{round(((((tolerancia/1.7308)**2)/2)**0.5),2)} m</b>, con RMSEr: <b>{tolerancia/1.7308:.2f} m</b> y Precisión Horizontal al 95% de confianza: <b>{tolerancia:.2f} m</b><br>"
					text_for += "<h3>Exactitud absoluta o externa</h3><br>"
					text_for += "<table border=1><tr><td colspan=3><h4>Medidas generales para incertidumbres posicionales</h4></td></tr>"
					text_for += f"<tr><td colspan=3><p style='text-align:left;'>Incertidumbres posicionales horizontales <b>(puntos muestreados {num_pt_r})</b></p></td></tr>"
					text_for += f"<tr><td><b>Valor medio de las incertidumbres posicionales</b></td><td>Medida 28</td><td>{vmip:.2f} m</td></tr>"
					text_for +=f"<tr><td><b>Sesgo de las posiciones</b></td><td>Medida 128</td><td>Sesgo en X:<b>{ax:.2f}</b> m\nSesgo en Y:<b>{ay:.2f}</b> m\nSesgo posicional:<b>{ap:.2f}</b> m</td></tr>"
					text_for +=f"<tr><td><b>Valor medio de las incertidumbres posicionales excluyendo atípicos ({exc})</b></td><td>Medida 29</td><td>Sesgo en X:<b>{axe:.2f}</b> m\nSesgo en Y:<b>{aye:.2f}</b> m\nSesgo posicional:<b>{ape:.2f}</b> m</td></tr>"
					text_for +=f"<tr><td><b>Número de incertidumbres posicionales mayores que el umbral (>{tolerancia} m)</b></td><td>Medida 30</td><td>{excluidos}</td></tr>"
					text_for +=f"<tr><td><b>Indice de errores posicionales mayores que un umbral (>{tolerancia} m)</b></td><td>Medida 31</td><td>{((excluidos/num_pt_r)*100):.2f} %</td></tr>"
					if msgBox == QMessageBox.Yes:
						text_for += f"<tr><td colspan=3><p style='text-align:left;'>Incertidumbres posicionales verticales <b>(puntos muestreados {cont_z})</b></p></td></tr>"
						text_for += f"<tr><td><b>Error lineal probable</b> (LEP Linear Error Probable) LE50</td><td>Medida 33</td><td>{le50:.2f} m</td></tr>"
						text_for += f"<tr><td><b>Error lineal tipico</b> (SLE standard linear error) LE68.3</td><td>Medida 34</td><td>{le683:.2f} m</td></tr>"
						text_for += f"<tr><td><b>Exactitud lineal al 90% de nivel de significación</b> (LMAS Linear Map Accuracy Standard) LE90</td><td>Medida 35</td><td>{le90:.2f} m</td></tr>"
						text_for += f"<tr><td><b>Exactitud lineal al 95% de nivel de significación</b> (LMAS Linear Map Accuracy Standard) LE95</td><td>Medida 36</td><td>{le95:.2f} m</td></tr>"
						text_for += f"<tr><td><b>Exactitud lineal al 99% de nivel de significación</b> (LMAS Linear Map Accuracy Standars) LE99</td><td>Medida 37</td><td>{le99:.2f} m</td></tr>"
						text_for += f"<tr><td><b>Error lineal casi cierto LE99.8</b></td><td>Medida 38</td><td>{le998:.2f} m</td></tr>"
						text_for += f"<tr><td><b>Error cuadrático medio ECM</b> (RMSE Root Mean Squared Error)</td><td>Medida 39</td><td>{ecm_z:.2f} m</td></tr>"
						#text_for += f"<tr><td><b>Error lineal absoluto al 90% de nivel de significación con sesgo</b> (LMAS Linear Map Accuracy Standard)</td><td>Medida 40</td><td>{lmas_z:.2f} m</td></tr>"
						text_for += f"<tr><td><b>Error lineal absoluto al 90% de nivel de significación con sesgo</b> (ALE Absolute Linear Error)</td><td>Medida 41</td><td>{ale_z:.2f} m</td></tr>"
					text_for +="</table><p>"

					text_for += "<table border=1><tr><td colspan=3><h4>Incertidumbres posicionales horizonales</h4></td></tr>"
					text_for += f"<tr><td><b>Desviación tipica circular</b>, error puntual de Helmert, CSE (Circular Standard Error)</td><td>Medida 42</td><td>{ce394:.2f} m</td></tr>"
					text_for +=f"<tr><td><b>Error Circular probable</b> CEP (Circular Error Probable)</td><td>Medida 43</td><td>{ce50:.2f} m</td></tr>"
					text_for +=f"<tr><td><b>Error circular estandar</b> (CMAS, Circular Map Accuracy Standard) 90% nivel de significación</td><td>Medida 44</td><td>{ce90:.2f} m</td></tr>"
					text_for +=f"<tr><td><b>Exactitud de navegación</b> (95% nivel de significación)</td><td>Medida 45</td><td>{ce95:.2f} m</td></tr>"
					text_for +=f"<tr><td><b>Error circular casi cierto</b> (CNCE Circular Near Certainty Error)</td><td>Medida 46</td><td>{ce998:.2f} m</td></tr>"
					text_for +=f"<tr><td><b>ECMP Error Cuadratico Medio Planimetrico</b> (RMSEP Root Mean Square Error of Planimetry)</td><td>Medida 47</td><td>{ecmp:.2f} m</td></tr>"
					#text_for +=f"<tr><td><b>Error circular absoluto al 90% del nivel de significacion con sesgo</b> (Nato Stanag 2215)</td><td>Medida 48</td><td>{eca:.2f} m</td></tr>"
					text_for +=f"<tr><td><b>Error circular para el producto evaluado al 90% del nivel de significacion con sesgo</b> (ACE Absolute circular error)</td><td>Medida 49</td><td>{ce90_m49:.2f} m</td></tr>"
					text_for +="</table><br>"
					text_for += "<h3>Exactitud relativa o interna</h3>"
					text_for += "<table border=1>"
					text_for += f"<tr><td colspan=3><p style='text-align:left;'>Incertidumbres posicionales relativas horizontales <b>(puntos muestreados {num_pt_r})</b></p></td></tr>"
					text_for += f"<tr><td><b>Error horizontal relativo</b> Rel CE90</td><td>Medida 53</td><td>{er_ce90:.2f} m</td></tr>"
					if msgBox == QMessageBox.Yes:
						text_for += f"<tr><td colspan=3><p style='text-align:left;'>Incertidumbres posicionales relativas verticales <b>(puntos muestreados {cont_z})</b></p></td></tr>"
						text_for += f"<tr><td><b>Error vertical relativo</b> Rel LE90</td><td>Medida 52</td><td>{er_le90:.2f} m</td></tr>"
					text_for +="</table>"

					mensaje_exac =	"<b>Coordenas puntos muestreados</b><p>"
					if len(vector_z)>0:
						mensaje_exac += "<table border=1><tr><td rowspan=2><b>Muestra</b></td><td colspan=2><b>CDE</b></td><td colspan=2><b>CDR</b></td><td rowspan=2><b>Error Norte</b></td><td rowspan=2><b>Error Este</b></td><td rowspan=2><b>Z CDE</b></td><td rowspan=2><b>Z CDR</b></td></tr>"
					else: 
						mensaje_exac += "<table border=1><tr><td rowspan=2><b>Muestra</b></td><td colspan=2><b>CDE</b></td><td colspan=2><b>CDR</b></td><td rowspan=2><b>Error Norte</b></td><td rowspan=2><b>Error Este</b></td></tr>"
					mensaje_exac += "<tr><td><b>Norte</b></td><td><b>Este</b></td><td><b>Norte</b></td><td><b>Este</b></td></tr>"
					cont=0
					for n in vec_coor:
						cont+=1
						if len(vector_z)>0:
							if z_cde[cont-1]=="":
								z_cde_m = ""
							else:
								z_cde_m = round(z_cde[cont-1],2)
							if z_cdr[cont-1]=="":
								z_cdr_m = ""
							else:
								z_cdr_m = round(z_cdr[cont-1],2)
							mensaje_exac += f"<tr><td>{cont}</td><td>{n[1]:.2f}</td><td>{n[0]:.2f}</td><td>{n[3]:.2f}</td><td>{n[2]:.2f}</td><td>{(n[0]-n[2]):.2f}</td><td>{(n[1]-n[3]):.2f}</td><td>{z_cde_m}</td><td>{z_cdr_m}</td></tr>"
						else:
							mensaje_exac += f"<tr><td>{cont}</td><td>{n[1]:.2f}</td><td>{n[0]:.2f}</td><td>{n[3]:.2f}</td><td>{n[2]:.2f}</td><td>{(n[0]-n[2]):.2f}</td><td>{(n[1]-n[3]):.2f}</td></tr>"			
					mensaje_exac += "</table><p>"
					mensaje_exac += f"<b>Distribución del error horizontal de los puntos muestreados ({cont} puntos)</b><p>"
					mensaje_exac += """<svg version='1.1' xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'>\n
						<circle cx='200' cy='200' r='180' fill='White' stroke='RoyalBlue' stroke-width='2'/>
						<line x1='20' y1='200' x2='380' y2='200' stroke-width='1' stroke='RoyalBlue' />
						<line x1='200' y1='20' x2='200' y2='380' stroke-width='1' stroke='RoyalBlue' />
						<line x1='327.279' y1='327.279' x2='72.721' y2='72.721' stroke-width='1' stroke='RoyalBlue' />
						<line x1='72.721' y1='327.279' x2='327.279' y2='72.721' stroke-width='1' stroke='RoyalBlue' />
						<text x='197' y='14' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>0°</text>
						<text x='-1' y='202' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>270°</text>
						<text x='385' y='202' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>90°</text>
						<text x='192' y='395' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>180°</text>
						<text x='330' y='75' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>45°</text>
						<text x='331' y='332' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>135°</text>
						<text x='47' y='332' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>225°</text>
						<text x='47' y='75' fill='Blue' stroke='blue' stroke-width='0.5px' style='font-family:Arial; font-size:10px;'>315°</text>
						"""
					sum_sen = 0
					sum_cos = 0
					sum_sen2 = 0
					sum_cos2 = 0
					cont = 0
					angulos = []
					# Calculo de la media y visualizacion de los puntos en el circulo unitario
					for n in vec_coor:
						delta_n = (n[3]-n[1])
						delta_e = (n[2]-n[0])
						if delta_n!=0 or delta_e!=0:
							if delta_n==0:
								if delta_e>0:
									angulo = 90*(math.pi)/180
									angulo2 = 2*(90*(math.pi)/180)
									pos_y = 0
									pos_x = 180
								elif delta_e<0:
									angulo = 270*(math.pi)/180
									angulo2 = 2*(270*(math.pi)/180)
									pos_y = 0
									pos_x = -180
							else:
								angulo = math.atan(delta_e/delta_n)
								angulo2 = 2*(math.atan(delta_e/delta_n))
							if delta_n>0 and delta_e>=0:
								pos_y = (math.cos(angulo))*180
								pos_x = (math.sin(angulo))*180
							if delta_n<0:
								angulo = (math.pi)+angulo
								angulo2 = 2*((math.pi)+angulo)  
								pos_y = (math.cos(angulo))*180
								pos_x = (math.sin(angulo))*180
							if delta_n>0 and delta_e<0:
								angulo = 2*(math.pi)+angulo
								angulo2 = 2*(2*(math.pi)+angulo)
								pos_y = (math.cos(angulo))*180
								pos_x = (math.sin(angulo))*180
							angulos.append(angulo)
							sum_sen += (math.sin(angulo))
							sum_sen2 += ((math.sin(angulo2)))
							sum_cos += (math.cos(angulo))
							sum_cos2 += ((math.cos(angulo2)))
							mensaje_exac+= f"<circle cx='{200+pos_x}' cy='{200-pos_y}' r='3' fill='Red' stroke='Red' stroke-width='1'/>"
							cont+=1
						else:
							mensaje_exac+= "<circle cx='200' cy='200' r='3' fill='Black' stroke='Black' stroke-width='1'/>"
					
					# Visualizacion del Angulo medio del error
					azi_med = math.atan(sum_sen/sum_cos)
					azi_med2 = math.atan(sum_sen2/sum_cos2)
					if sum_sen<0 and sum_cos<0:
						azi_med = (math.pi)+azi_med
						azi_med2 = (math.pi)+azi_med2
					pos_y = (math.cos(azi_med))*180
					pos_x = (math.sin(azi_med))*180
					if sum_sen>0 and sum_cos<0:
						pos_y=-pos_y
						pos_x=-pos_x
					mensaje_exac+= f"<line x1='200' y1='200' x2='{200+pos_x}' y2='{200-pos_y}' stroke-width='2' stroke='Red' />"
					mensaje_exac += "</svg><p>"

					# angulo medio del error en grados
					azi_med_g = azi_med*180/(math.pi)
					if azi_med_g<0:
						if sum_sen>0 and sum_cos<0:
							azi_med_g = 180+azi_med_g
						if sum_sen<0 and sum_cos>0:
							azi_med_g = 360+azi_med_g
					if azi_med_g>=360:
						azi_med_g = azi_med_g-360

					minutos, grados = math.modf(azi_med_g)
					segundos, minutos = math.modf(minutos*60)
					segundos = (segundos*60)
					mensaje_exac += f"Acimut medio (Grados): {grados:.0f}° {minutos:.0f}' {segundos:.2f}''<p>"

					# Modulo medio
					mod_med = (((sum_cos**2)+(sum_sen**2))**0.5)/cont
					mod_med2 = (((sum_cos2**2)+(sum_sen2**2))**0.5)/cont
					mensaje_exac += f"Modulo medio: {mod_med:.4f}<p>"

					# Varianza circular
					var_cir = 1 - mod_med
					mensaje_exac += f"Varianza circular: {var_cir:.4f}<p>"

					# Desviacion estandar circular
					des_cir = ((-2*(math.log(1-var_cir))))**0.5
					minutos, grados = math.modf(des_cir)
					segundos, minutos = math.modf(minutos*60)
					segundos = (segundos*60)
					mensaje_exac += f"Desviación estandar circular (Grados): {grados:.0f}° {minutos:.0f}' {segundos:.2f}''<p>"

					# Medidas de Asimetría (skewness o sesgo)
					skew = (mod_med2*math.sin(azi_med2-(2*azi_med)))/(1-mod_med)**(3/2)
					mensaje_exac += f"Asimetría (skewness o sesgo): {skew:.4f}<p>"

					# Medidas de Curtosis (o elevación)
					curt = ((mod_med2*math.cos(azi_med2-(2*azi_med)))-mod_med**4)/(1-mod_med)**2
					mensaje_exac += f"Curtosis (o elevación): {curt:.4f}<p>"

					# dispersión circular 
					disp_cir = (1-mod_med2)/(2*mod_med**2)
					mensaje_exac += f"Dispersión circular: {disp_cir:.4f}<p>"

					# Dispercion angular - Desviación estandar angular
					sum_ang = 0
					for x in angulos:
						sum_ang += math.pi-abs(math.pi-abs(x-azi_med))
					desv_ang = sum_ang/len(angulos)
					desv_ang = desv_ang*180/math.pi
					minutos, grados = math.modf(desv_ang)
					segundos, minutos = math.modf(minutos*60)
					segundos = (segundos*60)
					mensaje_exac += f"Desviación estandar angular: {grados:.0f}° {minutos:.0f}' {segundos:.2f}''<p>"

					# Dispercion angular - desviacion angular media
					desv_ang_med = (180/math.pi)*(2*(1-mod_med))**0.5
					minutos, grados = math.modf(desv_ang_med)
					segundos, minutos = math.modf(minutos*60)
					segundos = (segundos*60)
					mensaje_exac += f"Desviación angular media (Batschelet, 1981): {grados:.0f}° {minutos:.0f}' {segundos:.2f}''<p>"

					# Estimar el parámetro de concentración Para una distriubción von Mises
					if mod_med<0.53:
						k = (2*mod_med)+(mod_med**3)+((5/6)*mod_med**5)
					if mod_med>=0.53 and mod_med<0.85:
						k = (-0.4)+(1.39*mod_med)+(0.43/(1-mod_med))
					if mod_med>=0.85 and mod_med<0.90:
						k = 1/((2*(1-mod_med))+((1-mod_med)**2)-((1-mod_med)**3))
					if mod_med>=0.90:
						k = 1/(2*(1-mod_med))
					mensaje_exac += f"Parámetro Von Mises: {k:.4f}<p><br>"


					# Genera el mensaje
					mensaje = mensaje_exac+"<p>"

					resultado = str(ruta)+'/Resultados/Calidad_posicional.html'
					f = open (resultado, 'w')
					f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>Resultado de Evaluación Calidad - Exactitud Posiocional</title>\n')
					f.write('<style type="text/css">\nbody {font-family: arial; margin: 5%;}\ntable {border: 2px solid blue; border-collapse: collapse; font-family: arial; width: 80%;}\n')
					f.write('td {padding: 5px;text-align: center;}</style></head>\n<body>\n')
					f.write(text_for)
					f.write('\n<p>\n')
					f.write('<hr><p><h3>Reporte Detallado</h3><p>\n')
					f.write(mensaje)
					f.write('\n</html>')
					f.close()

					self.bt_resultado.setEnabled(True)
					self.bt_resultado.clicked.connect(self.ver_result_posi)
					   
					doc = """<style type='text/css'>
						table {border-collapse:collapse; border:1px; border-style:solid; border-color:darkblue; padding:3px; vertical-align:middle;} 
						td {padding: 3px;text-align: center;}</style>"""

					self.rel_val.setHtml(doc+text_for)
					self.pbr_elem.setValue(100)
				else:
					doc = """<style type='text/css'>
						table {border-collapse:collapse; border:1px; border-style:solid; border-color:darkblue; padding:3px; vertical-align:middle;} 
						td {padding: 3px;text-align: center;}</style>"""
					text_for=f"""Al eliminar {gros_c_e} puntos con errores groseros el total de puntos de la muestra es menor a 20, 
						de volver a aplicar la evaluación de exactitud posicional para realizar un nuevo muestreo."""
					self.rel_val.setHtml(doc+text_for)
			else:
				if curvas=="si":
					keys= capa_cde_posi.keys()
					for x in keys:
						p=x
					epsg=capa_cde_posi[p].crs().toWkt()

					ext_ext = ext.extent()
					diagonal = (((ext_ext.xMaximum()-ext_ext.xMinimum())**2+(ext_ext.yMaximum()-ext_ext.yMinimum())**2)**0.5)/10
					pts_muestreo = processing.run("native:randompointsinextent", {'EXTENT':ext_ext,'POINTS_NUMBER':num_pt,'MIN_DISTANCE':diagonal,'TARGET_CRS':QgsCoordinateReferenceSystem(epsg),'MAX_ATTEMPTS':200,'OUTPUT':'TEMPORARY_OUTPUT'})
					muestreo_cde = processing.run("native:rastersampling", {'INPUT':pts_muestreo['OUTPUT'],'RASTERCOPY':rlayer_cde,'COLUMN_PREFIX':'Z_CDE','OUTPUT':'TEMPORARY_OUTPUT'})
					muestreo_cdr = processing.run("native:rastersampling", {'INPUT':muestreo_cde['OUTPUT'],'RASTERCOPY':rlayer_cdr,'COLUMN_PREFIX':'Z_CDR','OUTPUT':'TEMPORARY_OUTPUT'})

					project.addMapLayer(muestreo_cdr['OUTPUT'], False)
					processing.run("native:renamelayer", {'INPUT': muestreo_cdr['OUTPUT'],'NAME': 'Muestreo Alturas'})
					migrupo.insertChildNode(-1, QgsLayerTreeLayer(muestreo_cdr['OUTPUT']))

					vr_des_z = []
					cont = 0
					for m in muestreo_cdr['OUTPUT'].getFeatures():
						if m.attributes()[1]!=None and m.attributes()[2]!=None:
							des_z = m.attributes()[1]-m.attributes()[2]
							cont +=1
							vr_des_z.append(des_z)
					cont_z = cont
					if len(vr_des_z)>1:
						desv_z = statistics.stdev(vr_des_z)
						desv_z_p = statistics.pstdev(vr_des_z)
					else:
						desv_z = 0

					# Errores groseros vertical
					error_gro_l = 1.9423+(0.5604*math.log10(cont_z-1))
					m1_desv = error_gro_l*desv_z_p
					gros_v = 0
					gros_v_e = 0
					for m in muestreo_cdr['OUTPUT'].getFeatures():
						if m.attributes()[1]!=None and m.attributes()[2]!=None:
							des_z = m.attributes()[1]-m.attributes()[2]
							residual = des_z-(statistics.mean(vr_des_z))
							if abs(residual)>m1_desv:
								gros_v += 1
								titulo = "Errores groseros verticales detectados"
								mens_b = f"El valor absoluto del residual {residual:.2f} es mayor a {m1_desv:.2f} del test lineal (NATO) ¿Desea eliminar este punto del muestreo vertical?"
								msgBox_e = QMessageBox().question(self,titulo, mens_b, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
								if msgBox_e == QMessageBox.Yes:
									ids = m.id()
									muestreo_cdr['OUTPUT'].dataProvider().deleteFeatures([ids])
									gros_v_e+=1

					# Calculo de estadisticos sin errores groseros
					vr_des_z = []
					sum_z = 0
					sum_z_40 = 0
					sum_z_40r = 0
					cont = 0
					for m in muestreo_cdr['OUTPUT'].getFeatures():
						if m.attributes()[1]!=None and m.attributes()[2]!=None:
							des_z = m.attributes()[1]-m.attributes()[2]
							sum_z += (m.attributes()[1]-m.attributes()[2])**2
							sum_z_40 += m.attributes()[1]-m.attributes()[2]
							sum_z_40r += (m.attributes()[1]-m.attributes()[2])**2
							cont +=1
							vr_des_z.append(des_z)
					cont_z = cont
					if len(vr_des_z)>1:
						desv_z = statistics.stdev(vr_des_z)
						desv_z_p = statistics.pstdev(vr_des_z)
					else:
						desv_z = 0

					# Prueba para errores sistematicos (sesgo)
					t10_v = scipy.stats.t.ppf(1-(0.10/2), (cont_z-1))
					desv_med_z = desv_z_p/(cont_z)**0.5
					bajo_z = (statistics.mean(vr_des_z))-t10_v*desv_med_z
					alto_z = (statistics.mean(vr_des_z))+t10_v*desv_med_z

					if bajo_z<=0 and alto_z>=0:
						mens_sesgo_z = "Se considera que <b>no existe</b> sesgo significativo en la posición <b>Z</b> con un nivel de confianza del 90%."
					else:
						mens_sesgo_z = "Se considera que <b>existe</b> sesgo significativo en la posición <b>Z</b> con un nivel de confianza del 90%"

					# Medidas de calidad Norma ISO 19157
					le50 = desv_z*0.6745  # Medida 33
					le683 = desv_z*1 # Medida 34
					le90 =  desv_z*1.6449 # Mediada 35 (Bias-free Estimate of LMAS)
					le95 =  desv_z*1.960 # Medida 36
					le99 =  desv_z*2.576 # Medida 37
					le998 = desv_z*3 # Medida 38
					ecm_z = (sum_z/cont)**0.5 # Medida 39 
					# medida 40
					val_abs_40 = abs(sum_z_40/cont)
					desv_zr = (sum_z_40r/cont)**0.5 
					desv_v = (ecm_z**2 + desv_zr**2)**0.5				
					# Se requiere conocer la desviacion estandar lineal del error en la CDR. 

					#ratio_z = abs(val_abs_40)/desv_v
					#if ratio_z>1.4:
					#	lmas_z = desv_v*(1.282+ratio_z)
					#else:
						#lmas_z = desv_v*(1.6435+(0.92*ratio_z**2)-(0.28*ratio_z**2))
					
					# Medida 41
					ratio_z = abs(val_abs_40)/ecm_z
					if ratio_z>1.4:
						k=1.2815
					else:
						k = 1.6435-(0.999556*ratio_z)+(0.923237*ratio_z**2)-(0.282533*ratio_z**3)
					ale_z= abs(val_abs_40)+(k*ecm_z)

					# Error relativo o interno
					comb_z = (math.factorial(cont_z))/(math.factorial(cont_z - 2)*math.factorial(2))
					sum_z  = 0
					for n in range(len(vr_des_z)-1):
						m = n + 1
						for t in range(m,len(vr_des_z)):
							sum_z += (vr_des_z[n]-vr_des_z[t])
					error_rel_z = ((sum_z**2)/(comb_z-1))**0.5

					er_le90 = 2.146*error_rel_z # Medida 52

					# Reporte de la evaluación
					text_for = "<center><h2>Evaluación Exactitud Posicional Vertical</h2></center>"
					text_for += f"Proyecto: <b>{ruta}</b><p>"
					text_for += f"La evaluación se realiza sobre: <b>{cob}</b> {area_cob}<p>"
					text_for += f"Fecha: <b>{hoy}</b><p>"
					text_for += "Método de evaluación: <b>Directo Externo</b><p>"
					text_for += "Enfoque de inspeción: <b>Automático / Muestreo</b><p>"
					text_for += "<h3>Relación de datos muestreados</h3>"
					text_for += f"<b>Puntos muestreo inicial: {num_pt}</b>"
					# Detallado en incertidumbre Z (errores groseros)
					text_for += "<h3>Detección de errores groseros (Outlier)</h3><p>"
					text_for += "<h4>Posiciones vertical</h4><p>"
					text_for += "<b>Test lineal</b><p>"
					text_for += f"Grados de libertad {cont_z-1} <p>"
					text_for += f"Potencial errores groseros (>): {m1_desv:.2f} m<p>"
					text_for += f"Errores groseros verticales encontrados: {gros_v}<p>"	
					text_for += f"Errores groseros verticales eliminados: {gros_v_e}<p><br>"													

					# Test sistematico
					text_for += "<h3>Test de significancia del sesgo calculado</h3><p>"
					text_for += f"Rango posiciones en <b>altura (Z): ({bajo_z:.4f} : {alto_z:.4f})</b><p>"
					text_for += f"<p>{mens_sesgo_z}</p>"

					text_for +="<table border=1><tr><td><b>Muestra</b></td><td><b>Cota CDE</b></td><td><b>Cota CDR</b></td><td><b>Diferencia (metros)</b></td><td><b>Fuente</b></td></tr>"
					
					z_cde = []
					z_cdr = []
					for m in muestreo_cdr['OUTPUT'].getFeatures():
						if m.attributes()[1]!=None:
							cota_cde = round(m.attributes()[1],2)
						else:
							cota_cde = ""
						if m.attributes()[2]!=None:
							cota_cdr = round(m.attributes()[2],2)
						else:
							cota_cdr = ""
						if cota_cde!="" and cota_cdr!="":
							dif_cota = round(cota_cde-cota_cdr,2)
						else:
							dif_cota= ""
						text_for +=f"<tr><td><b>{m.attributes()[0]}</b></td><td>{cota_cde}</td><td>{cota_cdr}</td><td>{dif_cota}</td><td>{capa_cde_posi[p].name()}</td></tr>"
						
					text_for += "</table><p>"
					text_for += "<h3>Exactitud absoluta o externa</h3>"
					text_for += """<h4>Criterios:</h4> <p>Selección aleatoria de puntos, siguiendo las recomendaciones para muestreo sistemático no alineado.</p><br>"""
					text_for += f"<b>Escala </b>1:{escala}<br>"
					text_for += f"Tolerancia <b>{opc_umb}</b> con un valor de: <b>{tolerancia} m</b><br>"
					text_for += "<table border=1><tr><td colspan=3><h4>Medidas generales para incertidumbres posicionales</h4></td></tr>"
					text_for += f"<tr><td colspan=3><p style='text-align:left;'>Incertidumbres posicionales verticales <b>(puntos muestreados {cont_z-gros_v_e})</b></p></td></tr>"
					text_for += f"<tr><td><b>Error lineal probable</b> (LEP Linear Error Probable) LE50</td><td>Medida 33</td><td>{le50:.2f} m</td></tr>"
					text_for += f"<tr><td><b>Error lineal tipico</b> (SLE standard linear error) LE68.3</td><td>Medida 34</td><td>{le683:.2f} m</td></tr>"
					text_for += f"<tr><td><b>Exactitud lineal al 90% de nivel de significación</b> (LMAS Linear Map Accuracy Standard) LE90</td><td>Medida 35</td><td>{le90:.2f} m</td></tr>"
					text_for += f"<tr><td><b>Exactitud lineal al 95% de nivel de significación</b> (LMAS Linear Map Accuracy Standard) LE95</td><td>Medida 36</td><td>{le95:.2f} m</td></tr>"
					text_for += f"<tr><td><b>Exactitud lineal al 99% de nivel de significación</b> (LMAS Linear Map Accuracy Standars) LE99</td><td>Medida 37</td><td>{le99:.2f} m</td></tr>"
					text_for += f"<tr><td><b>Error lineal casi cierto LE99.8</b></td><td>Medida 38</td><td>{le998:.2f} m</td></tr>"
					text_for += f"<tr><td><b>Error cuadrático medio ECM</b> (RMSE Root Mean Squared Error)</td><td>Medida 39</td><td>{ecm_z:.2f} m</td></tr>"
					#text_for += f"<tr><td><b>Error lineal absoluto al 90% de nivel de significación con sesgo</b> (LMAS Linear Map Accuracy Standard)</td><td>Medida 40</td><td>{lmas_z:.2f} m</td></tr>"
					text_for += f"<tr><td><b>Error lineal absoluto al 90% de nivel de significación con sesgo</b> (ALE Absolute Linear Error)</td><td>Medida 41</td><td>{ale_z:.2f} m</td></tr>"
					text_for +="</table><p>"
					text_for += "<h3>Exactitud relativa o interna</h3><br>"
					text_for += "<table border=1>"
					text_for += f"<tr><td colspan=3><p style='text-align:left;'>Incertidumbres posicionales relativas verticales <b>(puntos muestreados {cont_z})</b></p></td></tr>"
					text_for += f"<tr><td><b>Error vertical relativo</b> Rel LE90</td><td>Medida 52</td><td>{er_le90:.2f} m</td></tr>"
					text_for +="</table><br>"

					# Genera el mensaje
					mensaje_exac=""
					mensaje = mensaje_exac+"<p>"

					resultado = str(ruta)+'/Resultados/Calidad_posicional.html'
					f = open (resultado, 'w')
					f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>Resultado de Evaluación Calidad - Exactitud Posiocional</title>\n')
					f.write('<style type="text/css">\nbody {font-family: arial; margin: 5%;}\ntable {border: 2px solid blue; border-collapse: collapse; font-family: arial; width: 80%;}\n')
					f.write('td {padding: 5px;text-align: center;}</style></head>\n<body>\n')
					f.write(text_for)
					f.write('\n<p>\n')
					f.write('<hr><p><h3>Reporte Detallado</h3><p>\n')
					f.write(mensaje)
					f.write('\n</html>')
					f.close()

					self.bt_resultado.setEnabled(True)
					self.bt_resultado.clicked.connect(self.ver_result_posi)
				   
					doc = """<style type='text/css'>
						table {border-collapse:collapse; border:1px; border-style:solid; border-color:darkblue; padding:3px; vertical-align:middle;} 
						td {padding: 3px;text-align: center;}</style>"""

					self.rel_val.setHtml(doc+text_for)
					self.pbr_elem.setValue(100)
				else:
					doc = """<style type='text/css'>p {color:red;} </style>"""
					text_for = "<br><p><b>No se ejecutó la evaluación de la exactitud posicional</b></p><br>"
					text_for += "Se presentó uno de los siguientes problemas:<br><br>"
					text_for += " - No se cuenta con Conjunto de Datos (CD) suficientes.<br><br>"
					text_for += " - El tipo de CD no corresponde a entidades con información de elevación (Z).<br>"
					
					self.rel_val.setHtml(doc+text_for)

		else:
			doc = """<style type='text/css'>p {color:red;} </style>"""
			text_for = "<br><p><b>No se ejecutó la evaluación de la exactitud posicional</b></p><br>"
			text_for += "Se presentó uno de los siguientes problemas:<br><br>"
			text_for += " - Los CDE no cuentan con las instancias suficientes (minimo 25 instancias).<br><br>"
			self.rel_val.setHtml(doc+text_for)

