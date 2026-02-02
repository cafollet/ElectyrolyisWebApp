"""
API endpoint tests.
"""

import pytest
import json


class TestAPIInfo:
    """Test API information endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get('/api/v1/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'version' in data
        assert 'endpoints' in data


class TestMoleculeEndpoints:
    """Test molecule-related endpoints."""

    def test_get_presets(self, client):
        """Test preset molecules endpoint."""
        response = client.get('/api/v1/molecules/presets')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'presets' in data
        assert 'hydrogen' in data['presets']

    def test_validate_molecule(self, client):
        """Test molecule validation."""
        molecule = {
            'name': 'Test H2',
            'atoms': [
                {'symbol': 'H', 'position': [0, 0, 0]},
                {'symbol': 'H', 'position': [0, 0, 0.74]}
            ],
            'charge': 0,
            'multiplicity': 1,
            'basis_set': 'sto-3g'
        }

        response = client.post(
            '/api/v1/molecules/validate',
            data=json.dumps(molecule),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == True
        assert data['num_electrons'] == 2

    def test_get_elements(self, client):
        """Test supported elements endpoint."""
        response = client.get('/api/v1/molecules/elements')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'elements' in data
        assert len(data['elements']) > 0


class TestSimulationEndpoints:
    """Test simulation endpoints."""

    def test_create_simulation(self, client):
        """Test creating a simulation job."""
        request_data = {
            'molecule': {
                'name': 'Hydrogen',
                'atoms': [
                    {'symbol': 'H', 'position': [0, 0, -0.69]},
                    {'symbol': 'H', 'position': [0, 0, 0.69]}
                ],
                'charge': 0,
                'multiplicity': 1,
                'basis_set': 'sto-3g'
            },
            'method': 'vqe',
            'vqe_config': {
                'num_steps': 10,
                'step_size': 0.2
            }
        }

        response = client.post(
            '/api/v1/simulations',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'job_id' in data
        assert data['status'] == 'pending'

    def test_list_simulations(self, client):
        """Test listing simulations."""
        response = client.get('/api/v1/simulations')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'jobs' in data
        assert 'total' in data

    def test_invalid_method(self, client):
        """Test error handling for invalid method."""
        request_data = {
            'molecule': {
                'atoms': [{'symbol': 'H', 'position': [0, 0, 0]}],
            },
            'method': 'invalid_method'
        }

        response = client.post(
            '/api/v1/simulations',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        assert response.status_code == 400