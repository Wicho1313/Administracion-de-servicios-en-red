#!/usr/bin/python3
# importamos librerías a usar.
import paramiko, getpass, time
from graphviz import Digraph
# lista gateway que contiene el Gateway del router 1
gateway = ['148.204.56.1']
# lista que contiene los comandos que utilizaremos
commands = ['username pirata privilege 15 password pirata\n',
            'end\n', 'write\n', 'show ip route\n']

# usuario y contraseña de administrador
username = 'admin' 
password = 'firulais' 
# diccionarios que nos servirán para saber si está directamente conectado o no
direc = {}
via = {}

list_via = []
repeated = []


max_buffer = 65535
# Función clear buffer
def clear_buffer(connection):
    if connection.recv_ready():
        return connection.recv(max_buffer)

for device in gateway: 
    print("\nEntrando por la puerta de enlace: ", device, "\nEmpezando configuración...")
    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        conexion = connection.connect(device, username=username, password=password, look_for_keys=False, allow_agent=False)     
    except:
        print("Conexion NO exitosa con: \n", conexion)
        continue
    new_connection = connection.invoke_shell()
    output = clear_buffer(new_connection)
    new_connection.send("terminal length 0\n")
    time.sleep(3)
    output = clear_buffer(new_connection)
    new_connection.send("configure terminal\n")
    time.sleep(2)
    # Sacamos el router en el que nos posicionamos
    prompt = output.decode('utf-8')
    R = prompt.split('#')
    # ubicamos el índice de la letra R
    ri = R[0].index("R") 
    # seleccionamos la cadena para sacar la letra R
    router = R[0][ri:]
    if router in repeated:
        print("Router " + router + " ya analizado\n")
    else:
        repeated.append(router)
        print("Configurando router: " + router)
        output = clear_buffer(new_connection)
        for command in commands:
            new_connection.send(command)
            time.sleep(2)
            output = new_connection.recv(max_buffer)
        rows = output.decode('utf-8').splitlines()
        print(rows)        
        for line in rows:
            if 'via' in line:
                conexion = line.split('via ')[1].split(',')
                # descartamos las IP que tengan la palabra via
                if conexion[0] not in gateway:
                    gateway.append(conexion[0])
                if conexion[0] not in list_via:
                    list_via.append(conexion[0])
                via[device] = list_via

            if 'directly' in line:
                ip = line.split(' ')
                if ip[7] in direc.keys():
                    # descartando las IP que tengan la palabra directly
                    if router not in direc[ip[7]]:
                         direc[ip[7]].append(router)  
                else: 
                    direc[ip[7]] = [router]
        # cerramos la conexion
        new_connection.close()
# imprimimos las ip y sus conexiones
for item in direc.items():
    print(item)

# Agregamos un título a el gráfico y una cabeza de flecha de una sola línea
mi_grafica = Digraph (comment = 'Red Examen 1 parcial')
mi_grafica.edge_attr.update(arrowhead = 'none')
pcs = []
conectado = []
# agregamos un identificador y recorremos el diccionario para conectar
for id in direc.keys():
    # lista de PC's que 
    pcs = id.split('.')
    # sacamos la red (148. / 8. )
    red = int(pcs[0])
    # identificador de la computadora (.56, .57, etc)
    ip_pc = int(pcs[2])
    # recorremos las direcciones que están conectadas directamente
    for r in direc[id]:
        # si la red es mayor que 9 entonces son las computadoras de GNS3
        if red > 9 :
            # si la ip de la computadora es diferente de 56 (Máquina virtual)
            if ip_pc !=56:
                mi_grafica.node("PC"+r, shape = 'box',  color="mediumblue",style='filled', fillcolor="lightblue")
                conectado = direc[id]
                # conectamos 
                i = 0
                for x in conectado:
                    mi_grafica.edge("PC"+x, conectado[i])
                    print("conecté PC"+x+" con "+ conectado[i])
                    i = i+1
            # si la ip es la máquina virtual
            else:
                mi_grafica.node("PCV", shape = 'box',  color="mediumblue",style='filled', fillcolor="lightblue")
                mi_grafica.node("Sw", shape='box3d', color="lightblue",orientation='180',style='filled', fillcolor="darkolivegreen3")
                mi_grafica.edge("PCV",'Sw')
                conectado = direc[id]
                # conectamos
                i = 0
                for x in conectado:
                    mi_grafica.edge("Sw", conectado[i])
                    print("conecté PCV con "+conectado[i])
                    i = i+1
        # si la red es la .8 conectamos los routers
        else:
        
            mi_grafica.node(r, shape = 'cylinder',style='filled', fillcolor="antiquewhite3")
            conectado = direc[id]
            if len(conectado)==2 :
                mi_grafica.edge(conectado[0], conectado[1])
            else:
                continue
# exportamos el grafico como imagen con extensión .png
mi_grafica.render("Examen 1",format = "png")
# exportamos el grafico como imagen con extensión .dot
mi_grafica.render("Examen 1",format = "dot")





        


