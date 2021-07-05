from qgis.utils import iface
from qgis.core import QgsProject
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from qgis.core import Qgis, QgsField, QgsFeatureRequest, QgsVectorLayer
from qgis import processing
from qgis.PyQt.QtCore import QVariant
from datetime import datetime

# Se instancia el proyecto
project = QgsProject.instance()

    # COMPLECION
    # Funcion para la evaluacion de calidad del elemento de calidad de complecion
  
def complecion(self,capa_cde_comp,capa_cdr_comp,nom_cde_comp,nom_cdr_comp,ruta):

    iface.messageBar().pushMessage("Compleción",'En ejecición por favor espere', level=Qgis.Info, duration=10)
    now = datetime.now()
    hoy = now.strftime('%Y/%m/%d %H:%M')

    items = ("Cobertura Compartida", "Extensión CDE", "Extensión CDR")
    cob, ok = QInputDialog.getItem(self, "Extensión espacial de la evaluación", "Seleccione:", items, 0, False)

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

        mensaje_exac= "<table border=1><tr><td><b>CDE</b></td><td><b>CDR</b></td><td><b>N° Objetos CDE</b></td><td><b>N° Objetos CDR</b></td><td><b>Filtro CDR</b></td>"
        mensaje_exac+= "<td><b>Comisión</b></td><td><b>Índice de Comisión</b></td><td><b>Omisión</b></td><td><b>Índice de Omisión</b></td></tr>"

        acum_che = 0
        acum_com = 0
        acum_omi = 0
        cont_nom = 0
        keys= capa_cde_comp.keys()
        for x in keys:
            capa_cde_comp[x].removeSelection()
            if nom_cdr_comp[cont_nom]!="-":

                mens_b = f"¿Todas las entidades del CDR <b>{nom_cdr_comp[cont_nom]}</b> serán evaluadas?\n<b>SI</b> para utilizar todas las entidades\n"
                mens_b += "<b>NO</b> para seleccionar campo y atributo especifico"
                titulo = "Compleción para CDE: "+str(nom_cde_comp[cont_nom])
                msgBox = QMessageBox().question(self,titulo, mens_b, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if msgBox == QMessageBox.No:
                    campos = list(capa_cdr_comp[x].fields())
                    campos_lista=[]
                    for n in campos:
                        campos_lista.append(n.name())
                    mens_b = f"Campos de {nom_cdr_comp[cont_nom]}"
                    ok = ""
                    while ok=="" or ok==False:
                        item, ok = QInputDialog.getItem(self, mens_b, "Seleccione campo:", campos_lista, 0, False)
                    if ok and item:
                        atrib = []
                        for n in capa_cdr_comp[x].getFeatures():
                            ids = n.fieldNameIndex(item)
                            if not str(n.attributes()[ids]) in atrib:
                                atrib.append(str(n.attributes()[ids]))
                        mens_b = f"Atributos del campo {item} en {nom_cdr_comp[x]}"
                        ok = ""
                        while ok=="" or ok==False:
                            item_a, ok = QInputDialog.getItem(self, mens_b, "Seleccione atributo:", atrib, 0, False)

                    expression = f'"{item}"=\'{item_a}\''
                    selected_fid = []
                    for f in capa_cdr_comp[x].getFeatures(expression):
                        selected_fid.append(f)

                    epsg=capa_cdr_comp[x].crs().toWkt()
                    if capa_cdr_comp[x].geometryType()==0: # si la capa es  ######## PUNTO ######        
                        capa_sel = QgsVectorLayer("Point?crs="+ epsg, "temp", "Memory")
                    elif capa_cdr_comp[x].geometryType()==1: # si la capa es  ######## LINEA ######         
                        capa_sel = QgsVectorLayer("Linestring?crs="+ epsg, "temp", "Memory")
                    elif capa_cdr_comp[x].geometryType()==2: # si la capa es  ######## LINEA ######         
                        capa_sel = QgsVectorLayer("Polygon?crs="+ epsg, "temp", "Memory")

                    capa_sel.dataProvider().addAttributes([QgsField("ID", QVariant.String)])
                    capa_sel.updateFields()
                    capa_sel.dataProvider().addFeatures(selected_fid)
                    capa_cde_comp[x].removeSelection()

                processing.run("native:selectbylocation", {'INPUT':capa_cde_comp[x],'PREDICATE':[0,1],'INTERSECT':ext,'METHOD':0})
                num_cde = len(capa_cde_comp[x].selectedFeatures())
                capa_cde_comp[x].removeSelection()

                if msgBox == QMessageBox.No:
                    processing.run("native:selectbylocation", {'INPUT':capa_sel,'PREDICATE':[0,1],'INTERSECT':ext,'METHOD':0})
                    num_cdr = len(capa_sel.selectedFeatures())
                    capa_sel.removeSelection()
                    cam_atr = expression 
                else:
                    processing.run("native:selectbylocation", {'INPUT':capa_cdr_comp[x],'PREDICATE':[0,1],'INTERSECT':ext,'METHOD':0})
                    num_cdr = len(capa_cdr_comp[x].selectedFeatures())
                    capa_cdr_comp[x].removeSelection()
                    cam_atr = "Completa"

                if num_cde > num_cdr:
                    comi = num_cde-num_cdr
                    omis = 0
                    try:
                        por_comi = round(((comi/num_cdr)*100),2)
                    except ZeroDivisionError:
                        por_comi = 1
                    por_omi = 0                    
                else:
                    comi = 0
                    omis = num_cdr-num_cde
                    try:
                        por_omi = round(((omis/num_cdr)*100),2)
                    except ZeroDivisionError:
                        por_omi = 1
                    por_comi = 0 

                mensaje_exac += f"<tr><td><b>{nom_cde_comp[cont_nom]}</b></td><td><b>{nom_cdr_comp[cont_nom]}</b></td><td>{num_cde}</td><td>{num_cdr}</td><td>{cam_atr}</td><td>{comi}</td><td>{por_comi} %</td><td>{omis}</td><td>{por_omi} %</td></tr>"
                acum_che+=num_cdr
                acum_com+=comi
                acum_omi+=omis
            cont_nom+=1    

        # Validación de medidas para comisión
        if acum_com == 0:
            com1 = "Falso"
            com2 = 0
            com3 = 0.0
        else:
            com1 = "Verdadero"
            com2 = acum_com 
            com3 = round((com2/(acum_che))*100,2)

        # Validación de medidas para omisión
        if acum_omi == 0:
            omi5 = "Falso"
            omi6 = 0
            omi7 = 0.0
        else:
            omi5 = "Verdadero"
            omi6 = acum_omi 
            omi7 = round((acum_omi/(acum_che))*100,2)


        text_for = "<center><h2>Evaluación Compleción</h2></center>"
        text_for += f"Proyecto: <b>{ruta}</b><p>"
        text_for += f"La evaluación se realiza sobre: <b>{cob}</b> {area_cob}<p>"
        text_for += f"Fecha: <b>{hoy}</b><p>"
        text_for += "Método de evaluación: <b>Directo Externo</b><p>"
        text_for += "Enfoque de inspeción: <b>Automático / Inspección completa</b><p>"
        text_for += "<h3>Reporte resultados (Anexo D ISO 19157)</h3>"
        text_for += f"<b>Comisión / Omisión (elementos chequeados {acum_che})</b>"
        text_for +="<table border=1><tr><td></td><td><b>Medida 1</b></td><td><b>Medida 2</b></td><td><b>Medida 3</b></td></tr>"
        text_for +=f"<tr><td><b>Error de Comisión (verdadero indica que el ítem es excedente)</b></td><td>{com1}</td><td>{com2}</td><td>{com3} %</td></tr>"
        text_for +="</table><br><p>"
        text_for +="<table border=1><tr><td></td><td><b>Medida 5</b></td><td><b>Medida 6</b></td><td><b>Medida 7</b></td></tr>"
        text_for +=f"<tr><td><b>Error de Omisión (verdadero indica que el ítem es deficiente)</b></td><td>{omi5}</td><td>{omi6}</td><td>{omi7} %</td></tr>"
        text_for +="</table><br><p>"


        mensaje = "<b>Complecíon</b><p>"+mensaje_exac+"</table><p>"

        resultado = str(ruta)+'/Resultados/Complecion.html'
        f = open (resultado, 'w')
        f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>Resultado de Evaluación Calidad - Compleción</title>\n')
        f.write('<style type="text/css">\nbody {font-family: arial; margin: 5%;}\ntable {border: 2px solid blue; border-collapse: collapse; font-family: arial; width: 80%;}\n')
        f.write('td {padding: 5px;text-align: center;}</style></head>\n<body>\n')
        f.write(text_for)
        f.write('\n<p>\n')
        f.write('<hr><p><h3>Reporte Detallado</h3><p>\n')
        f.write(mensaje)
        f.write('\n</html>')
        f.close()

        self.bt_resultado.setEnabled(True)
        self.bt_resultado.clicked.connect(self.ver_result_comp)

        doc = """<style type='text/css'>
          table {border-collapse:collapse; border:1px; border-style:solid; border-color:darkblue; padding:3px; vertical-align:middle;} 
          td {padding: 3px;text-align: center;}</style>"""

        self.rel_val.setHtml(doc+text_for)


