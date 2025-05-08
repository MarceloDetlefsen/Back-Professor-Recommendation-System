from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "9vK@U$]73i{$")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Conexión exitosa.")
