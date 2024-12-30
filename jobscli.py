import typer
from typing import List, Optional
import requests #pede acesso ao api
from datetime import datetime
import json
import csv
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
def top(n: int, export_csv: bool = False):
    """ Lista os N trabalhos mais recentes publicados pela itjobs.pt """
    jobs = []
    page = 1
    while len(jobs) < n:
        data = response(page)
        jobs += data['results']
        page += 1
        if not data['results']: 
            break
    jobs = jobs[:n]
    output = exibir_output(jobs)
    if export_csv:
        exportar_csv(output)

@app.command()
def search(nome: str, localidade: str, n: Optional[int] = None, export_csv: bool = False):
    """ Lista todos os trabalhos full-time publicados por uma determinada empresa, numa determinada região. 
    Insira o nome da empresa e da localidade entre aspas para melhor funcionamento. """
    jobs_full_time = []
    page = 1 
    while True:
        data = response(page)
        if 'results' not in data or not data['results']: # verificar se a chave 'results' existe; verificar se 'results está vazio'
            break
        for job in data['results']:
            company_name = job.get('company', {}).get('name', None)  
            if company_name == nome:
                types = job.get('types', [{}]) 
                if types[0].get('name') == 'Full-time':
                    locations = job.get('locations', [{}]) 
                    if any(location.get('name', None) == localidade for location in locations):
                        jobs_full_time.append(job) 
        page += 1    
    if n is not None:
        jobs_full_time = jobs_full_time[:n]
    output = exibir_output(jobs_full_time)
    if export_csv:
        exportar_csv(output) 

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
                phones = re.search(r"\b((\+351)?(9|2)\d{2}\s?\d{3}\s?\d{3})\b", body) 
                if not phones:
                    description = company.get('description', None)
                    phones = re.search(r"\b((\+351)?(9|2)\d{2}\s?\d{3}\s?\d{3})\b", description)
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
                emails = re.search(r"\b[A-Za-z0-9._]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", body)
                if not emails:
                    description = company.get('description', None)
                    emails = re.search(r"\b[A-Za-z0-9._]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", description)
            break
        page += 1
    if emails:
        print(f"Emails disponíveis: {emails}")
    else:
        print("Nenhum email especificado.")

if __name__ == "_main_":
    app()