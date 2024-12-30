import typer
from typing import List, Optional
import requests #pede acesso ao api
from datetime import datetime
import json
import csv
import re
from bs4 import BeautifulSoup
from collections import defaultdict

API_KEY = '71c6f8366ef375e8b61b33a56a2ce9d9'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
    }

def response(page): #função para fazer a requisição
    url = f'https://api.itjobs.pt/job/list.json?api_key={API_KEY}&page={page}'
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def exportar_csv(data, filename='jobs.csv'):
    if not data:
        return
    fieldnames = list(data[0].keys()) #ordem do cabeçalho com base no primeiro elemento
    for entry in data[1:]: #todas as chaves são incluídas, mesmo se variarem entre entradas
        for key in entry.keys():
            if key not in fieldnames:
                fieldnames.append(key)
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

def fetch_ambitionbox_data(company_name):
    """Obtém informações sobre a empresa do site AmbitionBox."""
    url = f"https://www.ambitionbox.com/overview/{company_name.replace(' ', '-').lower()}-overview"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {
            "Rating da empresa (0 a 5)": "NA",
            "Principais benefícios de trabalhar na empresa": "NA"
        }
    soup = BeautifulSoup(response.text, 'html.parser')
    rating_span = soup.select_one('div[data-testid="reviewRating"] span')
    if rating_span:
        rating = rating_span.text
    else: 
        rating = "NA"
    category_ratings_div = soup.find('div', class_='css-175oi2r flex flex-col flex-1')
    h4_elements = category_ratings_div.find_all('h4')
    if h4_elements:
        benefits = []
        for h4 in h4_elements[:3]:
            benefits += [h4.get_text()]
    return {
        "Rating da empresa (0 a 5)": rating,
        "Principais benefícios de trabalhar na empresa": benefits
    }

def fetch_indeed_data(company_name):
    """Obtém informações sobre a empresa do site Indeed."""
    url = f"https://pt.indeed.com/cmp/{company_name.replace(' ', '-').lower()}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {
            "Rating da empresa (0 a 5)": "NA",
            "Setor da empresa": "NA"
        }
    soup = BeautifulSoup(response.text, 'html.parser')
    rating_span = soup.find('span', {'aria-hidden': 'true'})
    if rating_span:
        rating = rating_span.text
    else: 
        rating = "NA"
    setor_div = soup.find('div', class_='css-vjn8gb e1wnkr790')
    if setor_div:
        setor = setor_div.text
    else: 
        setor = "NA"
    return {
        "Rating da empresa (0 a 5)": rating,
        "Setor da empresa": setor
    }

def fetch_hired_data(company_name):
    """Obtém informações sobre a empresa do site SimplyHired."""
    url = f"https://www.simplyhired.pt/company/{company_name.replace(' ', '-').lower()}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {
            "Rating da empresa (0 a 5)": "NA",
            "Setor da empresa": "NA",
            "Principais benefícios de trabalhar na empresa": "NA"
        }
    soup = BeautifulSoup(response.text, 'html.parser')
    rating_span = soup.find('span', {'aria-hidden': 'true'})
    if rating_span > 0:
        rating = rating_span.text
    else: 
        rating = "NA"

    divisoes = soup.find_all('p', class_='chakra-text css-1tluwxv')
    if divisoes:
        benefits = []
        for divisao in divisoes[:3]:
            texto = divisao.get_text(strip=True).split('"')[-1]  # Extrair apenas o texto principal
            benefits.append(texto)

    setor_div = soup.find(attrs={"data-testid": "cp-industry"}).find_next("p")
    if setor_div:
        setor = setor_div.text
    else: 
        setor = "NA"
    return {
        "Rating da empresa (0 a 5)": rating,
        "Setor da empresa": setor,
        "Principais benefícios de trabalhar na empresa": benefits
    }

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
    
@app.command()
def statistics(export_csv: bool = False):
    """Cria um ficheiro CSV com as seguintes colunas: Título, Zona, Tipo de Trabalho, Nº de Vagas."""
    statistics = defaultdict(int)  
    page = 1
    while True:
        data = response(page)
        if not data.get('results'):
            break
        for job in data['results']:
            title = job.get("title", "").lower()
            locations = job.get("locations", [])
            types = job.get("types", [])
            for location in locations:
                for job_type in types:
                    key = (title, location.get("name", ""), job_type.get("name", ""))
                    statistics[key] += 1 
        page += 1
    data_to_export = sorted(
        [{"Título": key[0], "Zona": key[1], "Tipo de Trabalho": key[2], "Nº de Vagas": count}
         for key, count in statistics.items()],
        key=lambda x: x["Título"] 
    )
    if export_csv:
        exportar_csv(data_to_export)

@app.command()
def get_job_details(job_id: int, export_csv: bool = False, indeed: bool = False, simplyhired: bool = False):
    """Retorna informações detalhadas sobre uma vaga específica pelo job_id."""
    page = 1
    job_details = None
    while True:
        data = response(page)
        if 'results' not in data or not data['results']:
            print(f"Job com ID {job_id} não encontrado.")
            break
        for job in data['results']:
            if job['id'] == job_id:
                job_details = {
                    "Título": job.get('title', 'NA'),
                    "Empresa": job.get('company', {}).get('name', 'NA'),
                    "Descrição da vaga": job.get('body', 'NA'),
                    "Data de publicação": job.get('publishedAt', 'NA'),
                    "Localização": job['locations'][0].get('name', 'NA') if job.get('locations') else 'NA',
                    "Salário": job.get('wage', 'NA'),
                    "Descrição da empresa": job.get('company', {}).get('description', 'NA')
                }
                company_name = job_details["Empresa"]
                if company_name != "NA":
                    if indeed:
                        indeed_data = fetch_indeed_data(company_name)
                        job_details.update(indeed_data)
                    elif simplyhired:
                        hired_data = fetch_hired_data(company_name)
                        job_details.update(hired_data)
                    else:
                        ambitionbox_data = fetch_ambitionbox_data(company_name)
                        job_details.update(ambitionbox_data)
                break
        if job_details:
            break
        page += 1
    if job_details:
        print(json.dumps(job_details, indent=4, ensure_ascii=False))
        if export_csv:
            exportar_csv([job_details], filename=f'job_{job_id}.csv')
    else:
        print(f"Detalhes do job com ID {job_id} não encontrados.")

if __name__ == "__main__":
    app()