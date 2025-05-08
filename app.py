import tkinter as tk
from tkinter import ttk
from SPARQLWrapper import SPARQLWrapper, JSON


def get_actors_by_country(country):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    query = f"""
    SELECT DISTINCT ?actor ?actorLabel
    WHERE {{
        ?actor rdf:type dbo:Actor ;
               dbo:birthPlace ?place .
        ?place dbo:country dbr:{country} .
        ?actor rdfs:label ?actorLabel .
        FILTER(LANG(?actorLabel) = 'en')
    }}
    LIMIT 10
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    actors = []
    for result in results["results"]["bindings"]:
        actors.append(result["actorLabel"]["value"])
    return actors


def update_actor_list(*args):
    country = country_var.get()
    if country not in countries:
        listbox.delete(0, tk.END)
        return

    try:
        actors = get_actors_by_country(country)
        listbox.delete(0, tk.END)
        for actor in actors:
            listbox.insert(tk.END, actor)
    except Exception as e:
        listbox.delete(0, tk.END)
        listbox.insert(tk.END, f"Error: {str(e)}")


# Configurar ventana principal
window = tk.Tk()
window.title("Actores del mundo")

# Contenedor de filtros
filters_frame = tk.Frame(window)
filters_frame.pack(pady=10)

# Variables
country_var = tk.StringVar()
age_var = tk.StringVar()
genre_var = tk.StringVar()

# Listas de opciones
countries = ["United_States", "Japan", "Canada", "India", "Australia"]
ages = ["20-30", "30-40", "40-50"]
genres = ["Drama", "Action", "Comedy"]

# Country dropdown
# ttk.Label(filters_frame, text="Country:").grid(row=0, column=0)
country_dropdown = ttk.Combobox(filters_frame, textvariable=country_var, values=countries, state="readonly")
country_dropdown.set("País")
country_dropdown.grid(row=1, column=0, padx=5)

# Age dropdown
# ttk.Label(filters_frame, text="Age (not used):").grid(row=0, column=1)
age_dropdown = ttk.Combobox(filters_frame, textvariable=age_var, values=ages, state="readonly")
age_dropdown.set("Rango de edad")
age_dropdown.grid(row=1, column=1, padx=5)

# Genre dropdown
# ttk.Label(filters_frame, text="Genre (not used):").grid(row=0, column=2)
genre_dropdown = ttk.Combobox(filters_frame, textvariable=genre_var, values=genres, state="readonly")
genre_dropdown.set("Género")
genre_dropdown.grid(row=1, column=2, padx=5)

# Eventos
country_var.trace_add("write", update_actor_list)
age_var.trace_add("write", update_actor_list)
genre_var.trace_add("write", update_actor_list)

# Listbox
listbox = tk.Listbox(window, width=60, height=15)
listbox.pack(pady=20)

# Ejecutar
window.mainloop()
