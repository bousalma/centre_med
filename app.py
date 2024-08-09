import streamlit as st
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from snowflake.connector import connect

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

# Streamlit Functions
def show_hopitaux():
    response = requests.get("http://127.0.0.1:8000/hopitaux/")
    if response.status_code == 200:
        hopitaux = response.json()
        st.write("## Liste des hôpitaux")
        for hopital in hopitaux:
            st.write(f"ID: {hopital['HopitalID']}, Nom: {hopital['nom']}, Adresse: {hopital['address']}")
    else:
        st.error(f"Erreur lors de la récupération des hôpitaux : {response.json().get('detail')}")

def add_hopital():
    st.write("## Ajouter un Hôpital")
    name = st.text_input("Nom de l'Hôpital")
    address = st.text_input("Adresse")

    if st.button("Ajouter"):
        data = {"nom": name, "address": address}
        response = requests.post("http://127.0.0.1:8000/hopitaux/", json=data)
        if response.status_code == 200:
            st.success("Hôpital ajouté avec succès")
        else:
            st.error(f"Erreur lors de l'ajout de l'hôpital : {response.json().get('detail')}")

def show_departments():
    response = requests.get("http://127.0.0.1:8000/departments/")
    if response.status_code == 200:
        departments = response.json()
        st.write("## Liste des Départements")
        for dept in departments:
            st.write(f"ID: {dept['id']}, Nom: {dept['name']}, Emplacement: {dept['location']}")
    else:
        st.error(f"Erreur lors de la récupération des départements : {response.json().get('detail')}")

def add_department():
    st.write("## Ajouter un Département")
    name = st.text_input("Nom du Département")
    location = st.text_input("Emplacement")

    if st.button("Ajouter"):
        data = {"name": name, "location": location}
        response = requests.post("http://127.0.0.1:8000/departments/", json=data)
        if response.status_code == 200:
            st.success("Département ajouté avec succès")
        else:
            st.error(f"Erreur lors de l'ajout du département : {response.json().get('detail')}")
def get_hospital_department():
    # Fetch hospitals from Snowflake
    hospitals = SnowflakeConnectionManager.execute_query("SELECT HopitalID, nom FROM hopitaux")
    hospital_options = {nom: id for id, nom in hospitals} if hospitals else {}

    # Select hospital
    selected_hospital = st.selectbox("Nom de l'Hôpital", list(hospital_options.keys()))

    if selected_hospital:
        hospital_id = hospital_options[selected_hospital]
        
        # Fetch departments associated with the selected hospital
        response = requests.get(f"http://127.0.0.1:8000/hospital_departments/{hospital_id}")
        
        if response.status_code == 200:
            departments = response.json()
            st.write(f"## Liste des Départements pour l'Hôpital: {selected_hospital}")
            for dept in departments:
                st.write(f"ID: {dept['id']}, Nom: {dept['name']}, Emplacement: {dept['location']}")
        else:
            st.error(f"Erreur lors de la récupération des départements : {response.json().get('detail')}")

def add_hospital_department():
    st.write("## Associer un Département à un Hôpital")
    hospitals = SnowflakeConnectionManager.execute_query("SELECT HopitalID, nom FROM hopitaux")
    hospital_options = {nom: id for id, nom in hospitals} if hospitals else {}

    departments = SnowflakeConnectionManager.execute_query("SELECT id, name FROM departments")
    department_options = {name: id for id, name in departments} if departments else {}

    selected_hospital = st.selectbox("Nom de l'Hôpital", list(hospital_options.keys()))
    selected_department = st.selectbox("Nom du Département", list(department_options.keys()))

    if st.button("Associer"):
        hospital_id = hospital_options[selected_hospital]
        department_id = department_options[selected_department]

        check_query = """
            SELECT COUNT(*) FROM hospital_departments 
            WHERE hospital_id = %s AND department_id = %s
        """
        check_result = SnowflakeConnectionManager.execute_query(check_query, (hospital_id, department_id))
        
        if check_result and check_result.fetchone()[0] > 0:
            st.warning("Ce département est déjà associé à cet hôpital.")
        else:
            add_query = "INSERT INTO hospital_departments (hospital_id, department_id) VALUES (%s, %s)"
            add_result = SnowflakeConnectionManager.execute_query(add_query, (hospital_id, department_id))

            if add_result is not None:
                st.success("Département associé à l'hôpital avec succès.")
            else:
                st.error("Erreur lors de l'association du département.")
