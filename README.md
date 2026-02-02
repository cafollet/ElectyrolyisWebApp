# Quantum Chemistry Web Application

A full-stack web application for computing molecular ground state energies using quantum computing methods. Built with React + TypeScript frontend and Flask backend, leveraging quantum algorithms (VQE and SQD) for quantum chemistry simulations.

## Overview

This application enables:
- Building molecular structures using an interactive interface
- Run quantum chemistry simulations using VQE (Variational Quantum Eigensolver) or SQD (Sample-based Quantum Diagonalization)
- Visualize energy landscapes and simulation results
- Calculate adsorption energies for molecular interactions
- Track job status in real-time with WebSocket updates

## Architecture

### Backend (Python/Flask)
- **API Framework**: Flask with Flask-RESTX for RESTful API
- **Real-time Updates**: Flask-SocketIO for WebSocket communication
- **Task Queue**: Celery with Redis for async job processing
- **Database**: SQLAlchemy with SQLite for job management
- **Quantum Libraries**: 
  - PennyLane for VQE simulations
  - Qiskit with SQD addon for quantum diagonalization
  - PySCF for molecular calculations
  - JAX for automatic differentiation

### Frontend (React/TypeScript)
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **Styling**: Tailwind CSS
- **Charts**: Recharts for energy visualization
- **Build Tool**: Vite
- **Icons**: Lucide React

## Features

### Molecule Builder
- Interactive atom input system
- Preset molecular structures (H₂, H₂O, NH₃, CH₄, etc.)
- Support for custom molecular geometries
- Coordinate input in Angstroms

### Simulation Methods

#### VQE (Variational Quantum Eigensolver)
- Quantum circuit-based optimization
- Multiple fermion-to-qubit mappings:
  - Jordan-Wigner
  - Bravyi-Kitaev
  - Parity
- Configurable ansatz depth and convergence criteria
- Support for classical and quantum simulators

#### SQD (Sample-based Quantum Diagonalization)
- Efficient for larger molecular systems
- Configurable sample budgets
- Support for IBM Quantum hardware via API
- Automated error mitigation

### Results Visualization
- Energy convergence plots
- Molecular property display
- Job status tracking
- Historical results viewing

## Getting Started

### Prerequisites

#### Backend
- Python 3.10 or higher
- Redis (for Celery task queue)

#### Frontend
- Node.js 18 or higher
- npm or yarn

### Installation

#### 1. Clone the repository
```bash
git clone <repository-url>
cd ElectyrolyisWebApp
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

#### 3. Install Quantum Chemistry Package

```bash
# From project root
pip install -e .
```

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env
# Configure API endpoint in .env
```

### Running the Application

#### Start Redis
```bash
redis-server
```

#### Start Celery Worker
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

#### Start Backend Server
```bash
cd backend
python run.py
```

Backend will be available at: `http://localhost:5000`

#### Start Frontend Development Server
```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Project Structure

```
ElectyrolyisWebApp/
├── backend/                    # Flask backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   ├── molecules.py   # Molecule management
│   │   │   ├── simulation.py  # Simulation endpoints
│   │   │   └── routes.py      # Route registration
│   │   ├── models/            # Data models
│   │   │   ├── job.py         # Job model
│   │   │   └── schemas.py     # Marshmallow schemas
│   │   ├── services/          # Business logic
│   │   │   ├── job_manager.py
│   │   │   └── simulation_service.py
│   │   └── utils/             # Helper functions
│   ├── tests/                 # Backend tests
│   ├── requirements.txt
│   └── run.py
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── common/        # Reusable UI components
│   │   │   ├── layout/        # Layout components
│   │   │   ├── molecules/     # Molecule builder
│   │   │   └── simulation/    # Simulation components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── api/               # API client
│   │   ├── types/             # TypeScript types
│   │   └── utils/             # Utility functions
│   ├── package.json
│   └── vite.config.ts
├── quantum_chemistry/          # Core quantum chemistry package
│   ├── solvers/               # Quantum solvers
│   │   ├── vqe.py            # VQE implementation
│   │   ├── sqd.py            # SQD implementation
│   │   └── base.py           # Base solver class
│   ├── molecule.py           # Molecule wrapper
│   ├── simulator.py          # Main simulator interface
│   ├── config.py             # Configuration dataclasses
│   ├── mappings.py           # Fermion mappings
│   └── tests/                # Unit tests
└── pyproject.toml            # Python package configuration
```

## Configuration

### Backend Environment Variables (.env)
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=sqlite:///quantum_jobs.db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
IBM_QUANTUM_API_KEY=your-ibm-api-key  # Optional, for hardware access
```

### Frontend Environment Variables (.env)
```env
VITE_API_URL=http://localhost:5000/api/v1
```

## Running Tests

### Backend Tests
```bash
cd backend
pytest
```

### Quantum Chemistry Package Tests
```bash
pytest quantum_chemistry/tests/
```

## API Documentation

Once the backend is running, interactive API documentation is available at:
- Swagger UI: `http://localhost:5000/api/v1/doc`
- OpenAPI Spec: `http://localhost:5000/api/v1/swagger.json`

## Key API Endpoints

- `POST /api/v1/molecules/validate` - Validate molecular structure
- `POST /api/v1/simulation/start` - Start new simulation
- `GET /api/v1/simulation/job/{job_id}` - Get job status
- `GET /api/v1/simulation/results/{job_id}` - Get simulation results
- `GET /api/v1/simulation/history` - List all jobs

## Simulation Methods Details

### VQE (Variational Quantum Eigensolver)
VQE is a hybrid quantum-classical algorithm that:
1. Prepares a parameterized quantum state (ansatz)
2. Measures expectation value of molecular Hamiltonian
3. Uses classical optimizer to minimize energy
4. Iterates until convergence

**Use Cases**: Small to medium molecules (up to ~20 qubits)

### SQD (Sample-based Quantum Diagonalization)
SQD improves VQE accuracy by:
1. Collecting multiple quantum samples
2. Performing classical diagonalization on subspace
3. Achieving better accuracy with fewer quantum resources

**Use Cases**: Molecules requiring high accuracy, available quantum hardware

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Callum Follett**
- Email: callum.follett@ucalgary.ca
- Institution: University of Calgary

## References

- [PennyLane Documentation](https://docs.pennylane.ai/)
- [Qiskit Documentation](https://qiskit.org/documentation/)
- [VQE Algorithm Paper](https://arxiv.org/abs/1304.3061)
- [SQD Algorithm](https://arxiv.org/abs/2104.06314)

## Known Issues

- Large molecules (>12 qubits) may require significant computation time
- IBM Quantum API rate limits apply for hardware execution
- SQD requires stable internet connection for IBM backend

## Future Enhancements

- [ ] Add more molecular presets
- [ ] Implement excited state calculations
- [ ] Export results to multiple formats
- [ ] Integration with molecular visualization tools
- [ ] Batch job submission
- [ ] User authentication and job history
- [ ] Cloud deployment configuration

