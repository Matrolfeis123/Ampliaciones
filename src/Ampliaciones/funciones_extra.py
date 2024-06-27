import re
import numpy as np
import pdfplumber
import spacy
import os
from openpyxl import Workbook
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
from difflib import get_close_matches
from unidecode import unidecode
import simplekml
import time



def generar_diccionario_proyectos_v2(file):
    diccionario_obras_nuevas = {}
    diccionario_lineas_nuevas = {}
    paginas = [1,2]
    lista_titulos_largos = []

    with pdfplumber.open(file) as pdf:
        text = ""
        for i in paginas:
            text += pdf.pages[i].extract_text()

        matches = re.finditer(r'(Nueva (S/E|línea|líneas).*?)(?=\n\S)', text, re.DOTALL)
        for match in matches:
            line = match.group(0)
            if not re.match(r".*[0-9]{2}$", line):
                lista_titulos_largos.append(line)
                print("Título largo: ", line)
                titulo = input("Ingrese el título del proyecto según el índice del pdf: ")
                pag_inicio = int(input("Ingrese la página de inicio del proyecto según el índice del pdf: ")) - 1
                pag_final = pag_inicio + 3
##############################################################################################
                if "s/e" in titulo.lower() and "nuevas líneas" in titulo.lower():
                    # Por lo tanto, el proyecto se compone de una nueva s/e y nuevas lineas. 
                    # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                    # EJ: Nueva S/E Caracoles, nuevas líneas 2x220 kV Caracoles – Liqcau y 2x110 kV Guardiamarina – Caracoles
                    # Se almacenará en el diccionario de la siguiente manera:
                    aux = titulo.split(", nuevas líneas")

                    if len(aux) > 1:
                        
                        titulo_se_nva = aux[0].strip()
                        titulo_lineas_nvas = aux[1].split(" y ")

                    else:
                        aux = titulo.split(" y nuevas líneas")

                        if len(aux) > 1:
                            titulo_se_nva = aux[0].strip()
                            titulo_lineas_nvas = aux[1].split(" y ")

                        else:
                            print("No se pudo clasificar el proyecto: ", titulo)
                            continue

                    
                    
                    diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                    for linea in titulo_lineas_nvas:
                        diccionario_lineas_nuevas[linea.strip()] = (pag_inicio, pag_final)

                elif "nueva línea" in titulo.lower() and "s/e" in titulo.lower():
                    print(f"El proyecto es una línea nueva y una subestación nueva: {titulo}")
                    # Por lo tanto, el proyecto se compone de una nueva s/e y una nueva linea.
                    # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                    # EJ: Nueva S/E Alto Molle y nueva línea 2x110 kV Alto Molle – Cóndores

                    aux = titulo.split(" y nueva línea")
                    titulo_se_nva = aux[0].strip()
                    titulo_linea_nva = aux[1].strip()

                    diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                    diccionario_lineas_nuevas[titulo_linea_nva] = (pag_inicio, pag_final)

                elif "nueva línea" in titulo.lower():
                    # Por lo tanto, el proyecto se compone de una nueva linea.
                    # Por lo tanto, almacenaremos el titulo en el diccionario de lineas nuevas
                    titulo = titulo.replace("Nueva línea", "").strip()
                    diccionario_lineas_nuevas[titulo] = (pag_inicio, pag_final)

                elif "s/e" in titulo.lower():
                    # Por lo tanto, el proyecto se compone de una nueva s/e.
                    # Por lo tanto, almacenaremos el titulo en el diccionario de obras nuevas
                    diccionario_obras_nuevas[titulo.strip()] = (pag_inicio, pag_final)

                else:
                    print(f"No se pudo clasificar el proyecto: {titulo}")

##############################################################################################
            else:
                match = re.match(r'^(.*?)\s+(\d+)$', line)
                        
                if match:
                    titulo = match.group(1).replace(".", "")
                    pag_inicio = int(match.group(2)) - 1
                    pag_final = pag_inicio + 3

                    if "s/e" in titulo.lower() and "nuevas líneas" in titulo.lower():
                        # Por lo tanto, el proyecto se compone de una nueva s/e y nuevas lineas. 
                        # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                        # EJ: Nueva S/E Caracoles, nuevas líneas 2x220 kV Caracoles – Liqcau y 2x110 kV Guardiamarina – Caracoles
                        # Se almacenará en el diccionario de la siguiente manera:
                        aux = titulo.split(", nuevas líneas")
                        titulo_se_nva = aux[0]
                        titulo_lineas_nvas = aux[1].split(" y ")

                        diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                        for linea in titulo_lineas_nvas:
                            diccionario_lineas_nuevas[linea] = (pag_inicio, pag_final)

                    elif "nueva línea" in titulo.lower() and "s/e" in titulo.lower():
                        print(f"El proyecto es una línea nueva y una subestación nueva: {titulo}")
                        # Por lo tanto, el proyecto se compone de una nueva s/e y una nueva linea.
                        # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                        # EJ: Nueva S/E Alto Molle y nueva línea 2x110 kV Alto Molle – Cóndores

                        aux = titulo.split(" y nueva línea")
                        titulo_se_nva = aux[0]
                        titulo_linea_nva = aux[1]

                        diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                        diccionario_lineas_nuevas[titulo_linea_nva] = (pag_inicio, pag_final)

                    elif "nueva línea" in titulo.lower():
                        # Por lo tanto, el proyecto se compone de una nueva linea.
                        # Por lo tanto, almacenaremos el titulo en el diccionario de lineas nuevas
                        titulo = titulo.replace("Nueva línea", "")
                        diccionario_lineas_nuevas[titulo] = (pag_inicio, pag_final)

                    elif "s/e" in titulo.lower():
                        # Por lo tanto, el proyecto se compone de una nueva s/e.
                        # Por lo tanto, almacenaremos el titulo en el diccionario de obras nuevas
                        diccionario_obras_nuevas[titulo] = (pag_inicio, pag_final)

                    else:
                        print(f"No se pudo clasificar el proyecto: {titulo}")

                else:
                    print(f"No se pudo clasificar el proyecto: {line}")


        patron_final = r"El C.O.M.A"
        for diccionario in [diccionario_obras_nuevas, diccionario_lineas_nuevas]:
            for titulo, paginas in diccionario.items():
                for i in range(paginas[0], paginas[1]):
                    text = pdf.pages[i].extract_text()
                    if re.search(patron_final, text, re.DOTALL):
                        diccionario[titulo] = (paginas[0], i)


        print("Obras nuevas: ")
        for titulo, paginas in diccionario_obras_nuevas.items():
            print(f"{titulo}: {paginas}")

        print("Lineas nuevas: ")
        for titulo, paginas in diccionario_lineas_nuevas.items():
            print(f"{titulo}: {paginas}")

        return diccionario_obras_nuevas, diccionario_lineas_nuevas

