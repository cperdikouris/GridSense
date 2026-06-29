GridSense — Smart Power Grid Analytics Platform

GridSense is a polyglot-persistence prototype designed for the Regional Power Authority (RPA). It consolidates time-series sensor data, network topology, equipment metadata, and relational billing into a single, high-performance distributed architecture.

This platform utilizes five distinct database technologies, orchestrated by a FastAPI gateway, to reduce grid fault diagnosis times from 22 minutes down to sub-second responses.
ENVIRONMENT REQUIREMENTS

To run this project, the host machine must have the following installed:

    Docker (v24.0+ recommended)

    Docker Compose (v2.20+ recommended)

    Python 3.11+ (Only required if running scripts directly on the host)

    A properly configured .env file in the root directory containing all database credentials.

Required .env format:

Before starting, a .env file is necessary in the root folder. Do not commit this file to version control.

POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=gridsense
MONGO_URI=mongodb://root:your_secure_password@mongo:27017
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_URI=bolt://neo4j:7687
CASSANDRA_HOST=cassandra
STARTUP INSTRUCTIONS

The entire system is containerized and can be booted with a single command.

    Boot the cluster:
    From the root of the repository, run:
    docker compose up --build -d

Note: Wait approximately 60-90 seconds on the first boot for Cassandra and Neo4j to fully initialize and pass their health checks.

    Seed the databases:
    Once all containers are healthy, populate the system with the required test data by running the seed script inside the API container:
    docker compose exec api python scripts/seed.py

SERVICE ARCHITECTURE

The system consists of the following microservices:

    api (FastAPI): Port 8000. REST gateway; orchestrates all business logic and routes requests to the correct data store.

    timeseries-db (Apache Cassandra): Port 9042. Highly-available time-series storage for high-throughput smart meter sensor readings.

    graph-db (Neo4j Community): Ports 7474/7687. Property graph database storing physical network topology for sub-millisecond fault traversal.

    catalog-db (MongoDB): Port 27017. Document store for flexible, heterogeneous equipment metadata and schemas.

    billing-db (PostgreSQL): Port 5432. Relational database providing strict ACID guarantees for consumer billing, utilizing JSONB for dynamic tariff data.

    cache (Redis): Port 6379. In-memory key-value store serving high-speed dashboard telemetry with TTL expiry and Pub/Sub alerting.

EXAMPLE API CALLS (cURL)

    Graph Traversal (Neo4j):
    Simulate a failure at Substation 1 and retrieve all downstream affected nodes up to depth 6.
    curl -X GET "http://localhost:8000/grid/fault-impact/SS_001?max_depth=6" -H "Accept: application/json"

    High-Throughput Ingestion (Cassandra):
    Ingest a new voltage reading from a smart meter.
    curl -X POST "http://localhost:8000/sensors/readings" -H "Content-Type: application/json" -d '{"sensor_id": "SENSOR_1", "metric_type": "voltage", "value": 235.4, "unit": "V", "quality_flag": 0}'

    ACID Account Retrieval (PostgreSQL):
    Fetch the billing account details and current balance for a specific consumer premise.
    curl -X GET "http://localhost:8000/billing/account/PREM_10001" -H "Accept: application/json"

Note: To run the automated benchmarking suite for Part C, execute: docker compose exec api python scripts/measure.py
