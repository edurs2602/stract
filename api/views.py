import requests
from io import StringIO
import csv
from flask import current_app

def fetch_api(endpoint, params=None, use_bearer=True):
    """
    Realiza uma requisição GET para a API externa.
    
    :param endpoint: Caminho do endpoint (ex: "/platforms").
    :param params: Parâmetros da query string.
    :param use_bearer: Se True, inclui o token global no header.
    :return: JSON decodificado ou None em caso de erro.
    """
    base_url = current_app.config.get('BASE_API_URL')
    url = f"{base_url}{endpoint}"
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Flask-App'
    }
    if use_bearer:
        token = current_app.config.get('TOKEN')
        if token:
            headers['Authorization'] = f"Bearer {token}"
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()
        except Exception:
            return None
    return None

def get_platforms():
    """
    Obtém a lista de plataformas disponíveis (/platforms).
    
    :return: Lista de plataformas.
    """
    data = fetch_api("/platforms", params=None, use_bearer=True)
    if data and "platforms" in data:
        return data["platforms"]
    return []

def get_accounts(platform):
    """
    Obtém as contas de uma determinada plataforma (/accounts).
    
    :param platform: Código da plataforma.
    :return: Lista de contas.
    """
    accounts = []
    page = 1
    while True:
        params = {'platform': platform, 'page': page}
        data = fetch_api("/accounts", params=params, use_bearer=True)
        if not data:
            break
        new_accounts = data.get("accounts", [])
        if not new_accounts:
            break
        accounts.extend(new_accounts)
        pagination = data.get("pagination", {})
        if pagination.get("current", 1) >= pagination.get("total", 1):
            break
        page += 1
    return accounts

def get_fields(platform):
    """
    Obtém os campos disponíveis para uma plataforma (/fields).
    
    :param platform: Código da plataforma.
    :return: Lista com os códigos dos campos.
    """
    fields = []
    page = 1
    while True:
        params = {'platform': platform, 'page': page}
        data = fetch_api("/fields", params=params, use_bearer=True)
        if not data:
            break
        new_fields = data.get("fields", [])
        if not new_fields:
            break
        fields.extend(new_fields)
        pagination = data.get("pagination", {})
        if pagination.get("current", 1) >= pagination.get("total", 1):
            break
        page += 1
    return [field["value"] for field in fields]

def get_insights(platform, account, fields, account_token):
    """
    Obtém os insights para uma conta específica (/insights).
    
    :param platform: Código da plataforma.
    :param account: ID da conta.
    :param fields: Lista de campos a serem extraídos.
    :param account_token: Token da conta (passado via URL).
    :return: Lista de insights.
    """
    fields_str = ",".join(fields)
    insights = []
    page = 1
    while True:
        params = {
            'platform': platform,
            'account': account,
            'token': account_token,
            'fields': fields_str,
            'page': page
        }
        # Para insights, mantém o Bearer token global e envia o token da conta via URL
        data = fetch_api("/insights", params=params, use_bearer=True)
        if not data:
            break
        new_insights = data.get("insights", [])
        if not new_insights:
            break
        insights.extend(new_insights)
        pagination = data.get("pagination", {})
        if pagination.get("current", 1) >= pagination.get("total", 1):
            break
        page += 1
    return insights

def get_insights_for_platform(platform):
    """
    Para uma determinada plataforma, obtém todas as contas, campos e insights.
    
    :param platform: Código da plataforma.
    :return: Tuple com a lista de insights (com nome da conta e plataforma) e a lista de campos.
    """
    accounts = get_accounts(platform)
    fields = get_fields(platform)
    all_insights = []
    for account in accounts:
        account_id = account.get("id")
        account_token = account.get("token")
        account_name = account.get("name")
        insights = get_insights(platform, account_id, fields, account_token)
        for insight in insights:
            insight["Account"] = account_name
            insight["Platform"] = platform
            all_insights.append(insight)
    return all_insights, fields

def aggregate_by_account(insights, fields):
    """
    Agrega os insights por conta, somando os valores numéricos e deixando os campos de texto vazios (exceto o nome da conta).
    
    :param insights: Lista de insights.
    :param fields: Lista de campos.
    :return: Lista agregada.
    """
    aggregated = {}
    for row in insights:
        account = row.get("Account")
        if account not in aggregated:
            agg_row = {"Platform": row.get("Platform"), "Account": account}
            for field in fields:
                value = row.get(field)
                agg_row[field] = 0 if isinstance(value, (int, float)) else ""
            aggregated[account] = agg_row
        for field in fields:
            value = row.get(field)
            if isinstance(value, (int, float)):
                aggregated[account][field] += value
    return list(aggregated.values())

def get_all_insights():
    """
    Obtém insights de todas as plataformas disponíveis e unifica os campos.
    Calcula o "Cost per Click" para a plataforma ga4, se aplicável.
    
    :return: Tuple com a lista de insights e a lista completa de campos.
    """
    insights_all = []
    platforms = get_platforms()
    all_fields = set()
    for platform_obj in platforms:
        platform_value = platform_obj.get("value")
        ins, fields = get_insights_for_platform(platform_value)
        insights_all.extend(ins)
        all_fields.update(fields)
    all_fields = list(all_fields)
    all_fields = ["Platform", "Account"] + all_fields
    for row in insights_all:
        if row.get("Platform") == "ga4":
            spend = row.get("spend") or row.get("Spend") or 0
            clicks = row.get("clicks") or row.get("Clicks") or 0
            try:
                row["Cost per Click"] = float(spend) / float(clicks) if clicks else 0
            except Exception:
                row["Cost per Click"] = 0
            if "Cost per Click" not in all_fields:
                all_fields.append("Cost per Click")
    return insights_all, all_fields

def aggregate_by_platform(insights, all_fields):
    """
    Agrega os insights de todas as plataformas, somando os valores numéricos e deixando os campos de texto vazios (exceto o nome da plataforma).
    
    :param insights: Lista de insights.
    :param all_fields: Lista de campos.
    :return: Lista agregada.
    """
    aggregated = {}
    for row in insights:
        platform = row.get("Platform")
        if platform not in aggregated:
            agg_row = {"Platform": platform}
            for field in all_fields:
                if field == "Platform":
                    continue
                value = row.get(field, "")
                agg_row[field] = 0 if isinstance(value, (int, float)) else ""
            aggregated[platform] = agg_row
        for field in all_fields:
            if field == "Platform":
                continue
            value = row.get(field, "")
            if isinstance(value, (int, float)):
                aggregated[platform][field] += value
    return list(aggregated.values())

def generate_csv(rows, fieldnames):
    """
    Gera um CSV a partir de uma lista de dicionários e de uma lista de cabeçalhos.
    Campos extras são ignorados.
    
    :param rows: Lista de dicionários com os dados.
    :param fieldnames: Lista de cabeçalhos.
    :return: String com o conteúdo CSV.
    """
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()

