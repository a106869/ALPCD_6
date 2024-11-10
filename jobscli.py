import typer
import requests
import re

API_KEY = '71c6f8366ef375e8b61b33a56a2ce9d9'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', #engana o api a pensar que estou a aceder pro um navegador
}

def response(page): #função para fazer a requisição
    url = f'https://api.itjobs.pt/job/list.json?api_key={API_KEY}&page={page}'
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

app = typer.Typer()

@app.command()
def top(n: int):
    """ Lista os N trabalhos mais recentes publicados pela itjobs.pt"""
    #argumento opcional para csv

@app.command()
def search(n: int):
    """ Lista todos os trabalhos full-time publicados por uma determminada empresa, numa determinada região"""
    #tem que permitir inserir o número de traablhos a apresentar, caso contrário apresenta todos os trabalhos
    #argumento opcional para csv

@app.command()
def salary(job_id: int):
    """Extrai o salário de uma vaga pelo job_id."""
    page = 1
    while True:
        data = response(page)
        if 'results' not in data or not data['results']:
            print(f"Job com ID {job_id} não encontrado.")
            break
        job = None
        for job in data['results']:
            if job['id'] == job_id:
                break
        else:
            job = None
        if job:
            wage = job.get("wage")
            if wage:
                print(f"Salário: {wage}")
            else:
                body = job.get("body", "")
                wage_match = re.search(r"(\d{3,}([.,]\d{3})?\s?(€|\$|USD|£|₹))", body)
                if wage_match:
                    estimated_wage = wage_match.group(0) #group retorna as partes da string que correspondem ao padrão da repex
                    print(f"Salário: {estimated_wage}") #0 é o índice da correspondência
                else:
                    print("Salário não especificado")
            break
        page += 1

@app.command()
def skills(n:int):
    """ Quais os trabalhos que requerem uma determinada lista de skills, num determinado período de tempo"""
    #recebe a lista de skills e datas de início e de fim [skill1, skill2, skill3] dataInicial dataFinal
    #argumento opcional para csv

#para cada funcionalidade (exceto salary), deve poder exportar para CSV a informação com os campos: título, empresa, descrição, data de publicação, salário e localização
#para isso, é necessário poder adicionar um argumento opcional a cada um dos comandos

if __name__ == "__main__":
    app()