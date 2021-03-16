"""Revisa correo iribarrenpy@gmail.com y descarga archivos adjuntos de emails que contienen palabras clave en el subject.
Cada archivo es descargado en una carpeta llamada igual que la palabra clave dentro de la carpeta static. Si la carpeta
no existe la crea. Si ya hay una foto la reemplaza por la nueva y la otra la copia en carpeta de respaldo con fecha.
Envia todos los emails leidos a carpeta processed en gmail y limpia el inbox. Luego grafica los datos en matplotlib y Bokeh
y los guarda en la carpeta static/datos/ de cada estación"""

import email
import getpass, imaplib
import os
import sys
import time
from shutil import move,copyfile
from datetime import datetime
import matplotlib.pyplot as plt
import bokeh
import pandas as pd
from bokeh.io import output_file, show
from bokeh.layouts import row,column
from bokeh.plotting import figure,output_file, save, show, ColumnDataSource
from bokeh.models.tools import HoverTool
from collections import OrderedDict
import cv2
import numpy as np
import glob
import ffmpy



#Lista de sitios con estaciones de monitoreo. Cada estación debe enviar datos a iribarrenpy@gmail.com
#con nombre de estación en subject. Ese nombre será usado para guardar datos en carpeta destinada

######################################################################################################
clave= ["#casa_fotos","#casa_datos"] #Palabra que buscar en el subject del mensaje (siempre va con hashtag aquí)

#Agregar a la lista los directorios de nuevas estaciones para plotear
lista_path= ["./casa"]

########################################################################################################

#Si existe el archivo de la foto lo cortamos y pegamos en respaldo

#hoy = datetime.now()

#fechaHora = hoy.strftime("%d-%m-%Y_%H_%M")#Para nombrar foto que se respalda

#for i in clave:

#    crs= r"."+"/"+i[1:i.find("_")]+"/"+ i[i.find("_")+1:]+"/bmp280.csv"#Ruta a foto desplegada en sitio web

#    if os.path.exists(crs):
#        move(crs,"."+"/"+i[1:i.find("_")]+"/"+"respaldo_datos/"+fechaHora+".csv" )#Poner ruta a carpeta de respaldo de fotos

##################################################

detach_dir = r"." #descargará archivo
userName = 'iribarrenpy'
passwd = 'xynpbywetzlvhbqb'


#Proceso email
imapSession = imaplib.IMAP4_SSL('smtp.gmail.com',993)
typ, accountDetails = imapSession.login(userName, passwd)

imapSession.select('Inbox')

# Buscamos palabras claves en todos los emails de la bandeja de entrada y descargamos archivo adjunto en carpeta predefinida
#Luego eliminamos ese email

