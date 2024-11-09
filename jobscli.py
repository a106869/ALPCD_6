import typer
from typing import Optional, Annotated, List
import requests #pede acesso ao api
from datetime import datetime
import json

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
def skills(skill: List[str], datainicial: str, datafinal: str):
    """ Quais os trabalhos que requerem uma determinada lista de skills, num determinado período de tempo """    
    jobs = []
    page = 1
    
    # Coleta de todos os trabalhos paginados
    while True:
        data = response(page) 
        if 'results' not in data or not data['results']:
            break
        jobs.extend(data['results']) 
        page += 1

    # Conversão de datas de entrada para objetos datetime
    datainicial = datetime.strptime(datainicial, '%Y-%m-%d')
    datafinal = datetime.strptime(datafinal, '%Y-%m-%d')
    
    # Filtragem dos trabalhos com base nas skills e nas datas de publicação
    jobs_filtered = []
    for job in jobs:
        publishedAt = job['publishedAt']
        dataApi = datetime.strptime(publishedAt.split(' ')[0], '%Y-%m-%d')
        if datainicial <= dataApi <= datafinal:
            job_skills = job.get('body', '').lower()  # Converter para minúsculas para comparação
            if all(s.lower() in job_skills for s in skill):
                jobs_filtered.append(job)

    # Preparação da saída
    output = []
    for job in jobs_filtered:
        job_info = {
            "Título": job.get('title', 'NA'),
            "Empresa": job.get('company', {}).get('name', 'NA'),
            "Descrição": job.get('body', 'NA'),
            "Data de publicação": job.get('publishedAt', 'NA'), 
            "Localização": job['locations'][0].get('name', 'NA') if job.get('locations') else 'NA', 
            "Salário": job.get('wage', 'NA')
        }
        output.append(job_info)
    
    # Impressão dos resultados
    if output:
        print(json.dumps(output, indent=4, ensure_ascii=False))
    else:
        print("Nenhum trabalho encontrado com as skills e datas especificadas.")


    #recebe a lista de skills e datas de início e de fim [skill1, skill2, skill3] dataInicial dataFinal
    #argumento opcional para csv

#para cada funcionalidade (exceto salary), deve poder exportar para CSV a informação com os campos: título, empresa, descrição, data de publicação, salário e localização
#para isso, é necessário poder adicionar um argumento opcional a cada um dos comandos

if __name__ == "__main__":
    app()
