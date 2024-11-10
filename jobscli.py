import typer
import requests #pede acesso ao api
import re

API_KEY = '71c6f8366ef375e8b61b33a56a2ce9d9'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', #engana o api a pensar que estou a aceder pro um navegador
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
def salary(n: int):
    """ Extrai a informação relativa ao salário oferecido por uma determinado job id"""
    #mesmo que o valor seja 'wage a null'; neste caso usar expressões regulares para procurar noutros campos relevantes

@app.command()
def skills(n:int):
    """ Quais os trabalhos que requerem uma determinada lista de skills, num determinado período de tempo"""
    #recebe a lista de skills e datas de início e de fim [skill1, skill2, skill3] dataInicial dataFinal
    #argumento opcional para csv

@app.command()
def contacto(job_id:int):
    """ Extrai o número de telefone mencionado numa vaga. """
    page = 1 
    phones = None 
    while True: 
        data = response(page) 
        if 'results' not in data or not data['results']: 
            phones = None 
            break
        job = None 
        for x in data['results']: 
            if x['id'] == job_id: 
                job = x 
                break 
        if job: 
            company = job.get('company', {}) 
            phones = company.get('phone') 
            if not phones: 
                body = job.get("body", None) 
                phones = re.findall(r"\b((\+351)?(9|2)\d{2}\s?\d{3}\s?\d{3})\b", body) 
                if not phones:
                    description = company.get('description', None)
                    phones = re.findall(r"\b((\+351)?(9|2)\d{2}\s?\d{3}\s?\d{3})\b", description)
            break
        page += 1 
    if phones: 
        print(f"Telefones disponíveis: {phones}") 
    else:
        print("Nenhum número de telefone especificado.")

@app.command()
def email(job_id: int): 
    """Extrai o email mencionado numa vaga."""
    page = 1
    emails = None
    while True:
        data = response(page)
        if 'results' not in data or not data['results']:
            emails = None
            break
        job = None
        for x in data['results']:
            if x['id'] == job_id:
                job = x
                break
        if job: 
            company = job.get('company', {})
            emails = company.get('email')
            if not emails:
                body = job.get("body", None)
                emails = re.findall(r"\b[A-Za-z0-9._]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", body)
                if not emails:
                    description = company.get('description', None)
                    emails = re.findall(r"\b[A-Za-z0-9._]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", description)
            break
        page += 1
    if emails:
        print(f"Emails disponíveis: {emails}")
    else:
        print("Nenhum email especificado.")

if __name__ == "__main__":
    app()
