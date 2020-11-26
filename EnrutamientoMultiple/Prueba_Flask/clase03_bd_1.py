from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Crea una aplicación Flask, carga la configuración
# y crea el objeto SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miRed.db'
bd = SQLAlchemy(app)

# This is the database model object
class Dispositivo(bd.Model):
    __tablename__ = 'dispositivos'
    id = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(120), index=True)
    empresa = bd.Column(bd.String(40))

    def __init__(self, hostname, empresa):
        self.hostname = hostname
        self.empresa = empresa

    def __repr__(self):
        return '<Dispositivo %r>' % self.hostname


if __name__ == '__main__':
    bd.create_all()
    r1 = Dispositivo('R1', 'Cisco')
    r2 = Dispositivo('R2', 'Cisco')
    r3 = Dispositivo('R3', 'Cisco')
    r5 = Dispositivo('R5-tor', 'Juniper')
    r6 = Dispositivo('R6-edge', 'Juniper')
    bd.session.add(r1)
    bd.session.add(r2)
    bd.session.add(r3)
    bd.session.add(r5)
    bd.session.add(r6)
    bd.session.commit()

