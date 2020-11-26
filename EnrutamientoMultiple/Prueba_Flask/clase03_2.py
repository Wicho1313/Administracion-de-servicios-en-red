from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Estamos en index()'

@app.route('/routers/')
def routers():
    return 'Estamos en routers()'

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


