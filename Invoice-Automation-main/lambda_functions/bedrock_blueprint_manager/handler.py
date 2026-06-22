"""
Lambda handler for managing AWS Bedrock Data Automation blueprints and projects
Creates or updates blueprints and projects based on environment configuration
Uses AWS Lambda Powertools for structured logging, tracing, and metrics
"""
import os
import json
from bedrock_helpers import get_or_create_blueprint, get_or_create_project

# AWS Lambda Powertools
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Initialize Powertools
logger = Logger(service="bedrock_blueprint_manager")
tracer = Tracer(service="bedrock_blueprint_manager")
metrics = Metrics(namespace="FreightAuditAgent", service="bedrock_blueprint_manager")


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    """
    Lambda handler for blueprint and project setup

    Environment Variables:
        BLUEPRINT_NAME: Name for Bedrock blueprint (default: freight-invoice-blueprint)
        BLUEPRINT_FILE: JSON schema file (default: bedrock_invoice_blueprint.json)
        PROJECT_NAME: Bedrock project name (default: freight-audit-project)
    """
    logger.info("Blueprint manager triggered")

    # Get configuration from environment variables
    blueprint_name = os.getenv("BLUEPRINT_NAME", "freight-invoice-blueprint")
    blueprint_file_name = os.getenv("BLUEPRINT_FILE", "bedrock_invoice_blueprint.json")
    project_name = os.getenv("PROJECT_NAME", "freight-audit-project")

    logger.append_keys(
        blueprint_name=blueprint_name,
        project_name=project_name
    )

    try:
        # Create or get the blueprint
        with tracer.provider.in_subsegment("## setup_blueprint"):
            logger.info("Setting up blueprint",
                       extra={"blueprint_file": blueprint_file_name})

            blueprint_arn = get_or_create_blueprint(blueprint_name, blueprint_file_name)

            logger.info("Blueprint setup completed",
                       extra={"blueprint_arn": blueprint_arn})
            metrics.add_metric(name="BlueprintSetupSuccess", unit=MetricUnit.Count, value=1)

        # Create or update the project with the blueprint
        with tracer.provider.in_subsegment("## setup_project"):
            logger.info("Setting up project with blueprint")

            project_response = get_or_create_project(project_name, blueprint_arn)
            project_arn = project_response.get('project', {}).get('projectArn', 'N/A')

            logger.info("Project setup completed",
                       extra={"project_arn": project_arn})
            metrics.add_metric(name="ProjectSetupSuccess", unit=MetricUnit.Count, value=1)

        logger.info("Blueprint and project setup completed successfully")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Blueprint and project setup completed successfully',
                'blueprint_name': blueprint_name,
                'blueprint_arn': blueprint_arn,
                'project_name': project_name,
                'project_arn': project_arn
            })
        }

    except FileNotFoundError as e:
        error_msg = f"Blueprint file not found: {blueprint_file_name}"
        logger.error(error_msg,
                    exc_info=True,
                    extra={"error": str(e)})
        metrics.add_metric(name="BlueprintFileNotFoundError", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'message': 'Ensure blueprint JSON file is packaged with Lambda'
            })
        }

    except Exception as e:
        error_msg = "Error during blueprint/project setup"
        logger.error(error_msg,
                    exc_info=True,
                    extra={"error": str(e)})
        metrics.add_metric(name="SetupError", unit=MetricUnit.Count, value=1)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'error_details': str(e),
                'message': 'Failed to setup blueprint and project'
            })
        }
