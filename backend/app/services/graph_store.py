"""
MemoryVerse AI — Neo4j Knowledge Graph Store

Handles all graph node and relationship operations with Neo4j AuraDB.
Per Architecture.md §5: Neo4j is accessed strictly through this graph_store.py wrapper.
Per Rules.md §3: all queries are wrapped in specific try/except blocks with loud error handling.
Per Design.md §2: Gold color (#E8A93B) for achievements/certs, Sage (#6FA98C) for skills/projects.
"""

import logging
from typing import Optional
from neo4j import GraphDatabase, Driver

from app.config import Settings
from app.models.schemas import (
    DocumentRecord,
    DocumentCategory,
    GraphNode,
    GraphEdge,
    GraphDataResponse,
    TimelineEvent,
    TimelineResponse,
)
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

# Design.md Color Tokens
COLOR_GOLD = "#E8A93B"       # Achievements, Certifications
COLOR_SAGE = "#6FA98C"       # Skills, Projects, Technologies
COLOR_SURFACE = "#293D34"    # Organizations, Roles, General Documents
COLOR_TEXT = "#F2EFE6"       # General nodes


class GraphStoreError(Exception):
    """Custom exception for Neo4j Graph Store operations."""

    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


class GraphStore:
    """
    Neo4j AuraDB client wrapper for MemoryVerse Knowledge Graph.
    """

    def __init__(self, settings: Settings):
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
        self._driver: Optional[Driver] = None

    def _get_driver(self) -> Driver:
        """Lazy initialization of Neo4j driver."""
        if self._driver is None:
            if not self.uri or not self.password:
                raise GraphStoreError(
                    message="Neo4j connection credentials missing in settings",
                    detail="NEO4J_URI or NEO4J_PASSWORD is empty.",
                )
            try:
                self._driver = GraphDatabase.driver(
                    self.uri, auth=(self.user, self.password)
                )
                self._driver.verify_connectivity()
                logger.info("Connected successfully to Neo4j AuraDB at %s", self.uri)
            except Exception as e:
                logger.error("Failed to connect to Neo4j AuraDB: %s", str(e))
                raise GraphStoreError(
                    message="Failed to connect to Neo4j Knowledge Graph database",
                    detail=str(e),
                )
        return self._driver

    def close(self):
        """Close Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def sync_document(self, record: DocumentRecord, llm_client: Optional[LLMClient] = None) -> None:
        """
        Write a document and its extracted entities as graph nodes in Neo4j AuraDB.
        Creates MENTIONS edges between Document and Entities.
        Infers relationships with existing entities and generates LLM edge explanations.
        """
        driver = self._get_driver()

        # Color coding per Design.md
        if record.category in [DocumentCategory.CERTIFICATIONS, DocumentCategory.ACHIEVEMENTS]:
            doc_color = COLOR_GOLD
        else:
            doc_color = COLOR_SAGE

        cypher_doc = """
        MERGE (d:Document {id: $id})
        SET d.title = $title,
            d.filename = $filename,
            d.category = $category,
            d.issuer = $issuer,
            d.date = $date,
            d.summary = $summary,
            d.color = $color,
            d.updated_at = timestamp()
        """

        cypher_entity = """
        MATCH (d:Document {id: $doc_id})
        MERGE (e:Entity {name: $entity_name, type: $entity_type})
        ON CREATE SET e.id = randomUUID(), e.color = $entity_color
        MERGE (d)-[r:MENTIONS]->(e)
        ON CREATE SET r.id = randomUUID(),
                      r.explanation = $explanation
        """

        try:
            with driver.session() as session:
                # 1. Create Document Node
                session.run(
                    cypher_doc,
                    id=record.id,
                    title=record.title,
                    filename=record.filename,
                    category=record.category.value,
                    issuer=record.issuer or "",
                    date=record.date or record.uploaded_at[:10],
                    summary=record.summary or "",
                    color=doc_color,
                )

                # 2. Create Entity Nodes & MENTIONS edges
                for entity in record.entities:
                    e_color = COLOR_GOLD if entity.type.value in ["certification", "achievement"] else COLOR_SAGE
                    explanation = f"Document '{record.title}' references {entity.type.value} '{entity.name}'."
                    session.run(
                        cypher_entity,
                        doc_id=record.id,
                        entity_name=entity.name,
                        entity_type=entity.type.value,
                        entity_color=e_color,
                        explanation=explanation,
                    )

                # 3. Infer entity-to-entity & doc-to-doc relationships across shared entities
                self._infer_and_connect_shared_entities(session, record, llm_client)

                logger.info(
                    "Synced document '%s' and %d entities to Neo4j AuraDB",
                    record.title, len(record.entities),
                )
        except Exception as e:
            logger.error("Failed to sync document '%s' to Neo4j: %s", record.title, str(e))
            raise GraphStoreError(
                message="Failed to update Knowledge Graph in Neo4j",
                detail=str(e),
            )

    def _infer_and_connect_shared_entities(
        self, session, record: DocumentRecord, llm_client: Optional[LLMClient]
    ):
        """
        Find other documents/entities that share skills or technologies and create CONNECTED_TO edges.
        """
        cypher_connect = """
        MATCH (d1:Document {id: $doc_id})-[r1:MENTIONS]->(e:Entity)<-[r2:MENTIONS]-(d2:Document)
        WHERE d1.id <> d2.id
        MERGE (d1)-[rel:SHARED_CONTEXT {source: d1.id, target: d2.id, shared_entity: e.name}]->(d2)
        ON CREATE SET rel.id = randomUUID(),
                      rel.explanation = $explanation
        """

        for entity in record.entities:
            explanation = (
                f"Connected via shared {entity.type.value} '{entity.name}', "
                f"linking {record.category.value} to your broader identity record."
            )
            if llm_client:
                try:
                    llm_exp = llm_client.generate_json(
                        f"Write a single concise sentence (under 15 words) explaining how document '{record.title}' "
                        f"and other documents connecting through '{entity.name}' relate in a career portfolio.\n"
                        f"Return JSON format: {{\"explanation\": \"...\"}}"
                    )
                    explanation = llm_exp.get("explanation", explanation)
                except Exception:
                    pass

            session.run(cypher_connect, doc_id=record.id, explanation=explanation)

    def get_graph_data(self) -> GraphDataResponse:
        """
        Query all nodes and edges from Neo4j AuraDB formatted for react-force-graph rendering.
        """
        driver = self._get_driver()

        cypher_nodes = """
        MATCH (n)
        RETURN
            elementId(n) AS internal_id,
            COALESCE(n.id, elementId(n)) AS id,
            COALESCE(n.title, n.name, "Unnamed Node") AS name,
            labels(n)[0] AS type,
            n.category AS category,
            n.color AS color
        """

        cypher_edges = """
        MATCH (source)-[r]->(target)
        RETURN
            COALESCE(r.id, elementId(r)) AS id,
            COALESCE(source.id, elementId(source)) AS source,
            COALESCE(target.id, elementId(target)) AS target,
            type(r) AS relationship,
            COALESCE(r.explanation, "Connected relationship in knowledge graph") AS explanation
        """

        try:
            with driver.session() as session:
                nodes_res = session.run(cypher_nodes)
                edges_res = session.run(cypher_edges)

                nodes = []
                seen_nodes = set()
                for row in nodes_res:
                    node_id = str(row["id"])
                    if node_id in seen_nodes:
                        continue
                    seen_nodes.add(node_id)

                    node_type = row["type"] or "Entity"
                    category = row["category"]
                    color = row["color"] or (
                        COLOR_GOLD if category in ["Certifications", "Achievements"] else COLOR_SAGE
                    )

                    nodes.append(
                        GraphNode(
                            id=node_id,
                            name=row["name"] or "Unnamed Node",
                            type=node_type,
                            category=category,
                            color=color,
                            val=25 if node_type == "Document" else 15,
                            source_doc_id=node_id if node_type == "Document" else None,
                        )
                    )

                edges = []
                seen_edges = set()
                for row in edges_res:
                    edge_id = str(row["id"])
                    if edge_id in seen_edges:
                        continue
                    seen_edges.add(edge_id)

                    edges.append(
                        GraphEdge(
                            id=edge_id,
                            source=str(row["source"]),
                            target=str(row["target"]),
                            relationship=row["relationship"],
                            explanation=row["explanation"],
                        )
                    )

                return GraphDataResponse(
                    nodes=nodes,
                    edges=edges,
                    total_nodes=len(nodes),
                    total_edges=len(edges),
                )
        except Exception as e:
            logger.error("Failed to query graph data from Neo4j: %s", str(e))
            raise GraphStoreError(
                message="Failed to retrieve Knowledge Graph data",
                detail=str(e),
            )

    def get_timeline(self, doc_records: list[DocumentRecord]) -> TimelineResponse:
        """
        Generate chronological timeline events from document records.
        """
        events = []
        for doc in doc_records:
            event_date = doc.date or doc.uploaded_at[:10]
            events.append(
                TimelineEvent(
                    id=doc.id,
                    date=event_date,
                    title=doc.title,
                    category=doc.category,
                    summary=doc.summary or f"{doc.category.value} document: {doc.filename}",
                    issuer=doc.issuer,
                    document_id=doc.id,
                    entities=doc.entities,
                )
            )

        events.sort(key=lambda x: x.date, reverse=True)

        return TimelineResponse(
            events=events,
            total=len(events),
        )
