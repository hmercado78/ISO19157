import os
import pandas as pd
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtGui import QTextDocument
from qgis.core import (QgsVectorLayer, QgsPointXY, QgsDistanceArea, 
    QgsField, QgsProject, QgsWkbTypes, QgsMarkerSymbol, QgsFeature, 
    QgsGeometry, QgsFeatureRequest)
from qgis.PyQt.QtCore import QVariant
from qgis import processing
from processing.tools import dataobjects
from collections import Counter
from qgis.gui import QgsMessageBar
import threading
from qgis.utils import iface
from qgis.core import Qgis
from math import sqrt
import itertools
from datetime import datetime

# Se instancia el proyecto
project = QgsProject.instance()

    # CONSISTENCIA DE FORMATO
    # Funcion para la evaluacion de calidad del elemento de calidad consistencia logica
  
def conLogica(self,capa_cde_cons,nom_cde_cons,ruta):
    iface.messageBar().pushMessage("Consistencia Lógica",'En ejecición por favor espere', level=Qgis.Info, duration=10)

    now = datetime.now()
    hoy = now.strftime('%Y/%m/%d %H:%M')

    est_vector=0
    no_est_vector=0
    root = project.layerTreeRoot()

    # Se configura el contexto para utilziarlo en los geoprocesos que requieran trabajar con geometrias invalidas
    context = dataobjects.createContext()
    context.setInvalidGeometryCheck(QgsFeatureRequest.GeometryNoCheck)
    # ------

    ruta_cata = os.path.join(os.path.dirname(__file__), r'..\datos')
    contenido = os.listdir(ruta_cata)
    lista_res = []
    for fichero in contenido:
      if os.path.isfile(os.path.join(ruta_cata, fichero)) and fichero.endswith('.txt'):
                lista_res.append(fichero)
    ok=""
    while ok=="" or ok==False:
      catalogo_file, ok = QInputDialog.getItem(self, "Catalogo de objetos", "Seleccione el catalogo de objetos:", lista_res, 0, False)

    texto_cata = f"<h4>Catálogo de Objetos</h4><br><b>Ruta: </b>{ruta_cata}<br><b>Catálogo: </b>{catalogo_file}"
    self.rel_val.setHtml(texto_cata)

    # Se pregunta al usuario para verificar la consistencia de formato -- legibilidad
    msgBox = QMessageBox().question(self,"Consistencia de Formato","¿Todos los CD de interes cargaron y se visualizaron de manera exitosa?", QMessageBox.Yes, QMessageBox.No)

    if msgBox == QMessageBox.Yes:
      legib119 = "Falso"
      num_arc_e = 0
      ok = True
    else: 
      legib119 = "Verdadero"
      num_arc_e, ok = QInputDialog.getInt(self,"Consistencia de Formato", "Entre el numero de archivos que no logro visualizar en Qgis",1,1,50,1)

    if ok==True:
      legib20 = round(((num_arc_e/(len(capa_cde_cons)+num_arc_e)))*100,2)
      
      # La verificacion del formato Shape es automatica, dado que el Plugin solo Acepta añadir este formato

      # Se revisa en la consistencia de formato la estructura vector
      keys= capa_cde_cons.keys()
      for x in keys:
        if isinstance(capa_cde_cons[x], QgsVectorLayer):
          est_vector +=1
        else: 
          no_est_vector +=1

      if no_est_vector>0:
        est_vector119="Verdadero"
      else:
        est_vector119="Falso"
   
      est_vector20 = round((no_est_vector/len(capa_cde_cons)),4)

      # Se revisa el nombre los archivos si estan dentro del catalogo de objetos del BTN25

      cata_sel = (os.path.join(ruta_cata, catalogo_file))
      if os.stat(cata_sel).st_size != 0:
        f = open (cata_sel, 'r')
        catalogo = pd.read_csv(f)
        f.close()

      nom_cat119 = ""
      nom_cat19 = 0
      cont_key=0
      tabla_catalo=dict()
      mensaje_nomb ="<table border=1><tr><td><b>Nombre Archivo</b></td><td><b>Nombre especificaciones BTN25</b></td></tr>"
      for capas in nom_cde_cons:
        tabla_cat = list()
        
        x=0
        for tabla in catalogo['TABLA'].tolist():
          if tabla in capas:
            nom_tabla = tabla
            nom_cat119 = "Falso"
            tabla_cat.append(x)
          x+=1
        key="c"+str(cont_key)
        cont_key+=1
        tabla_catalo[key]=tabla_cat
        
        if nom_cat119!="Falso":
          mensaje_nomb+= "<tr><td>"+capas+"</td><td></td></tr>"
          nom_cat119 = "Verdadero"
          nom_cat19 += 1
        else: 
          mensaje_nomb+= "<tr><td>"+capas+"</td><td>"+nom_tabla+"</td></tr>" 

      nom_cat20=round(nom_cat19/len(nom_cde_cons),4)


      x = 0
      acierto_campo=0
      acierto_tipo=0
      cont_key=0
      total=0
      mensaje_t_atrib="<table border=1><tr><td><b>Conjunto de Datos</b></td><td><b>Nombre Atributo</b></td><td><b>Tipo en CDE</b></td><td><b>Tipo en Especificación</b></td></tr>"
      mensaje_n_atrib="<table border=1><tr><td><b>Conjunto de Datos</b></td><td><b>Nombre Atributo en CDE</b></td><td><b>Nombre Atributo Especificación</b></td></tr>"
      mensaje_v_atrib="<table border=1><tr><td><b>Conjunto de Datos</b></td><td><b>Nombre Atributo</b></td><td><b># Chequeos</b></td><td><b># Inconsistencias</b></td></tr>"
      mensaje_topo="<table border=1><tr><td><b>Conjunto de Datos</b></td><td><b># Chequeos</b></td><td><b>Pt/Vert Duplicados</b></td>"
      mensaje_topo+="<td><b>Pts Superfluos</b></td><td><b>Bucles</b></td><td><b>entidades atributos duplicados</b></td><td><b>Elementos Solapados</b></td>"
      mensaje_topo+="<td><b>Elementos unificados</b></td><td><b>cruces / Anclajes Exceso</b></td><td><b>Anclajes por defecto</b></td><td><b>Contornos disjuntos</b></td></tr>"
      mensaje_topo+="<tr><td><b></b></td><td></td><td></td><td></td><td>Medida 26</td><td>Medida 4</td><td>Medida 27</td><td></td><td>Medida 24</td><td>Medida 23</td><td>Medida 11</td></tr>"
      mensaje_topo+="<tr><td><b>Simbología</b></td><td></td><td>&#9723; - &#128710;</td><td>O</td><td>X</td><td>En capa</td><td>En capa</td><td>&#9475;</td><td>&#9547;</td><td>></td><td>En capa</td></tr>"
      acum_dom_n = 0
      acum_dom_s = 0
      acum_to =0
      acum_to_pt = 0
      acum_to_li = 0
      acum_to_pl = 0
      acum_int_con = 0
      acum_feat = 0
      acum_error_ord = 0
      acum_feat_r = 0
      acum_pr = 0
      acum_ps = 0
      acum_buc = 0
      acum_dup_atr = 0
      acum_res_sol = 0
      acum_unif = 0
      acum_cruces = 0
      acum_anclajes = 0
      acum_disjuntos = 0
      pol_no_cer = 0
      error_pr=0
      error_ps=0
      total_chequeos = 0
      distance = QgsDistanceArea()
      lista_geo_pt = list()
      lista_geo_li = list()
      lista_geo_pl = list()
      lista_comp = list()
      lista_id = list()
      nom_pol_no_cer =""
      nom_con_int =""
      nom_ord_ver =""

      # se realiza la verificacion capa por capa
      cont_nom = 0
      keys= capa_cde_cons.keys()
      for x in keys:
        num_buc = "-"
        num_cruces = "-"
        num_disjuntos = "-"
        res_solapados = "-"
        num_unificado ="-"
        num_int_con = "-"
        num_anclajes = "-"
        pts_val = ""
        error_ps=0
        num_solapados = 0
        campos = capa_cde_cons[x].fields().toList()
        num_cde = capa_cde_cons[x].featureCount()

        lista_campos=list()
        n_atrib=list()
        ver_lista=list()
        dic_campos = dict()
        cont_dict=0
        for campo in campos:
          lista_campos.append(campo.name())
          dic_campos[campo.name()]=cont_dict
          cont_dict += 1

        key="c"+str(cont_key)
        cont_key+=1
        total += len(tabla_catalo[key])
        for linea in tabla_catalo[key]:
          # Verificar el nombre del atributo
          nom_campo=catalogo['ATRIBUTO'][linea]
          if nom_campo in lista_campos:
            ver_lista.append(nom_campo)
            nom_campo_r = nom_campo
            acierto_campo +=1
                      
            # Verificar el dominio del tipo de atributo
            tipo_atrib=catalogo['TIPO'][linea]
            mensaje_t_atrib += "<tr><td>"+nom_cde_cons[cont_nom]+"</td><td>"+nom_campo+"</td>"

            # Verificacion de los valores del dominio
            dom_atrib=catalogo['DOMINIO'][linea]
            if pd.isna(dom_atrib)==False:
              dom_atrib_lista = dom_atrib.split('-')
            else:
              dom_atrib_lista = []
            mensaje_v_atrib += "<tr><td>"+nom_cde_cons[cont_nom]+"</td><td>"+nom_campo+"</td>"

            for campo in campos:
              nom_campo_c = campo.name()
              if campo.name()==nom_campo:
                # Consistencia de Dominio (tipo de atributo)
                if tipo_atrib==campo.typeName():
                  acierto_tipo +=1
                  mensaje_t_atrib += "<td>"+campo.typeName()+"</td>"
                else:
                  mensaje_t_atrib += "<td><font color=#FF0000><b>"+campo.typeName()+"</b></font></td>"
                n_atrib.append(nom_campo_c)

                # Consistencia de Dominio (dominios).
                valor = dic_campos[campo.name()]
                valores = capa_cde_cons[x].uniqueValues(valor)
                acierto_dom = 0
                no_acierto_dom = 0
                if len(dom_atrib_lista) > 0:
                  for valor_c in valores:
                    if valor_c in dom_atrib_lista:
                      acierto_dom += 1
                    else:
                      no_acierto_dom +=1

                  if no_acierto_dom>0:
                    mensaje_v_atrib += "<td>"+str(acierto_dom+no_acierto_dom)+"</td><td><font color=#FF0000><b>"+str(no_acierto_dom)+"</b></font></td></tr>"
                  else:
                    mensaje_v_atrib += "<td>"+str(acierto_dom+no_acierto_dom)+"</td><td>"+str(no_acierto_dom)+"</td></tr>"
                  
                  acum_dom_n += no_acierto_dom
                  acum_dom_s += acierto_dom
                else:
                  mensaje_v_atrib += "<td></td><td></td></tr>"
            mensaje_t_atrib +="<td>"+tipo_atrib+"</td></tr>"

          else:
            ver_lista.append(nom_campo)
        
        for ver_nom in ver_lista:
          enc=0
          for enc_nom in n_atrib:
            if ver_nom==enc_nom:
              mensaje_n_atrib += f"<tr><td>{nom_cde_cons[cont_nom]}</td><td>{enc_nom}</td><td>{ver_nom}</td></tr>"
              enc+=1
          if enc==0:
            mensaje_n_atrib += f"<tr><td><font color=#FF0000><b>{nom_cde_cons[cont_nom]}</td><td></font></td><td>{ver_nom}</b></td></tr>"


        # Consistencia Topologica
        # Se crea una capa tipo punto para almacenar los errores topologicos
        epsg=capa_cde_cons[x].crs().toWkt()
        error_topo = QgsVectorLayer("Point?crs="+ epsg, "Topologia", "Memory")
        error_topo.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
        error_topo.updateFields()


        conteo=x+1
        grupo = "Conj_Datos_"+str(conteo)
        migrupo = project.layerTreeRoot().findGroup(grupo) 

        geo_inval = 0

        # Buscar elementos duplicados segun los atributos.
        dup_atr = processing.run("native:removeduplicatesbyattribute", {'INPUT':capa_cde_cons[x], 'FIELDS':lista_campos,'OUTPUT':'TEMPORARY_OUTPUT','DUPLICATES':'TEMPORARY_OUTPUT'})
        project.addMapLayer(dup_atr['DUPLICATES'], False)
        project.addMapLayer(dup_atr['OUTPUT'], False)

        if capa_cde_cons[x].geometryType()==0: # si la capa es  ######## PUNTO ######
          lista_geo_pt.append(capa_cde_cons[x])

          # verificacion de puntos repetidos
          cont = 0
          lista_geom = list()
          for feat in capa_cde_cons[x].getFeatures():
            geom = feat.geometry()
            geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
            if geom.type() == QgsWkbTypes.PointGeometry:
              if geomSingleType:
                lista_geom.append(geom.asPoint())
              else:
                lista_geom.append(geom.asMultiPoint())
            cont += 1
            val = 5 + int(50*cont/len(list(capa_cde_cons[x].getFeatures())))  
            self.pbr_elem.setValue(val)

          elem = list()
          error_pr = 0 # Contador puntos repetidos
          cont = 0
          for l in range(len(lista_geom)):
            i = l+1
            for t in range(i,len(lista_geom)):
              if type(lista_geom[l])==list:
                dist = distance.measureLine(lista_geom[l][0],lista_geom[t][0])
              elif type(lista_geom[l])==QgsPointXY:            
                dist = distance.measureLine(lista_geom[l],lista_geom[t])

              # Puntos repetidos en layer tipo punto
              if dist==0:
                gPnt_g = QgsFeature()
                gPnt_g.setFields(error_topo.fields())
                if type(lista_geom[l])==list:
                  gPnt = QgsGeometry.fromPointXY(lista_geom[l][0])
                elif type(lista_geom[l])==QgsPointXY:
                  gPnt = QgsGeometry.fromPointXY(lista_geom[l])
                gPnt_g.setGeometry(gPnt)
                gPnt_g.setAttribute(0,"Error Duplicado")
                elem.append(gPnt_g)
                error_pr+=1
            
            # Para visualizar la barra de progreso
            cont += 1
            val = 50 + int(35*l/len(lista_geom))  
            self.pbr_elem.setValue(val)

          total_chequeos = len(lista_geom)
          error_topo.dataProvider().addFeatures(elem)
          # ------

          # Se visualiza si los elementos tienen todos los atributos duplicados 
          if len(dup_atr['DUPLICATES'])>0:
            processing.run("native:renamelayer", {'INPUT': dup_atr['DUPLICATES'],'NAME': 'Elem atributos duplicados'})
            migrupo.addLayer(dup_atr['DUPLICATES'])
          num_dup_atr = len(dup_atr['DUPLICATES'])
          # ------

          cont=0
          for n in capa_cde_cons[x].getFeatures():
            # Para generar un listado con todos los valores de ID, verificacion del modelo conceptual
            ids = n.fieldNameIndex('ID')
            lista_id.append(n.attributes()[ids])
        #  FIN verificacion en capas de punto


        if capa_cde_cons[x].geometryType()==1: # si la capa es  ########  LINEA ######## 
          lista_geo_li.append(capa_cde_cons[x])

          # Consistencia del modelo - ordenacion de los veritices de rios.
          if '302L' in capa_cde_cons[x].name():
            rios_z = processing.run("native:extractzvalues", {'INPUT':capa_cde_cons[x],'SUMMARIES':[0,8], 'OUTPUT':'TEMPORARY_OUTPUT'})
            project.addMapLayer(rios_z['OUTPUT'], False)

            error_ord = 0
            elem = list()
            for m in rios_z['OUTPUT'].getFeatures():
              acum_feat_r += 1
              ids_f = m.fieldNameIndex('z_first')
              ids_m = m.fieldNameIndex('z_max')
              if m.attributes()[ids_f]!=m.attributes()[ids_m]:
                error_ord += 1
                rios_feat = QgsVectorLayer("Linestring?crs="+ epsg, "rios_zmax", "Memory")
                rios_feat.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
                rios_feat.updateFields()
                rios_feat.dataProvider().addFeatures([m])
                rios_vert = processing.run("native:extractvertices", {'INPUT':rios_feat,'OUTPUT':'TEMPORARY_OUTPUT'})
                project.addMapLayer(rios_vert['OUTPUT'], False)
                rios_z = processing.run("native:extractzvalues", {'INPUT':rios_vert['OUTPUT'],'SUMMARIES':[8], 'OUTPUT':'TEMPORARY_OUTPUT'})
                project.addMapLayer(rios_z['OUTPUT'], False)
                rios_zmax = processing.run("native:extractbyattribute", {'INPUT':rios_z['OUTPUT'],'FIELD':'z_max','OPERATOR':'0','VALUE':m.attributes()[ids_m],'OUTPUT':'TEMPORARY_OUTPUT'})
                project.addMapLayer(rios_zmax['OUTPUT'], False)
                for n in rios_zmax['OUTPUT'].getFeatures():
                  n.setAttribute(0,"Ordenacion de Vertices (Z max)")
                  elem.append(n)
            error_topo.dataProvider().addFeatures(elem)
            
            if error_ord>0:
              nom_ord_ver += capa_cde_cons[x].name()+", "

            acum_error_ord += error_ord
            capa_rio = "si"
            self.pbr_elem.setValue(10)


          # Para obtener los cruces
          pts_rep_v = processing.run("native:extractvertices", {'INPUT':capa_cde_cons[x],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_rep_v['OUTPUT'], False)
          pts_int = processing.run("native:lineintersections", {'INPUT':capa_cde_cons[x],'INTERSECT':capa_cde_cons[x],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_int['OUTPUT'], False)        
          pts_cru = processing.run("native:difference", {'INPUT': pts_int['OUTPUT'] ,'OVERLAY': pts_rep_v['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_cru['OUTPUT'], False)
          pts_cruces = processing.run("native:deleteduplicategeometries", {'INPUT':pts_cru['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_cruces['OUTPUT'], False)
          self.pbr_elem.setValue(20)
          # -------

          # Para obtener los vertices repetidos
          pts_val  = processing.run("qgis:checkvalidity", {'INPUT_LAYER':capa_cde_cons[x],'METHOD':1,'IGNORE_RING_SELF_INTERSECTION':False,'VALID_OUTPUT':'TEMPORARY_OUTPUT','INVALID_OUTPUT':'TEMPORARY_OUTPUT','ERROR_OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_val['VALID_OUTPUT'], False)
          project.addMapLayer(pts_val['INVALID_OUTPUT'], False)
          project.addMapLayer(pts_val['ERROR_OUTPUT'], False)
          self.pbr_elem.setValue(30)
          # ------ 

          for n in capa_cde_cons[x].getFeatures():
            # Para generar un listado con todos los valores de ID, verificacion del modelo conceptual
            ids = n.fieldNameIndex('ID')
            lista_id.append(n.attributes()[ids])


          # Para chequear puntos superfluos
          error_ps = 0
          tipo_geo = n.geometry()
          geomSingleType = QgsWkbTypes.isSingleType(tipo_geo.wkbType())
          if not geomSingleType:
            mul_mono = processing.run("native:multiparttosingleparts", {'INPUT':capa_cde_cons[x],'OUTPUT':'TEMPORARY_OUTPUT'})
            layer = mul_mono['OUTPUT']
          else: 
            layer = capa_cde_cons[x]

          features = layer.getFeatures()
          lines = [m.geometry().asPolyline() for m in features]

          total_chequeos = 0
          elem = []
          for points in lines:
            n = len(points)
            total_chequeos += n
            rango = range(n)

            for i,j in itertools.combinations(rango, 2):
              if (j - i) == 1:
                longit = sqrt(points[i].sqrDist(points[j]))
                if longit>0 and longit<=1.5:
                  gPnt_g = QgsFeature()
                  gPnt_g.setFields(error_topo.fields())
                  gPnt = QgsGeometry.fromPointXY(points[j])
                  gPnt_g.setGeometry(gPnt)
                  gPnt_g.setAttribute(0,"Error Superfluo")
                  elem.append(gPnt_g)
                  error_ps += 1
          error_topo.dataProvider().addFeatures(elem)
          layer=""
          self.pbr_elem.setValue(40)
          # ------

          # Anclajes por defecto
          mul_mono = processing.run("native:multiparttosingleparts", {'INPUT':capa_cde_cons[x],'OUTPUT':'TEMPORARY_OUTPUT'})
          lines = [m.geometry() for m in mul_mono['OUTPUT'].getFeatures()]
          
          lista_pt = []
          num_anclajes=0
          for k in lines:
            copia_lines = lines.copy()
            copia_lines.remove(k)
            h = k.asPolyline() 
      
            for n in copia_lines:
              cercano = n.closestVertex(h[0])
              if cercano[4]>0 and cercano[4]<6.5:
                gPnt_g = QgsFeature()
                gPnt_g.setFields(error_topo.fields())
                gPnt = QgsGeometry.fromPointXY(cercano[0])
                gPnt_g.setGeometry(gPnt)
                gPnt_g.setAttribute(0,"Error de Anclaje por defecto")
                lista_pt.append(gPnt_g)

              cercano = n.closestVertex(h[-1])
              if cercano[4]>0 and cercano[4]<6.5:
                gPnt_g = QgsFeature()
                gPnt_g.setFields(error_topo.fields())
                gPnt = QgsGeometry.fromPointXY(cercano[0])
                gPnt_g.setGeometry(gPnt)
                gPnt_g.setAttribute(0,"Error de Anclaje por defecto")
                lista_pt.append(gPnt_g)

          pt_cer = QgsVectorLayer('Point?crs='+ epsg, 'cercanos', 'Memory')
          pt_cer.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
          pt_cer.updateFields()
          pt_cer.dataProvider().addFeatures(lista_pt)

          pts_int = processing.run("native:deleteduplicategeometries", {'INPUT':pt_cer,'OUTPUT':'TEMPORARY_OUTPUT'})
          QgsProject.instance().addMapLayer(pts_int['OUTPUT'], False)
          num_anclajes=len(pts_int['OUTPUT'])
          
          acum_anclajes += num_anclajes

          for n in pts_int['OUTPUT'].getFeatures():
            error_topo.dataProvider().addFeatures([n])      


          #QgsProject.removeMapLayer([pts_rep_v['OUTPUT'].id()])
          #QgsProject.removeMapLayer([pts_int['OUTPUT'].id()])


          # Se verifica si hay elementos repetidos por atributos y elementos unificados
          # Se aplica sobre el resultado de verificar los features que tienen todos los atributos duplicados
          num_solapados = 0
          if len(dup_atr['DUPLICATES'])>0:
            # Para verficar que los elementos duplicados no correspondan a elementos en el borde de la hoja
            ext_cde = QgsProject.instance().mapLayersByName('Extension_CDE')[0]
            pol_lin = processing.run("native:polygonstolines", {'INPUT':ext_cde,'OUTPUT':'TEMPORARY_OUTPUT'})
            QgsProject.instance().addMapLayer(pol_lin['OUTPUT'], False)
            bufer = processing.run("native:buffer", {'INPUT':pol_lin['OUTPUT'],'DISTANCE':6.25,'SEGMENTS':5,'END_CAP_STYLE':2,'JOIN_STYLE':2,'MITER_LIMIT':1,'DISSOLVE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
            QgsProject.instance().addMapLayer(bufer['OUTPUT'], False)
            tocar = processing.run("native:extractbylocation", {'INPUT':capa_cde_cons[x], 'PREDICATE':0,'INTERSECT':bufer['OUTPUT'], 'OUTPUT':'TEMPORARY_OUTPUT'})
            QgsProject.instance().addMapLayer(tocar['OUTPUT'], False)
            elem_dup = processing.run("native:difference", {'INPUT': dup_atr['DUPLICATES'] ,'OVERLAY': tocar['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
            project.addMapLayer(elem_dup['OUTPUT'], False)

            if len(elem_dup['OUTPUT'])>0:
              processing.run("native:renamelayer", {'INPUT': elem_dup['OUTPUT'],'NAME': 'Elem atributos duplicados'})
              migrupo.addLayer(elem_dup['OUTPUT'])

            # para verificar solapados. se intersecta los elementos con atributos duplicados contra los elementos sin duplicados
            sol = processing.run("native:intersection", {'INPUT':dup_atr['DUPLICATES'],'OVERLAY':dup_atr['OUTPUT'],'INPUT_FIELDS':[],'OVERLAY_FIELDS':[],'OVERLAY_FIELDS_PREFIX':'','OUTPUT':'TEMPORARY_OUTPUT'})
            project.addMapLayer(sol['OUTPUT'], False)

            # El resultado de "sol" tiene los campos ID y ID_2, si son iguales los elementos estan solapados.
            if len(sol['OUTPUT'])>0:
              selected_fid = []
              sol['OUTPUT'].removeSelection()
              for m in sol['OUTPUT'].getFeatures():
                ids_f = m.fieldNameIndex('ID')
                ids_m = m.fieldNameIndex('ID_2')
                if m.attributes()[ids_f]!=m.attributes()[ids_m]:
                  selected_fid.append(m.id())
              sol['OUTPUT'].select(selected_fid)
              sol['OUTPUT'].dataProvider().deleteFeatures(selected_fid)
              sol['OUTPUT'].removeSelection()

              processing.run("native:renamelayer", {'INPUT': sol['OUTPUT'],'NAME': 'Elem Solapados'})
              project.addMapLayer(sol['OUTPUT'], False)
              migrupo.addLayer(sol['OUTPUT'])
            num_solapados = len(sol['OUTPUT'])

            # Para unificados se parte de los elementos que sean duplicados y luego se verifican que puedan estar continuos
            valores = dup_atr['DUPLICATES'].uniqueValues(0)
            num_unificado = 0
            for m in valores:
              expression = 'ID = '+str(m)
              request = QgsFeatureRequest().setFilterExpression(expression)
              selected_fid = []
              for f in capa_cde_cons[x].getFeatures(request):
                selected_fid.append(f.id())
              capa_cde_cons[x].select(selected_fid)
              n = capa_cde_cons[x].selectedFeatures()
              capa_sel = QgsVectorLayer("Linestring?crs="+ epsg, "temp", "Memory")
              capa_sel.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
              capa_sel.updateFields()
              capa_sel.dataProvider().addFeatures(n)
              capa_cde_cons[x].removeSelection()

              capa_lim = processing.run("native:deleteduplicategeometries", {'INPUT':capa_sel,'OUTPUT':'TEMPORARY_OUTPUT'})
              QgsProject.instance().addMapLayer(capa_lim['OUTPUT'], False)

              capa_lim = processing.run("native:difference", {'INPUT': capa_lim['OUTPUT'] ,'OVERLAY': sol['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
              project.addMapLayer(capa_lim['OUTPUT'], False)

              ver = processing.run("native:extractspecificvertices", {'INPUT':capa_lim['OUTPUT'],'VERTICES':'0,-1','OUTPUT':'TEMPORARY_OUTPUT'})
              QgsProject.instance().addMapLayer(ver['OUTPUT'], False)

              lista_geom = list()
              for feat in ver['OUTPUT'].getFeatures():
                geom = feat.geometry()
                geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
                if geom.type() == QgsWkbTypes.PointGeometry:
                  if geomSingleType:
                    lista_geom.append(geom.asPoint())
                  else:
                    lista_geom.append(geom.asMultiPoint())
          
                elem = list()
                error_unif = 0 # Contador vertices unificados
                cont = 0
                for l in range(len(lista_geom)):
                  i = l+1
                  for t in range(i,len(lista_geom)):
                    if type(lista_geom[l])==list:
                      dist = distance.measureLine(lista_geom[l][0],lista_geom[t][0])
                    elif type(lista_geom[l])==QgsPointXY:            
                      dist = distance.measureLine(lista_geom[l],lista_geom[t])
              
                    # Vertices que estan unificados 
                    if dist==0:
                      gPnt_g = QgsFeature()
                      gPnt_g.setFields(ver['OUTPUT'].fields())
                      if type(lista_geom[l])==list:
                        gPnt = QgsGeometry.fromPointXY(lista_geom[l][0])
                      elif type(lista_geom[l])==QgsPointXY:
                        gPnt = QgsGeometry.fromPointXY(lista_geom[l])
                      gPnt_g.setGeometry(gPnt)
                      gPnt_g.setAttribute(0,"Error Unificados")
                      elem.append(gPnt_g)
                      error_unif+=1
              num_unificado += error_unif
              error_topo.dataProvider().addFeatures(elem)        

            self.pbr_elem.setValue(40)
          else:
            num_unificado = 0

          try:
            if len(elem_dup['OUTPUT'])>0:
              num_dup_atr = len(elem_dup['OUTPUT'])
            else:
              num_dup_atr = 0
          except NameError:
            num_dup_atr = 0  

          # ------
          self.pbr_elem.setValue(80)
        # Fin a a las verificaciones en capas de lineas

        if capa_cde_cons[x].geometryType()==2:   # Si la capa ######## POLIGONO ########
          lista_geo_pl.append(capa_cde_cons[x])

          # Se chequea validez para detectar puntos repetidos, bucles y errores de interseccion de anillos
          pts_val = processing.run("qgis:checkvalidity", {'INPUT_LAYER':capa_cde_cons[x],'METHOD':1,'IGNORE_RING_SELF_INTERSECTION':False,'VALID_OUTPUT':'TEMPORARY_OUTPUT','INVALID_OUTPUT':'TEMPORARY_OUTPUT','ERROR_OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_val['VALID_OUTPUT'], False)
          project.addMapLayer(pts_val['INVALID_OUTPUT'], False)
          project.addMapLayer(pts_val['ERROR_OUTPUT'], False)
          self.pbr_elem.setValue(10) 
          # ------

          # para la verificacion de elementos disjuntos
          lista_feat = list(capa_cde_cons[x].getFeatures())
          disju = QgsVectorLayer('Polygon?crs='+ epsg, 'Disjuntos', 'Memory')
          disju.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
          disju.updateFields()
          cont=0
          elementos = []
          # ------

          num_int_con = 0
          for f in capa_cde_cons[x].getFeatures():
            # Generacion de las areas disjuntos
            cont+=1
            for m in range(cont,len(lista_feat)):
              geom = f.geometry().intersection(lista_feat[m].geometry())
              if geom.type()==2:
                if not geom.isEmpty():
                  elem = QgsFeature()
                  elem.setFields(disju.fields())
                  atrib = str(f.id())+"-"+str(lista_feat[m].id())
                  elem.setGeometry(geom)
                  elem.setAttribute(0,atrib)
                  elementos.append(elem)

            val = 10 + int(35*cont/len(list(capa_cde_cons[x].getFeatures())))  
            self.pbr_elem.setValue(val)

            # Para generar un listado con todos los valores de ID, verificacion del modelo conceptual
            ids = f.fieldNameIndex('ID')
            lista_id.append(f.attributes()[ids])

            # Para verificar la consistencia modelo conceptual (errores de contornos internos consistentes)
            inter_int = QgsVectorLayer('Polygon?crs='+ epsg, 'inter_int', 'Memory')
            inter_int.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
            inter_int.updateFields()
            inter_int.dataProvider().addFeatures([f])
            pol_lin = processing.run("native:polygonstolines", {'INPUT':inter_int,'OUTPUT':'TEMPORARY_OUTPUT'}, context=context)
            project.addMapLayer(pol_lin['OUTPUT'], False)
            mul_mono = processing.run("native:multiparttosingleparts", {'INPUT':pol_lin['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
            project.addMapLayer(mul_mono['OUTPUT'], False)
            pts_int = processing.run("native:lineintersections", {'INPUT':mul_mono['OUTPUT'],'INTERSECT':mul_mono['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
            project.addMapLayer(pts_int['OUTPUT'], False)
            pts_int = processing.run("native:deleteduplicategeometries", {'INPUT':pts_int['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
            project.addMapLayer(pts_int['OUTPUT'], False)

            if len(pts_int['OUTPUT'])>0:
              for m in pts_int['OUTPUT'].getFeatures():
                m.setAttribute(0,"Error contornos interiores")
                error_topo.dataProvider().addFeatures([m])
                num_int_con += 1
            acum_feat += 1

          if num_int_con>0:
            nom_con_int += capa_cde_cons[x].name()+", "
          acum_int_con += num_int_con 

          # Se visualiza si los elementos tienen todos los atributos duplicados
          ext_cde = QgsProject.instance().mapLayersByName('Extension_CDE')[0]
          pol_lin = processing.run("native:polygonstolines", {'INPUT':ext_cde,'OUTPUT':'TEMPORARY_OUTPUT'})
          QgsProject.instance().addMapLayer(pol_lin['OUTPUT'], False)
          bufer = processing.run("native:buffer", {'INPUT':pol_lin['OUTPUT'],'DISTANCE':6.25,'SEGMENTS':5,'END_CAP_STYLE':2,'JOIN_STYLE':2,'MITER_LIMIT':1,'DISSOLVE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
          QgsProject.instance().addMapLayer(bufer['OUTPUT'], False)
          tocar = processing.run("native:extractbylocation", {'INPUT':capa_cde_cons[x], 'PREDICATE':0,'INTERSECT':bufer['OUTPUT'], 'OUTPUT':'TEMPORARY_OUTPUT'}, context=context)
          QgsProject.instance().addMapLayer(tocar['OUTPUT'], False)
          elem_dup = processing.run("native:difference", {'INPUT': dup_atr['DUPLICATES'] ,'OVERLAY': tocar['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'}, context=context)
          project.addMapLayer(elem_dup['OUTPUT'], False)

          if len(elem_dup['OUTPUT'])>0:
            processing.run("native:renamelayer", {'INPUT': elem_dup['OUTPUT'],'NAME': 'Elem atributos duplicados'})
            migrupo.addLayer(elem_dup['OUTPUT'])
          num_dup_atr = len(elem_dup['OUTPUT'])
          # ------
          
          # Se visualiza el resultado de las areas de disjuntos
          disju.dataProvider().addFeatures(elementos)
          project.addMapLayer(disju, False)

          disju = processing.run("native:difference", {'INPUT': disju,'OVERLAY': dup_atr['DUPLICATES'],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(disju['OUTPUT'], False)
          disju['OUTPUT'].setName('Disjuntos')

          if len(disju['OUTPUT'])>0:
            migrupo.addLayer(disju['OUTPUT']) 
          # --------

          # Para obtener los cruces
          pts_rep_v = processing.run("native:extractvertices", {'INPUT':capa_cde_cons[x],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_rep_v['OUTPUT'], False)
          pol_lin = processing.run("native:polygonstolines", {'INPUT':capa_cde_cons[x],'OUTPUT':'TEMPORARY_OUTPUT'}, context=context)
          project.addMapLayer(pol_lin['OUTPUT'], False)
          pts_int = processing.run("native:lineintersections", {'INPUT':pol_lin['OUTPUT'],'INTERSECT':pol_lin['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_int['OUTPUT'], False)        
          pts_cru = processing.run("native:difference", {'INPUT': pts_int['OUTPUT'] ,'OVERLAY': pts_rep_v['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_cru['OUTPUT'], False)
          pts_cruces = processing.run("native:deleteduplicategeometries", {'INPUT':pts_cru['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
          project.addMapLayer(pts_cruces['OUTPUT'], False)

          # Para chequear puntos superfluos
          error_ps = 0

          geomSingleType = QgsWkbTypes.isSingleType(pol_lin['OUTPUT'].wkbType())
          if not geomSingleType:
            mul_mono = processing.run("native:multiparttosingleparts", {'INPUT':pol_lin['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
            layer = mul_mono['OUTPUT']
          else: 
            layer = pol_lin['OUTPUT']

          features = layer.getFeatures()
          lines = [m.geometry().asPolyline() for m in features]

          total_chequeos = 0
          elem = []
          cont = 0
          for points in lines:
            n = len(points)
            total_chequeos += n
            rango = range(n)

            for i,j in itertools.combinations(rango, 2):
              if (j - i) == 1:
                longit = sqrt(points[i].sqrDist(points[j]))
                if longit>0 and longit<=1.5:
                  gPnt_g = QgsFeature()
                  gPnt_g.setFields(error_topo.fields())
                  gPnt = QgsGeometry.fromPointXY(points[j])
                  gPnt_g.setGeometry(gPnt)
                  gPnt_g.setAttribute(0,"Error Superfluo")
                  elem.append(gPnt_g)
                  error_ps += 1
            cont += 1
            val = 60 + int(30*cont/n)  
            self.pbr_elem.setValue(val)
          layer=""
          error_topo.dataProvider().addFeatures(elem)
          # ------
        # FIN de verificaciones en capas de poligonos


                ## Orden y presentacion de los parametros calculados ##
        # Adicion de los puntos de errores topologicos a la lista de errores
        if capa_cde_cons[x].geometryType()==1 or capa_cde_cons[x].geometryType()==2:
          if len(pts_val['ERROR_OUTPUT'])>0:
            num_buc = 0
            error_pr = 0
            for f in pts_val['ERROR_OUTPUT'].getFeatures():
              # se adicionan los puntos de Bucle a la lista de errores
              if 'intersect' in f["message"]:
                num_buc += 1
                f.setAttribute(0,"Error Bucle")
                error_topo.dataProvider().addFeatures([f])
              # se adicionan los vertices repetidos a la lista de errores
              if 'duplicate' in f["message"]:
                error_pr += 1
                f.setAttribute(0,"Error Vertice Duplicado")
                error_topo.dataProvider().addFeatures([f])
              if ('cerrado' in f["message"]) or ('closed' in f["message"]):
                nom_pol_no_cer += capa_cde_cons[x].name()+", "
                pol_no_cer += 1
                f.setAttribute(0,"Poligono no cerrado")
                error_topo.dataProvider().addFeatures([f])
          else:
            num_buc = 0
            error_pr = 0

          # se adicionan los puntos de cruce a la lista de errores
          if len(pts_cruces['OUTPUT'])>0:
            num_cruces = 0
            for f in pts_cruces['OUTPUT'].getFeatures():
              num_cruces +=1
              f.setAttribute(0,"Error Cruces")
              error_topo.dataProvider().addFeatures([f])
          else:
            num_cruces = 0

        # Visualizacion de los resultados
        project.addMapLayer(error_topo, False)

        if error_topo.featureCount()>0:
          if capa_cde_cons[x].geometryType()==0:
            ruta_estilo = os.path.join(os.path.dirname(__file__), r'..\datos\\estilos_pt.qml') 
          if capa_cde_cons[x].geometryType()==1:
            ruta_estilo = os.path.join(os.path.dirname(__file__), r'..\datos\\estilos_l.qml') 
          if capa_cde_cons[x].geometryType()==2:
            ruta_estilo = os.path.join(os.path.dirname(__file__), r'..\datos\\estilos_pl.qml') 

          processing.run("native:setlayerstyle", {'INPUT':error_topo,'STYLE':ruta_estilo})
          migrupo.addLayer(error_topo)
        

        # Visualizacion del reporte de la evaluacion.
        try:
          if len(disju['OUTPUT'])>=0:
            num_disjuntos = len(disju['OUTPUT'])
            del disju
        except NameError:
          num_disjuntos = "-"   
            
        mensaje_topo += f"<tr><td>{nom_cde_cons[cont_nom]}</td><td>{total_chequeos}</td><td>{error_pr}</td><td>{error_ps}</td>"
        mensaje_topo += f"<td>{(num_buc)}</td><td>{num_dup_atr}</td><td>{num_solapados}</td>"
        mensaje_topo += f"<td>{num_unificado}</td><td>{num_cruces}</td><td>{num_anclajes}</td><td>{num_disjuntos}</td></tr>"
        if capa_cde_cons[x].geometryType()==0: acum_to_pt += total_chequeos
        if capa_cde_cons[x].geometryType()==1: acum_to_li += total_chequeos
        if capa_cde_cons[x].geometryType()==2: acum_to_pl += total_chequeos
        acum_to = acum_to_pt + acum_to_li + acum_to_pl 
        acum_pr += error_pr
        if error_ps!="-": acum_ps += error_ps
        if num_buc!="-": acum_buc += num_buc
        acum_dup_atr += num_dup_atr
        if num_solapados>0: acum_res_sol += num_solapados
        if num_unificado!="-": acum_unif += num_unificado
        if num_cruces!="-": acum_cruces += num_cruces
        if num_disjuntos!="-": acum_disjuntos += num_disjuntos
        cont_nom +=1
      # Termina la verificacion capa pór capa

      # comparacion para nombre de atributo
      if total == 0:
          nom_atrib119 = "Falso"
          nom_atrib19 = "-"
          nom_atrib20 = "-"
      else:
        if total == acierto_campo:
          nom_atrib119 = "Falso"
          nom_atrib19 = 0
          nom_atrib20 = 0
        else:
          nom_atrib119 = "Verdadero"
          nom_atrib19 = total - acierto_campo
          nom_atrib20 = round((nom_atrib19/total)*100,2)

      # Consistencia de dominio
      # comparacion para tipo de atributo
      if total == 0:
        tipo_atrib119 = "Falso"
        tipo_atrib19 = "-"
        tipo_atrib20 = "-"
      else:
        if total == acierto_tipo:
          tipo_atrib119 = "Falso"
          tipo_atrib19 = 0
          tipo_atrib20 = 0
        else:
          tipo_atrib119 = "Verdadero"
          tipo_atrib19 = total - acierto_tipo - nom_atrib19 
          tipo_atrib20 = round((tipo_atrib19/total)*100,2)

      # Consistencia de dominio
      # comparacion para valores de atributo
      if total == 0:
        val_atrib119 = "Falso"
        val_atrib19 = "-"
        val_atrib20 = "-"
      else:
        if acum_dom_n == 0:
          val_atrib119 = "Falso"
          val_atrib19 = 0
          val_atrib20 = 0
        else:
          val_atrib119 = "Verdadero"
          val_atrib19 = acum_dom_n 
          val_atrib20 = round((acum_dom_n/(acum_dom_n+acum_dom_s))*100,2)

      # Consistencia Conceptual
      # incumplimiento al esquema conceptual
        # Identificadores unicos
      num_list_id = [x for x, y in Counter(lista_id).items() if y > 1]
      mensaje_conc =f"<table border=1><tr><td>identificadores unicos (item chequeados:{len(lista_id)})</td><td>{num_list_id}</td></tr>"

      if len(num_list_id)>0:
        id_unicos9 = "Falso"
        id_unicos10 = len(num_list_id)
        id_unicos12 = round((id_unicos10/len(lista_id))*100,2)
      else:
        id_unicos9 = "Verdadero"
        id_unicos10 = 0
        id_unicos12 = 0

        # Elementos superficiales cerrados
      mensaje_conc +=f"<tr><td>Elementos superficiales cerrados (item chequeados:{acum_feat} elementos)</td><td>{nom_pol_no_cer}</td></tr>"  
      if pol_no_cer>0:
        pol_no_cer9 = "Falso"
        pol_no_cer10 = pol_no_cer
        pol_no_cer12 = round((pol_no_cer10/acum_feat)*100,2)
      else:
        pol_no_cer9 = "Verdadero"
        pol_no_cer10 = 0
        pol_no_cer12 = 0

        # Constornos internos consistentes
      mensaje_conc +=f"<tr><td>Contornos internos consistentes (chequeados {acum_feat} elementos)</td><td>{nom_con_int}</td></tr>" 
      if acum_int_con>0:
        int_con9 = "Falso"
        int_con10 = acum_int_con
        int_con12 = round((acum_int_con/acum_feat)*100,2)
      else:
        int_con9 = "Verdadero"
        int_con10 = 0
        int_con12 = 0

        # Ordenacion de los vertices
      mensaje_conc +=f"<tr><td>Ordenación de los vertices (chequeados {acum_feat_r} elementos)</td><td>{nom_ord_ver}</td></tr>" 
      if acum_error_ord>0:
        orde9 = "Falso"
        orde10 = acum_error_ord
        orde12 = round((acum_error_ord/acum_feat_r)*100,2)
      else:
        orde9 = "Verdadero"
        orde10 = 0
        orde12 = 0

      # Consistencia Topologica
      # incumplimiento a las normas topologicas establecidas en las espeficiaciones BTN25
        # Puntos (vertices) repetidos 
      if acum_pr>0:
        pr1 = "Falso"
        pr2 = acum_pr
        pr3 = round((acum_pr/(acum_to))*100,2)
      else:
        pr1 = "Verdadero"
        pr2 = 0
        pr3 = 0

        # Puntos (vertices) Superfluos (linesa y poligonos) 
      if acum_ps>0:
        ps1 = "Falso"
        ps2 = acum_ps
        ps3 = round((acum_ps/(acum_to_li+acum_to_pl))*100,2)
      else:
        ps1 = "Verdadero"
        ps2 = 0
        ps3 = 0

        # Bucles (linesa y poligonos) 
      if acum_buc>0:
        bu1 = "Falso"
        bu2 = acum_buc
        bu3 = round((acum_buc/(acum_to_li+acum_to_pl))*100,2)
      else:
        bu1 = "Verdadero"
        bu2 = 0
        bu3 = 0

        # Elementos repetidos (todos)
      if acum_dup_atr>0:
        er1 = "Falso"
        er2 = acum_dup_atr
        er3 = round((acum_dup_atr/(acum_to))*100,2)
      else:
        er1 = "Verdadero"
        er2 = 0
        er3 = 0

        # Elementos solapados (lineas)
      if acum_res_sol>0:
        es1 = "Falso"
        es2 = acum_res_sol
        es3 = round((acum_res_sol/(acum_to_li))*100,2)
      else:
        es1 = "Verdadero"
        es2 = 0
        es3 = 0

        # Elementos unificados (lineas)
      if acum_unif>0:
        eu1 = "Falso"
        eu2 = acum_unif
        eu3 = round((acum_unif/(acum_to_li))*100,2)
      else:
        eu1 = "Verdadero"
        eu2 = 0
        eu3 = 0

        # Cruces y anclajes en exceso (lineas y poligonos) 
      if acum_cruces>0:
        cu1 = "Falso"
        cu2 = acum_cruces
        cu3 = round((acum_cruces/(acum_to_li+acum_to_pl))*100,2)
      else:
        cu1 = "Verdadero"
        cu2 = 0
        cu3 = 0

        # Anclajes por defecto (lineas) 
      if acum_anclajes>0:
        ad1 = "Falso"
        ad2 = acum_anclajes
        ad3 = round((acum_anclajes/(acum_to_li))*100,2)
      else:
        ad1 = "Verdadero"
        ad2 = 0
        ad3 = 0

        # Contornos disjuntos (poligonos) 
      if acum_disjuntos>0:
        cd1 = "Falso"
        cd2 = acum_disjuntos
        cd3 = round((acum_disjuntos/(acum_to_pl))*100,2)
      else:
        cd1 = "Verdadero"
        cd2 = 0
        cd3 = 0

      # Visualizacion de los resultados de la consistencia logica"
      text_for = "<center><h2>Evaluación Consistencia Lógica</h2></center>"
      text_for += f"Proyecto: <b>{ruta}</b><p>"
      text_for += f"Fecha: <b>{hoy}</b><p>"
      text_for += "Método de evaluación: <b>Directo Interno</b><p>"
      text_for += "Enfoque de inspeción: <b>Automático / Inspección completa</b><p>"
      text_for += f"Catálogo de objetos: <b>{catalogo_file}</b><p>"
      text_for += "<h3>Reporte resultados (Anexo D ISO 19157)</h3>"
      text_for += "<b>Consistencia Conceptual</b><br>"
      text_for +="<table border=1><tr><td></td><td><b>Simbología</b></td><td><b>Medida 9</b></td><td><b>Medida 10</b></td><td><b>Medida 12</b></td></tr>"
      text_for +=f"<tr><td><b>Identificadores Unicos </b>(chequedados {len(lista_id)} elementos)</td><td></td><td>{id_unicos9}</td><td>{id_unicos10}</td><td>{id_unicos12} %</td></tr>"
      text_for +=f"<tr><td><b>Elementos superfiales cerrados </b>(chequeados {acum_feat} elementos)</td><td></td><td>{pol_no_cer9}</td><td>{pol_no_cer10}</td><td>{pol_no_cer12} %</td></tr>"
      text_for +=f"<tr><td><b>Contornos internos consistentes </b>(chequeados {acum_feat} elementos)</td><td>&#11046;</td><td>{int_con9}</td><td>{int_con10}</td><td>{int_con12} %</td></tr>"
      text_for +=f"<tr><td><b>Ordenación de los vertices </b>(chequeados {acum_feat_r} elementos)</td><td>&#10032;</td><td>{orde9}</td><td>{orde10}</td><td>{orde12} %</td></tr>"
      text_for +="</table><br><p>" 

      text_for += f"<b>Consistencia de Formato (elementos chequeados {(len(capa_cde_cons)+num_arc_e)})</b><br>"
      text_for +="<table border=1><tr><td></td><td><b>Medida 119</b></td><td><b>Medida 19</b></td><td><b>Medida 20</b></td></tr>"
      text_for +=f"<tr><td><b>Error de legibilidad</b></td><td>{legib119}</td><td>{num_arc_e}</td><td>{legib20} %</td></tr>"
      text_for +="<tr><td><b>Error de formato Shape</b></td><td>Falso</td><td>0</td><td>0.0 %</td></tr>"
      text_for +=f"<tr><td><b>Error de estructura vector</b></td><td>{est_vector119}</td><td>{no_est_vector}</td><td>{est_vector20} %</td></tr>"
      text_for +=f"<tr><td><b>Error en nombre del catálogo</b></td><td>{nom_cat119}</td><td>{nom_cat19}</td><td>{nom_cat20} %</td></tr>"
      text_for +=f"<tr><td><b>Error en atributos del catálogo</b></td><td>{nom_atrib119}</td><td>{nom_atrib19}</td><td>{nom_atrib20} %</td></tr>"
      text_for +="</table><br><p>" 
      text_for +="<b>Consistencia de Dominio</b><br>"
      text_for +="<table border=1><tr><td></td><td><b>Medida 15</b></td><td><b>Medida 16</b></td><td><b>Medida 18</b></td></tr>"
      text_for +=f"<tr><td><b>Error de tipo atributo</b></td><td>{tipo_atrib119}</td><td>{tipo_atrib19}</td><td>{tipo_atrib20}</td></tr>"
      text_for +=f"<tr><td><b>Error en valores de atributo</b></td><td>{val_atrib119}</td><td>{val_atrib19}</td><td>{val_atrib20}</td></tr>"
      text_for +="</table><br><p>" 
      text_for +="<b>Consistencia Topológica</b><br>"
      text_for +="<table border=1><tr><td></td><td><b>Medidas</b></td><td><b>Simbología</b></td><td><b>Consistencia</b></td><td><b>Recuento</b></td><td><b>Indice</b></td></tr>"
      text_for +=f"<tr><td><b>Pt/Vert Duplicados </b>(chequeados {acum_to} elementos)</td><td></td><td>&#9723; - &#128710;</td><td>{pr1}</td><td>{pr2}</td><td>{pr3} %</td></tr>"
      text_for +=f"<tr><td><b>Puntos Superfluos (lineas y poligonos) </b>(chequeados {(acum_to_li+acum_to_pl)} elementos)</td><td></td><td>O</td><td>{ps1}</td><td>{ps2}</td><td>{ps3} %</td></tr>"
      text_for +=f"<tr><td><b>Bucles (lineas y poligonos) </b>(chequeados {(acum_to_li+acum_to_pl)} elementos)</td><td>Medida 26</td><td>X</td><td>{bu1}</td><td>{bu2}</td><td>{bu3} %</td></tr>" 
      text_for +=f"<tr><td><b>Entidades atributos duplicados </b>(chequeados {acum_to} elementos)</td><td>Medida 4</td><td>En capa</td><td>{er1}</td><td>{er2}</td><td>{er3} %</td></tr>"  
      text_for +=f"<tr><td><b>Elementos solapados (lineas) </b>(chequeados {acum_to_li} elementos)</td><td>Medida 27</td><td>En capa</td><td>{es1}</td><td>{es2}</td><td>{es3} %</td></tr>"   
      text_for +=f"<tr><td><b>Elementos unificados (lineas) </b>(chequeados {acum_to_li} elementos)</td><td></td><td>&#9475;</td><td>{eu1}</td><td>{eu2}</td><td>{eu3} %</td></tr>"    
      text_for +=f"<tr><td><b>Cruces y anclajes en exceso (lineas y poligonos) </b>(chequeados {(acum_to_li+acum_to_pl)} elementos)</td><td>Medida 24</td><td>&#9547;</td><td>{cu1}</td><td>{cu2}</td><td>{cu3} %</td></tr>" 
      text_for +=f"<tr><td><b>Anclajes por defecto (lineas) </b>(chequeados {acum_to_li} elementos)</td><td>Medida 23</td><td>></td><td>{ad1}</td><td>{ad2}</td><td>{ad3} %</td></tr>"     
      text_for +=f"<tr><td><b>Contornos disjuntos (poligonos) </b>(chequeados {acum_to_pl} elementos)</td><td>Medida 11</td><td>En capa</td><td>{cd1}</td><td>{cd2}</td><td>{cd3} %</td></tr>"  
      text_for +="</table><br><p>" 

      # Visualizacion de la evaluacion de consistencia de logica.
      #mensaje = str(acierto_campo)+"/"+str(total)
      mensaje = "<b>Consistencia Conceptual </b><p>"+mensaje_conc+"</table><p>"
      mensaje += "<b>Consistencia de Formato </b> Nombre del catalogo (item chequeados:"+str(len(capa_cde_cons)+num_arc_e)+")<p>"+mensaje_nomb+"</table><p>"
      mensaje += "<b>Consistencia de Formato </b> Nombres de atributos (item chequeados:"+str(total)+")<p>"+mensaje_n_atrib+"</table><p>"
      mensaje += "<b>Consistencia de Dominio </b> Tipo de atributos (item chequeados:"+str(total)+")<p>"+mensaje_t_atrib+"</table><p>"
      mensaje += "<b>Consistencia de Dominio </b> Valores de atributos (item chequeados:"+str(acum_dom_n+acum_dom_s)+")<p>"+mensaje_v_atrib+"</table><p>"
      mensaje += "<b>Consistencia Topológica </b> (item chequeados:"+str(acum_to)+")<p>"+"<p>"+mensaje_topo+"</table><p>"

      resultado = str(ruta)+'/Resultados/Consistencia_logica.html'
      f = open (resultado, 'w')
      f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>Resultado de Evaluación Consistencia Lógica</title>\n')
      f.write('<style type="text/css">\nbody {font-family: arial; margin: 5%;}\ntable {border: 2px solid blue; border-collapse: collapse; font-family: arial; width: 80%;}\n')
      f.write('td {padding: 5px;text-align: center;}</style></head>\n<body>\n')
      f.write(text_for)
      f.write('\n<p>\n')
      f.write('<hr><p><h3>Reporte Detallado</h3><p>\n')
      f.write(mensaje)
      f.write('\n</html>')
      f.close()

      self.bt_resultado.setEnabled(True)
      self.bt_resultado.clicked.connect(self.ver_result_cons)

      doc = """<style type='text/css'>
        table {border-collapse:collapse; border:1px; border-style:solid; border-color:darkblue; padding:3px; vertical-align:middle;} 
        td {padding: 3px;text-align: center;}</style>"""

      self.rel_val.setHtml(doc+text_for)

