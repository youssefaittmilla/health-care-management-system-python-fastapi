import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app

# Fix : importer get_db APRÈS app (évite imports circulaires)
from app.api.deps import get_db

@pytest.fixture(scope="function")
def client():
    def override_get_db():
        # Mock Session COMPLET pour tous les appels
        db = Mock(spec=Session)
        db.__enter__ = Mock(return_value=db)
        db.__aenter__ = Mock(return_value=db)
        
        # Query chain: db.query().filter().first()
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None  # Pas de patient existant
        db.query.return_value = query_mock
        
        # CRUD methods
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.delete = Mock()
        db.close = Mock()
        
        return db
    
    # Override AVANT TestClient
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
