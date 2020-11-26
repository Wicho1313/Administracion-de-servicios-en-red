import pexpect


def show_version(device,ip, password):
    child = pexpect.spawn('telnet ' + ip)
    child.expect('Password:')
    child.sendline(password)
    child.expect(device+'>')
    child.sendline('enable')
    child.expect('Password:')
    child.sendline(password)
    child.expect(device+'#')
    child.sendline('show version | i V')
    child.expect(device+'#')
    result = child.before
    child.sendline('exit')
    return device, result

if __name__ == '__main__':
    password = 'cisco'
    print(show_version('R1', '192.168.0.6', password))
    print(show_version('R2', '192.168.0.10', password))
    print(show_version('R3', '192.168.0.14', password))
    print(show_version('R5-tor', '192.168.0.1', password))
    print(show_version('R6-edge', '192.168.0.18', password))

