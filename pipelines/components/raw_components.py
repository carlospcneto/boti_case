import os
from kfp import dsl

BASE_IMAGE = os.getenv('IMAGE_URI')

@dsl.component(
    base_image=BASE_IMAGE
)
def create_table_if_exists(project_id: str, dataset_id: str, table_id: str, schema: list):
    """
    Cria a tabela no BigQuery.
    """
    from google.cloud import bigquery
    from google.api_core.exceptions import NotFound

    client = bigquery.Client(project=project_id)

    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_id} já existe.")
    except NotFound:
        print(f"Dataset {dataset_id} não encontrado. Criando...")
        client.create_dataset(dataset_ref, exists_ok=True)
        print(f"Dataset {dataset_id} criado com sucesso.")
    
    table_ref = dataset_ref.table(table_id)
    table = bigquery.Table(table_ref, schema=schema)

    try:
        client.create_table(table, exists_ok=True)
        print(f"Tabela {table_id} criada com sucesso ou já existente.")
    except Exception as e:
        print(f"Erro ao criar a tabela {table_id}: {e}")
        raise e

# @dsl.component(
#     base_image=BASE_IMAGE
# )
# def insert_data(project_id: str, dataset_id: str, table_id: str, data, end_date: str):
#     """
#     Insere dados na tabela do BigQuery.
#     """
#     from google.cloud import bigquery
#     import pandas as pd

#     client = bigquery.Client(project=project_id)
#     table_ref = f"{project_id}.{dataset_id}.{table_id}"

#     end_date = end_date[:10]

#     data = data[data['dt_refe_crga'] == end_date]

#     data = data.drop(columns=['dt_refe_crga']).to_dict(orient='records')
   
#     errors = client.insert_rows_json(table_ref, data)
    
#     if errors:
#         print(f"Erro ao inserir dados na tabela {table_id}: {errors}")
#         raise Exception(f"Erro ao inserir dados: {errors}")
#     else:
#         print(f"Dados inseridos com sucesso na tabela {table_id}.")
