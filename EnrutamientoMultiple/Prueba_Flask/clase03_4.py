from flask import Flask, url_for

app = Flask(__name__)

@app.route('/<hostname>/lista_interfaces')
def dispositivo(hostname):
    if hostname in routers:
        return 'Lista de interfaces para %s' % hostname
    else: 
        return 'Hostname invalido'

routers = ['R1', 'R2', 'R3','R5-tor','R6-edge']
for router in routers: 
    with app.test_request_context():
        print(url_for('dispositivo', hostname=router))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


