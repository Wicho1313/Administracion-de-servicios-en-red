from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/routers/<hostname>/interface/<int:num_interface>')
def interface(hostname, num_interface):
    return jsonify(name=hostname, interface=num_interface)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