def get_chambres():
    response = requests.get("http://127.0.0.1:8000/chambres/")
   
    if response.status_code == 200:
        chambres = response.json()
        st.write("## Liste des chambres")
        for chambre in chambres:
            st.write(f"ID: {chambre.get('id')}, Department: {chambre.get('name')}, Numéro: {chambre.get('numero')}, Nombre Chambre: {chambre.get('nombre_chambre')}")
    else:
        st.error(f"Erreur lors de la récupération des chambres : {response.json().get('detail')}")


def add_chambre():
    st.write("## Ajouter une Chambre")
    
    departments = SnowflakeConnectionManager.execute_query("SELECT id, name FROM departments")
    department_options = {name: id for id, name in departments} if departments else {}

    
    selected_department = st.selectbox("Nom du Département", list(department_options.keys()))
    
    numero = st.number_input("Numéro de la Chambre", min_value=1)
    nombre_chambre = st.number_input("Nombre de Chambres", min_value=1)

    if st.button("Ajouter Chambre"):
        department_id = department_options[selected_department]
        data = {
            "department_id":department_id ,
            "numero": numero,
            "nombre_chambre": nombre_chambre
        }
        response = requests.post("http://127.0.0.1:8000/chambres/", json=data)
        if response.status_code == 200:
            st.success("Chambre ajoutée avec succès")
        else:
            st.error(f"Erreur lors de l'ajout de la chambre : {response.json().get('detail')}")

def add_lit():
    st.write("## Ajouter un Lit")
    chambres = SnowflakeConnectionManager.execute_query("SELECT id, numero FROM centre_medecine.centrem.chambres")
    chambre_options = {numero: id for id, numero in chambres} if chambres else {}
    
    selected_chambres = st.selectbox("Num du chambre", list(chambre_options.keys()))
    number = st.number_input("Numéro du Lit", min_value=1)

    if st.button("Ajouter Lit"):
        chambre_id = chambre_options[selected_chambres]
        data = {
            "chambre_id": chambre_id,  # Ensure chambre_id is an integer
            "number": int(number),  # Ensure number is an integer
            "is_occupied": False
        }
        response = requests.post("http://127.0.0.1:8000/lits/", json=data)
        if response.status_code == 200:
            st.success("Lit ajouté avec succès")
        else:
            st.error(f"Erreur lors de l'ajout du lit : {response.json().get('detail')}")


def get_lit():
    response = requests.get("http://127.0.0.1:8000/lits/")
    
    # Print or log the response content and headers
    # print("Response status code:", response.status_code)
    # print("Response content:", response.text)
    # print("Response headers:", response.headers)
    
    if response.status_code == 200:
        try:
            lits = response.json()
            st.write("## Liste des lits")
            for lit in lits:
                st.write(f"ID: {lit.get('id')}, Department: {lit.get('department_name')}, Numéro: {lit.get('numero')}, Nombre Chambre: {lit.get('nombre_chambre')}, Occupied: {lit.get('is_occupied')}")
        except ValueError as e:
            st.error(f"Erreur lors de la décodage JSON : {str(e)}")
    else:
        st.error(f"Erreur lors de la récupération des lits : {response.text}")
# Streamlit Interface
selected_option = st.sidebar.selectbox("Select an option", ["Départements", "Hôpitaux", "Gestion des Hôpitaux et Départements", "Gestion Chambre", "Gestion Lits"])

if selected_option == "Départements":
    option = st.sidebar.radio("", ["Voir Départements", "Ajouter Département"])
elif selected_option == "Hôpitaux":
    option = st.sidebar.radio("", ["Voir Hôpitaux", "Ajouter Hôpital"])
elif selected_option == "Gestion des Hôpitaux et Départements":
    option = st.sidebar.radio("", ["Associer Département à Hôpital", "list Département à Hôpital"])
elif selected_option == "Gestion Chambre":  # Removed the extra space here
    option = st.sidebar.radio("", ["Ajouter Chambre", "list chambre"])
elif selected_option == "Gestion Lits":
    option = st.sidebar.radio("", ["Ajouter Lit", "list lits"])

if option == "Voir Départements":
    show_departments()
elif option == "Ajouter Département":
    add_department()
elif option == "Voir Hôpitaux":
    show_hopitaux()
elif option == "Ajouter Hôpital":
    add_hopital()
elif option == "Associer Département à Hôpital":
    add_hospital_department()
elif option == "list Département à Hôpital":
    get_hospital_department()
elif option == "Ajouter Chambre":
    add_chambre()
elif option == "list chambre":
    get_chambres()
elif option == "Ajouter Lit":
    add_lit()
elif option == "list lits":
    get_lit()

