"""
Unit tests for bedrock_blueprint_manager/bedrock_helpers.py
Tests helper functions for AWS Bedrock Data Automation blueprint and project management
"""
import pytest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add lambda function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda_functions/bedrock_blueprint_manager'))

from bedrock_helpers import (
    read_json_as_str,
    create_blueprint,
    get_or_create_blueprint,
    get_or_create_project
)
from tests.fixtures.sample_responses import (
    get_bedrock_list_blueprints_response,
    get_bedrock_create_blueprint_response,
    get_bedrock_list_projects_response,
    get_bedrock_create_project_response
)


class TestReadJsonAsStr:
    """Test cases for read_json_as_str function"""

    def test_read_json_as_str_success(self):
        """Test successfully reading JSON file and converting to string"""
        # Create temporary JSON file
        test_data = {"field1": "value1", "field2": "value2"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file_path = f.name

        try:
            result = read_json_as_str(temp_file_path)

            # Verify result is string and contains expected data
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert parsed_result == test_data
        finally:
            os.unlink(temp_file_path)

    def test_read_json_as_str_file_not_found(self):
        """Test handling of non-existent file"""
        with pytest.raises(FileNotFoundError):
            read_json_as_str("non_existent_file.json")

    def test_read_json_as_str_invalid_json(self):
        """Test handling of invalid JSON file"""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("This is not valid JSON {invalid}")
            temp_file_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                read_json_as_str(temp_file_path)
        finally:
            os.unlink(temp_file_path)


class TestCreateBlueprint:
    """Test cases for create_blueprint function"""

    @patch('bedrock_helpers.bda_client')
    def test_create_blueprint_success(self, mock_bda_client):
        """Test successful blueprint creation"""
        mock_bda_client.create_blueprint.return_value = get_bedrock_create_blueprint_response()

        schema_str = json.dumps({"field": "value"})
        response = create_blueprint("test-blueprint", schema_str)

        # Verify API was called correctly
        mock_bda_client.create_blueprint.assert_called_once_with(
            blueprintName="test-blueprint",
            type='DOCUMENT',
            blueprintStage='LIVE',
            schema=schema_str
        )

        # Verify response structure
        assert 'blueprint' in response
        assert response['blueprint']['blueprintName'] == "test-blueprint"

    @patch('bedrock_helpers.bda_client')
    def test_create_blueprint_api_error(self, mock_bda_client):
        """Test handling of Bedrock API error during blueprint creation"""
        mock_bda_client.create_blueprint.side_effect = Exception("Bedrock API error")

        schema_str = json.dumps({"field": "value"})

        with pytest.raises(Exception) as exc_info:
            create_blueprint("test-blueprint", schema_str)

        assert "Bedrock API error" in str(exc_info.value)


class TestGetOrCreateBlueprint:
    """Test cases for get_or_create_blueprint function"""

    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_blueprint_existing(self, mock_bda_client):
        """Test getting existing blueprint"""
        mock_bda_client.list_blueprints.return_value = get_bedrock_list_blueprints_response()

        blueprint_arn = get_or_create_blueprint(
            "test-freight-invoice-blueprint",
            "bedrock_invoice_blueprint.json"
        )

        # Should return existing blueprint ARN
        assert "test-freight-invoice-blueprint" in blueprint_arn
        assert blueprint_arn.startswith("arn:aws:bedrock:")

        # Should only call list_blueprints, not create
        mock_bda_client.list_blueprints.assert_called_once()
        mock_bda_client.create_blueprint.assert_not_called()

    @patch('bedrock_helpers.read_json_as_str')
    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_blueprint_create_new(self, mock_bda_client, mock_read_json):
        """Test creating new blueprint when it doesn't exist"""
        # Mock empty list (blueprint doesn't exist)
        mock_bda_client.list_blueprints.return_value = {"blueprints": []}
        mock_bda_client.create_blueprint.return_value = get_bedrock_create_blueprint_response()
        mock_read_json.return_value = json.dumps({"field": "value"})

        blueprint_arn = get_or_create_blueprint(
            "new-blueprint",
            "blueprint_file.json"
        )

        # Should create new blueprint
        assert "new-blueprint" in blueprint_arn
        mock_bda_client.list_blueprints.assert_called_once()
        mock_bda_client.create_blueprint.assert_called_once()
        mock_read_json.assert_called_once_with("blueprint_file.json")

    @patch('bedrock_helpers.read_json_as_str')
    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_blueprint_file_not_found(self, mock_bda_client, mock_read_json):
        """Test handling of missing blueprint file"""
        mock_bda_client.list_blueprints.return_value = {"blueprints": []}
        mock_read_json.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError):
            get_or_create_blueprint("new-blueprint", "missing_file.json")


