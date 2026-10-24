
from flask import Flask

# Cria a aplicação Flask
app = Flask(__name__)

# Define a rota da página inicial
@app.route("/")
def inicio():
    return "Bem-vindo ao AgroGest!"

# Inicia o servidor em modo de desenvolvimento
if __name__ == "__main__":
    app.run(debug=True)
