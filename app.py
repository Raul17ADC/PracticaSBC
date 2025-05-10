import tkinter as tk
from tkinter import ttk
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.request import urlopen
from PIL import Image, ImageTk
import io
from datetime import datetime

# Nombres en español para los países y géneros
pais_display_to_query = {
    "Sin seleccionar": None,
    "Estados Unidos": "United_States",
    "Japón": "Japan",
    "España": "Spain",
    "India": "India",
    "Australia": "Australia"
}

genero_display_to_query = {
    "Sin seleccionar": None,
    "Acción": "Action",
    "Comedia": "Comedy",
    "Drama": "Drama",
    "Romance": "Romance",
    "Suspenso": "Thriller",
    "Aventura": "Adventure"
}


# Funciones para obtener datos de DBpedia y Wikidata
def get_actors_by_country(country):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.addCustomHttpHeader("User-Agent",
                               "ActoresDelMundo/1.0 (contacto@ejemplo.com)")
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
    return [(r["actorLabel"]["value"], r["actor"]["value"])
            for r in results["results"]["bindings"]]


def get_wikidata_info(actor_name):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.addCustomHttpHeader("User-Agent",
                               "ActoresDelMundo/1.0 (contacto@ejemplo.com)")
    sparql.setQuery(f"""
    SELECT ?person ?personLabel ?dob ?countryLabel ?image ?abstract ?genderLabel ?height ?awardLabel WHERE {{
      ?person ?label "{actor_name}"@en.
      ?person wdt:P31 wd:Q5.
      OPTIONAL {{ ?person wdt:P569 ?dob. }}
      OPTIONAL {{ ?person wdt:P27 ?country. }}
      OPTIONAL {{ ?person wdt:P18 ?image. }}
      OPTIONAL {{ ?person schema:description ?abstract FILTER(LANG(?abstract) = "es") }}
      OPTIONAL {{ ?person wdt:P21 ?gender. }}
      OPTIONAL {{ ?person wdt:P2048 ?height. }}
      OPTIONAL {{ ?person wdt:P166 ?award. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }} LIMIT 50
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if not results["results"]["bindings"]:
        return None

    r = results["results"]["bindings"][0]
    awards = {
        entry["awardLabel"]["value"]
        for entry in results["results"]["bindings"] if "awardLabel" in entry
    }

    return {
        "Nombre": r.get("personLabel", {}).get("value", "No disponible"),
        "Fecha de nacimiento": r.get("dob", {}).get("value", "No disponible"),
        "País": r.get("countryLabel", {}).get("value", "No disponible"),
        "Imagen": r.get("image", {}).get("value", None),
        "Descripción": r.get("abstract", {}).get("value", "No disponible"),
        "Género": r.get("genderLabel", {}).get("value", "No disponible"),
        "Altura": r.get("height", {}).get("value", "No disponible"),
        "Premios": ", ".join(awards) if awards else "No disponible"
    }


def get_actor_movies(actor_name):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.addCustomHttpHeader("User-Agent", "ActoresDelMundo/1.0 (contacto@ejemplo.com)")
    sparql.setQuery(f"""
    SELECT DISTINCT ?filmLabel WHERE {{
      ?actor rdfs:label "{actor_name}"@en.
      ?film wdt:P161 ?actor.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }}
    LIMIT 10
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return [r["filmLabel"]["value"] for r in results["results"]["bindings"]]

def get_actor_movie_genres(actor_name):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.addCustomHttpHeader("User-Agent", "ActoresDelMundo/1.0 (contacto@ejemplo.com)")
    sparql.setQuery(f"""
    SELECT DISTINCT ?genreLabel WHERE {{
      ?actor ?label "{actor_name}"@en.
      ?actor wdt:P31 wd:Q5.
      ?film wdt:P161 ?actor.
      ?film wdt:P136 ?genre.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }}
    LIMIT 20
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return [r["genreLabel"]["value"] for r in results["results"]["bindings"]]

def calculate_age(dob_str):
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%dT%H:%M:%SZ")
        today = datetime.today()
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day))
    except:
        return None


def ejecutar_busqueda(loading_window, country_disp, age_range, genre_disp):
    try:
        global actors_list
        country = pais_display_to_query.get(country_disp)
        genre = genero_display_to_query.get(genre_disp)
        raw_actors = []

        if country:
            raw_actors = get_actors_by_country(country)
        else:
            for c in pais_display_to_query.values():
                if c:
                    raw_actors += get_actors_by_country(c)

        filtered_actors = []

        for actor_name, uri in raw_actors:
            info = get_wikidata_info(actor_name)
            if not info:
                continue

            age = calculate_age(info.get("Fecha de nacimiento", ""))
            if age is None:
                continue
            if age_range == "20-30" and not (20 <= age <= 30):
                continue
            if age_range == "31-40" and not (31 <= age <= 40):
                continue
            if age_range == "41-50" and not (41 <= age <= 50):
                continue

            if genre:
                movie_genres = get_actor_movie_genres(actor_name)
                if not any(genre.lower() in g.lower() for g in movie_genres):
                    continue

            filtered_actors.append((actor_name, uri))

            if len(filtered_actors) >= 30:
                break

        actors_list = filtered_actors
        listbox.delete(0, tk.END)

        if not actors_list:
            listbox.insert(
                tk.END,
                "No se encontraron actores con los filtros seleccionados.")
        else:
            for actor_name, _ in actors_list:
                listbox.insert(tk.END, actor_name)

    except Exception as e:
        listbox.delete(0, tk.END)
        listbox.insert(tk.END, f"Error: {str(e)}")
    finally:
        loading_window.destroy()


def search_actors():
    country_disp = country_var.get()
    age_range = age_var.get()
    genre_disp = genre_var.get()

    if country_disp == "Sin seleccionar" and age_range == "Sin seleccionar" and genre_disp == "Sin seleccionar":
        warning = tk.Toplevel(window)
        warning.title("Consulta inválida")
        warning.geometry("320x120")
        warning.resizable(False, False)
        warning.grab_set()
        warning.transient(window)

        tk.Label(
            warning,
            text="Selecciona al menos un filtro para realizar la búsqueda.",
            font=("Arial", 10),
            wraplength=280).pack(pady=20)
        tk.Button(warning, text="Cerrar", command=warning.destroy).pack()

        x = window.winfo_x() + (window.winfo_width() // 2) - 160
        y = window.winfo_y() + (window.winfo_height() // 2) - 60
        warning.geometry(f"+{x}+{y}")
        return

    loading_window = tk.Toplevel(window)
    loading_window.title("Realizando búsqueda...")
    loading_window.geometry("250x100")
    loading_window.resizable(False, False)
    loading_window.grab_set()
    loading_window.transient(window)

    tk.Label(loading_window, text="Buscando actores...",
             font=("Arial", 10)).pack(expand=True, pady=20)

    x = window.winfo_x() + (window.winfo_width() // 2) - 125
    y = window.winfo_y() + (window.winfo_height() // 2) - 50
    loading_window.geometry(f"+{x}+{y}")

    loading_window.update_idletasks()
    window.after(100, ejecutar_busqueda, loading_window, country_disp,
                 age_range, genre_disp)


# --- Interfaz principal ---
window = tk.Tk()
window.title("Actores del mundo")
window.geometry("800x560")
window.resizable(False, False)

filters_frame = tk.Frame(window)
filters_frame.pack(pady=10)

country_var = tk.StringVar()
age_var = tk.StringVar()
genre_var = tk.StringVar()

# Etiquetas de filtros
tk.Label(filters_frame, text="País").grid(row=0, column=0)
tk.Label(filters_frame, text="Rango de edad").grid(row=0, column=1)
tk.Label(filters_frame, text="Género de películas").grid(row=0, column=2)

countries = list(pais_display_to_query.keys())
ages = ["Sin seleccionar", "20-30", "31-40", "41-50"]
genres = list(genero_display_to_query.keys())

ttk.Combobox(filters_frame,
             textvariable=country_var,
             values=countries,
             state="readonly",
             width=18).grid(row=1, column=0, padx=5)
ttk.Combobox(filters_frame,
             textvariable=age_var,
             values=ages,
             state="readonly",
             width=18).grid(row=1, column=1, padx=5)
ttk.Combobox(filters_frame,
             textvariable=genre_var,
             values=genres,
             state="readonly",
             width=18).grid(row=1, column=2, padx=5)

tk.Button(filters_frame, text="Buscar", command=search_actors).grid(row=1,
                                                                    column=3,
                                                                    padx=10)

country_var.set("Sin seleccionar")
age_var.set("Sin seleccionar")
genre_var.set("Sin seleccionar")

results_frame = tk.Frame(window)
results_frame.pack(pady=20)

scrollbar = tk.Scrollbar(results_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox = tk.Listbox(results_frame,
                     width=80,
                     height=20,
                     yscrollcommand=scrollbar.set)
listbox.pack(side=tk.LEFT, fill=tk.BOTH)
scrollbar.config(command=listbox.yview)

# Segunda funcionalidad
selected_actor_var = tk.StringVar()


def on_actor_selected(event):
    selection = listbox.curselection()
    if not selection:
        selected_actor_var.set("")
        return
    index = selection[0]
    actor_name, _ = actors_list[index]
    selected_actor_var.set(actor_name)


def buscar_detalles_actor():
    actor_name = selected_actor_var.get()
    if not actor_name:
        return

    info = get_wikidata_info(actor_name)
    peliculas = get_actor_movies(actor_name)
    generos_peliculas = get_actor_movie_genres(actor_name)

    detail_window = tk.Toplevel(window)
    detail_window.title("Ficha del actor/actriz")
    detail_window.geometry("625x540")
    detail_window.resizable(False, False)

    # Scroll
    canvas = tk.Canvas(detail_window, borderwidth=0, bg="#f5f5f5")
    scroll_frame = tk.Frame(canvas, bg="white")
    vsb = tk.Scrollbar(detail_window, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scroll_frame.bind("<Configure>", on_configure)

    main_frame = tk.Frame(scroll_frame, bg="white", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    top_frame = tk.Frame(main_frame, bg="white")
    top_frame.pack(fill="x")

    table_frame = tk.Frame(top_frame, bg="white")
    table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def format_fecha(fecha_str):
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%d-%m-%Y")
        except:
            return "No disponible"

    def add_row(label, value, row):
        tk.Label(table_frame, text=label + ":", font=("Arial", 10, "bold"), bg="white",fg="black", anchor="w")\
            .grid(row=row, column=0, sticky="w", pady=2)
        tk.Label(table_frame, text=value, font=("Arial", 10), bg="white", anchor="w", fg="black", wraplength=300)\
            .grid(row=row, column=1, sticky="w", pady=2)

    add_row("Nombre", info.get("Nombre", actor_name), 0)
    add_row("Fecha de nacimiento",
            format_fecha(info.get("Fecha de nacimiento", "")), 1)
    add_row("País", info.get("País", "No disponible"), 2)
    add_row("Género", info.get("Género", "No disponible"), 3)

    altura = info.get("Altura")
    if altura and altura != "No disponible":
        try:
            altura_valor = float(altura)
            if altura_valor < 10:  # metros
                altura_cm = round(altura_valor * 100)
            else:  # ya está en centímetros
                altura_cm = round(altura_valor)
            altura_str = f"{altura_cm} cm"
        except:
            altura_str = "No disponible"
    else:
        altura_str = "No disponible"
    add_row("Altura", altura_str, 4)

    # Imagen
    image_url = info.get("Imagen")
    if image_url:
        try:
            image_bytes = urlopen(image_url).read()
            img = Image.open(io.BytesIO(image_bytes)).resize((120, 160))
            photo = ImageTk.PhotoImage(img)
            image_label = tk.Label(top_frame, image=photo, bg="white")
            image_label.image = photo
            image_label.pack(side=tk.RIGHT, padx=10)
        except:
            tk.Label(top_frame,
                     text="Imagen no disponible",
                     bg="white",
                     font=("Arial", 9, "italic")).pack(side=tk.RIGHT, padx=10)
    else:
        tk.Label(top_frame,
                 text="Imagen no disponible",
                 bg="white",
                 font=("Arial", 9, "italic")).pack(side=tk.RIGHT, padx=10)

    def separador():
        tk.Frame(main_frame, bg="#cccccc", height=1).pack(fill="x", pady=10)

    # Películas
    separador()
    tk.Label(main_frame,
             text="Películas:",
             font=("Arial", 10, "bold"),
             bg="white",
             fg="black",
             anchor="w").pack(fill="x")
    peliculas_text = ", ".join(peliculas) if peliculas else "No disponible"
    pel_text = tk.Text(main_frame,
                       height=4,
                       wrap="word",
                       bg="#f9f9f9",
                       fg="black",
                       font=("Arial", 10),
                       relief="groove")
    pel_text.insert("1.0", peliculas_text)
    pel_text.config(state="disabled")
    pel_text.pack(fill="x")

    # Géneros de películas
    separador()
    tk.Label(main_frame,
            text="Géneros de películas:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="black",
            anchor="w").pack(fill="x")

    generos_text = ", ".join(generos_peliculas) if generos_peliculas else "No disponible"
    genre_box = tk.Text(main_frame,
                    height=3,
                    wrap="word",
                    bg="#f9f9f9",
                    fg="black",
                    font=("Arial", 10),
                    relief="groove")
    genre_box.insert("1.0", generos_text)
    genre_box.config(state="disabled")
    genre_box.pack(fill="x", pady=(0, 10))

    # Descripción
    separador()
    tk.Label(main_frame,
             text="Descripción:",
             font=("Arial", 10, "bold"),
             bg="white",
             fg="black",
             anchor="w").pack(fill="x")
    desc_text = tk.Text(main_frame,
                    height=4,
                    wrap="word",
                    bg="#f9f9f9",
                    fg="black",  # color del texto
                    font=("Arial", 10),
                    relief="groove")
    desc_text.insert("1.0", info.get("Descripción", "No disponible"))
    desc_text.config(state="disabled")
    desc_text.pack(fill="x")

    # Premios
    separador()
    tk.Label(main_frame,
             text="Premios:",
             font=("Arial", 10, "bold"),
             bg="white",
             fg="black",
             anchor="w").pack(fill="x")
    awards_text = tk.Text(main_frame,
                          height=4,
                          wrap="word",
                          bg="#f9f9f9",
                          fg="black",
                          font=("Arial", 10),
                          relief="groove")
    awards_text.insert("1.0", info.get("Premios", "No disponible"))
    awards_text.config(state="disabled")
    awards_text.pack(fill="x", pady=(0, 10))


listbox.bind("<<ListboxSelect>>", on_actor_selected)

extra_frame = tk.Frame(window)
extra_frame.pack(pady=10)

tk.Label(extra_frame, text="Buscar más información de:").grid(row=0,
                                                              column=0,
                                                              padx=5)

ttk.Entry(extra_frame,
          textvariable=selected_actor_var,
          width=40,
          state="readonly").grid(row=1, column=0, padx=5)
tk.Button(extra_frame, text="Detalles",
          command=buscar_detalles_actor).grid(row=1, column=1, padx=5)

window.mainloop()
