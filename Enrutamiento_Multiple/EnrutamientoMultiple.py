from flask import Flask, url_for, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
# importamos la función hecha para la conexion ssh
from conexionSSH import enrutar, show_ip_route

# Crea una aplicación Flask, carga la configuración
# y crea el objeto SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miRed.db'
bd = SQLAlchemy(app)

# usuario y contraseña para entrar por ssh
username = 'admin'
password = 'admin'

# Con esto creamos la base de datos con los parmámetros que necesitamos
class Dispositivo(bd.Model):
    __tablename__ = 'Dispositivos'
    id = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(64), unique=True)
    loopback = bd.Column(bd.String(120), unique=True)
    ip = bd.Column(bd.String(120), unique=True)
    
    def dame_url(disp):
        return url_for('dame_dispositivo', id=disp.id, _external=True)
    
    def exporta_datos(disp):
        return {
            'disp_url': disp.dame_url(),
            'hostname': disp.hostname,
            'loopback': disp.loopback,
            'ip': disp.ip,
        }

    def importa_datos(disp, datos):
        try:
            disp.hostname = datos['hostname']
            disp.loopback = datos['loopback']
            disp.ip = datos['ip']
        except KeyError as e:
            raise ValidationError('Invalid dispositivo: missing ' + e.args[0])
        return disp

# Con el método GET de http consultamos los dispositivos en la base de datos
# método dame_dispositivo: recibe -> vacío. D
# evuelve -> la lista de dispositivos en formato json
@app.route('/dispositivos/', methods=['GET'])
def dame_dispositivos():
    return jsonify({'dispositivos': [dispositivo.dame_url() 
                               for dispositivo in Dispositivo.query.all()]})

# Con el método GET de http consultamos la información del dispositivo ingresado en formato json
# método dame_dispositivo: 
# recibe: id de dispositivo.
# devuelve: la información del dispositivo ingresado en formato json
@app.route('/dispositivos/<int:id>', methods=['GET'])
def dame_dispositivo(id):
    return jsonify(Dispositivo.query.get_or_404(id).exporta_datos())

# Con el método GET de http llamámos al método enrutar y show_ip route del programa conexionSSH.py
# método dame_dispositivo_enrutar: 
# recibe: id de dispositivo
# devuelve: el json del comando show ip route y el enrutamiento del router 4
@app.route('/dispositivos/<int:id>/enrutar', methods=['GET'])
def dame_dispositivo_enrutar(id):
    dispositivo = Dispositivo.query.get_or_404(id)
    hostname = dispositivo.hostname
    ip = dispositivo.ip
    # si el id es el router 4, entonces lo enrutamos
    if id == 4:
        # mandamos a llamar a los métodos del programa conexionSSH.py
        resultado = enrutar(hostname, ip, username, password)
        return jsonify({"enrutado: ": str(resultado)})
    else:
        # si queremos enrutar cualquier otro dispositivo solo muestra la tabla de enrutamiento
        resultado = show_ip_route(hostname, ip, username, password)
        return jsonify({"Ya enrutado: ": str(resultado)})

# con el método GET de http solo obtenemos la tabla de enrutamiento del dispositivo dado
# método dame_dispositivo_tabla
# recibe: id de dispositivo
# devuelve: tabla de enrutamiento en formato json
@app.route('/dispositivos/<int:id>/tabla_enrutamiento', methods=['GET'])
def dame_dispositivo_tabla(id):
    dispositivo = Dispositivo.query.get_or_404(id)
    hostname = dispositivo.hostname
    ip = dispositivo.ip
    resultado = show_ip_route(hostname, ip, username, password)
    return jsonify({"Tabla de enrutamiento: ": str(resultado)})


# con el método POST de http agregamos un dispositivo nuevo
# método nuevo_ dispositivo
# recibe: vacío
# devuelve: el código 201 indicando que ha sido agregado correctamente
@app.route('/dispositivos/', methods=['POST'])
def nuevo_dispositivo():
    dispositivo = Dispositivo()
    dispositivo.importa_datos(request.json)
    bd.session.add(dispositivo)
    bd.session.commit()
    return jsonify({}), 201, {'Locacion': dispositivo.dame_url()}

# con el método PUT de http modificamos un dispositivo ya ingresado en la base de datos
# método edita_dispositivo:
# recibe: id dispositivo
# devuelve: la modificación del dispositivo en formato json
@app.route('/dispositivos/<int:id>', methods=['PUT'])
def edita_dispositivo(id):
    dispositivo = Dispositivo.query.get_or_404(id)
    dispositivo.importa_datos(request.json)
    bd.session.add(dispositivo)
    bd.session.commit()
    return jsonify({})

# método principal del programa EnrutamientoMultiple.py
if __name__ == '__main__':
    bd.create_all()
    app.run(host='0.0.0.0', debug=True)
