import typer
from typing import List, Optional
import requests #pede acesso ao api
from datetime import datetime
import json
import csv
import re
from collections import Counter
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

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

# skills de um job específico
def get_skills_from_job(job_url: str):
    response = requests.get(job_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    skills_elements = soup.find_all('a', class_='body-medium chip') #tags das skills
    skills = [skill.get_text(strip=True).lower() for skill in skills_elements] #nome das skills
    return skills

# links dos jobs na página de pesquisa
def get_job_urls(job_title: str):
    job_title = job_title.replace(" ", "-") #limpa o nome do job
    url = f"https://www.ambitionbox.com/jobs/{job_title}-jobs-prf"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    job_elements = soup.find_all('div', class_='jobsInfoCardCont') #divs com os links dos jobs
    job_urls = [f"https://www.ambitionbox.com{job.find('a')['href']}" for job in job_elements] #urls dos jobs
    return job_urls

app = typer.Typer()

@app.command()
def list_skills(job_title: str, export_csv: bool = False):
    """Listar as skills mais pedidas para um trabalho."""
    job_urls = get_job_urls(job_title)
    all_skills = []
    for url in job_urls: #para cada url, vai buscar as skills
        skills = get_skills_from_job(url)
        all_skills.extend(skills)
    skill_count = Counter(all_skills)
    sorted_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True) #ordena as skills por ordem crescente de frequência
    skills = [{"skill": skill, "count": count} for skill, count in sorted_skills]
    print(json.dumps(skills, indent=4))
    if export_csv:
        exportar_csv(skills, filename=f'lista_skills_{job_title}.csv')

if __name__ == "__main__":
    app()