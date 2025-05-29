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
    faltantes_estado = {}

    with driver.session() as session:
        # Nodos con propiedad 'faltante'
        for row in session.run("MATCH (p:Pieza) RETURN p.id AS id, p.faltante AS faltante"):
            nodos.add(row["id"])
            faltantes_estado[row["id"]] = row.get("faltante", False)

        # Relaciones macho->hembra
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
            relacion_info[(t, f)] = (pd, po)

    return nodos, grafo, relacion_info, faltantes_estado


# Actualizar la propiedad 'faltante' de los nodos en Neo4j
def actualizar_faltantes_en_neo4j(ids_faltantes, todos_los_ids):
    with driver.session() as session:
        session.run("MATCH (p:Pieza) SET p.faltante = false")
        for id_f in ids_faltantes:
            if id_f in todos_los_ids:
                session.run("MATCH (p:Pieza {id: $id}) SET p.faltante = true", id=id_f)


# Resolver rompecabezas irregular como árbol sin superar 4 conexiones por pieza
def resolver_rompecabezas(nodos, grafo, relacion_info):
    total = len(nodos)
    grados = defaultdict(int)
    usadas = set()
    conexiones = []

    def backtrack():
        if len(usadas) == total:
            return True
        for u in list(usadas):
            for v in grafo[u]:
                if v not in usadas and grados[u] < 4 and grados[v] < 4:
                    usadas.add(v)
                    grados[u] += 1
                    grados[v] += 1
                    conexiones.append((u, v))

                    if backtrack():
                        return True

                    conexiones.pop()
                    usadas.remove(v)
                    grados[u] -= 1
                    grados[v] -= 1
        return False

    for seed in nodos:
        usadas = {seed}
        grados = defaultdict(int)
        conexiones = []
        if backtrack():
            return conexiones

    return None


# Obtener pasos (DFS) desde una pieza específica
def obtener_pasos_desde(origen_inicial, grafo, relacion_info, faltantes_estado):
    pasos = []
    visitados = set()

    def dfs(actual):
        visitados.add(actual)
        for vecino in grafo[actual]:
            if vecino not in visitados:
                origen_con, destino_con = relacion_info[(actual, vecino)]

                origen_str = f"Pieza {actual} ({origen_con})"
                destino_str = f"Pieza {vecino} ({destino_con})"

                if faltantes_estado.get(actual, False):
                    origen_str += " FALTANTE"
                if faltantes_estado.get(vecino, False):
                    destino_str += " FALTANTE"

                pasos.append(f"{origen_str} → {destino_str}")
                dfs(vecino)

    dfs(origen_inicial)
    return pasos

# Encabezado del programa
def mostrar_encabezado():
    print(r"""
               H  E  I  N  Z
        Armado de Rompecabezas con Neo4j
    """)
    print("=" * 60)

# Ejecución principal
if __name__ == "__main__":
    mostrar_encabezado()

    nodos, grafo, relaciones, faltantes_estado = cargar_datos()
    solucion = resolver_rompecabezas(nodos, grafo, relaciones)

    if solucion:
        try:
            origen_usuario = int(input("\nIngrese el ID de la pieza desde la cual desea iniciar: "))

            faltantes_input = input("¿Falta alguna pieza? Ingrese los ID separados por coma (o deje vacío si no): ").strip()
            piezas_faltantes = set()

            if faltantes_input:
                piezas_faltantes = {int(x) for x in faltantes_input.split(",") if x.strip().isdigit()}

            # Actualiza la base según entrada del usuario
            actualizar_faltantes_en_neo4j(piezas_faltantes, nodos)

            # Recargar datos actualizados
            _, _, _, faltantes_estado = cargar_datos()

            if origen_usuario in grafo:
                print(f"\nPasos desde pieza {origen_usuario}:")
                for paso in obtener_pasos_desde(origen_usuario, grafo, relaciones, faltantes_estado):
                    print(paso)
            else:
                print("La pieza ingresada no tiene conexiones o no existe.")
        except ValueError:
            print("Entrada no válida. Debe ingresar un número de ID de pieza.")
    else:
        print("No se encontró solución")