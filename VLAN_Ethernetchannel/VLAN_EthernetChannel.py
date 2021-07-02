from flask import Flask, url_for, jsonify, request, render_template, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import paramiko, time, sys, socket
from sqlalchemy import exc, delete


# Crea una aplicación Flask, carga la configuración
# y crea el objeto SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miRed.db'
bd = SQLAlchemy(app)
# variables globales
max_buffer=65535

# Con esto creamos la base de datos con los parmámetros que necesitamos
class Dispositivo(bd.Model):
    __tablename__ = 'Dispositivos'
    id = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(64), unique=True)
    usuario = bd.Column(bd.String(120), unique=True)
    contra = bd.Column(bd.String(120), unique=True)
    ip = bd.Column(bd.String(120), unique=True)
    
    def dame_url(disp):
        return url_for('dame_dispositivo', hostname=disp.hostname, _external=True)
    
    def exporta_datos(disp):
        return {
            'disp_url': disp.dame_url(),
            'hostname': disp.hostname,
            'usuario': disp.usuario,
            'contra': disp.contra,
            'ip': disp.ip,
        }

    def importa_datos(disp, datos):
        try:
            disp.hostname = datos['hostname']
            disp.usuario = datos['usuario']
            disp.contra = datos['contra']
            disp.ip = datos['ip']
        except KeyError as e:
            raise KeyError('Invalid dispositivo: missing ' + e.args[0])
        return disp

# base de datos de las VLAN que nos servirán para guardar las VLAN en el dispositivo
class VLAN(bd.Model):
    __tablename__ = 'VLAN'
    id = bd.Column(bd.Integer, primary_key=True)
    nombre = bd.Column(bd.String(120), unique=False)
    numero = bd.Column(bd.String(120), unique=False)
    ip = bd.Column(bd.String(120), unique=False)
    interfaz = bd.Column(bd.String(120), unique=False)
    
    def dame_url(disp):
        return url_for('dame_dispositivo', numero=disp.numero, _external=True)
    
    def exporta_datos(disp):
        return {
            'disp_url': disp.dame_url(),
            'nombre': disp.nombre,
            'numero': disp.numero,
            'ip': disp.ip,
            'interfaz': disp.interfaz,
        }

    def importa_datos(disp, datos):
        try:
            disp.nombre = datos['nombre']
            disp.numero = datos['numero']
            disp.ip = datos['ip']
            disp.interfaz = datos['interfaz']
        except KeyError as e:
            raise KeyError('Invalid dispositivo: missing ' + e.args[0])
        return disp


#funcion que limpia el buffer en la conexion
def clear_buffer(connection,buffer):
		if connection.recv_ready():
			return connection.recv(buffer)


# FUncion que nos permite crear una nueva VLAN en los dispositivos
def accionVLAN (ip, username, password, numero, nombre, ipVlan, mascara, interfaz, accion):
    print ("entré a la función ACCION")
    commandsSW = ['conf t','interface vlan '+numero, 'ip address '+ipVlan+' '+mascara, 'no shut', 'interface '+interfaz.replace('_','/'), 
    'switchport access vlan '+numero, 'end', 'vlan database', 'vlan '+numero+' name '+nombre, 'apply', 'exit']
    # print(commandsSW)
    commandsR = ['conf t', 'interface fastethernet '+'0/0.'+numero, 'encapsulation dot1Q '+ numero, 'ip address '+ipVlan+' '+mascara, 'end']
    # print (commandsR)
    commandsB = ['conf t', 'no interface vlan '+numero, 'end', 'vlan database', 'no vlan '+numero, 'exit']
    commandsBR = ['conf t', 'no interface fastethernet '+'0/0.'+numero, 'end']
    try:
        connection = paramiko.SSHClient()
        connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)
        new_connection = connection.invoke_shell()
        output = clear_buffer(new_connection, max_buffer)
        time.sleep(2)
        if accion == 'sw':
            for command in commandsSW:
                print ('Entré al switch\nEnviando comando: ',command)
                new_connection.send(command+'\n')
                time.sleep(2)
                output = new_connection.recv(max_buffer)
                # print(output)
        elif accion == 'b':
            for command in commandsB:
                print ('Entré al switch para borrar\nEnviando comando: ',command)
                new_connection.send(command+'\n')
                time.sleep(2)
                output = new_connection.recv(max_buffer)
        elif accion == 'br':
            for command in commandsBR:
                print ('Entré al router para borrar\nEnviando comando: ',command)
                new_connection.send(command.strip()+'\n')
                time.sleep(2)
                output = new_connection.recv(max_buffer)
                print(output)
        else:
            for command in commandsR:
                print ('Entre al router\nEnviando comando: ',command)
                new_connection.send(command+'\n')
                time.sleep(2)
                output = new_connection.recv(max_buffer)
                #print (output)
        result = output.decode('utf-8').splitlines()
        print (result)
        # Cerramos la conexion de ssh con el dispositivo
        new_connection.close()  
        return 'BORRADA CON ÉXITO'
    except:
        print('Error interno: ', sys.exc_info())
        return 'Error en crear'

