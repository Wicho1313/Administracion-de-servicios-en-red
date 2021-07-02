from flask import Flask
app = Flask(__name__)

@app.route('/routers/<hostname>')
def router(hostname):
    return 'Estamos en el router %s' % hostname

@app.route('/routers/<hostname>/interface/<int:num_interface>')
def interface(hostname, num_interface):
    return 'Estamos en el router %s interface %d' % (hostname, num_interface)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


