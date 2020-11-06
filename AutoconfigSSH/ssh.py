#!/usr/bin/python3

import getpass
import pexpect
import sys

devices = {'R1': {'router': 'R1#', 'ip': '192.168.122.65'}, 
           'R2': {'router': 'R2#', 'ip': '192.168.122.130'},
           'R3': {'router': 'R3#', 'ip': '192.168.122.138'},
           'R4': {'router': 'R4#', 'ip': '192.168.122.134'}}

commands = ['terminal length 0','conf t', 'ip domain-name adminredes.escom.ipn.mx',
            'ip ssh rsa keypair-name sshkey', 'crypto key generate rsa usage-keys label sshkey modulus 1024',
            'ip ssh v 2', 'ip ssh authentication-retries 3', 'line vty 0 15', 'login local', 'transport input ssh', 'end']
            
username = "admin"
password = "admin01"
# Starts the loop for devices
for device in devices.keys(): 
    # generamos un telnet hacia el host
    child = pexpect.spawn ('telnet ' + devices[device]['ip'], encoding = 'utf-8')
    # definimos que la salida del comando la imprima en terminal
    child.logfile = sys.stdout
    # print ("Verificar en equipo: ", devices[device]['router'])
    # al conectar telnet esperamos que el equipo entregue la linea Username
    child.expect(['Username:',pexpect.EOF], timeout=30)
    # si es asi le enviamos el usuario
    child.sendline(username)
    # si el equipo entrega la linea Password
    child.expect(['Password:', pexpect.EOF])
    # enviamos el password
    child.sendline(password)
    # recuperamos el router
    child.expect([devices[device]['router'], pexpect.EOF])
    for command in commands:
       child.sendline(command)