def generar_diccionario_ampliaciones(file):
    diccionario_obras_ampliacion = {}

    paginas = [1, 2]

    with pdfplumber.open(file) as pdf:
        text = ""
        for i in paginas:
            text += pdf.pages[i].extract_text()

        matches = re.finditer(r'((Ampliación en S/E).*?)(?=\n\S)', text, re.DOTALL)
        for match in matches:
            line = match.group(0)
            if not re.match(r".*[0-9]{2}$", line):
                print("Título largo: ", line)
                titulo = input("Ingrese el título del proyecto según el índice del pdf: ")
                pag_inicio = int(input("Ingrese la página de inicio del proyecto según el índice del pdf: ")) - 1
                pag_final = pag_inicio + 3

            else:
                match = re.match(r'^(.*?)\s+(\d+)$', line)
                if match:
                    titulo = match.group(1).replace(".", "")
                    pag_inicio = int(match.group(2)) - 1
                    pag_final = pag_inicio + 3

            
            diccionario_obras_ampliacion[titulo] = (pag_inicio, pag_final)


    return diccionario_obras_ampliacion

def extraer_texto_entre_delimitadores_v2(texto, delimitador_inicial, delimitador_final):
    pattern = re.compile(rf"{re.escape(delimitador_inicial)}(.*?){re.escape(delimitador_final)}.*?\.", re.DOTALL)
    match = pattern.search(texto)
    return match.group(0) if match else "ERROR EXTRAYENDO TEXTO"

def generar_diccionario_descripciones_amp(file, diccionario):
    dic_descripciones = {}
    try:

        with pdfplumber.open(file) as pdf:
            for titulo, paginas in diccionario.items():
                text = ""
                for i in range(paginas[0], paginas[1] + 1):
                    text += pdf.pages[i].extract_text()

                text = text.replace("\n", " ")
                text = text.replace("  ", " ")
                texto_limpio = re.sub(r'\d{1,2}—–——–', "", text)
                texto_limpio = re.sub(r'—–——–', "", texto_limpio)
                texto_limpio = texto_limpio.replace("  ", " ")
                descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación", "moneda de los Estados Unidos de América")

                

                if titulo.strip() == "Ampliación en S/E Las Arañas (RTR ATMT)":
                    texto_limpio = re.sub(r'\d{1,2}—–——–', "", text)
                    texto_limpio = re.sub(r'—–——–', "", texto_limpio)
                    texto_limpio = texto_limpio.replace("  ", " ")
                    descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación de la obra El proyecto consiste en el aumento de capacidad de la subestación Las Arañas", "moneda de los Estados Unidos de América")

                dic_descripciones[titulo] = descripcion_def
                    


    except Exception as e:
        print(f"Error en la ejecución del análisis: {e}")


    return dic_descripciones

def encontrar_indices_parrafos(descripcion):

    """
    La funcion devolverá una lista, donde cada elemento es la posición de inicio de un párrafo en la descripción.
    Se considera que un párrafo inicia con una de las frases de inicio definidas en la lista frases_inicio.

    Se pueden utilizar dichos indices para extraer los parrafos de la descripcion segun se necesite.
    Por ejemplo, para separar los distintos patios, lineas nuevas, etc.
    """



    # Lista de frases de inicio de los párrafos
    frases_inicio = [
        "El proyecto consiste en",
        "A su vez, el proyecto incluye",
        "A su vez, el proyecto considera",
        "A su vez, el proyecto consiste en",
        "A su vez, el proyecto contempla",
        "Adicionalmente, el proyecto considera",
        "Adicionalmente, el proyecto contempla",
        "Además, el proyecto contempla",
        "Además, el proyecto considera"
    ]
    
    # Crear un patrón de expresión regular que busque todas las frases de inicio
    pattern = re.compile('|'.join(re.escape(frase) for frase in frases_inicio))

    # Encontrar todas las posiciones de inicio de las frases
    indices = [match.start() for match in pattern.finditer(descripcion)]
    
    return indices

def extraer_parrafo_v3(descripcion, indice_inicio):
    pattern = re.compile(r'(?<!\d)\.(?!\d)')

    match = pattern.search(descripcion, indice_inicio)
    if match:
        indice_fin = match.start()
        return descripcion[indice_inicio:indice_fin+1]
    
    else:
        return descripcion[indice_inicio:]

#Vamos a crear una funcion para comprobar el contenido de las paginas asociadas a cada titulo del indice
def imprimir_contenido_proyectos(diccionario, file):
    with pdfplumber.open(file) as pdf:
        for titulo, paginas in diccionario.items():
            print(f"Proyecto: {titulo}")
            for i in range(paginas[0], paginas[1]):
                page = pdf.pages[i]
                text = page.extract_text()
                print(f"Contenido de la pagina {i+1}:")
                print(text)
                print("-" * 50)  # Separador entre páginas

