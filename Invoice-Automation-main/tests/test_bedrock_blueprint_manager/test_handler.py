"""
Unit tests for bedrock_blueprint_manager/handler.py
Tests Lambda handler for managing AWS Bedrock blueprints and projects
"""
import pytest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch
import importlib.util

# Load the specific handler module to avoid import conflicts
handler_path = os.path.join(os.path.dirname(__file__), '../../lambda_functions/bedrock_blueprint_manager/handler.py')
spec = importlib.util.spec_from_file_location("blueprint_manager_handler", handler_path)
blueprint_manager_handler = importlib.util.module_from_spec(spec)
sys.modules['blueprint_manager_handler'] = blueprint_manager_handler
spec.loader.exec_module(blueprint_manager_handler)

lambda_handler = blueprint_manager_handler.lambda_handler


class TestLambdaHandler:
    """Test cases for lambda_handler function"""

    @patch('blueprint_manager_handler.get_or_create_project')
    @patch('blueprint_manager_handler.get_or_create_blueprint')
    def test_lambda_handler_success(
        self,
        mock_get_blueprint,
        mock_get_project,
        lambda_context,
        mock_env_vars_blueprint_manager
    ):
        """Test successful blueprint and project setup"""
        # Mock successful responses
        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"
        project_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/test-project"

        mock_get_blueprint.return_value = blueprint_arn
        mock_get_project.return_value = {
            'project': {
                'projectArn': project_arn
            }
        }

        # Execute handler
        response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Blueprint and project setup completed successfully'
        assert body['blueprint_name'] == 'test-freight-invoice-blueprint'
        assert body['blueprint_arn'] == blueprint_arn
        assert body['project_name'] == 'test-freight-audit-project'
        assert body['project_arn'] == project_arn

        # Verify helper functions were called
        mock_get_blueprint.assert_called_once_with(
            'test-freight-invoice-blueprint',
            'bedrock_invoice_blueprint.json'
        )
        mock_get_project.assert_called_once_with(
            'test-freight-audit-project',
            blueprint_arn
        )

    @patch('blueprint_manager_handler.get_or_create_blueprint')
    def test_lambda_handler_default_env_values(
        self,
        mock_get_blueprint,
        lambda_context
    ):
        """Test handler uses default values when environment variables not set"""
        # Don't set environment variables (will use defaults)
        mock_get_blueprint.return_value = "arn:aws:bedrock:us-east-1:123456789012:blueprint/default"

        with patch('handler.get_or_create_project') as mock_get_project:
            mock_get_project.return_value = {
                'project': {
                    'projectArn': 'arn:aws:bedrock:us-east-1:123456789012:data-automation-project/default'
                }
            }

            response = lambda_handler({}, lambda_context)

        # Verify defaults were used
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['blueprint_name'] == 'freight-invoice-blueprint'
        assert body['project_name'] == 'freight-audit-project'

        # Verify default blueprint file was used
        mock_get_blueprint.assert_called_once_with(
            'freight-invoice-blueprint',
            'bedrock_invoice_blueprint.json'
        )

    @patch('blueprint_manager_handler.get_or_create_blueprint')
    def test_lambda_handler_blueprint_file_not_found(
        self,
        mock_get_blueprint,
        lambda_context,
        mock_env_vars_blueprint_manager
    ):
        """Test handling of missing blueprint file"""
        # Mock FileNotFoundError
        mock_get_blueprint.side_effect = FileNotFoundError("Blueprint file not found")

        # Execute handler
        response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Blueprint file not found' in body['error']
        assert 'bedrock_invoice_blueprint.json' in body['error']

    @patch('blueprint_manager_handler.get_or_create_blueprint')
    def test_lambda_handler_blueprint_creation_error(
        self,
        mock_get_blueprint,
        lambda_context,
        mock_env_vars_blueprint_manager
    ):
        """Test handling of Bedrock API error during blueprint creation"""
        # Mock generic exception
        mock_get_blueprint.side_effect = Exception("Bedrock API error: Invalid schema")

        # Execute handler
        response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error'] == 'Error during blueprint/project setup'
        assert 'error_details' in body
        assert 'Bedrock API error' in body['error_details']

    @patch('blueprint_manager_handler.get_or_create_project')
    @patch('blueprint_manager_handler.get_or_create_blueprint')
    def test_lambda_handler_project_creation_error(
        self,
        mock_get_blueprint,
        mock_get_project,
        lambda_context,
        mock_env_vars_blueprint_manager
    ):
        """Test handling of error during project creation"""
        # Mock successful blueprint but failed project
        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"
        mock_get_blueprint.return_value = blueprint_arn
        mock_get_project.side_effect = Exception("Project creation failed")

        # Execute handler
        response = lambda_handler({}, lambda_context)

        # Assertions
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Error during blueprint/project setup' in body['error']
        assert 'Project creation failed' in body['error_details']

    @patch('blueprint_manager_handler.get_or_create_project')
    @patch('blueprint_manager_handler.get_or_create_blueprint')
    def test_lambda_handler_custom_env_vars(
        self,
        mock_get_blueprint,
        mock_get_project,
        lambda_context,
        monkeypatch
    ):
        """Test handler with custom environment variables"""
        # Set custom environment variables
        monkeypatch.setenv('BLUEPRINT_NAME', 'custom-blueprint-name')
        monkeypatch.setenv('BLUEPRINT_FILE', 'custom_blueprint_file.json')
        monkeypatch.setenv('PROJECT_NAME', 'custom-project-name')

        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/custom"
        project_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/custom"

        mock_get_blueprint.return_value = blueprint_arn
        mock_get_project.return_value = {
            'project': {
                'projectArn': project_arn
            }
        }

        # Execute handler
        response = lambda_handler({}, lambda_context)

        # Verify custom values were used
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['blueprint_name'] == 'custom-blueprint-name'
        assert body['project_name'] == 'custom-project-name'

        mock_get_blueprint.assert_called_once_with(
            'custom-blueprint-name',
            'custom_blueprint_file.json'
        )
        mock_get_project.assert_called_once_with(
            'custom-project-name',
            blueprint_arn
        )

    @patch('blueprint_manager_handler.get_or_create_project')
    @patch('blueprint_manager_handler.get_or_create_blueprint')
    def test_lambda_handler_project_response_without_arn(
        self,
        mock_get_blueprint,
        mock_get_project,
        lambda_context,
        mock_env_vars_blueprint_manager
    ):
        """Test handling of project response without ARN"""
        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"
        mock_get_blueprint.return_value = blueprint_arn

        # Mock project response without projectArn
        mock_get_project.return_value = {
            'project': {}
        }

        # Execute handler
        response = lambda_handler({}, lambda_context)

        # Should still succeed but show N/A for project ARN
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['project_arn'] == 'N/A'
