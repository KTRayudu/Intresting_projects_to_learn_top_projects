"""
Helper functions for AWS Bedrock Data Automation blueprint and project management
Handles blueprint creation, versioning, and project configuration
"""
import boto3
from botocore.config import Config
import json
from aws_lambda_powertools import Logger

# Initialize logger as child logger
logger = Logger(service="bedrock_blueprint_manager", child=True)

# Increase timeout limits for Bedrock operations
boto_config = Config(
    connect_timeout=300,
    read_timeout=300,
)

# AWS clients
bda_client = boto3.client('bedrock-data-automation', config=boto_config)


def read_json_as_str(file_name):
    """
    Read JSON file and convert to string

    Args:
        file_name: Name of JSON file to read

    Returns:
        str: JSON content as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    logger.debug("Reading JSON file", extra={"file_name": file_name})

    with open(file_name, 'r') as file:
        blueprint_schema = json.load(file)
        schema_string = json.dumps(blueprint_schema)

    logger.debug("Successfully read JSON file",
                extra={"file_name": file_name, "size": len(schema_string)})
    return schema_string


def create_blueprint(blueprint_name, schema_str):
    """
    Create a new Bedrock Data Automation blueprint

    Args:
        blueprint_name: Name for the blueprint
        schema_str: JSON schema as string

    Returns:
        dict: Response from create_blueprint API
    """
    logger.info("Creating new blueprint", extra={"blueprint_name": blueprint_name})

    response = bda_client.create_blueprint(
        blueprintName=blueprint_name,
        type='DOCUMENT',
        blueprintStage='LIVE',
        schema=schema_str
    )

    blueprint_arn = response.get('blueprint', {}).get('blueprintArn', 'N/A')
    logger.info("Blueprint created successfully",
               extra={
                   "blueprint_name": blueprint_name,
                   "blueprint_arn": blueprint_arn
               })

    return response


def get_or_create_blueprint(blueprint_name, blueprint_file_name):
    """
    Get existing blueprint or create new one if it doesn't exist

    Args:
        blueprint_name: Name of the blueprint
        blueprint_file_name: JSON file containing blueprint schema

    Returns:
        str: Blueprint ARN
    """
    logger.info("Checking for existing blueprint", extra={"blueprint_name": blueprint_name})

    blueprint_arn = ""
    all_blueprint_response = bda_client.list_blueprints(blueprintStageFilter='LIVE')

    for item in all_blueprint_response.get('blueprints', []):
        if blueprint_name in item['blueprintName']:
            blueprint_arn = item['blueprintArn']
            logger.info("Found existing blueprint",
                       extra={
                           "blueprint_name": blueprint_name,
                           "blueprint_arn": blueprint_arn
                       })
            break

    if blueprint_arn == "":
        logger.info("Blueprint not found, creating new one",
                   extra={"blueprint_name": blueprint_name})

        blueprint_schema = read_json_as_str(blueprint_file_name)
        blueprint_response = create_blueprint(blueprint_name, blueprint_schema)
        blueprint_arn = blueprint_response['blueprint']['blueprintArn']

    return blueprint_arn


def get_or_create_project(bda_project_name, blueprint_arn, bda_project_stage='LIVE'):
    """
    Check if a data automation project exists, create it if it doesn't, or update it if it does

    Args:
        bda_project_name: Name of the data automation project
        blueprint_arn: ARN of the blueprint to add to the project
        bda_project_stage: Stage of the project (default: 'LIVE')

    Returns:
        dict: Response from create_data_automation_project or update_data_automation_project
    """
    logger.info("Checking for existing project", extra={"project_name": bda_project_name})

    # Standard output configuration
    standard_output_configuration = {
        'document': {
            'extraction': {
                'granularity': {'types': ['DOCUMENT']},
                'boundingBox': {'state': 'DISABLED'}
            },
            'generativeField': {'state': 'ENABLED'},
            'outputFormat': {
                'textFormat': {'types': ['MARKDOWN']},
                'additionalFileFormat': {'state': 'ENABLED'}
            }
        }
    }

    # Custom output configuration with blueprint
    custom_output_configuration = {
        'blueprints': [
            {
                'blueprintArn': blueprint_arn,
                'blueprintStage': 'LIVE'
            }
        ]
    }

    # Override configuration
    override_configuration = {
        'document': {
            'splitter': {
                'state': 'ENABLED'
            }
        }
    }

    # Check if project exists
    list_project_response = bda_client.list_data_automation_projects(projectStageFilter=bda_project_stage)
    project = next((project for project in list_project_response.get('projects', [])
                   if project['projectName'] == bda_project_name), None)

    if not project:
        logger.info("Project not found, creating new project",
                   extra={"project_name": bda_project_name})

        response = bda_client.create_data_automation_project(
            projectName=bda_project_name,
            projectDescription='Freight invoice document processing combining blueprints with data projects',
            projectStage=bda_project_stage,
            standardOutputConfiguration=standard_output_configuration,
            customOutputConfiguration=custom_output_configuration,
            overrideConfiguration=override_configuration
        )

        project_arn = response.get('project', {}).get('projectArn', 'N/A')
        logger.info("Project created successfully",
                   extra={
                       "project_name": bda_project_name,
                       "project_arn": project_arn
                   })
    else:
        logger.info("Project found, updating configuration",
                   extra={
                       "project_name": bda_project_name,
                       "project_arn": project['projectArn']
                   })

        response = bda_client.update_data_automation_project(
            projectArn=project['projectArn'],
            projectStage=bda_project_stage,
            standardOutputConfiguration=standard_output_configuration,
            customOutputConfiguration=custom_output_configuration,
            overrideConfiguration=override_configuration
        )

        logger.info("Project updated successfully",
                   extra={"project_name": bda_project_name})

    return response
