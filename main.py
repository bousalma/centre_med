from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from snowflake.connector import connect

app = FastAPI()

# Configuration Snowflake
class SnowflakeConnectionManager:
    @staticmethod
    def connect_to_snowflake():
        try:
            conn = connect(
                user="ASAA",
                password="Maghreb1234",
                account="lsyveyx-vd01067",
                database='CENTRE_MEDECINE',
                schema='CENTREM'
            )
            print("Connexion à Snowflake réussie")
            return conn
        except Exception as e:
            print(f"Erreur lors de la connexion à Snowflake : {str(e)}")
            return None

    @staticmethod
    def execute_query(query, params=None):
        conn = SnowflakeConnectionManager.connect_to_snowflake()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
            except Exception as e:
                print(f"Erreur lors de l'exécution de la requête : {str(e)}")
                return None
            finally:
                conn.close()
        else:
            return None

# Modèles Pydantic
class Department(BaseModel):
    name: str
    location: str

class Hopital(BaseModel):
    nom: str
    address: str

class HospitalDepartmentAssociation(BaseModel):
    hospital_id: int
    department_id: int

class Chambre(BaseModel):
    department_id: int
    numero: int
    nombre_chambre: int
class Lit(BaseModel):
    id: int
    name: str
    numero: str
    nombre_chambre: str
    is_occupied: bool
# Endpoints
@app.post("/hopitaux/")
async def create_hopital(hopital: Hopital):
    query = "INSERT INTO hopitaux (nom, address) VALUES (%s, %s)"
    params = (hopital.nom, hopital.address)
    result = SnowflakeConnectionManager.execute_query(query, params)

    if result is not None:
        return {"message": "Hôpital ajouté avec succès"}
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de l'ajout de l'hôpital")

@app.get("/hopitaux/")
async def list_hopitaux():
    query = "SELECT HopitalID, nom, address FROM hopitaux"
    result = SnowflakeConnectionManager.execute_query(query)

    if result:
        hopitaux = result.fetchall()
        return [{"HopitalID": hopital[0], "nom": hopital[1], "address": hopital[2]} for hopital in hopitaux]
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des hôpitaux")

@app.post("/departments/")
async def create_department(department: Department):
    query = "INSERT INTO departments (name, location) VALUES (%s, %s)"
    params = (department.name, department.location)
    result = SnowflakeConnectionManager.execute_query(query, params)

    if result is not None:
        return {"message": "Département ajouté avec succès"}
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de l'ajout du département")

@app.get("/departments/")
async def list_departments():
    query = "SELECT id, name, location FROM departments"
    result = SnowflakeConnectionManager.execute_query(query)

    if result:
        departments = result.fetchall()
        return [{"id": dept[0], "name": dept[1], "location": dept[2]} for dept in departments]
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des départements")

@app.post("/hospital_departments/")
async def associate_department(association: HospitalDepartmentAssociation):
    hospital_id = association.hospital_id
    department_id = association.department_id

    check_query = "SELECT COUNT(*) FROM hospital_departments WHERE hospital_id = %s AND department_id = %s"
    check_result = SnowflakeConnectionManager.execute_query(check_query, (hospital_id, department_id))

    if check_result and check_result.fetchone()[0] > 0:
        raise HTTPException(status_code=400, detail="Ce département est déjà associé à cet hôpital.")
    
    add_query = "INSERT INTO hospital_departments (hospital_id, department_id) VALUES (%s, %s)"
    add_result = SnowflakeConnectionManager.execute_query(add_query, (hospital_id, department_id))

    if add_result is not None:
        return {"message": "Département associé à l'hôpital avec succès."}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de l'association du département.")

@app.get("/hospital_departments/{hopital_id}")
async def list_hospital_departments(hopital_id: int):
    query = """
        SELECT D.id, D.name, D.location 
        FROM hospital_departments AS HD 
        JOIN departments AS D ON HD.department_id = D.id 
        JOIN hopitaux AS H ON HD.hospital_id = H.HopitalID 
        WHERE H.HopitalID = %s
    """
    result = SnowflakeConnectionManager.execute_query(query, (hopital_id,))

    if result:
        departments = result.fetchall()
        return [{"id": dept[0], "name": dept[1], "location": dept[2]} for dept in departments]
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des départements")

@app.post("/chambres/")
async def create_chambre(chambre: Chambre):
    query = "INSERT INTO chambres (department_id, numero, nombre_chambre) VALUES (%s, %s, %s)"
    params = (chambre.department_id, chambre.numero, chambre.nombre_chambre)
    result = SnowflakeConnectionManager.execute_query(query, params)

    if result is not None:
        return {"message": "Chambre ajoutée avec succès"}
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de l'ajout de la chambre")

@app.get("/chambres/")
async def list_chambres():
    query = """
    SELECT C.id, D.name, C.numero, C.nombre_chambre
    FROM centre_medecine.centrem.chambres AS C
    JOIN centre_medecine.centrem.departments AS D
    ON D.id = C.department_id
    """
    result = SnowflakeConnectionManager.execute_query(query)

    if result:
        chambres = result.fetchall()
        chambre_list = [{"id": chambre[0], "name": chambre[1], "numero": chambre[2], "nombre_chambre": chambre[3]} for chambre in chambres]
        print(chambre_list)  # Log or print the result
        return chambre_list
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des chambres")


@app.post("/lits/")
async def create_lit(lit: Lit):
    query = "INSERT INTO lits (chambre_id, number, is_occupied) VALUES (%s, %s, %s)"
    params = (lit.chambre_id, lit.number, lit.is_occupied)
    result = SnowflakeConnectionManager.execute_query(query, params)

    if result is not None:
        return {"message": "Lit ajouté avec succès"}
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de l'ajout du lit")

@app.get("/lits/")
async def list_lits():
    query = """
    SELECT 
        d.name AS department_name,
        c.numero,
        c.nombre_chambre,
        l.is_occupied
    FROM 
        centre_medecine.centrem.lits l
    JOIN 
        centre_medecine.centrem.chambres c ON c.id = l.chambre_id
    JOIN 
        centre_medecine.centrem.departments d ON d.id = c.department_id
    """
    result = SnowflakeConnectionManager.execute_query(query)

    if result:
        lits = result.fetchall()
        lits_list = [
            {"id": index + 1, "department_name": lit[0], "numero": lit[1], "nombre_chambre": lit[2], "is_occupied": lit[3]} 
            for index, lit in enumerate(lits)
        ]
        return lits_list
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des lits")