class TestGetOrCreateProject:
    """Test cases for get_or_create_project function"""

    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_project_create_new(self, mock_bda_client):
        """Test creating new project when it doesn't exist"""
        # Mock empty list (project doesn't exist)
        mock_bda_client.list_data_automation_projects.return_value = {"projects": []}
        mock_bda_client.create_data_automation_project.return_value = get_bedrock_create_project_response()

        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"
        response = get_or_create_project("new-project", blueprint_arn)

        # Verify create was called
        mock_bda_client.create_data_automation_project.assert_called_once()
        call_kwargs = mock_bda_client.create_data_automation_project.call_args[1]

        assert call_kwargs['projectName'] == "new-project"
        assert call_kwargs['projectStage'] == 'LIVE'
        assert 'standardOutputConfiguration' in call_kwargs
        assert 'customOutputConfiguration' in call_kwargs
        assert call_kwargs['customOutputConfiguration']['blueprints'][0]['blueprintArn'] == blueprint_arn

        # Verify update was not called
        mock_bda_client.update_data_automation_project.assert_not_called()

        # Verify response structure
        assert 'project' in response

    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_project_update_existing(self, mock_bda_client):
        """Test updating existing project"""
        # Mock existing project
        mock_bda_client.list_data_automation_projects.return_value = get_bedrock_list_projects_response()
        mock_bda_client.update_data_automation_project.return_value = get_bedrock_create_project_response()

        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"
        response = get_or_create_project("test-freight-audit-project", blueprint_arn)

        # Verify update was called, not create
        mock_bda_client.update_data_automation_project.assert_called_once()
        mock_bda_client.create_data_automation_project.assert_not_called()

        # Verify update parameters
        call_kwargs = mock_bda_client.update_data_automation_project.call_args[1]
        assert 'projectArn' in call_kwargs
        assert 'customOutputConfiguration' in call_kwargs

    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_project_with_custom_stage(self, mock_bda_client):
        """Test creating project with custom stage"""
        mock_bda_client.list_data_automation_projects.return_value = {"projects": []}
        mock_bda_client.create_data_automation_project.return_value = get_bedrock_create_project_response()

        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"
        response = get_or_create_project("new-project", blueprint_arn, bda_project_stage='DEVELOPMENT')

        # Verify custom stage was used
        call_kwargs = mock_bda_client.create_data_automation_project.call_args[1]
        assert call_kwargs['projectStage'] == 'DEVELOPMENT'

    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_project_api_error(self, mock_bda_client):
        """Test handling of Bedrock API error"""
        mock_bda_client.list_data_automation_projects.side_effect = Exception("Bedrock API error")

        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"

        with pytest.raises(Exception) as exc_info:
            get_or_create_project("new-project", blueprint_arn)

        assert "Bedrock API error" in str(exc_info.value)

    @patch('bedrock_helpers.bda_client')
    def test_get_or_create_project_output_configuration(self, mock_bda_client):
        """Test that output configuration is correctly structured"""
        mock_bda_client.list_data_automation_projects.return_value = {"projects": []}
        mock_bda_client.create_data_automation_project.return_value = get_bedrock_create_project_response()

        blueprint_arn = "arn:aws:bedrock:us-east-1:123456789012:blueprint/test-blueprint"
        response = get_or_create_project("new-project", blueprint_arn)

        call_kwargs = mock_bda_client.create_data_automation_project.call_args[1]

        # Verify standard output configuration
        std_config = call_kwargs['standardOutputConfiguration']
        assert 'document' in std_config
        assert 'extraction' in std_config['document']
        assert 'generativeField' in std_config['document']
        assert std_config['document']['generativeField']['state'] == 'ENABLED'

        # Verify custom output configuration includes blueprint
        custom_config = call_kwargs['customOutputConfiguration']
        assert 'blueprints' in custom_config
        assert len(custom_config['blueprints']) == 1
        assert custom_config['blueprints'][0]['blueprintArn'] == blueprint_arn
        assert custom_config['blueprints'][0]['blueprintStage'] == 'LIVE'

        # Verify override configuration
        override_config = call_kwargs['overrideConfiguration']
        assert 'document' in override_config
        assert 'splitter' in override_config['document']
        assert override_config['document']['splitter']['state'] == 'ENABLED'
