import argparse, logging, random, time, copy, json
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
import apache_beam.transforms.window as window

class GenerateSalesFn(beam.DoFn):
    def process(self, element, base_data_customers, base_data_products, data_models):
        DEFAULT_MULTIPLIER = 0.01

        while True:
            day_valor = random.randint(1, 10)            
            for client_info in base_data_customers:
                customer_id = client_info['customer_id']
                seed = client_info['seed']
                
                if (seed*day_valor)/10 > 100:
                    multipliers = data_models.get(customer_id, {})
                    for product_info in base_data_products:
                        product_id = product_info['product_id']
                        base_price = product_info['base_price']
                        campaing_impact = multipliers.get(product_id, DEFAULT_MULTIPLIER)

                        if campaing_impact * day_valor >= 0.1:
                            discount = (campaing_impact*0.5)
                            sale_price = base_price * (1.0 - discount)
                            sale = {
                                'customer_id': customer_id,
                                'product_id': product_id,
                                'product_price': sale_price,
                                'order_quantity': random.randint(1, 3)
                            }
                            yield sale
            time.sleep(360)

def convert_data_model_to_map(data_model):
    if not isinstance(data_model, list):
        return {}
    
    result = {}
    for item in data_model:
        if len(item) < 11:  # Verifica se tem customer_id + 10 produtos
            continue
        customer_id = item[0]
        products = item[1:11]  # Pega os 10 primeiros produtos
        product_map = {f'product_{i:02}': products[i] for i in range(len(products))}
        result[customer_id] = product_map
    return result

class LatestCombineFn(beam.CombineFn):
    def create_accumulator(self):
        return None

    def add_input(self, accumulator, input):
        return input

    def merge_accumulators(self, accumulators):
        return list(accumulators)[-1] if accumulators else None

    def extract_output(self, accumulator):
        return accumulator

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_topic', required=True, help='Tópico Pub/Sub de saída.')
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=pipeline_options) as p:
        # Corrigido: estava lendo tb_customers duas vezes
        base_data_customers = p | 'ReadCustomers' >> beam.io.ReadFromBigQuery(
            table='raw_data.tb_customers')
        
        base_data_products = p | 'ReadProducts' >> beam.io.ReadFromBigQuery(
            table='raw_data.tb_products')  # Assumindo que o nome correto é tb_products

        latest_modifier_map = (
            p
            | 'ReadModifierTopic' >> beam.io.ReadFromPubSub(
                topic='projects/boti-project-cpcn/topics/data_model')
            | 'DecodeModifierMsg' >> beam.Map(lambda msg: json.loads(msg.decode('utf-8')))
            | 'ConvertToMap' >> beam.Map(convert_data_model_to_map)
            | 'WindowInto' >> beam.WindowInto(window.GlobalWindows())
            | 'GetLatestMap' >> beam.CombineGlobally(LatestCombineFn()).without_defaults()
        )

        generated_sales = (
            p
            | 'StartGenerator' >> beam.Create([None])
            | 'GenerateContinuously' >> beam.ParDo(
                GenerateSalesFn(),
                base_data_customers=beam.pvalue.AsList(base_data_customers),
                base_data_products=beam.pvalue.AsList(base_data_products),
                data_models=beam.pvalue.AsSingleton(latest_modifier_map, default_value={})
            )
        )

        ( 
            generated_sales
            | 'EncodeOutput' >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
            | 'WriteToOutputTopic' >> beam.io.WriteToPubSub(topic=known_args.output_topic)
        ) # type: ignore

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    main()