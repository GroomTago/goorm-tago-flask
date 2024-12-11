from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods = ['GET'])
def server_status():
    data = {'status':'ok'}
    return jsonify(data)
    
if __name__ == '__main__':
    app.run()