# Funcion que nos permite consultar las VLAN en los dispositivos
def consulta (ip, username, password, comando1, comando2):
    try:		
        connection = paramiko.SSHClient()
        connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)
        new_connection = connection.invoke_shell()
        output = clear_buffer(new_connection,max_buffer)
        time.sleep(2)
        new_connection.send(comando1+'\n')
        time.sleep(2)
        output = new_connection.recv(max_buffer)
        info = output.decode('utf-8')
        lines = info.splitlines()
        # diccionario de los datos de las vlan
        vlans = {}
        # recorriendo la salida de los comandos en formato de lista    
        for line in lines:
            # se salta cada elemento de la lista que esté en blanco
            if line == '':
                continue
            # comprobando los numeros de las VLAN
            if line[0] >= '0' and line[0] <= '9':
                datos = line.split()
                vlans[datos[0]] = datos
            
        # mandamos el segundo comando 
        new_connection.send(comando2+'\n')
        time.sleep(2)
        output = new_connection.recv(max_buffer)
        info = output.decode('utf-8')
        lines = info.splitlines()
        # diccionario donde guardaremos las ip de las VLAN
        ipVlan = {}
        # recorremos la salida de la conexion ssh
        for line in lines:
            # se salta cada elemento de la lista que esté en blanco
            if line == '':
                continue
            # sacamos las ip de cada VLAN y lo agregamos al diccionario
            if '192' in line:
                ip = line.split()
                ipVlan[ip[0]] = ip

        # print(ipVlan)
        # cerramos la conexion de ssh
        new_connection.close()  
        return vlans, ipVlan
    except:
        print('Error interno: ', sys.exc_info())
        return 'Error en conexion'


# método para consultar las VLAN en nuestros dispositivos
@app.route('/ConsultaVLAN', methods=['GET','POST','PUT'])
def consulta_VLAN():
    print('Entré a consultar...')
    # consulta a la base de datos
    dispositivo = Dispositivo.query.get_or_404(int(1))
    usuario = dispositivo.usuario
    contra = dispositivo.contra
    ip = dispositivo.ip
    # mandamos los comandos y recuperamos los diccionarios que contienen la información de las vlan
    vlans, ips = consulta(ip, usuario, contra, 'sh vlan-s | include VLAN', 'sh ip int br | include Vlan')
    # declaramos un diccionario auxiliar (sirve para quitar el primer elemento y hacer match con los 2 diccionarios)
    aux = {}
    # recorremos el diccionario en el que se encuentra el valor que no necesitamos por ahora
    for i in ips.keys():
        if i != 'Vlan1':
            aux[i] = ips[i]
    # declaramos 2 listas que nos servirán para hacer match de los 2 diccionarios
    lista1 = []
    lista2 = []
    # recorremos los 2 diccionarios originales para agregar su contenido a su respectiva lista
    for i in vlans:
        lista1.append({i:vlans[i]})
    for i in aux:
        lista2.append({i:aux[i]})
    # recorremos cualquiera de las listas puesto que ambas siempre serán del mismo tamaño
    for i in range(0,len(lista1)):
        # accediendo a los valores de la lista para extraerlos
        var = lista1[i]
        var2 = lista2[i]
        cl = str(list(var.keys())[0])
        cl2 = str(list(var2.keys())[0])
        # hacemos match con las 2 listas y sacamos los valores que necesitamos 
        if len(var[cl]) == 3: 
            registro = dict(nombre = var[cl][1], numero = var[cl][0], ip = var2[cl2][1], interfaz = "interfaz no asignada")
            print (registro)
        else:
            registro = dict(nombre = var[cl][1], numero = var[cl][0], ip = var2[cl2][1], interfaz = var[cl][3])
            print (registro)
        # agregamos cada registro a la base de datos
        vlan = VLAN()
        reg = vlan.importa_datos(registro)
        bd.session.add(reg)
        bd.session.commit()
    # hacemos una consulta a la base de datos
    result = VLAN.query.all()
    # abrimos la página  en la que representaremos los datos de la consulta a la base
    return render_template('ConsultaVLAN.html', data = result)


