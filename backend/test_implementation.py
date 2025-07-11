"""
Test script for the enhanced Agent Mesh backend
"""

import asyncio
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.core.config import settings
from app.models.enhanced_agent import Agent, BaseModel
from app.models.master_data import Skill, Constraint
from app.models.user import User
from app.services.agent_service import AgentService
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.services.observability_service import ObservabilityService


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def client(db_session):
    """Create a test client."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestLLMService:
    """Test LLM Service"""
    
    @pytest.mark.asyncio
    async def test_llm_service_initialization(self):
        """Test LLM service initialization"""
        llm_service = LLMService()
        assert llm_service is not None
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Test embedding generation"""
        llm_service = LLMService()
        
        # Test with mock embedding (fallback)
        embedding = await llm_service.generate_embedding("test text")
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # Standard embedding size
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models"""
        llm_service = LLMService()
        models = await llm_service.get_available_models()
        
        assert isinstance(models, list)
        # Should have at least some models even without API keys
        for model in models:
            assert "name" in model
            assert "provider" in model
            assert "type" in model


class TestSearchService:
    """Test Search Service"""
    
    @pytest.mark.asyncio
    async def test_search_service_initialization(self):
        """Test search service initialization"""
        search_service = SearchService()
        assert search_service is not None
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Test search service embedding generation"""
        search_service = SearchService()
        
        embedding = await search_service.generate_embedding("test search text")
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)


class TestObservabilityService:
    """Test Observability Service"""
    
    @pytest.mark.asyncio
    async def test_observability_service_initialization(self):
        """Test observability service initialization"""
        obs_service = ObservabilityService()
        assert obs_service is not None
    
    @pytest.mark.asyncio
    async def test_transaction_logging(self):
        """Test transaction logging"""
        obs_service = ObservabilityService()
        
        trace_id = "test-trace-123"
        
        # Test transaction start
        await obs_service.log_transaction_start(
            trace_id=trace_id,
            session_id="test-session",
            entity_type="agent",
            entity_id="test-agent",
            user_id="test-user",
            input_data={"message": "test"}
        )
        
        assert trace_id in obs_service.transactions
        assert obs_service.transactions[trace_id]["status"] == "started"
        
        # Test transaction end
        await obs_service.log_transaction_end(
            trace_id=trace_id,
            output_data={"response": "test response"},
            llm_usage={"tokens": 100, "model": "gpt-3.5-turbo"}
        )
        
        assert obs_service.transactions[trace_id]["status"] == "completed"
        assert "duration_seconds" in obs_service.transactions[trace_id]
    
    @pytest.mark.asyncio
    async def test_get_system_health(self):
        """Test system health check"""
        obs_service = ObservabilityService()
        
        health = await obs_service.get_system_health()
        assert "status" in health
        assert "metrics" in health
        assert "timestamp" in health


class TestAgentService:
    """Test Agent Service"""
    
    @pytest.mark.asyncio
    async def test_agent_service_initialization(self):
        """Test agent service initialization"""
        agent_service = AgentService()
        assert agent_service is not None
        assert agent_service.llm_service is not None
        assert agent_service.search_service is not None


def test_configuration():
    """Test configuration loading"""
    assert settings.PROJECT_NAME == "Agent Mesh Backend"
    assert settings.VERSION == "1.0.0"
    assert settings.AGENT_BASE_PORT == 9000
    assert settings.MAX_AGENT_PORTS == 1000


def test_api_health_check():
    """Test API health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_api_version():
    """Test API version endpoint"""
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    
    data = response.json()
    assert "version" in data
    assert data["version"] == "1.0.0"


if __name__ == "__main__":
    """Run tests directly"""
    import sys
    
    print("🧪 Running Agent Mesh Backend Tests")
    print("===================================")
    
    # Test configuration
    print("\n1. Testing Configuration...")
    test_configuration()
    print("✅ Configuration tests passed")
    
    # Test API endpoints
    print("\n2. Testing API Endpoints...")
    test_api_health_check()
    test_api_version()
    print("✅ API endpoint tests passed")
    
    # Run async tests
    print("\n3. Running Service Tests...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test LLM Service
        llm_test = TestLLMService()
        loop.run_until_complete(llm_test.test_llm_service_initialization())
        loop.run_until_complete(llm_test.test_generate_embedding())
        loop.run_until_complete(llm_test.test_get_available_models())
        print("✅ LLM Service tests passed")
        
        # Test Search Service
        search_test = TestSearchService()
        loop.run_until_complete(search_test.test_search_service_initialization())
        loop.run_until_complete(search_test.test_generate_embedding())
        print("✅ Search Service tests passed")
        
        # Test Observability Service
        obs_test = TestObservabilityService()
        loop.run_until_complete(obs_test.test_observability_service_initialization())
        loop.run_until_complete(obs_test.test_transaction_logging())
        loop.run_until_complete(obs_test.test_get_system_health())
        print("✅ Observability Service tests passed")
        
        # Test Agent Service
        agent_test = TestAgentService()
        loop.run_until_complete(agent_test.test_agent_service_initialization())
        print("✅ Agent Service tests passed")
        
    finally:
        loop.close()
    
    print("\n🎉 All tests passed!")
    print("\nNext steps:")
    print("1. Set up PostgreSQL with pgvector extension")
    print("2. Configure environment variables in .env file")
    print("3. Run database migrations: alembic upgrade head")
    print("4. Start the backend server: uvicorn main:app --reload")
    print("5. Run the full test suite: pytest")
    
    sys.exit(0)
