from flask import Flask
from routes import seletor_blueprint, validadores
import sqlite3

app = Flask(__name__)
app.register_blueprint(seletor_blueprint)


def getValidatorsFromDB():
    global validadores
    conn = sqlite3.connect('validators.db')

    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS validators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saldo REAL,
            flags INTEGER,
            validacoes INTEGER,
            transacoes_corretas INTEGER,
            hold BOOLEAN,
            hold_expires INTEGER,
            addr VARCHAR
        )
        """
    )
    cursor.execute("SELECT * FROM validators")
    data = cursor.fetchall()
    validadores = data
    print(validadores)

    conn.close()

if __name__ == '__main__':
    getValidatorsFromDB()

    app.run(host='0.0.0.0', port=5001)