# método para CREAR las VLAN en nuestros dispositivos
@app.route('/FormCrearVLAN', methods=['GET','POST'])
def crear_VLAN():
    print ("Entré a crear una VLAN")
    # se guarda en una veriable lo que se ingresó en el forms de la pag
    numero = request.form['numero']
    print(numero)
    nombre = request.form['nombre']
    print (nombre)
    ipVlan = request.form['ipVlan']
    print (ipVlan)
    mascara = request.form['mascara']
    print(mascara, type(mascara))
    interfaz = request.form['interfaz'].replace('/','_')
    print (interfaz)
    # consulta a la base de datos
    dispositivo = Dispositivo.query.get_or_404(int(1))
    usuario = dispositivo.usuario
    contra = dispositivo.contra
    ipUsu = dispositivo.ip
    # se conecta al router para crear una sub interfaz
    z = accionVLAN('192.168.1.1', usuario, contra, numero, nombre, ipVlan, mascara, interfaz, 'r')
    # se conecta al switch para crear la VLAN
    v = accionVLAN(ipUsu, usuario, contra, numero, nombre, ipVlan, mascara, interfaz, 'sw')

    return jsonify({'Estado de conexion con switch': v,
                    'Estado de conexion con Router': z})	


# método para BORRAR las VLAN en nuestros dispositivos
@app.route('/FormBorrarVLAN', methods=['GET','POST'])
def borrar_VLAN():
    print ("Entré a borrar una VLAN")
    # se guarda en una veriable lo que se ingresó en el forms de la pag
    numeroB = request.form['numeroB']
    print(numeroB)
    dispositivo = Dispositivo.query.get_or_404(int(1))
    usuario = dispositivo.usuario
    contra = dispositivo.contra
    ipUsu = dispositivo.ip
    # se conecta al switch para BORRAR la VLAN
    z = accionVLAN(ipUsu, usuario, contra, numeroB, "", "", "", "", 'br')
    v = accionVLAN(ipUsu, usuario, contra, numeroB, "", "", "", "", 'b')
    
    return jsonify({'Estado de conexion con switch': v,
                    'Estado de conexion con Router': z})	


# método para CREAR las VLAN en nuestros dispositivos
@app.route('/CrearVLAN', methods=['GET','POST'])
def Formulario_crear_VLAN():
    print ("Entré al formulario para CREAR")
    return render_template('CrearVLAN.html')


# método para BORRAR las VLAN en nuestros dispositivos
@app.route('/BorrarVLAN', methods=['GET','POST'])
def Formulario_borrar_VLAN():
    print ("Entré al formulario para BORRAR")
    return render_template('BorrarVLAN.html')


# DIrección de dispositivo a consultar
@app.route('/dispositivo/<int:id>', methods=['GET'])
def get_dispositivo(id):
    # consulta a la base de datos
    dispositivo = Dispositivo.query.get_or_404(id)
    hostname = dispositivo.hostname
    ip = dispositivo.ip
    usuario = dispositivo.usuario    
    contra = dispositivo.contra    
    datos = ['Dispositivo: '+hostname, 'Direccion ip: '+ip, 'Usuario: '+usuario, 'Contraseña: '+contra]

    # Abrir página menú
    return render_template('Menu.html', data = datos)


# Dirección de dispositivo
@app.route('/dispositivo', methods=['POST'])
def set_dispositivo():
    # se guarda en una veriable lo que se ingresó en el forms de la pag
    dev = request.form['device']
    ip = request.form['ip']
    username = request.form['usuario']
    contra = request.form['contra']
    # se hace llamada a la base de datos Dispositivo
    dispositivo = Dispositivo()
    registro = dict(hostname = dev, usuario = username, contra = contra, ip=ip)
    dispositivo.importa_datos(registro)
    bd.session.add(dispositivo)
    bd.session.commit()
    
    # Abre la página menú
    return redirect('/dispositivo/'+str(dispositivo.id))


# Página web raíz 
@app.route('/', methods=['POST','GET'])
def get_datosLogin():
    return render_template('Index.html')


# método principal del programa
if __name__ == '__main__':
    bd.drop_all()
    time.sleep(1)
    bd.create_all()
    app.run(host='0.0.0.0', debug=True)