def crear_excel_proyectos(l_proyectos, nombre_archivo):
    # Crear un libro de Excel
    libro = Workbook()
    hoja = libro.active

    # Crear una lista con los nombres de las columnas
    columnas = [['Nombre Proyecto', 'Nro patios', 'Ubicacion']]

    i = 0
    for proyecto in l_proyectos:
        nombre_proyecto = str(proyecto.nombre)
        nro_patios = str(len(proyecto.patios))
        ubicacion = str(proyecto.ubicacion)

        lista_datos_proyecto = [nombre_proyecto, nro_patios, ubicacion]

        j = 0
        for patio in proyecto.patios:
            j += 1
            # Agregar en el encabezado las columnas correspondientes a cada patio (i) si y solo si j es mayor que i
            if j > i:
                columnas[0].extend([f"Nombre Patio {i+1}", f"Configuración Patio {i+1}", f"Nro Posiciones Patio {i+1}", f"Conexiones Patio {i+1}"])
                i = j

            nombre_patio = str(patio.nombre)
            configuracion_patio = str(patio.configuracion)
            posiciones_patio = str(patio.posiciones_disponibles)

            # Concatenar las conexiones en un solo string para que se vea mejor en el excel
            if hasattr(patio, 'lista_conexiones'):
                conexiones = ', '.join(patio.lista_conexiones)
            else:
                conexiones = "No se encontraron conexiones para este patio"

            lista_datos_proyecto.extend([nombre_patio, configuracion_patio, posiciones_patio, conexiones])

        columnas.append(lista_datos_proyecto)

    # Escribir los datos en el archivo Excel
    for row in columnas:
        hoja.append(row)

    # Guardar el archivo
    nombre_archivo = nombre_archivo+".xlsx"

    libro.save(nombre_archivo)
    print("Archivo resumen_proyectos.xlsx guardado con éxito")

    return ""

############################################################################################################
############################################################################################################
######################################### MODULO CONSULTAS A KMZ ###########################################


def buscar_subestacion_por_nombre(kml_file, nombre_subestacion_referencia):

    tree = ET.parse(kml_file)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    folders = root.findall(".//kml:Folder", ns)


    try:
        for folder in folders:
            name = folder.find("kml:name", ns).text

            if name == "Subestaciones":
                encontrado = False
                breakpoint()
                cutoff = 0.9
                tiempo_inicio = time.time()
                while not encontrado and tiempo_inicio - time.time() < 15:
                    for placemark in folder.findall(".//kml:Placemark", ns):
                        placemark_name = placemark.find("kml:name", ns).text.lower()
                        nombre_subestacion = nombre_subestacion_referencia.lower()

                        print("Nombre subestacion: ", nombre_subestacion)
                        print("Nombre placemark: ", placemark_name)
                        
                        if nombre_subestacion in placemark_name:
                            print("Nombre: ", placemark.find("kml:name", ns).text)
                            longitud, latitud = placemark.find(".//kml:coordinates", ns).text.split(",")[0:2]
                            print("Coordenadas: ", placemark.find(".//kml:coordinates", ns).text.split(",")[0:2])
                            print("Latitud: ", latitud)
                            print("Longitud: ", longitud)

                            encontrado = input("¿Es correcta la subestacion? (True/False): ")

                            if encontrado == "True":
                                return latitud, longitud


                        #coincidencias = get_close_matches(nombre_subestacion, [placemark_name], n=1, cutoff=cutoff)
                        
                            
                        # if coincidencias:
                        #     print("Nombre: ", placemark.find("kml:name", ns).text)
                        #     longitud, latitud = placemark.find(".//kml:coordinates", ns).text.split(",")[0:2]
                        #     print("Coordenadas: ", placemark.find(".//kml:coordinates", ns).text.split(",")[0:2]) # Aca tenemos las coordenadas de la subestacion
                        #     print("Latitud: ", latitud)
                        #     print("Longitud: ", longitud)
                        #     encontrado = input("¿Es correcta la subestacion? (True/False): ")

                        #     if encontrado == "True":
                        #         return latitud, longitud #ver si entrego como tupla
                            
                        # else:
                        #     cutoff -= 0.00005

                    if cutoff < 0.5:
                        raise ValueError("No se encontraron coincidencias con el nombre de la subestacion")
                
                # Si no se encontro la subestacion cuando ya paso el tiempo limite, se ingresa el nombre manualmente

                nombre_subestacion = input("Ingrese el nombre de la subestacion: ")

                for placemark in folder.findall(".//kml:Placemark", ns):
                    placemark_name = placemark.find("kml:name", ns).text.lower()
                    if nombre_subestacion.lower() in placemark_name:
                        print("Nombre: ", placemark.find("kml:name", ns).text)
                        longitud, latitud = placemark.find(".//kml:coordinates", ns).text.split(",")[0:2]
                        print("Coordenadas: ", placemark.find(".//kml:coordinates", ns).text.split(",")[0:2])

                        return latitud, longitud
            



    except ValueError as e:
        print(e)

        # Vamos a 

def format_line_segment(input_string):
    try:
            
        segments = input_string.replace(",0", "").strip().split(" ")
        
        formatted_segments = []
        for segment in segments:
            lon, lat = map(float, segment.split(","))
            formatted_segments.append((lat, lon))

        return formatted_segments
    
    except Exception as e:
        print("Error al formatear las coordenadas de la linea de transmision: ", e)
        return None

