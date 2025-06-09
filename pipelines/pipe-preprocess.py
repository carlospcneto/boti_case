from kfp import dsl
from kfp.compiler import compiler
from google.cloud.bigquery import SchemaField
from pipelines.components.raw_components import create_table_if_exists
import pandas as pd

@dsl.pipeline(
    name='pipe-preprocess',
    description='Pipeline para criar os dados brutos no BigQuery'
)
def preprocess_pipe(
    project_id: str = 'boti-project-cpcn',    
):
    """
    Pipeline para criar as tabelas caso não existam no BigQuery.
    """

    schemas_tables = [
        {
            'dataset_id': 'raw_data',
            'table_id': 'customers',
            'schema': [
                {'name': 'customer_id', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'name', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'email', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'created_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'}
            ]        
        },
        {
            'dataset_id': 'raw_data',
            'table_id': 'orders',
            'schema': [
                {'name': 'order_id', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'customer_id', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'order_date', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
                {'name': 'product_id', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'quantity', 'type': 'INTEGER', 'mode': 'REQUIRED'},
                {'name': 'price', 'type': 'FLOAT', 'mode': 'REQUIRED'}
            ]
        },
        {
            'dataset_id': 'raw_data',
            'table_id': 'products',
            'schema': [
                {'name': 'product_id', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'name', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'description', 'type': 'STRING', 'mode': 'NULLABLE'},
                {'name': 'price', 'type': 'FLOAT', 'mode': 'REQUIRED'},
                {'name': 'dt_refe', 'type': 'STRING', 'mode': 'REQUIRED'},
            ]
        }
    ]

    for table in schemas_tables:

        create_table_op = create_table_if_exists(
            project_id=project_id,
            dataset_id=table['dataset_id'],
            table_id=table['table_id'],
            schema=table['schema']
        )

        # insert_data_op = insert_data(
        #     project_id=project_id,
        #     dataset_id=table['dataset_id'],
        #     table_id=table['table_id'],
        #     data=pd.read_csv(f'data/raw/{table['table_id']}.csv'),  # Aqui você deve passar os dados que deseja inserir
        #     end_date='{{kfp.pipeline_start_time}}'
        # )


   
if __name__ == '__main__':
    compiler.Compiler().compile(
        pipeline_func=preprocess_pipe,
        package_path='preprocess_pipe.yaml')