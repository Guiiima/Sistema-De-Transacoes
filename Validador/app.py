from flask import Flask
from routes import validador_blueprint

app = Flask(__name__)
app.register_blueprint(validador_blueprint)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