def buscar_linea_transmision_por_nombre(kml_file, nombre_linea_transmision):
    
    try:
    # Dentro de el nombre de la linea de transmision, se debe extraer la tension de la linea, para identificar la carpeta dentro de la cual
    # se encuentra la linea de transmision. Esta informacion sigue un patron del tipo 2x220, 2x110, wtx. Es decir, la cantidad de conductores y la tension de la linea

        patron_tension = r'\d{2,3} kv\b'
        patron_tension_extended = r'\b\d+x\d{2,3} kv\b'
        match = re.search(patron_tension, nombre_linea_transmision.lower()) # a veces, en el informe vienen sin el kV, manejar ese caso!!

        if match:
            tension = match.group()
            print("Tension: ", tension)


        elif "kv" not in nombre_linea_transmision.lower():
            # como no hay match, implica que las letras kV no estan presentes en el nombre
            #vamos a agregar las letras para acompañar la tension para que el patron de busqueda sea mas efectivo
            print("El nombre de la linea de transmision no contiene la tension, probando con patron extendido")

            #primero, buscamos los digitos de la tension
            match = re.search(r'\d{2,3}', nombre_linea_transmision.lower())
            if match:
                tension = match.group() + " kv"
                print("Tension: ", tension)
                nombre_linea_transmision = re.sub(r'\d{2,3}', tension, nombre_linea_transmision.lower()).strip()
                print("Nombre de la linea de transmision: ", nombre_linea_transmision)
             



        else: 
            print("No se")
            patron_extended_sin_kv = r'\d+x\d{2,3}'
            match = re.search(patron_extended_sin_kv, nombre_linea_transmision.lower())
            if match:
                tension = match.group() + " kV"
                print("Tension: ", tension)
                nombre_linea_transmision = re.sub(patron_extended_sin_kv, tension, nombre_linea_transmision.lower())

            else:
                raise ValueError("No se encontro la tension")

        
        
        nombre_sin_tension = re.sub(patron_tension_extended, '', nombre_linea_transmision.lower()).strip()
        print("Nombre sin tension: ", nombre_sin_tension)
        subestaciones = re.split(r'\s+–\s+|\s+-\s+|\s+a\s+|\s+y\s+|\s+en\s+', nombre_sin_tension.lower())
        subestaciones = [unidecode(subestacion).lower() for subestacion in subestaciones if subestacion.strip()]
        print("Subestaciones: ", subestaciones)


        tree = ET.parse(kml_file)
        root = tree.getroot()

        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        folders = root.findall(".//kml:Folder", ns)

        for folder in folders:
            name = folder.find("kml:name", ns).text
            if name == "Línea de Transmisión":
                for subfolder in folder.findall(".//kml:Folder", ns):
                    subfolder_name = subfolder.find("kml:name", ns).text.lower()
                    if tension.lower() in subfolder_name.lower():
                        for placemark in subfolder.findall(".//kml:Placemark", ns):
                                placemark_name = placemark.find("kml:name", ns).text.lower()
                                if all(subestacion in unidecode(placemark_name).lower() for subestacion in subestaciones):
                                    print("Nombre: ", placemark.find("kml:name", ns).text)
                                    coordenadas = placemark.find(".//kml:coordinates", ns).text.strip()
                                    coordenadas_formateadas = format_line_segment(coordenadas)
                                    print("Coordenadas formateadas: ", coordenadas_formateadas)
                                    return coordenadas_formateadas
                                
        raise Exception("No se encontro la linea de transmision!")


    except Exception as e:
        print(e)
        return None

def find_location_def(start_point, points, distance, accurracy):
    """
    
    Encuentra la ubicacion a una distancia especifica desde un punto de inicio 
    y siguiendo una linea de transmision como referencia.

    Args:
    - start_point: tupla de (latitud, longitud) representando el punto de inicio.
    - points: lista de tuplas (latitud, longitud) representando los puntos de la linea de transmision.
    - distance: flotante representando la distancia objetivo desde el punto de inicio.
    - accurracy: flotante representando la accurracy deseada en la distancia objetivo.

    Returns:
    - Una tupla conteniendo la ubicacion (latitud, longitud) a la distancia objetivo.
    """
    
    # Find the two points that enclose the target distance
    point1, point2 = find_two_points_enclosing_distance(start_point, points, distance)
    print("Punto 1: ", point1)
    print("Punto 2: ", point2)

    epsilon = accurracy 
    t = 0.5
    step = 0.25

    # Interpolamos entre los dos puntos que encierran la distancia objetivo con un t inicial de 0.5
    p_act = interpolate_geodesic(point1, point2, t)
    dist = geodesic(start_point, p_act).km
    

    i = 0
    # Aplicamos un algoritmo de busqueda binaria para encontrar el punto que cumple con la distancia objetivo
    while abs(dist - distance) > epsilon:
        if dist < distance:
            t += step
        else:
            t -= step
            
        step /= 2
        p_act = interpolate_geodesic(point1, point2, t)
        dist = geodesic(start_point, p_act).km
        
        i += 1
        if i % 1000 == 0:
            print(f"Resultado parcial: t={t}, Distancia={dist}, pos={p_act}")
            i += 1

    
    print(f"Resultado final: t={t}, Distancia={dist}")
    
    return p_act


def interpolate_geodesic(point1, point2, t):
    """
    Interpolate between two geographic points.
    
    Args:
    - point1: tuple of (latitude, longitude) for the first point.
    - point2: tuple of (latitude, longitude) for the second point.
    - t: float between 0 and 1 representing the interpolation fraction.
    
    Returns:
    - Interpolated point as a tuple (latitude, longitude).
    """
    try:
            
        if not (0 <= t <= 1):
            raise ValueError("t must be between 0 and 1")

        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad, lon1_rad = np.radians([lat1, lon1])
        lat2_rad, lon2_rad = np.radians([lat2, lon2])
        
        # Spherical linear interpolation (slerp)
        d = geodesic(point1, point2).km
        if d == 0:
            return point1
        
        A = np.sin((1 - t) * d) / np.sin(d)
        B = np.sin(t * d) / np.sin(d)
        
        x = A * np.cos(lat1_rad) * np.cos(lon1_rad) + B * np.cos(lat2_rad) * np.cos(lon2_rad)
        y = A * np.cos(lat1_rad) * np.sin(lon1_rad) + B * np.cos(lat2_rad) * np.sin(lon2_rad)
        z = A * np.sin(lat1_rad) + B * np.sin(lat2_rad)
        
        lat_interp_rad = np.arctan2(z, np.sqrt(x ** 2 + y ** 2))
        lon_interp_rad = np.arctan2(y, x)
        
        # Convert back to degrees
        lat_interp = np.degrees(lat_interp_rad)
        lon_interp = np.degrees(lon_interp_rad)
        
        return (lat_interp, lon_interp)
    
    except ValueError as e:
        print("Error en la interpolacion geodesica: ", e)
        return None



