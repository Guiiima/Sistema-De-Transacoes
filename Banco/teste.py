import requests

#Criando clientes
#response = requests.post('http://localhost:5000/cliente/clayton/1234/500')
#response = requests.post('http://localhost:5000/cliente/claytin/1234/500')
#Editando clientes
response = requests.post('http://localhost:5000/cliente/1/250')
#response = requests.post('http://localhost:5000/cliente/2/300')
#response = requests.delete('http://localhost:5000/cliente/2')
#Criando seletores
#response = requests.post('http://localhost:5000/seletor/seletor1/123.123')
#response = requests.post('http://localhost:5000/seletor/seletor2/122.122')
#Editando seletores
#response = requests.post('http://localhost:5000/seletor/1/seletorB/111111')
#response = requests.post('http://localhost:5000/seletor/2/seletorA/222222')
#response = requests.delete('http://localhost:5000/seletor/2')

print(response.text)