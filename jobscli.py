import typer
from typing import List
import requests #pede acesso ao api
from datetime import datetime
import json
import csv

API_KEY = '71c6f8366ef375e8b61b33a56a2ce9d9'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', #engana o api a pensar que estou a aceder pro um navegador
}

def response(page): #função para fazer a requisição
    url = f'https://api.itjobs.pt/job/list.json?api_key={API_KEY}&page={page}'
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def exportar_csv(data, filename='jobs.csv'): 
    fieldnames = ["Título", "Empresa", "Descrição", "Data de publicação", "Localização", "Salário"]
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Dados exportados para {filename}")

def exibir_output(jobs):
    output = []
    for job in jobs:
        job_info = {
            "Título": job.get('title', 'NA'),
            "Empresa": job.get('company', {}).get('name', 'NA'),
            "Descrição": job.get('body', 'NA'),
            "Data de publicação": job.get('publishedAt', 'NA'),
            "Localização": job['locations'][0].get('name', 'NA') if job.get('locations') else 'NA',
            "Salário": job.get('wage', 'NA')
        }
        output.append(job_info)
    if output:
        print(json.dumps(output, indent=4, ensure_ascii=False))
    else:
        print("Não foram encontradas correspondências para a sua pesquisa.")
    return output

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
def skills(skill: List[str], datainicial: str, datafinal: str, export_csv: bool = False):
    """ Quais os trabalhos que requerem uma determinada lista de skills, num determinado período de tempo """    
    jobs = []
    page = 1
    while True:
        data = response(page) 
        if 'results' not in data or not data['results']:
            break
        jobs.extend(data['results']) 
        page += 1
    datainicial = datetime.strptime(datainicial, '%Y-%m-%d') # converter as datas para datetime
    datafinal = datetime.strptime(datafinal, '%Y-%m-%d')
    jobs_filtered = []
    for job in jobs:
        publishedAt = job['publishedAt']
        dataApi = datetime.strptime(publishedAt.split(' ')[0], '%Y-%m-%d')
        if datainicial <= dataApi <= datafinal:
            job_skills = job.get('body', '').lower()  # converter para minúsculas para facilitar a comparação
            if all(s.lower() in job_skills for s in skill):
                jobs_filtered.append(job)
    output = exibir_output(jobs_filtered)
    if export_csv:
        exportar_csv(output)

if __name__ == "__main__":
    app()
