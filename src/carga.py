import csv
from neo4j import GraphDatabase

uri = "neo4j+s://<TU-URI>.databases.neo4j.io"
user = "<TU-USUARIO>"
password = "<TU-CONTRASEÑA>"

driver = GraphDatabase.driver(uri, auth=(user, password))

def subir_piezas():
    with open("data/piezas.csv", newline='') as file:
        reader = csv.DictReader(file)
        with driver.session() as session:
            for row in reader:
                session.run("""
                    MERGE (p:Pieza {id: toInteger($id)})
                    SET p.label = $label
                """, id=row["id:ID"], label=row["label"])

def subir_conexiones():
    with open("data/conexiones.csv", newline='') as file:
        reader = csv.DictReader(file)
        with driver.session() as session:
            for row in reader:
                session.run("""
                    MATCH (a:Pieza {id: toInteger($from_id)}), (b:Pieza {id: toInteger($to_id)})
                    MERGE (a)-[:CONECTA {
                        pieza_origen: $po,
                        pieza_destino: $pd
                    }]->(b)
                """,
                from_id=int(row[":START_ID"]),
                to_id=int(row[":END_ID"]),
                po=row["pieza_origen"],
                pd=row["pieza_destino"]
                )

# Ejecutar
subir_piezas()
subir_conexiones()
print("✔ CSVs cargados exitosamente en Neo4j Aura.")
