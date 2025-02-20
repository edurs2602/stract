from flask import Blueprint, Response
from . import views
from flasgger import swag_from

bp = Blueprint('main', __name__)

@bp.route("/")
@swag_from({
    'responses': {
        200: {
            'description': 'Retorna dados do desenvolvedor em CSV.',
            'content': {
                'text/csv': {
                    'schema': {'type': 'string'}
                }
            }
        }
    },
    'tags': ['Informações']
})
def index():
    """
    Retorna os dados do desenvolvedor (nome, email, LinkedIn) em formato CSV.
    """
    info = {
        "Nome": "Luís Eduardp",
        "Email": "contato@luiseduardo.dev.br",
        "LinkedIn": "https://www.linkedin.com/in/edurs2602/"
    }
    from io import StringIO
    import csv
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["Nome", "Email", "LinkedIn"], extrasaction='ignore')
    writer.writeheader()
    writer.writerow(info)
    return Response(output.getvalue(), mimetype="text/csv")

@bp.route("/<platform>")
@swag_from({
    'parameters': [
        {
            'name': 'platform',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Código da plataforma (ex: meta_ads, ga4, tiktok_insights)'
        }
    ],
    'responses': {
        200: {
            'description': 'Relatório CSV de anúncios para a plataforma especificada.',
            'content': {
                'text/csv': {'schema': {'type': 'string'}}
            }
        },
        404: {'description': 'Plataforma não encontrada ou sem dados.'}
    },
    'tags': ['Relatórios']
})
def platform_report(platform):
    """
    Retorna um relatório CSV onde cada linha representa um anúncio veiculado na plataforma especificada.
    As colunas incluem todos os campos de insights e o nome da conta.
    """
    insights, fields = views.get_insights_for_platform(platform)
    if not insights:
        return f"Plataforma {platform} não encontrada ou sem dados.", 404
    fieldnames = ["Platform", "Account"] + fields
    csv_data = views.generate_csv(insights, fieldnames)
    return Response(csv_data, mimetype="text/csv")

@bp.route("/<platform>/resumo")
@swag_from({
    'parameters': [
        {
            'name': 'platform',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Código da plataforma (ex: meta_ads, ga4, tiktok_insights)'
        }
    ],
    'responses': {
        200: {
            'description': 'Relatório resumido CSV para a plataforma, agregando por conta.',
            'content': {
                'text/csv': {'schema': {'type': 'string'}}
            }
        },
        404: {'description': 'Plataforma não encontrada ou sem dados.'}
    },
    'tags': ['Relatórios']
})
def platform_summary(platform):
    """
    Retorna um relatório CSV resumido para a plataforma, agregando insights por conta.
    Os valores numéricos são somados e os campos de texto ficam vazios (exceto o nome da conta).
    """
    insights, fields = views.get_insights_for_platform(platform)
    if not insights:
        return f"Plataforma {platform} não encontrada ou sem dados.", 404
    aggregated = views.aggregate_by_account(insights, fields)
    fieldnames = ["Platform", "Account"] + fields
    csv_data = views.generate_csv(aggregated, fieldnames)
    return Response(csv_data, mimetype="text/csv")

@bp.route("/geral")
@swag_from({
    'responses': {
        200: {
            'description': 'Relatório CSV com todos os anúncios de todas as plataformas.',
            'content': {
                'text/csv': {'schema': {'type': 'string'}}
            }
        },
        404: {'description': 'Nenhum dado encontrado.'}
    },
    'tags': ['Relatórios']
})
def geral_report():
    """
    Retorna um relatório CSV com todos os anúncios de todas as plataformas.
    Inclui colunas para identificar a plataforma e a conta; campos são unificados e o "Cost per Click" é calculado quando necessário.
    """
    insights, all_fields = views.get_all_insights()
    if not insights:
        return "Nenhum dado encontrado.", 404
    csv_data = views.generate_csv(insights, all_fields)
    return Response(csv_data, mimetype="text/csv")

@bp.route("/geral/resumo")
@swag_from({
    'responses': {
        200: {
            'description': 'Relatório resumido CSV com dados agregados por plataforma.',
            'content': {
                'text/csv': {'schema': {'type': 'string'}}
            }
        },
        404: {'description': 'Nenhum dado encontrado.'}
    },
    'tags': ['Relatórios']
})
def geral_summary():
    """
    Retorna um relatório CSV resumido com todos os anúncios, agregando os dados por plataforma.
    Os valores numéricos são somados e os campos de texto ficam vazios (exceto o nome da plataforma).
    """
    insights, all_fields = views.get_all_insights()
    if not insights:
        return "Nenhum dado encontrado.", 404
    aggregated = views.aggregate_by_platform(insights, all_fields)
    csv_data = views.generate_csv(aggregated, all_fields)
    return Response(csv_data, mimetype="text/csv")


