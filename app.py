import tkinter as tk
from tkinter import ttk
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.request import urlopen
from PIL import Image, ImageTk
import io

# Obtener lista de actores desde DBpedia
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
    LIMIT 100
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return [(r["actorLabel"]["value"], r["actor"]["value"]) for r in results["results"]["bindings"]]

# Obtener detalles del actor desde Wikidata
def get_wikidata_info(actor_name):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(f"""
    SELECT ?person ?personLabel ?dob ?occupationLabel ?countryLabel ?image WHERE {{
      ?person ?label "{actor_name}"@en.
      ?person wdt:P31 wd:Q5.
      OPTIONAL {{ ?person wdt:P569 ?dob. }}
      OPTIONAL {{ ?person wdt:P106 ?occupation. }}
      OPTIONAL {{ ?person wdt:P27 ?country. }}
      OPTIONAL {{ ?person wdt:P18 ?image. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT 1
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if not results["results"]["bindings"]:
        return None
    r = results["results"]["bindings"][0]
    return {
        "Label": r.get("personLabel", {}).get("value", ""),
        "Date of birth": r.get("dob", {}).get("value", "Unknown"),
        "Occupation": r.get("occupationLabel", {}).get("value", "Unknown"),
        "Country": r.get("countryLabel", {}).get("value", "Unknown"),
        "Image": r.get("image", {}).get("value", None)
    }

# Mostrar ventana de detalles con tabla + imagen
def show_actor_details(event):
    selection = listbox.curselection()
    if not selection:
        return
    index = selection[0]
    actor_name, _ = actors_list[index]
    info = get_wikidata_info(actor_name)

    detail_window = tk.Toplevel(window)
    detail_window.title(actor_name)
    detail_window.configure(bg="#f5f5f5")
    detail_window.geometry("500x300")

    # Contenedor principal horizontal
    main_frame = tk.Frame(detail_window, bg="white", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    # Tabla de información
    table_frame = tk.Frame(main_frame, bg="white")
    table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def add_row(label, value, row):
        tk.Label(table_frame, text=label + ":", font=("Arial", 10, "bold"), bg="white", anchor="w").grid(row=row, column=0, sticky="w", pady=2)
        tk.Label(table_frame, text=value, font=("Arial", 10), bg="white", anchor="w").grid(row=row, column=1, sticky="w", pady=2)

    add_row("Name", info.get("Label", actor_name), 0)
    add_row("Date of Birth", info.get("Date of birth", "Unknown"), 1)
    add_row("Occupation", info.get("Occupation", "Unknown"), 2)
    add_row("Country", info.get("Country", "Unknown"), 3)

    # Imagen en el lateral derecho
    image_url = info.get("Image")
    if image_url:
        try:
            image_bytes = urlopen(image_url).read()
            img = Image.open(io.BytesIO(image_bytes)).resize((120, 160))
            photo = ImageTk.PhotoImage(img)

            image_label = tk.Label(main_frame, image=photo, bg="white")
            image_label.image = photo  # guardar referencia
            image_label.pack(side=tk.RIGHT, padx=10)
        except:
            pass

# Actualizar lista de actores
def update_actor_list(*args):
    country = country_var.get()
    if country not in countries:
        listbox.delete(0, tk.END)
        return
    try:
        global actors_list
        actors_list = get_actors_by_country(country)
        listbox.delete(0, tk.END)
        for actor_name, _ in actors_list:
            listbox.insert(tk.END, actor_name)
    except Exception as e:
        listbox.delete(0, tk.END)
        listbox.insert(tk.END, f"Error: {str(e)}")

# Ventana principal
window = tk.Tk()
window.title("Actores del mundo")

# Frame de filtros
filters_frame = tk.Frame(window)
filters_frame.pack(pady=10)

country_var = tk.StringVar()
age_var = tk.StringVar()
genre_var = tk.StringVar()

countries = ["United_States", "Japan", "Spain", "India", "Australia"]
ages = ["20-30", "30-40", "40-50"]
genres = ["Drama", "Action", "Comedy"]

ttk.Combobox(filters_frame, textvariable=country_var, values=countries, state="readonly").grid(row=1, column=0, padx=5)
ttk.Combobox(filters_frame, textvariable=age_var, values=ages, state="readonly").grid(row=1, column=1, padx=5)
ttk.Combobox(filters_frame, textvariable=genre_var, values=genres, state="readonly").grid(row=1, column=2, padx=5)

country_var.set("País")
age_var.set("Rango de edad")
genre_var.set("Género")

country_var.trace_add("write", update_actor_list)
age_var.trace_add("write", update_actor_list)
genre_var.trace_add("write", update_actor_list)

# Resultados con scroll
results_frame = tk.Frame(window)
results_frame.pack(pady=20)

scrollbar = tk.Scrollbar(results_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox = tk.Listbox(results_frame, width=60, height=15, yscrollcommand=scrollbar.set)
listbox.pack(side=tk.LEFT, fill=tk.BOTH)
scrollbar.config(command=listbox.yview)

listbox.bind("<<ListboxSelect>>", show_actor_details)

window.mainloop()