def find_two_points_enclosing_distance(start_point, line_points, distance):
    """
    Encuentra dos puntos que encierran la distancia objetivo desde el punto de inicio.

    Args:
    - start_point: tupla de (latitud, longitud) representando el punto de inicio.
    - line_points: lista de tuplas (latitud, longitud) representando los puntos de la linea.
    - distance: flotante representando la distancia objetivo desde el punto de inicio.

    Returns:
    - Una tupla conteniendo dos puntos que encierran la distancia objetivo.
    """


    enclosing_points = []

    # Calculamos la distancia de cada punto de la linea con respecto al punto de inicio
    for point in line_points:
        dist = geodesic(start_point, point).kilometers
        enclosing_points.append((point, dist))
    

    # Ordenamos los puntos de la linea segun la distancia al punto de inicio, aplicando un sort por la distancia
    enclosing_points.sort(key=lambda x: x[1])
    
    low = None
    high = None

    # Buscamos los dos puntos que encierran la distancia objetivo
    for i in range(len(enclosing_points)):
        if enclosing_points[i][1] <= distance:
            low = enclosing_points[i]
        if enclosing_points[i][1] >= distance and (high is None or enclosing_points[i][1] < high[1]):
            high = enclosing_points[i]
        if low and high:
            break
            
    return low[0], high[0]

############################################################################################################
############################################################################################################

def contar_patios(diccionario):
    # Inicializar contador de patios
    contador_patios = 0
    
    # Iterar sobre las claves del diccionario
    for key in diccionario.keys():
        # Comprobar si la clave empieza con 'PATIO_'
        if key.startswith('PATIO_'):
            contador_patios += 1
            
    return contador_patios

def agregar_proyecto_nuevo(kml_file, diccionario_kmz):
    """
    Esta funcion se encarga de agregar un nuevo proyecto al archivo KMZ, a partir de la informacion
    contenida en el diccionario_kmz. Este diccionario debe contener la informacion necesaria para
    ubicar la nueva subestacion de referencia y la linea de transmision de referencia.
    """
    try:
        tree = ET.parse(kml_file)
        root = tree.getroot()

    except ET.ParseError as e:
        print("Error al abrir el archivo KML: ", e)
        return None
    
    except FileNotFoundError as e:
        print("Error al abrir el archivo KML: ", e)
        return None
    
    except Exception as e:
        print("Error inesperado: ", e)
        return None
    
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    try:
        folders = root.findall(".//kml:Folder", ns)
        target_folder = None

        for folder in folders:
            name = folder.find("kml:name", ns).text
            if name == "Proyectos S/E":
                target_folder = folder
                break

        if not target_folder:
            raise ValueError("No se encontro la carpeta de escritura de proyectos nuevos")
        
        placemark = ET.SubElement(target_folder, "{http://www.opengis.net/kml/2.2}Placemark")

        #Crear un nombre para el placemark
        name = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}name")
        name.text = diccionario_kmz["OBRA"]

        # Aca debemos verificar si el proyecto tiene uno o dos patios, para agregar el estilo correspondiente
        numero_patios = contar_patios(diccionario_kmz)
        if numero_patios == 1:
            style = "#ONva1"
            schema = "#ONva_din"
                    # Agregar los datos del proyecto
            simple_data_list = [
                ("OBRA", diccionario_kmz["OBRA"]),
                ("DECRETO", diccionario_kmz["DECRETO"]),
                ("TIPO", diccionario_kmz["TIPO"]),
                ("VI", diccionario_kmz["V_INV"]),
                ("ENTRADA_OP", diccionario_kmz["E_OP"]),
                ("RESUMEN", diccionario_kmz["RESUMEN"] if diccionario_kmz["RESUMEN"] else "N/A"),
                ("patio1_tension", diccionario_kmz["PATIO_0"]["TENSION"]),
                ("patio1_conexiones", diccionario_kmz["PATIO_0"]["CONEXIONES"] if diccionario_kmz["PATIO_0"]["CONEXIONES"] else "N/A"),
                ("patio1_posiciones_disponibles", diccionario_kmz["PATIO_0"]["POSDISP"])
            ]

        elif numero_patios == 2:
            style = "#ONva2"
            schema = "#ONva_din2"
                    # Agregar los datos del proyecto
            simple_data_list = [
                ("OBRA", diccionario_kmz["OBRA"]),
                ("DECRETO", diccionario_kmz["DECRETO"]),
                ("TIPO", diccionario_kmz["TIPO"]),
                ("VI", diccionario_kmz["V_INV"]),
                ("ENTRADA_OP", diccionario_kmz["E_OP"]),
                ("RESUMEN", diccionario_kmz["RESUMEN"] if diccionario_kmz["RESUMEN"] else "N/A"),
                ("patio1_tension", diccionario_kmz["PATIO_0"]["TENSION"]),
                ("patio1_conexiones", diccionario_kmz["PATIO_0"]["CONEXIONES"] if diccionario_kmz["PATIO_0"]["CONEXIONES"] else "N/A"),
                ("patio1_posiciones_disponibles", diccionario_kmz["PATIO_0"]["POSDISP"]),
                ("patio2_tension", diccionario_kmz["PATIO_1"]["TENSION"]),
                ("patio2_conexiones", diccionario_kmz["PATIO_1"]["CONEXIONES"] if diccionario_kmz["PATIO_1"]["CONEXIONES"] else "N/A"),
                ("patio2_posiciones_disponibles", diccionario_kmz["PATIO_1"]["POSDISP"])
            ]



        # Agregar el estilo del placemark
        style_url = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}styleUrl")
        style_url.text = style # En este punto, debo hacer una condicion para elegir el estilo si es uno o dos patios

        # Agregar la descripcion del placemark
        extended_data = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}ExtendedData")
        schema_data = ET.SubElement(extended_data, "{http://www.opengis.net/kml/2.2}SchemaData", schemaUrl=schema)




        for key, value in simple_data_list:
            simple_data = ET.SubElement(schema_data, "{http://www.opengis.net/kml/2.2}SimpleData", {"name": key})
            simple_data.text = str(value)

        point = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}Point")
        coordinates = ET.SubElement(point, "{http://www.opengis.net/kml/2.2}coordinates")
        coordinates.text = f"{diccionario_kmz["COORDENADAS"][1]},{diccionario_kmz["COORDENADAS"][0]},0"

        try:
            tree.write(kml_file)
            print("Proyecto agregado con exito!!")
            return "Proyecto agregado con exito!!"
        
        except Exception as e:
            print("Error al escribir el archivo KML: ", e)
            return None
        
    except KeyError as e:
        print(f"Clave faltante en diccionario_kmz: {e}")

    except Exception as e:
        print("Error inesperado: ", e)
        return None

