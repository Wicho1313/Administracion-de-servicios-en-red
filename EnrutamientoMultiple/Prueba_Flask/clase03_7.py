# la referencia a este ejemplo la encuentran en
# el código de Miguel Grinberg's en Github:
# https://github.com/miguelgrinberg/oreilly-flask-apis-video/commit/98855d48f52f4dc0f9728c841bdd0645810d708e
#

from flask import Flask, url_for, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from clase03_pexpect_1 import show_version

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miRed.db'
bd = SQLAlchemy(app)

class ValidacionError(ValueError):
    pass


class Dispositivo(bd.Model):
    __tablename__ = 'Dispositivos'
    id = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(64), unique=True)
    loopback = bd.Column(bd.String(120), unique=True)
    admin_ip = bd.Column(bd.String(120), unique=True)
    rol = bd.Column(bd.String(64))
    empresa = bd.Column(bd.String(64))
    so = bd.Column(bd.String(64))

    def dame_url(disp):
        return url_for('dame_dispositivo', id=disp.id, _external=True)

    def exporta_datos(disp):
        return {
            'disp_url': disp.dame_url(),
            'hostname': disp.hostname,
            'loopback': disp.loopback,
            'admin_ip': disp.admin_ip,
            'rol': disp.rol,
            'empresa': disp.empresa,
            'so': disp.so
        }

    def importa_datos(disp, datos):
        try:
            disp.hostname = datos['hostname']
            disp.loopback = datos['loopback']
            disp.admin_ip = datos['admin_ip']
            disp.rol = datos['rol']
            disp.empresa = datos['empresa']
            disp.so = datos['so']
        except KeyError as e:
            raise ValidationError('Invalid dispositivo: missing ' + e.args[0])
        return disp


@app.route('/dispositivos/', methods=['GET'])
def dame_dispositivos():
    return jsonify({'dispositivos': [dispositivo.dame_url() 
                               for dispositivo in Dispositivo.query.all()]})

@app.route('/dispositivos/<int:id>', methods=['GET'])
def dame_dispositivo(id):
    return jsonify(Dispositivo.query.get_or_404(id).exporta_datos())


@app.route('/dispositivos/<int:id>/version', methods=['GET'])
def dame_dispositivo_version(id):
    dispositivo = Dispositivo.query.get_or_404(id)
    hostname = dispositivo.hostname
    ip = dispositivo.admin_ip
    resultado = show_version(hostname, ip, 'cisco')
    return jsonify({"version": str(resultado)})

@app.route('/dispositivos/<dispositivo_rol>/version', methods=['GET'])
def dame_rol_version(dispositivo_rol):
    dispositivo_id_list = [dispositivo.id for dispositivo in Dispositivo.query.all() if dispositivo.rol == dispositivo_rol]
    resultado = {}
    for id in dispositivo_id_list:
        dispositivo = Dispositivo.query.get_or_404(id)
        hostname = dispositivo.hostname
        ip = dispositivo.admin_ip
        dispositivo_res = show_version(hostname, ip, 'cisco')
        resultado[hostname] = str(dispositivo_res)
    return jsonify(resultado)

@app.route('/dispositivos/', methods=['POST'])
def nuevo_dispositivo():
    dispositivo = Dispositivo()
    dispositivo.importa_datos(request.json)
    bd.session.add(dispositivo)
    bd.session.commit()
    return jsonify({}), 201, {'Locacion': dispositivo.dame_url()}

@app.route('/dispositivos/<int:id>', methods=['PUT'])
def edita_dispositivo(id):
    dispositivo = Dispositivo.query.get_or_404(id)
    dispositivo.importa_datos(request.json)
    bd.session.add(dispositivo)
    bd.session.commit()
    return jsonify({})


if __name__ == '__main__':
    bd.create_all()
    app.run(host='0.0.0.0', debug=True)





