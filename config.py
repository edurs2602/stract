import os

class Config:
    BASE_API_URL = "https://sidebar.stract.to/api"
    TOKEN = "ProcessoSeletivoStract2025"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-senha'