def probar_localizacion_proyecto():

    pdf_file = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "PDFs", "plan_expansion_final_2023.pdf"))
    kml_file = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "KMZs", "SEN_coordinador", "doc_coordinador.kml"))


    get_se_referencia = input("Ingrese el nombre de la subestacion de referencia: ")
    get_se_referencia = get_se_referencia.lower()
    get_se_referencia = unidecode(get_se_referencia)
 
    start_point = buscar_subestacion_por_nombre(kml_file, get_se_referencia)

    while not start_point:
        get_se_referencia = input("Ingrese el nombre de la subestacion de referencia: ")
        get_se_referencia = get_se_referencia.lower()
        get_se_referencia = unidecode(get_se_referencia)
        start_point = buscar_subestacion_por_nombre(kml_file, get_se_referencia)

    print("Punto de inicio: ", start_point)

    nombre_linea_transmision = input("Ingrese el nombre de la linea de transmision (Ej: 2x220 kV Nueva Cardones - Nueva Pan de Azucar): ")
    line_points = buscar_linea_transmision_por_nombre(kml_file, nombre_linea_transmision)
    confirmacion = input("¿Es correcta la linea de transmision? (y/n): ")

    while confirmacion.lower() != "y":
        nombre_linea_transmision = input("Ingrese el nombre de la linea de transmision (Ej: 2x220 kV Nueva Cardones - Nueva Pan de Azucar): ")
        line_points = buscar_linea_transmision_por_nombre(kml_file, nombre_linea_transmision)
        confirmacion = input("¿Es correcta la linea de transmision? (y/n): ")

    print("Puntos de la linea de transmision: ", line_points)

    distance = float(input("Ingrese la distancia objetivo desde la referencia (en km): "))
    accuracy = float(input("Ingrese la precision deseada (en km): "))
    print("Calculando punto objetivo...")
    location = find_location_def(start_point, line_points, distance, accuracy)
    print("Punto objetivo: ", location)

def manejar_proyectos_con_problemas(diccionario_problemas):
    # Imprimir el diccionario con problemas
    print("Diccionario de proyectos con problemas:")
    for llave, valor in diccionario_problemas.items():
        print(f"{llave}: {valor}")

    # Preguntar al usuario la llave que quiere ingresar manualmente
    llave_a_actualizar = input("Ingrese la llave que desea actualizar: ")

    # Comprobar si la llave existe en el diccionario
    if llave_a_actualizar in diccionario_problemas:
        # Pedir al usuario el nuevo valor para la llave
        nuevo_valor = input(f"Ingrese el nuevo valor para '{llave_a_actualizar}': ")

        # Actualizar el diccionario con el nuevo valor
        diccionario_problemas[llave_a_actualizar] = nuevo_valor

        print(f"'{llave_a_actualizar}' ha sido actualizado a: {diccionario_problemas[llave_a_actualizar]}")
        return diccionario_problemas
    
    else:
        print(f"La llave '{llave_a_actualizar}' no existe en el diccionario.")
        return manejar_proyectos_con_problemas(diccionario_problemas)

############################################################################################################
############################################################################################################

