"""
Search Service - Handles semantic search and vector operations
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.enhanced_agent import Agent
from app.services.llm_service import LLMService
from app.core.config import settings


class SearchService:
    """Service for handling search operations"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Generate embedding for text"""
        try:
            return await self.llm_service.generate_embedding(text, model)
        except Exception as e:
            # Fallback to mock embedding for development
            import hashlib
            hash_object = hashlib.md5(text.encode())
            hex_dig = hash_object.hexdigest()
            
            # Generate mock embedding
            embedding = [ord(c) / 255.0 for c in hex_dig[:1536]]
            # Pad to 1536 dimensions
            while len(embedding) < 1536:
                embedding.append(0.0)
            
            return embedding[:1536]
    
    async def semantic_search_agents(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int = 20,
        offset: int = 0,
        similarity_threshold: float = 0.7
    ) -> List[Agent]:
        """Perform semantic search on agents"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # For development, we'll use a simple text search
            # In production, this would use pgvector similarity search
            return await self._fallback_text_search(query, filters, limit, offset)
            
        except Exception as e:
            # Fallback to text search
            return await self._fallback_text_search(query, filters, limit, offset)
    
    async def _fallback_text_search(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int,
        offset: int
    ) -> List[Agent]:
        """Fallback text search when vector search is not available"""
        # This would be implemented with your database session
        # For now, return empty list
        return []
    
    async def _vector_search_agents(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int,
        offset: int,
        similarity_threshold: float,
        db: AsyncSession
    ) -> List[Agent]:
        """Perform vector similarity search using pgvector"""
        try:
            # Build the base query
            query_conditions = []
            
            # Add filters
            if filters.get('owner_id'):
                query_conditions.append(f"owner_id = '{filters['owner_id']}'")
            
            if filters.get('type'):
                query_conditions.append(f"type = '{filters['type']}'")
            
            if filters.get('status'):
                query_conditions.append(f"status = '{filters['status']}'")
            
            if filters.get('tags'):
                tags = filters['tags']
                if isinstance(tags, list):
                    tags_condition = " OR ".join([f"'{tag}' = ANY(tags)" for tag in tags])
                    query_conditions.append(f"({tags_condition})")
            
            # Build WHERE clause
            where_clause = ""
            if query_conditions:
                where_clause = f"WHERE {' AND '.join(query_conditions)}"
            
            # Build the vector search query
            vector_query = f"""
                SELECT *,
                       (search_vector <=> '{query_embedding}') as similarity
                FROM agents
                {where_clause}
                ORDER BY search_vector <=> '{query_embedding}'
                LIMIT {limit} OFFSET {offset}
            """
            
            # Execute query
            result = await db.execute(text(vector_query))
            rows = result.fetchall()
            
            # Convert to Agent objects
            agents = []
            for row in rows:
                if row.similarity <= (1.0 - similarity_threshold):  # pgvector uses distance, not similarity
                    agent = Agent(**{col: getattr(row, col) for col in row._fields if col != 'similarity'})
                    agents.append(agent)
            
            return agents
            
        except Exception as e:
            print(f"Vector search failed: {e}")
            return []
    
    async def update_agent_search_vector(
        self,
        agent_id: str,
        content: str,
        db: AsyncSession
    ) -> bool:
        """Update agent's search vector"""
        try:
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            # Update agent
            await db.execute(
                text("UPDATE agents SET search_vector = :embedding WHERE id = :agent_id"),
                {"embedding": embedding, "agent_id": agent_id}
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to update search vector: {e}")
            return False
    
    async def find_similar_agents(
        self,
        agent_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Agent]:
        """Find agents similar to the given agent"""
        try:
            # Get the agent's search vector
            agent_result = await db.execute(
                text("SELECT search_vector FROM agents WHERE id = :agent_id"),
                {"agent_id": agent_id}
            )
            
            agent_row = agent_result.fetchone()
            if not agent_row or not agent_row.search_vector:
                return []
            
            # Find similar agents
            similar_query = f"""
                SELECT *,
                       (search_vector <=> '{agent_row.search_vector}') as similarity
                FROM agents
                WHERE id != :agent_id
                  AND search_vector IS NOT NULL
                ORDER BY search_vector <=> '{agent_row.search_vector}'
                LIMIT {limit}
            """
            
            result = await db.execute(text(similar_query), {"agent_id": agent_id})
            rows = result.fetchall()
            
            # Convert to Agent objects
            agents = []
            for row in rows:
                agent = Agent(**{col: getattr(row, col) for col in row._fields if col != 'similarity'})
                agents.append(agent)
            
            return agents
            
        except Exception as e:
            print(f"Find similar agents failed: {e}")
            return []
    
    async def search_agents_by_tags(
        self,
        tags: List[str],
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0
    ) -> List[Agent]:
        """Search agents by tags"""
        try:
            # Build tag search conditions
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(f"'{tag}' = ANY(tags)")
            
            tags_where = " OR ".join(tag_conditions)
            
            query = f"""
                SELECT *
                FROM agents
                WHERE {tags_where}
                ORDER BY created_at DESC
                LIMIT {limit} OFFSET {offset}
            """
            
            result = await db.execute(text(query))
            rows = result.fetchall()
            
            # Convert to Agent objects
            agents = []
            for row in rows:
                agent = Agent(**{col: getattr(row, col) for col in row._fields})
                agents.append(agent)
            
            return agents
            
        except Exception as e:
            print(f"Tag search failed: {e}")
            return []
    
    async def get_search_suggestions(
        self,
        query: str,
        db: AsyncSession,
        limit: int = 5
    ) -> List[str]:
        """Get search suggestions based on query"""
        try:
            # Simple implementation - search for agent names and descriptions
            suggestion_query = f"""
                SELECT DISTINCT name
                FROM agents
                WHERE name ILIKE '%{query}%'
                   OR description ILIKE '%{query}%'
                ORDER BY name
                LIMIT {limit}
            """
            
            result = await db.execute(text(suggestion_query))
            rows = result.fetchall()
            
            suggestions = [row.name for row in rows]
            
            # Add tag suggestions
            tag_query = f"""
                SELECT DISTINCT unnest(tags) as tag
                FROM agents
                WHERE unnest(tags) ILIKE '%{query}%'
                ORDER BY tag
                LIMIT {limit - len(suggestions)}
            """
            
            if len(suggestions) < limit:
                tag_result = await db.execute(text(tag_query))
                tag_rows = tag_result.fetchall()
                suggestions.extend([row.tag for row in tag_rows])
            
            return suggestions[:limit]
            
        except Exception as e:
            print(f"Get search suggestions failed: {e}")
            return []
    
    async def index_agent_content(
        self,
        agent: Agent,
        db: AsyncSession
    ) -> bool:
        """Index agent content for search"""
        try:
            # Combine searchable content
            content_parts = [
                agent.name,
                agent.description or "",
                agent.prompt or "",
                " ".join(agent.tags or [])
            ]
            
            content = " ".join(filter(None, content_parts))
            
            # Generate and update search vector
            return await self.update_agent_search_vector(
                str(agent.id),
                content,
                db
            )
            
        except Exception as e:
            print(f"Index agent content failed: {e}")
            return False
