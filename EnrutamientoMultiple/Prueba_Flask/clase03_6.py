# Este ejemplo usa como referencia al código de Miguel Grinberg en Github:
# https://github.com/miguelgrinberg/oreilly-flask-apis-video/commit/98855d48f52f4dc0f9728c841bdd0645810d708e
#

from flask import Flask, url_for, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miRed.db'
bd = SQLAlchemy(app)

class ValidaError(ValueError):
    pass


class Dispositivo(bd.Model):
    __tablename__ = 'dispositivos'
    id = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(64), unique=True)
    loopback = bd.Column(bd.String(120), unique=True)
    admin_ip = bd.Column(bd.String(120), unique=True)
    rol = bd.Column(bd.String(64))
    empresa = bd.Column(bd.String(64))
    so = bd.Column(bd.String(64))

    def dame_url(dis):
        return url_for('dame_dispositivo', id=dis.id, _external=True)

    def exporta_datos(dis):
        return {
            'url': dis.dame_url(),
            'hostname': dis.hostname,
            'loopback': dis.loopback,
            'admin_ip': dis.admin_ip,
            'rol': dis.rol,
            'empresa': dis.empresa,
            'so': dis.so
        }

    def importa_datos(dis, datos):
        try:
            dis.hostname = datos['hostname']
            dis.loopback = datos['loopback']
            dis.admin_ip = datos['admin_ip']
            dis.rol = datos['rol']
            dis.empresa = datos['empresa']
            dis.so = datos['so']
        except KeyError as e:
            raise ValidaError('Dispositivo invalido: caido ' + e.args[0])
        return dis


@app.route('/dispositivos/', methods=['GET'])
def dame_dispositivos():
    return jsonify({'dispositivo': [dispositivo.dame_url() 
                               for dispositivo in Dispositivo.query.all()]})

@app.route('/dispositivos/<int:id>', methods=['GET'])
def dame_dispositivo(id):
    return jsonify(Dispositivo.query.get_or_404(id).exporta_datos())

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





