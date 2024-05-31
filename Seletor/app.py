from flask import Flask
from routes import seletor_blueprint

app = Flask(__name__)
app.register_blueprint(seletor_blueprint)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