def buscar_subestacion_por_nombre_trinergy_v2(kml_file, nombre_subestacion_referencia):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    ns = {'ns0': 'http://www.opengis.net/kml/2.2'}
    
    nombre_subestacion_referencia = (nombre_subestacion_referencia).lower()
    subestaciones = {}

    try:
        for folder in root.findall(".//ns0:Folder", ns):
            folder_name = folder.find("ns0:name", ns).text
            if folder_name and ("proyectos s/e" in folder_name.lower()):
                print(f"Buscando en la carpeta: {folder_name}")
                for placemark in folder.findall(".//ns0:Placemark", ns):
                    placemark_name = placemark.find("ns0:name", ns).text
                    if placemark_name:
                        placemark_name = (placemark_name).lower()
                        extended_data = placemark.find("ns0:ExtendedData/ns0:SchemaData", ns)
                        if extended_data is not None:
                            for simple_data in extended_data.findall("ns0:SimpleData", ns):
                                if simple_data.get("name") == "OBRA":
                                    obra_name = simple_data.text
                                    if obra_name:
                                        obra_name = unidecode(obra_name).lower()
                                        if nombre_subestacion_referencia in obra_name:
                                            coordinates = placemark.find("ns0:Point/ns0:coordinates", ns).text.strip().split(",")
                                            latitud = coordinates[1]
                                            longitud = coordinates[0]
                                            print(f"Subestación encontrada: {placemark_name}")
                                            print(f"Latitud: {latitud}, Longitud: {longitud}")
                                            return float(latitud), float(longitud)
                
        raise ValueError("No se encontraron coincidencias con el nombre de la subestación")
    
    except ValueError as e:
        print(e)
        return None
    except ET.ParseError:
        print("Error al parsear el archivo KML.")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def buscar_subestacion_por_nombre_coordinador(kml_file, nombre_subestacion_referencia):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    ns = {'ns0': 'http://www.opengis.net/kml/2.2'}
    
    nombre_subestacion_referencia = (nombre_subestacion_referencia).lower().strip()
    nombre_subestacion_referencia = f"s/e {nombre_subestacion_referencia}"
    subestaciones = {}

    try:
        for folder in root.findall(".//ns0:Folder", ns):
            folder_name = folder.find("ns0:name", ns).text
            if folder_name and ("subestaciones" in folder_name.lower()):
                print(f"Buscando en la carpeta: {folder_name}")
                for placemark in folder.findall(".//ns0:Placemark", ns):
                    placemark_name = placemark.find("ns0:name", ns).text
                    if placemark_name:
                        placemark_name = unidecode(placemark_name).lower()
                        placemark_name = placemark_name.split("_")[-1].strip()
                        print("Placemark name: ", placemark_name, " - ", nombre_subestacion_referencia)
                        if nombre_subestacion_referencia in placemark_name:
                            coordinates = placemark.find("ns0:Point/ns0:coordinates", ns).text.strip().split(",")
                            latitud = coordinates[1]
                            longitud = coordinates[0]
                            print(f"Subestación encontrada: {placemark_name}")
                            print(f"Latitud: {latitud}, Longitud: {longitud}")
                            breakpoint()
                            return float(latitud), float(longitud)

                
        raise ValueError("No se encontraron coincidencias con el nombre de la subestación")
    
    except ValueError as e:
        print(e)
        return None
    except ET.ParseError:
        print("Error al parsear el archivo KML.")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def buscar_subestacion_por_nombre_trinergy_v3(kml_file, nombre_subestacion_referencia):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    ns = {'ns0': 'http://www.opengis.net/kml/2.2'}
    
    nombre_subestacion_referencia = unidecode(nombre_subestacion_referencia).lower()

    try:
        for folder in root.findall(".//ns0:Folder", ns):
            folder_name = folder.find("ns0:name", ns).text
            if folder_name and ("proyectos s/e" in folder_name.lower()):
                print(f"Buscando en la carpeta: {folder_name}")
                for placemark in folder.findall(".//ns0:Placemark", ns):
                    placemark_name = placemark.find("ns0:name", ns).text
                    if placemark_name:
                        placemark_name_normalized = unidecode(placemark_name).lower()
                        if re.search(nombre_subestacion_referencia, placemark_name_normalized):
                            coordinates = placemark.find("ns0:Point/ns0:coordinates", ns).text.strip().split(",")
                            latitud = coordinates[1]
                            longitud = coordinates[0]
                            print(f"Subestación encontrada: {placemark_name}")
                            print(f"Latitud: {latitud}, Longitud: {longitud}")
                            return float(latitud), float(longitud)
                        
                        extended_data = placemark.find("ns0:ExtendedData/ns0:SchemaData", ns)
                        if extended_data is not None:
                            for simple_data in extended_data.findall("ns0:SimpleData", ns):
                                if simple_data.get("name") == "OBRA":
                                    obra_name = simple_data.text
                                    if obra_name:
                                        obra_name_normalized = unidecode(obra_name).lower()
                                        if re.search(nombre_subestacion_referencia, obra_name_normalized):
                                            coordinates = placemark.find("ns0:Point/ns0:coordinates", ns).text.strip().split(",")
                                            latitud = coordinates[1]
                                            longitud = coordinates[0]
                                            print(f"Subestación encontrada: {placemark_name}")
                                            print(f"Latitud: {latitud}, Longitud: {longitud}")
                                            return float(latitud), float(longitud)
                
        raise ValueError("No se encontraron coincidencias con el nombre de la subestación")
    
    except ValueError as e:
        print(e)
        return None
    except ET.ParseError:
        print("Error al parsear el archivo KML.")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def generar_segmento_linea_kml(nombre, tension, capacidad, nombre_proyecto, l_coordenadas, entrada_op):
    coordenadas_str = "\n".join([f"{coord[1]},{coord[0]},0" for coord in l_coordenadas])
    
    if "66" in tension:
        style_url = "#Linea66"

    elif "110" in tension:
        style_url = "#Linea110"

    elif "220" in tension:
        style_url = "#Linea220"

    kml_template = f"""
    <Placemark>
        <name>{nombre_proyecto}</name>
        <styleUrl>{style_url}</styleUrl>
        <ExtendedData>
            <SchemaData schemaUrl="#NuevaLine">
                <SimpleData name="NOMBRE">{nombre}</SimpleData>
                <SimpleData name="DECRETO">PET 2023</SimpleData>
                <SimpleData name="ESTADO">{entrada_op}</SimpleData>
                <SimpleData name="CAPACIDAD">{capacidad}</SimpleData>
                <SimpleData name="TRAZADO">{nombre_proyecto}</SimpleData>
            </SchemaData>
        </ExtendedData>
        <LineString>
            <tessellate>1</tessellate>
            <coordinates>{coordenadas_str}</coordinates>
        </LineString>
    </Placemark>

    """

    return kml_template.strip()

