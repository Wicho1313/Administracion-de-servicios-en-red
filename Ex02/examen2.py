from flask import Flask, url_for, jsonify, request, render_template, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import netifaces, os
import paramiko, time, sys,socket,threading
from graphviz import Graph

max_buffer=65535
username = 'admin'
password = 'admin'


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miRed.db'
bd = SQLAlchemy(app)
gws = []
modelo = []
nodos= {}
layouts={}
FastEth={}
activas = {}
users = {}
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#---------------------TABLAS DE LA BASA DE DATOS---------------------
class ValidacionError(ValueError):
    pass
class Interface(bd.Model):
	__tablename__ = 'Interfaces'
	id= bd.Column(bd.Integer, primary_key=True)
	hostname = bd.Column(bd.String(64))
	name = bd.Column(bd.String(64))
	IPInt = bd.Column(bd.String(64))
	mascara = bd.Column(bd.String(64))
	subred = bd.Column(bd.String(64))

	def get_url(disp):
		return url_for('get_interfaces', hostname=disp.hostname, interface=disp.name, _external=True)

	def get_data(disp):
		return {
			'hostname': disp.hostname,
			'name': disp.name,
			'IP de interfaz': disp.IPInt,
			'mascara': disp.mascara,
			'subred': disp.subred,    
		}

	def set_data(disp, datos):
		try:
			disp.hostname = datos['hostname']
			disp.name = datos['name']
			disp.IPInt = datos['IPInt']
			disp.mascara = datos['mascara']
			disp.subred = datos['subred']

		except KeyError as e:
			raise ValidationError('Invalid dispositivo: missing ' + e.args[0])
		return disp

		
class Dispositivo(bd.Model):
    __tablename__ = 'Dispositivos'
    id = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(64))
    identificador = bd.Column(bd.String(120))
    marca = bd.Column(bd.String(120))
    so = bd.Column(bd.String(64))
    Interfaces = bd.Column(bd.Integer)

    def dame_url(disp):
        return url_for('dame_dispositivo', hostname=disp.hostname, _external=True)

    def exporta_datos(disp):
        return {
            'disp_url': disp.dame_url(),
            'hostname': disp.hostname,
            'identificador': disp.identificador,
            'marca': disp.marca,
            'so': disp.so,
            'Interfaces': disp.Interfaces,
            
        }

    def importa_datos(disp, datos):
        try:
            disp.hostname = datos['hostname']
            disp.identificador = datos['identificador']
            disp.marca = datos['marca']
            disp.so = datos['so']
            disp.Interfaces = datos['Interfaces']
            
        except KeyError as e:
            raise ValidationError('Invalid dispositivo: missing ' + e.args[0])
        return disp

class Usuario(bd.Model):
	__tablename__ = 'Usuarios'
	id = bd.Column(bd.Integer, primary_key=True)
	hostname = hostname = bd.Column(bd.String(64))
	usr = bd.Column(bd.String(64))
	passw = bd.Column(bd.String(120))
	
	def get_url2(disp):
		return url_for('get_usuarios', hostname=disp.hostname, usr=disp.usr, _external=True)

	def get_data(disp):
		return {
			'hostname' : disp.hostname,
			'Usuario' : disp.usr,
			'password' : disp.passw,
		}
	def set_data(disp,datos):
		try:
			disp.hostname =  datos['hostname']
			disp.usr = datos['usr']
			disp.passw = datos['passw']
            
		except KeyError as e:
			raise ValidationError('Invalid dispositivo: missing ' + e.args[0])
		return disp
	
#------------------------------------------------------------------------	

#-------------Mapeo y creacion de imagen de red----------------------------
def clear_buffer(connection,buffer):
		if connection.recv_ready():
			return connection.recv(buffer)
