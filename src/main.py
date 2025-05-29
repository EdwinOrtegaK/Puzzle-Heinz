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
        # Nodos
        for row in session.run("MATCH (p:Pieza) RETURN p.id AS id"):
            nodos.add(row["id"])

        # Relaciones macho<->hembra
        for row in session.run("""
            MATCH (a:Pieza)-[r:CONECTA]->(b:Pieza)
            WHERE 
              (r.pieza_origen STARTS WITH 'macho' AND r.pieza_destino STARTS WITH 'hembra')
              OR
              (r.pieza_origen STARTS WITH 'hembra' AND r.pieza_destino STARTS WITH 'macho')
            RETURN a.id AS f, b.id AS t, r.pieza_origen AS po, r.pieza_destino AS pd
        """):
            f = row["f"]; t = row["t"]
            po, pd = row["po"], row["pd"]

            # Arista en ambos sentidos
            grafo[f].append(t)
            grafo[t].append(f)

            # Etiquetas para imprimir
            relacion_info[(f, t)] = (po, pd)
            # para el inverso, intercambiamos roles
            relacion_info[(t, f)] = (pd, po)

    return nodos, grafo, relacion_info


# Resolver rompecabezas irregular como árbol sin superar 4 conexiones por pieza
def resolver_rompecabezas(nodos, grafo, relacion_info):
    total = len(nodos)
    grados = defaultdict(int)
    usadas = set()
    conexiones = []

    def backtrack():
        # todos conectados → éxito
        if len(usadas) == total:
            return True

        # iterar sobre TODAS las piezas ya usadas
        for u in list(usadas):
            # tratar todas las aristas u → v
            for v in grafo[u]:
                if v not in usadas and grados[u] < 4 and grados[v] < 4:
                    # añadimos la arista al árbol
                    usadas.add(v)
                    grados[u] += 1
                    grados[v] += 1
                    conexiones.append((u, v))

                    if backtrack():
                        return True

                    # deshacer (backtrack)
                    conexiones.pop()
                    usadas.remove(v)
                    grados[u] -= 1
                    grados[v] -= 1

        return False

    # probar cada nodo como semilla
    for seed in nodos:
        usadas = {seed}
        grados = defaultdict(int)
        conexiones = []
        if backtrack():
            return conexiones

    return None


# Obtener pasos (DFS) desde una pieza específica
def obtener_pasos_desde(origen, grafo, relacion_info):
    pasos = []
    visitados = set()

    def dfs(u):
        visitados.add(u)
        for v in grafo[u]:
            if v not in visitados:
                po, pd = relacion_info.get((u, v), ("?", "?"))
                pasos.append(f"Pieza {u} ({po}) → Pieza {v} ({pd})")
                dfs(v)

    dfs(origen)
    return pasos

if __name__ == "__main__":
    nodos, grafo, relaciones = cargar_datos()
    solucion = resolver_rompecabezas(nodos, grafo, relaciones)

    if solucion:
        print("Resolucion de rompecabeza")

        # Ahora permitimos al usuario ver el subárbol desde una pieza
        try:
            origen_usuario = int(input("\nID de la pieza para ver sus conexiones de árbol: "))
            if origen_usuario in nodos:
                print(f"\nPasos desde pieza {origen_usuario}:")
                for paso in obtener_pasos_desde(origen_usuario, grafo, relaciones):
                    print(f"  {paso}")
            else:
                print("La pieza ingresada no existe en el grafo.")
        except ValueError:
            print("Entrada no válida. Debe ingresar un número entero.")
    else:
        print("No se encontró solución")
