#!/usr/bin/python3
import pexpect, paramiko, time, sys
from pexpect import pxssh
# diccionario de datos con los dispositivos de prueba
devices = {'R1': {'prompt': 'R1#', 'ip': '172.16.1.20'}, 
           'R2': {'prompt': 'R2#', 'ip': '172.16.1.21'},
           'R3': {'prompt': 'R3#', 'ip': '172.16.1.22'}}
# abre el archivo de texto que contiene los comandos a ejecutar.
with open('R4_comandos.txt', 'r') as f: 
    commands = [line for line in f.readlines()]
    
max_buffer = 65535

# Función clear buffer
def clear_buffer(connection):
    if connection.recv_ready():
        return connection.recv(max_buffer)

# método enrutar aplica una serie de comandos de enrutamiento por medio de paramiko y guarda los comandos en un archivo de texto
# recibe: 'device': el nombre del dispositivo
#         'ip': dirección IP del dispositivo a enrutar
#         'username': nombre de usuario para conectarse por ssh
#         'password': contraseña del usuario para conectarse por ssh
# devuelve: 'device' el dispositivo al que nos conectamos.
#           'resultado' que es todo el texto que aparece cuandos se manda el comando
def enrutar (device, ip, username, password):
    try:
        outputFileName = device + '_salida_enrutamiento.txt'
        connection = paramiko.SSHClient()
        connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)
        new_connection = connection.invoke_shell()
        output = clear_buffer(new_connection)
        time.sleep(2)
        # new_connection.send("terminal length 0\n")
        # output = clear_buffer(new_connection)
        with open(outputFileName, 'wb') as f:
            for command in commands:
                new_connection.send(command)
                time.sleep(2)
                output = new_connection.recv(max_buffer)
                f.write(output)
        result = output.decode('utf-8').splitlines()
        new_connection.close()  
        return device, result
    except:
        print('Error interno: ', sys.exc_info())
        return 'Error en enrutar'

# método show_ip_route que hace el comando para obtener la tabla de enrutamiento por medio de pexpect
# recibe: 'device': el nombre del dispositivo
#         'ip': dirección IP del dispositivo a consultar la tabla de enrutamiento
#         'username': nombre de usuario para conectarse por ssh
#         'password': contraseña del usuario para conectarse por ssh
# devuelve: 'device' el dispositivo al que nos conectamos.
#           'resultado' que es todo el texto que aparece cuandos se manda el comando
def show_ip_route(device, ip, username, password):
    child = pxssh.pxssh()
    # iniciamos sesión
    child.login(ip, username, password, auto_prompt_reset=False)
    # enviamos cada comando de la lista
    child.sendline('show ip route list 1')
    # esperamos la etiqueta del router
    child.expect(device+'#')
    # la propiedad before guarda el texto imprimible hasta el texto esperado
    result = child.before
    # cierra la sesión
    child.logout()
    # regresa el dispositivo y el resultado
    return device, result

# programa principal para pruebas
if __name__ == '__main__':
    # lista de comandos a enviar a los routers
    commands = ['show version', 'show run']
    # el usuario y contraseña con la que accederemos a los routers
    username = 'admin'
    password = 'admin'
    # accediendo al diccionario de routers y recorriendolo
    for device in devices.keys():
        enrutar(commands, device, devices[device]['ip'], devices[device]['prompt'], username,password)

    


    
    

