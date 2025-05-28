from neo4j import GraphDatabase
from collections import defaultdict

# Conexión a Neo4j Aura
uri = "neo4j+s://<TU-URI>.databases.neo4j.io"
user = "<TU-USUARIO>"
password = "<TU-CONTRASEÑA>"

driver = GraphDatabase.driver(uri, auth=(user, password))

# Cargar piezas y conexiones desde Neo4j
def cargar_datos():
    nodos = set()
    grafo = defaultdict(list)
    relacion_info = {}

    with driver.session() as session:
        # Obtener nodos
        result_nodos = session.run("MATCH (p:Pieza) RETURN p.id AS id")
        for row in result_nodos:
            nodos.add(row["id"])

        # Obtener relaciones macho -> hembra
        result_relaciones = session.run("""
            MATCH (a:Pieza)-[r:CONECTA]->(b:Pieza)
            WHERE r.pieza_origen STARTS WITH 'macho' AND r.pieza_destino STARTS WITH 'hembra'
            RETURN a.id AS from, b.id AS to, r.pieza_origen AS pieza_origen, r.pieza_destino AS pieza_destino
        """)
        for row in result_relaciones:
            f, t = row["from"], row["to"]
            grafo[f].append(t)
            relacion_info[(f, t)] = (row["pieza_origen"], row["pieza_destino"])

    return nodos, grafo, relacion_info


# Ejecutar todo
nodos, grafo, relaciones = cargar_datos()