def hilo_conexion(direction):
	connection = paramiko.SSHClient()
	connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	
	try:
		connection.connect(direction,username=username,password=password,timeout = 5,look_for_keys=False,allow_agent=False)
		print('conectando a '+ direction)
	
	except:
		print('ERROR INTERNO :' , sys.exc_info())
	print('despues del try')
	new_connection = connection.invoke_shell()
	output = clear_buffer(new_connection,max_buffer)
	new_connection.send('show ip ospf neighbor\n')
	time.sleep(1)
	output = new_connection.recv(max_buffer)
	neighbors = output.decode('utf-8')
	output = clear_buffer(new_connection,max_buffer)
	prompt = neighbors[-3:-1]
	print('este es prompt : '+prompt)
	ks = nodos.keys()
	if prompt not in ks:
		nodos[prompt]=[]
		layouts[prompt]=[]
		FastEth[prompt]=[]
		activas[prompt]=[]
		users[prompt]=[]
		aux = neighbors.splitlines();
		for line in aux:
			if 'FULL' in line:
				ipNieg = line[50:62].strip()
				if ipNieg not in gws:
					#print('next ip ssh'+ipNieg)
					gws.append(ipNieg)
		new_connection.send('show ip route list 1\n')
		time.sleep(1)
		output = new_connection.recv(max_buffer)
		tabla = output.decode('utf-8')
		output = clear_buffer(new_connection,max_buffer)
		aux2 = tabla.splitlines();
		sub = ''
		for linea in aux2:
			if linea[0:1].find('C') != -1 and linea.find('192')==-1:
				red = linea.split(' ')
				#print('red directamente conectada: '+red[7])
				if red[7] not in nodos[prompt]:
					output=clear_buffer(new_connection,max_buffer)
					new_connection.send('ping '+red[7]+' repeat 2 timeout 1'+'\n')
					time.sleep(3)
					output=new_connection.recv(max_buffer)
					temp = output.decode('utf-8')
					validacion = temp.splitlines()
					if validacion[5].find('e')==1:
						nodos[prompt].append(red[7])
						FastEth[prompt].append(red[11]+' '+red[7])
		output = (new_connection,max_buffer)
		new_connection.send('show running-config | include (interface|ip address)'+'\n')
		time.sleep(2)
		output=new_connection.recv(max_buffer)
		interfaces=output.decode('utf-8')
		output = clear_buffer(new_connection,max_buffer)
		aux3=interfaces.splitlines()
		for inter in aux3:
			#print('interfaces de  '+prompt+' '+inter)
			try:
				if 'interface' in inter:
					name = inter[inter.index('ace')+4:]
				else:
					if 'no' not in inter:
						ip = inter[inter.index('ss')+3:]
						
						layouts[prompt].append(name+' '+ip+' ')
			except:
				continue
		otput = (new_connection,max_buffer)
		new_connection.send('show running-config | include user\n')
		time.sleep(2)
		output = new_connection.recv(max_buffer)
		info = output.decode('utf-8')
		output = clear_buffer(new_connection,max_buffer)
		lines = info.splitlines()
		b = lines[1].split(' ')
		print('usuarios y constraseñas obtenidas :'+prompt +' user '+b[1]+ 'pass '+b[6])
		users[prompt].append(b[1])
		users[prompt].append(b[6])		
	
		connection.close()
	connection.close()

def Marca(gateway):
	
	connection = paramiko.SSHClient()
	connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())	
	try:
		connection.connect(gateway,username=username,password=password,timeout = 5,look_for_keys=False,allow_agent=False)
	except:
		print('ERROR INTERNO :' , sys.exc_info())
	print('obteniendo SO y MODELO')
	new_connection = connection.invoke_shell()
	output = clear_buffer(new_connection,max_buffer)
	time.sleep(1)
	new_connection.send('show version | include IOS\n')
	time.sleep(2)
	output = new_connection.recv(max_buffer)
	info = output.decode('utf-8')
	lines = info.splitlines()
	b = lines[2].split(' ')
	modelo.append(b[0]+' '+b[3])
	modelo.append(b[4]+' '+b[5][:-1])
	print(str(modelo))
	
	connection.close()


def imagen(gateway):
	#nodos redes activas
	temporal = sorted(nodos.items())
	nodos.clear()
	for i in temporal:
		nodos[i[0]]=i[1]
	#layouts interfaces reportadas en tabla route
	temp2 = sorted(layouts.items())
	layouts.clear()
	for interfaz in temp2:
		layouts[interfaz[0]]=interfaz[1]
	#FastEth interfaces activas incompletas
	temp2 = sorted(FastEth.items())
	FastEth.clear()
	for fa in temp2:
		FastEth[fa[0]]=fa[1]
	#Activas interfaces activas completas
	name = layouts.keys()
	for uno in name:
		for i in FastEth[uno]:
			fa = i[:i.index(' ')]
			for r in layouts[uno]:
				if fa in r:
					i=i+r[r.index(' '):]
					activas[uno].append(i)#
	temp2 = sorted(activas.items())
	activas.clear()
	for fa in temp2:
		activas[fa[0]]=fa[1]
	
	dicredes={}
	cad = ''
	grafica=Graph('red')
	grafica.node('linux mint',shape='rectangle', label='MV'+'\n'+gateway)
	grafica.node('switch', shape='rectangle')
	grafica.edge('linux mint','switch')
	for x in nodos:
	    aux4 = activas[x]
	    for y in aux4:
	    	cad = cad + y +'\n'
	    grafica.node(x, label=x+'\n'+cad, shape='rectangle')
	    cad=''
	    redes=nodos[x]
	    for red in redes:
	        if red not in dicredes.keys():
	            dicredes[red]=[]
	            dicredes[red].append(x)
	        else:
	            dicredes[red].append(x)
	for d in dicredes:
	    print(d + ':' + str(dicredes[d]))
	    if d.find('56')>=0:
	        for each in dicredes[d]:
	            
	            grafica.edge('switch',each,label=d)
	    if len(dicredes[d]) == 2 and d.find('8')==0:   
	        grafica.edge(dicredes[d][0],dicredes[d][1],label=d)
	grafica.format = 'png'
	grafica.render('static/red')	