def agregar_linea_a_kml(kml_file, nombre, tension, capacidad, nombre_proyecto, coordenadas):
    try:
        tree = ET.parse(kml_file)
        root = tree.getroot()

    except ET.ParseError as e:
        print("Error al abrir el archivo KML: ", e)
        return None
    
    except FileNotFoundError as e:
        print("Error al abrir el archivo KML: ", e)
        return None
    
    except Exception as e:
        print("Error inesperado: ", e)
        return None
    
    ns = {'ns0': 'http://www.opengis.net/kml/2.2'}

    try:
        folder_nuevas_lineas = None
        for folder in root.findall(".//ns0:Folder", ns):
            print("Folder name: ", folder.find("ns0:name", ns).text)
            folder_name = folder.find("ns0:name", ns).text

        #vamos a buscar la subcarpeta correspondiente a la tension de la linea
        subfolder_tension = None
        for subfolder in folder_nuevas_lineas.findall(".//ns0:Folder", ns):
            subfolder_name = subfolder.find("ns0:name", ns).text
            print("Subfolder name: ", subfolder_name)
            if tension in subfolder_name:
                subfolder_tension = subfolder
                break

        segmento_linea_kml = generar_segmento_linea_kml(nombre, tension, capacidad, nombre_proyecto, coordenadas)
        segmento_linea = ET.fromstring(segmento_linea_kml)

        subfolder_tension.append(segmento_linea)

        tree.write(kml_file)

        print("Linea agregada con exito!!")

    except Exception as e:
        print("Error al agregar la linea al archivo KML: ", e)
        return None

def agregar_linea_a_kml_v2(kml_trinergy_file, kml_coordinador_file, diccionario_linea_kmz):
    #EDITAR LA EJECUCION PARA QUE FUNCIONE CON EL DICCIONARIO DE LINEAS
    l_coordenadas = []
    for se in diccionario_linea_kmz["subestaciones"]:
        nombre_se = f"Nueva S/E {se}"
        print(f"Buscando coordenadas de la subestacion {nombre_se}...")
        coordenadas = buscar_subestacion_por_nombre_trinergy_v3(kml_trinergy_file, nombre_se)
        if coordenadas is None:
            nombre_se_formato_coordinador = unidecode(se.lower())
            #nombre_se_formato_coordinador = f"s/e {nombre_se_formato_coordinador}"
            print(f"Buscando coordenadas de la subestacion {nombre_se_formato_coordinador}...")
            coordenadas = buscar_subestacion_por_nombre_coordinador(kml_coordinador_file, nombre_se_formato_coordinador)

            if coordenadas is None:
                #pedir input para ingresar las coordenadas manualmente
                print("No se encontraron las coordenadas de la subestacion")
                coordenadas = input("Ingrese las coordenadas de la subestacion (latitud, longitud): ")
                coordenadas = tuple(map(float, coordenadas.split(",")))
        
        print(f"Coordenadas de la subestacion {nombre_se}: {coordenadas}")
        l_coordenadas.append(coordenadas)

    print(f"Coordenadas de las subestaciones: {l_coordenadas}")

    # Cargar y parsear el archivo KL
    try:
        tree = ET.parse(kml_trinergy_file)
        root = tree.getroot()

    except ET.ParseError as e:
        print("Error al abrir el archivo KML: ", e)
        return None
    
    except FileNotFoundError as e:
        print("Error al abrir el archivo KML: ", e)
        return None
    
    except Exception as e:
        print("Error inesperado: ", e)
        return None
    
    ns = {'ns0': 'http://www.opengis.net/kml/2.2'}
    
    
    
    tree = ET.parse(kml_trinergy_file)
    root = tree.getroot()

    # Definir el namespace si es necesario
    ns = {'ns0': 'http://www.opengis.net/kml/2.2'}

    # Buscar la subcarpeta específica
    def find_subfolder(root, folder_name):
        for folder in root.findall('.//ns0:Folder', ns):
            element_name = folder.find('ns0:name', ns).text
            if element_name is not None and element_name == folder_name:
                return folder
        return None

    # Especifica el nombre de la subcarpeta que buscas
    subfolder_name = diccionario_linea_kmz["tension"]
    print(f'Buscando subcarpeta "{subfolder_name}"...')
    subfolder = find_subfolder(root, subfolder_name)


    if subfolder is not None:
        print(f'Subcarpeta "{subfolder_name}" encontrada.')
        segmento_linea_kml = generar_segmento_linea_kml(diccionario_linea_kmz["nombre"], diccionario_linea_kmz["tension"], diccionario_linea_kmz["capacidad"], diccionario_linea_kmz["nombre_proyecto"], l_coordenadas, diccionario_linea_kmz["entrada_operacion"])
        segmento_linea = ET.fromstring(segmento_linea_kml)

        subfolder.append(segmento_linea)


        tree.write(kml_trinergy_file)

        # Puedes trabajar con la subcarpeta encontrada aquí
    else:
        print(f'Subcarpeta "{subfolder_name}" no encontrada.')

########################################################################################
########################################################################################

def main_agregar_lineas_a_kmz(diccionario_kmz):
    kml_file = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "KMZs", "SEN_trinergy", "doc_trinergy.kml"))
    opc = ""
    while opc != "exit":
        opc = input("Pegar diccionario_kmz: ")

        agregar_linea_a_kml_v2(kml_file, diccionario_kmz["nombre_proyecto"], diccionario_kmz["tension"], "90 MVA", diccionario_kmz["nombre_proyecto"], diccionario_kmz["subestaciones"])

def main_agregar_proyecto_a_kmz():
    kml_file = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "KMZs", "SEN_trinergy", "doc_trinergy.kml"))

    diccionario_kmz = ""
    while diccionario_kmz != "exit":
        diccionario_kmz = input("Pegar diccionario_kmz: ")
        #Debemos convertir el string a un diccionario
        diccionario_kmz = eval(diccionario_kmz)

        agregar_proyecto_nuevo(kml_file, diccionario_kmz)


if __name__ == "__main__":
    main_agregar_lineas_a_kmz()
