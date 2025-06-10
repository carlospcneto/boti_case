from google.cloud import aiplatform
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Inicializa o AI Platform com parâmetros.")
    parser.add_argument("--project", type=str, default="boti-project-cpcn", help="ID do projeto GCP")
    parser.add_argument("--region", type=str, default="us-central1", help="Região do AI Platform")
    parser.add_argument("--pipeline-root", type=str, default="gs://boti-project-cpcn/pipelines", help="Caminho raiz do pipeline no Cloud Storage")
    parser.add_argument("--service_account", type=str, help="Conta de serviço para executar o pipeline")

    args = parser.parse_args()
    aiplatform.init(
        project=args.project,
        location=args.region,
        staging_bucket=args.pipeline_root,
        service_account=args.service_account
    )

    job = aiplatform.PipelineJob(
        display_name="preprocess-pipeline",
        enable_caching=False,
        template_path="pipelines/pipe-preprocess.yaml",
        pipeline_root=args.pipeline_root,
        parameter_values={
            "project_id": args.project,
        })

    job.submit()

     