def config_user (ip, username, password, comando):
	try:
		
		connection = paramiko.SSHClient()
		connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		connection.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)
		new_connection = connection.invoke_shell()
		output = clear_buffer(new_connection,max_buffer)
		time.sleep(2)
		commands = ['conf t \n',comando+'\n']
		for command in commands:
			new_connection.send(command)
			time.sleep(2)
			output = new_connection.recv(max_buffer)
		new_connection.close()  
	except:
		print('Error interno: ', sys.exc_info())
		return 'Error en enrutar'

#-----------------------------------------------------------------------------

#-------------MODULOS DE MANIPULACION DE USUARIOS-----------------------------
@app.route('/CrearUser', methods=['POST'])
def CrearUser():
	ht = request.form['hostname']
	newU = request.form['newUser']
	p = request.form['pass']
	user = Usuario()
	reg = dict(hostname=ht, usr = newU, passw=p)
	user.set_data(reg)
	bd.session.add(user)
	bd.session.commit()
	au = ht.split('R')
	a = int(au[1])
	if a == 1:
		ip = gws[0]
	elif a == 2:
		ip = gws[3]
	elif a == 3:
		ip = gws[2]
	elif a == 4:
		ip = gws[1]
	elif a == 5:
		ip = gws[4]
	elif a == 6:
		ip = gws[5]
	comando = str('username '+newU+' privilege 15 password '+p)
	config_user (ip, username, password, comando)
	
	return redirect('/dispositivos/'+ht)

@app.route('/EditUser', methods=['POST'])
def edita_user():
	ht = request.form['hostname']
	u = request.form['usr']
	newU = request.form['newUser']
	p = request.form['pass']
	user = Usuario.query.filter_by(hostname=ht).filter_by(usr=u).first_or_404()
	reg = dict(hostname=ht, usr = newU, passw=p)
	user.set_data(reg)
	bd.session.add(user)
	bd.session.commit()
	au = ht.split('R')
	a = int(au[1])
	if a == 1:
		ip = gws[0]
	elif a == 2:
		ip = gws[3]
	elif a == 3:
		ip = gws[2]
	elif a == 4:
		ip = gws[1]
	elif a == 5:
		ip = gws[4]
	elif a == 6:
		ip = gws[5]
	comando = str('username '+newU+' privilege 15 password '+p)
	config_user (ip, username, password, comando)
	
	
	return redirect('/dispositivos/'+ht)

@app.route('/EliminaUser', methods=['POST'])
def DelUser():
	ht = request.form['hostname']
	newU = request.form['usr']
	user = Usuario.query.filter_by(hostname=ht).filter_by(usr=newU).first_or_404()
	bd.session.delete(user)
	bd.session.commit()
	au = ht.split('R')
	a = int(au[1])
	if a == 1:
		ip = gws[0]
	elif a == 2:
		ip = gws[3]
	elif a == 3:
		ip = gws[2]
	elif a == 4:
		ip = gws[1]
	elif a == 5:
		ip = gws[4]
	elif a == 6:
		ip = gws[5]
	comando = str('no username '+newU)
	config_user (ip, username, password, comando)
	return redirect('/dispositivos/'+ht)

@app.route('/usarios/<hostname>/<usr>', methods=['GET'])
def get_usuarios(hostname,usr):
	h=hostname
	u= usr
	reusult = Usuario.query.filter_by(hostname=h).filter_by(usr=u).first_or_404().get_data()

	return render_template('Usuario.html', data = reusult)

#-------------------------------------------------------------------------------