for i in clave:

    typ, data = imapSession.search(None, 'SUBJECT', i)

  # Iterando sobre todo los emails

    for msgId in data[0].split():
        typ, messageParts = imapSession.fetch(msgId, '(RFC822)')

        emailBody = messageParts[0][1]
        mail = email.message_from_bytes(emailBody)

        for part in mail.walk():

            fileName = part.get_filename()

            if bool(fileName):
                print(i)
                filePath = os.path.join(detach_dir+"/"+i[1:i.find("_")], i[i.find("_")+1:], fileName)

                fp = open(filePath, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

#Moviendo emails a procesados y limpiando inbox

imapSession.select(mailbox='inbox', readonly=False)
resp, items = imapSession.search(None, 'All')
email_ids = items[0].split()

for email in email_ids:

        #move to processed
    result = imapSession.store(email, '+X-GM-LABELS', 'Processed')

    if result[0] == 'OK':

        #delete from inbox
        imapSession.store(email, '+FLAGS', '\\Deleted')

#END OF MOVING EMAILS TO PROCESSED

imapSession.close()
imapSession.logout()

##################BOKEH##########################


for i in lista_path:

    data= pd.read_csv(i+"/datos/bmp280.csv")
    data= data.iloc[:,1:]
    data.columns=["Date","Temp","Hum","Press","lluvia"]#Renombro columnas porque se me dan vuelta :)
    data['Date'] = pd.to_datetime(data['Date'])
    data.set_index("Date",inplace=True)
    data["temp_roll"]=data["Temp"].rolling(1008,win_type="triang").mean()#1008 corresponde a una semana 6*24*7
    data["hum_roll"]=data["Hum"].rolling(1008,win_type="triang").mean()
    data["press_roll"]=data["Press"].rolling(1008,win_type="triang").mean()
    source= ColumnDataSource(data=data)


   #HUMEDAD

    s1 = figure(width=750, plot_height=250, title=None,x_axis_type = "datetime",tools= 'pan,box_zoom,save,reset,hover')#,tools= 'pan,box_zoom,save,reset,hover'

    s1.line(x="Date",y="Hum",color='skyblue',line_width = 1,legend= "Humidity (%)",source=source)
    s1.line(x="Date",y="hum_roll",color='blue',line_width = 1,legend="Running mean 7 days",source=source)

    s1.xaxis.axis_label = "Date"
    s1.yaxis.axis_label = "Humidity(%)"

    s1.legend.location = "top_left"
    s1.legend.click_policy="hide"
    s1.legend.padding=1
    s1.legend.margin=0


    hover = s1.select(dict(type=HoverTool))
    hover.tooltips = [("Hum", "@Hum")]

# TEMPERATURA

    s2 = figure(width=750, height=250, title=None,x_axis_type = "datetime",tools= 'pan,box_zoom,save,reset,hover')
    s2.line(x="Date",y="Temp",color='salmon',line_width = 1,legend="Temperature (°C)",source=source)
    s2.line(x="Date",y="temp_roll",color='red',line_width = 1,legend="Running mean 7 days",source=source)


    s2.xaxis.axis_label = "Date"
    s2.yaxis.axis_label = "Temperature(º)"
    s2.legend.location = "top_left"
    s2.legend.click_policy="hide"
    s2.legend.padding=1
    s2.legend.margin=0

    hover2 = s2.select(dict(type=HoverTool))
    hover2.tooltips = [("Temp", "@Temp")]

# PRESION

    s3 = figure(width=750, height=250, title=None, x_axis_type='datetime',tools= 'pan,box_zoom,save,reset,hover')
    s3.line(x="Date",y="Press",color='lawngreen',line_width = 1,legend="Pressure (mb)",source=source)
    s3.line(x="Date",y="press_roll",color='green',line_width = 1,legend="Running mean 7 days",source=source)


    s3.xaxis.axis_label = "Date"
    s3.yaxis.axis_label = "Pressure(mb)"

    s3.legend.location = "top_left"
    s3.legend.click_policy="hide"
    s3.legend.padding=1
    s3.legend.margin=0

    hover3 = s3.select(dict(type=HoverTool))
    hover3.tooltips = [("Press", "@Press")]

# put all the plots in a grid layout

#show(row(s1, s2, s3))

    output_file(i+"/datos/bmp280.html")
    save(column(s1, s2, s3))

######################MATPLOTLIB####################
for i in lista_path:

    data= pd.read_csv(i+"/datos/bmp280.csv")
    data= data.iloc[-144:,1:]
    data.columns=["Date","Temp","Hum","Press","lluvia"]#Renombro columnas porque se me dan vuelta :)
    data['Date'] = pd.to_datetime(data['Date'])
    data.set_index("Date",inplace=True)

    fig= plt.figure(figsize=(12,9))
    ax= fig.add_subplot(221)
    data["Temp"].plot(ax=ax,color="red",rot=90)
    plt.ylabel("Temperatura (°C)",fontweight="bold",fontsize=16)
    plt.grid()
    plt.xlabel("Fecha y hora",fontweight="bold",fontsize=16)
    #plt.tight_layout();

    ax1= fig.add_subplot(222)
    data["Hum"].plot(ax=ax1,color="blue",rot=90)
    plt.ylabel("Humedad atmosférica (%)",fontweight="bold",fontsize=16)
    plt.xlabel("Fecha y hora",fontweight="bold",fontsize=16)
    plt.grid()
    #plt.tight_layout();


    ax2= fig.add_subplot(223)
    data["Press"].plot(ax=ax2,rot=90)
    plt.ylabel("Presión atmosférica (mb)",fontweight="bold",fontsize=16)
    plt.xlabel("Fecha y hora",fontweight="bold",fontsize=16)
    plt.grid()
    plt.tight_layout();

    ax3= fig.add_subplot(224)
    data["lluvia"].plot(ax=ax3,rot=90,style="*",c="green")
    plt.xlabel("Fecha y hora",fontweight="bold",fontsize=16)
    plt.ylabel("Precipitación",fontweight="bold",fontsize=16)
    ax3.set_yticks([1,0])
    ax3.set_yticklabels(["Llueve","No llueve"], rotation=90)
    plt.grid()
    plt.tight_layout();
    fig.savefig(i+"/datos/bmp280.png",DPI=1500)

####################### Hacer video con últimas 8 imágenes################################

img_array = []
imagenes= glob.glob('./casa/fotos/*.jpg')
imagenes.sort(key=os.path.getmtime)
ultimas_ocho= imagenes[-8:]


for filename in ultimas_ocho:
    img = cv2.imread(filename)
    height, width, layers = img.shape
    size = (width,height)
    img_array.append(img)


out = cv2.VideoWriter('./casa/fotos/TimeLapseCasa.avi',cv2.VideoWriter_fourcc(*'DIVX'), 1, size)

for i in range(len(img_array)):
    out.write(img_array[i])
out.release()

#Transformando avi a MP4

#avitomp4 = ffmpy.FFmpeg(
#inputs={'./casa/fotos/TimeLapseCasa.avi': None},
#    outputs={'./casa/fotos/TimeLapseCasa.mp4': '-y'})

# windows
avitomp4 = ffmpy.FFmpeg(executable='./ffmpeg/bin/ffmpeg.exe', inputs={'./casa/fotos/TimeLapseCasa.avi': None}, outputs={'./casa/fotos/TimeLapseCasa.mp4': '-y'})
avitomp4.run()