#--------------PRIMER LLENADO DE LA BASE DE DATOS -------------------------
@app.route('/Routers',methods=['POST','GET'])
def Routers():
	
	for router in layouts:
		i = layouts[router][0][layouts[router][0].index('ck')+4:layouts[router][0].index('ck')+15]
		numInt = len(activas[router])
		datos = dict(hostname=router, identificador=i,marca=modelo[0],so=modelo[1],Interfaces=numInt)
		d = Dispositivo()
		f = d.importa_datos(datos)
		bd.session.add(f)
		bd.session.commit()
		i=''

	for r in activas:
		lista = activas[r]
		
		for dato in lista:
			info = dato.split(' ')
			send = dict(hostname=r, name=info[0].replace('/','_'), IPInt=info[2], mascara=info[3], subred=info[1])
			I = Interface()
			b = I.set_data(send)
			bd.session.add(b)
			bd.session.commit()
	for u in users:
		l = users[u]
		
		registro = dict(hostname=u, usr=l[0], passw=l[1])
		U = Usuario()
		reg = U.set_data(registro)
		bd.session.add(reg)
		bd.session.commit()

	return redirect('/dispositivos')

#---------------------------------------------------------------------------

##--------MODULOS DE EDICION DE ROUTERS E INTERDACES -------------------------
@app.route('/Routers/Editar',methods=['GET'])
def EditarRouter():
	return render_template("E_R.html")
@app.route('/EditRouter', methods=['POST'])
def edita_dispositivo():
	
	ht = request.form['hostname']
	iden = request.form['id']
	mar = request.form['marca']
	system = request.form['so']
	NI = request.form['inter']
	dispositivo = Dispositivo.query.get_or_404(int(ht[1:]))
	datos = dict(hostname=ht, identificador=iden,marca=mar,so=system,Interfaces=int(NI))
	dispositivo.importa_datos(datos)
	bd.session.add(dispositivo)
	bd.session.commit()

	return redirect('/dispositivos')


@app.route('/EditInterface', methods=['POST'])
def edita_inter():
	ht = request.form['hostname']
	n = request.form['name']
	newN = request.form['newName']
	ip = request.form['IPInt']
	ma = request.form['mascara']
	s = request.form['subred']
	interface = Interface.query.filter_by(hostname=ht).filter_by(name=n).first_or_404()
	datos = dict(hostname=ht, name=newN,IPInt=ip,mascara=ma,subred=s)
	interface.set_data(datos)
	bd.session.add(interface)
	bd.session.commit()

	return redirect('/dispositivos/'+ht)

#--------------------------------------------------------------------------------


#----------MOdulos de despliegue de informacion---------------------------------
@app.route('/dispositivos/', methods=['GET'])
def dame_dispositivos():
    return jsonify({'dispositivo': [dispositivo.dame_url() 
                               for dispositivo in Dispositivo.query.all()]})	

@app.route('/dispositivos/<hostname>', methods=['GET'])
def dame_dispositivo(hostname):
	id = int(hostname[1:])
	return jsonify({'Dispositivo': [Dispositivo.query.get_or_404(id).exporta_datos()],
					'Interfaces activas': [uno.get_url()
										for uno in Interface.query.filter_by(hostname=hostname).all()],
					'Usuarios del router': [y.get_url2()
										for y in Usuario.query.filter_by(hostname=hostname).all()],})	


@app.route('/dispositivos/<hostname>/<interface>/', methods=['GET'])
def get_interfaces(hostname,interface):
	h=hostname
	i = interface
	reusult  = Interface.query.filter_by(hostname=h).filter_by(name=i).first_or_404().get_data()
	return render_template('Interface.html', data = reusult)
#-------------------------------------------------------------------------



@app.route('/informacion_de_red', methods=['POST','GET'])
def ShowInfo():
	return render_template('info_page.html')

@app.route('/', methods=['POST','GET'])
def GeneraTopologia():
	aux = netifaces.gateways()
	gw = aux['default'][netifaces.AF_INET]
	
	gws.append(str(gw[0]))
	print('este es el default '+gws[0])
	for g in gws:
		hilo = threading.Thread(target=hilo_conexion,
								args=(g,))
		hilo.start()
		time.sleep(2)
	time.sleep(7)
	imagen(gw[0])
	Marca(gw[0])
	time.sleep(1)
	return redirect('/informacion_de_red')


if __name__ == '__main__':
	#bd.drop_all()
	time.sleep(1)
	bd.create_all()
	app.run(host='0.0.0.0', debug=True)
