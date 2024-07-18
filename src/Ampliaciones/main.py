from funciones_extra import generar_diccionario_ampliaciones, generar_diccionario_descripciones_amp
from proyecto_ampliacion import Proyecto_ampliacion
import os
from unidecode import unidecode
from difflib import get_close_matches
import xml.etree.ElementTree as ET

############################################################################################################
#### Lista funciones que deben borrarse, ya que no se utilizan en el programa principal ####################
############################################################################################################

def buscar_subestacion_reserva(kml_file, nombre_subestacion):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    
    # Namespaces
    ns = {
        'kml': 'http://www.opengis.net/kml/2.2',
    }
    
    # Buscamos todas las subestaciones que coincidan con el nombre dado
    subestaciones = root.findall(".//kml:Placemark[kml:name[contains(text(), '{}')]]".format(nombre_subestacion), ns)
    
    if not subestaciones:
        print("No se encontró ninguna subestación con el nombre proporcionado.")
        return None

    # Si se encontró al menos una subestación
    opciones = []
    for i, sub in enumerate(subestaciones):
        nombre = sub.find('kml:name', ns).text
        coordinates = sub.find('.//kml:coordinates', ns).text
        opciones.append((nombre, coordinates))
    
    def mostrar_opciones(opciones):
        for i, (nombre, coordinates) in enumerate(opciones):
            print(f"Opción {i+1}: {nombre} - Coordenadas: {coordinates}")

    while True:
        mostrar_opciones(opciones)
        seleccion = input("Ingrese el número de la opción correcta (o 'n' para mostrar más opciones): ")

        if seleccion.lower() == 'n':
            # Mostrar siguientes 3 o 4 opciones
            if len(opciones) > 4:
                opciones = opciones[4:]
                if not opciones:
                    print("No hay más opciones disponibles.")
                    return None
            else:
                print("No hay más opciones disponibles.")
                return None
        else:
            try:
                seleccion = int(seleccion)
                if 1 <= seleccion <= len(opciones):
                    nombre_correcto, coordinates_correctas = opciones[seleccion-1]
                    print(f"Subestación seleccionada: {nombre_correcto} - Coordenadas: {coordinates_correctas}")
                    return nombre_correcto, coordinates_correctas
                else:
                    print("Opción no válida, por favor ingrese un número dentro del rango.")
            except ValueError:
                print("Entrada no válida, por favor ingrese un número.")

def buscar_subestacion_por_nombre_v2(kml_file, nombre_subestacion_referencia):
    """
    Busca la subestación en el archivo KML por el nombre proporcionado.

    Args:
        kml_file (str): Ruta del archivo KML.
        nombre_subestacion_referencia (str): Nombre de la subestación a buscar.

    Returns:
        tuple: Coordenadas de la subestación (latitud, longitud) si se encuentra.
        None: Si no se encuentra la subestación.
    """
    
    def parse_kml(kml_file):
        tree = ET.parse(kml_file)
        root = tree.getroot()
        return root

    def find_subestaciones_folder(root, ns):
        folders = root.findall(".//kml:Folder", ns)
        for folder in folders:
            name = folder.find("kml:name", ns).text
            if name == "Subestaciones":
                return folder
        return None

    def search_subestacion(folder, nombre_subestacion_referencia, ns):
        cutoff = 0.8
        while cutoff >= 0.5:
            for placemark in folder.findall(".//kml:Placemark", ns):
                placemark_name = placemark.find("kml:name", ns).text.lower()
                coincidencias = get_close_matches(nombre_subestacion_referencia.lower(), [placemark_name], n=1, cutoff=cutoff)
                if coincidencias:
                    return placemark, cutoff
            cutoff -= 0.1
        return None, cutoff

    def extract_coordinates(placemark, ns):
        coordinates = placemark.find(".//kml:coordinates", ns).text.split(",")
        return coordinates[1], coordinates[0]  # latitud, longitud
    
    root = parse_kml(kml_file)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    folder = find_subestaciones_folder(root, ns)
    
    if folder is None:
        print("No se encontró la carpeta 'Subestaciones' en el archivo KML.")
        return None
    
    try:
        placemark, cutoff = search_subestacion(folder, nombre_subestacion_referencia, ns)
        
        if placemark:
            while True:
                nombre = placemark.find("kml:name", ns).text
                latitud, longitud = extract_coordinates(placemark, ns)
                print(f"Nombre: {nombre}")
                print(f"Coordenadas: {latitud}, {longitud}")
                
                correcto = input("¿Es correcta la subestación? (True/False): ")
                
                if correcto.lower() == 'true':
                    return latitud, longitud
                else:
                    placemark, cutoff = search_subestacion(folder, nombre_subestacion_referencia, ns)
                    if not placemark or cutoff < 0.5:
                        raise ValueError("No se encontraron coincidencias con el nombre de la subestación")
        else:
            raise ValueError("No se encontraron coincidencias con el nombre de la subestación")
    
    except ValueError as e:
        print(e)
        return None


############################################################################################################



def agregar_proyecto_ampliacion_v2(kml_file, diccionario_proyecto, nombre_esquema):
    try:
        #parsear el archivo kml
        tree = ET.parse(kml_file)
        root = tree.getroot()

    except ET.ParseError as e:
        print("Error al parsear el archivo KML: ", e)
        return
    
    except FileNotFoundError as e:
        print("Error al abrir el archivo KML: ", e)
        return
    
    except Exception as e:
        print("Error inesperado: ", e)
        return
    
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    try:
        # Buscar la carpeta de ampliaciones, denominada: "Ampliaciones a S/E"
        folders = root.findall(".//kml:Folder", ns)
        target_folder = None

        for folder in folders:
            name = folder.find("kml:name", ns).text
            if name == "Ampliaciones":
                target_folder = folder
                # Crear un nuevo placemark
                placemark = ET.SubElement(folder, "{http://www.opengis.net/kml/2.2}Placemark")

                # Crear un nombre para el placemark
                name = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}name")
                name.text = diccionario_proyecto["obra"]

                # Agregar el estilo del Placemark
                style_url = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}styleUrl")
                style_url.text = f"#{nombre_esquema}"

                # Agregar los datos extendidos del Placemark
                extended_data = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}ExtendedData")
                schema_data = ET.SubElement(extended_data, "{http://www.opengis.net/kml/2.2}SchemaData", schemaUrl=f"#{nombre_esquema}")

                simple_data_list = [
                    ("OBRA", diccionario_proyecto["obra"]),
                    ("DECRETO", diccionario_proyecto["decreto"]),
                    ("TIPO", diccionario_proyecto["tipo"]),
                    ("VI", diccionario_proyecto["vi"]),
                    ("ENTRADA_OP", diccionario_proyecto["entrada_op"]),
                    ("RESUMEN", diccionario_proyecto["resumen"] if diccionario_proyecto["resumen"] else "N/A")
                ]



                dic_patios = diccionario_proyecto["patios"]
                for key, value in dic_patios.items():
                    simple_data_list.extend([
                        (f"{key}_tipo", value["tipo"]),
                        (f"{key}_tension", value["tension"]),
                        (f"{key}_configuracion", value["configuracion"]),
                        (f"{key}_conexiones", value["conexiones"]),
                        (f"{key}_posiciones_disponibles", value["posiciones_disponibles"])
                    ])

                dic_trafos = diccionario_proyecto["trafos"]
                for key, value in dic_trafos.items():
                    simple_data_list.extend([
                        (f"{key}_tipo", value.get("tipo", "N/A")),
                        (f"{key}_tension_trafo_reemplazado", value.get("tension_cap_trafo_reemplazado", "N/A")),
                        (f"{key}_tension_trafo_nvo", value.get("tension_cap_nvo_trafo", "N/A")),
                        (f"{key}_Capacidad", value.get("capacidad_trafo_nuevo", "N/A"))
                    ])


                dic_otros = diccionario_proyecto["otros"]
                parrafo = dic_otros.get("parrafo1", "N/A")
                simple_data_list.extend([
                    ("parrafo1", parrafo)
                ])

                for key, value in simple_data_list:
                    data = ET.SubElement(schema_data, "{http://www.opengis.net/kml/2.2}SimpleData", {"name": key})
                    data.text = str(value)

                point = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}Point")
                coordinates = ET.SubElement(point, "{http://www.opengis.net/kml/2.2}coordinates")
                coordinates.text = f"{diccionario_proyecto["coordenadas"][1]},{diccionario_proyecto["coordenadas"][0]}, 0"

                try:
                    tree.write(kml_file, encoding="utf-8", xml_declaration=True)
                except Exception as e:
                    print("Error al escribir el archivo KML: ", e)

        if not target_folder:
            raise KeyError("No se encontró la carpeta de ampliaciones")
            
    except KeyError as e:
        print(f"Clave faltante en diccionario_proyecto: {e}")
        return

    except Exception as e:
        print("Error inesperado: ", e)
        return

def agregar_proyecto_ampliacion_licitacion_v2(kml_file, diccionario_proyecto, nombre_esquema):
    try:
        #parsear el archivo kml
        tree = ET.parse(kml_file)
        root = tree.getroot()

    except ET.ParseError as e:
        print("Error al parsear el archivo KML: ", e)
        return
    
    except FileNotFoundError as e:
        print("Error al abrir el archivo KML: ", e)
        return
    
    except Exception as e:
        print("Error inesperado: ", e)
        return
    
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    try:
        # Buscar la carpeta de ampliaciones, denominada: "Ampliaciones a S/E"
        folders = root.findall(".//kml:Folder", ns)
        target_folder = None

        for folder in folders:
            name = folder.find("kml:name", ns).text
            if name == "Ampliaciones":
                target_folder = folder
                # Crear un nuevo placemark
                placemark = ET.SubElement(folder, "{http://www.opengis.net/kml/2.2}Placemark")

                # Crear un nombre para el placemark
                name = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}name")
                name.text = diccionario_proyecto["obra"]

                # Agregar el estilo del Placemark
                style_url = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}styleUrl")
                style_url.text = f"#{nombre_esquema}_l"

                # Agregar los datos extendidos del Placemark
                extended_data = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}ExtendedData")
                schema_data = ET.SubElement(extended_data, "{http://www.opengis.net/kml/2.2}SchemaData", schemaUrl=f"#{nombre_esquema}_l")

                simple_data_list = [
                    ("OBRA", diccionario_proyecto["obra"]),
                    ("DECRETO", diccionario_proyecto["decreto"]),
                    ("TIPO", diccionario_proyecto["tipo"]),
                    ("VI", diccionario_proyecto["vi"]),
                    ("ENTRADA_OP", diccionario_proyecto["entrada_op"]),
                    ("LICITACION", diccionario_proyecto["licitacion"]),
                    ("RESUMEN", diccionario_proyecto["resumen"] if diccionario_proyecto["resumen"] else "N/A")
                ]



                dic_patios = diccionario_proyecto["patios"]
                for key, value in dic_patios.items():
                    simple_data_list.extend([
                        (f"{key}_tipo", value["tipo"]),
                        (f"{key}_tension", value["tension"]),
                        (f"{key}_configuracion", value["configuracion"]),
                        (f"{key}_conexiones", value["conexiones"]),
                        (f"{key}_posiciones_disponibles", value["posiciones_disponibles"])
                    ])

                dic_trafos = diccionario_proyecto["trafos"]
                for key, value in dic_trafos.items():
                    simple_data_list.extend([
                        (f"{key}_tipo", value.get("tipo", "N/A")),
                        (f"{key}_tension_trafo_reemplazado", value.get("tension_cap_trafo_reemplazado", "N/A")),
                        (f"{key}_tension_trafo_nvo", value.get("tension_cap_nvo_trafo", "N/A")),
                        (f"{key}_Capacidad", value.get("capacidad_trafo_nuevo", "N/A"))
                    ])


                dic_otros = diccionario_proyecto["otros"]
                parrafo = dic_otros.get("parrafo1", "N/A")
                simple_data_list.extend([
                    ("parrafo1", parrafo)
                ])

                for key, value in simple_data_list:
                    data = ET.SubElement(schema_data, "{http://www.opengis.net/kml/2.2}SimpleData", {"name": key})
                    data.text = str(value)

                point = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}Point")
                coordinates = ET.SubElement(point, "{http://www.opengis.net/kml/2.2}coordinates")
                coordinates.text = f"{diccionario_proyecto["coordenadas"][1]},{diccionario_proyecto["coordenadas"][0]}, 0"

                try:
                    tree.write(kml_file, encoding="utf-8", xml_declaration=True)
                except Exception as e:
                    print("Error al escribir el archivo KML: ", e)

        if not target_folder:
            raise KeyError("No se encontró la carpeta de ampliaciones")
            
    except KeyError as e:
        print(f"Clave faltante en diccionario_proyecto: {e}")
        return

    except Exception as e:
        print("Error inesperado: ", e)
        return

def buscar_subestacion_por_nombre_v3(kml_file, nombre_subestacion_referencia):
    """
    Busca la subestación en el archivo KML por el nombre proporcionado y maneja casos de múltiples coincidencias.

    Args:
        kml_file (str): Ruta del archivo KML.
        nombre_subestacion_referencia (str): Nombre de la subestación a buscar.

    Returns:
        tuple: Coordenadas de la subestación (latitud, longitud) si se encuentra.
        None: Si no se encuentra la subestación.
    """
    
    def parse_kml(kml_file):
        tree = ET.parse(kml_file)
        root = tree.getroot()
        return root

    def find_subestaciones_folder(root, ns):
        folders = root.findall(".//kml:Folder", ns)
        for folder in folders:
            name = folder.find("kml:name", ns).text
            if name == "Subestaciones":
                return folder
        return None

    def search_subestaciones(folder, nombre_subestacion_referencia, ns):
        placemarks = []
        cutoff = 0.8
        while cutoff >= 0.5:
            for placemark in folder.findall(".//kml:Placemark", ns):
                placemark_name = placemark.find("kml:name", ns).text.lower()
                coincidencias = get_close_matches(nombre_subestacion_referencia.lower(), [placemark_name], n=1, cutoff=cutoff)
                if coincidencias:
                    placemarks.append((placemark, cutoff))
            if placemarks:
                break
            cutoff -= 0.1
        return placemarks

    def extract_coordinates(placemark, ns):
        coordinates = placemark.find(".//kml:coordinates", ns).text.split(",")
        return coordinates[1], coordinates[0]  # latitud, longitud

    root = parse_kml(kml_file)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    folder = find_subestaciones_folder(root, ns)
    
    if folder is None:
        print("No se encontró la carpeta 'Subestaciones' en el archivo KML.")
        return None
    
    try:
        placemarks = search_subestaciones(folder, nombre_subestacion_referencia, ns)
        
        if placemarks:
            while True:
                for i, (placemark, cutoff) in enumerate(placemarks[:4]):
                    nombre = placemark.find("kml:name", ns).text
                    latitud, longitud = extract_coordinates(placemark, ns)
                    print(f"Opción {i+1}:")
                    print(f"  Nombre: {nombre}")
                    print(f"  Coordenadas: {latitud}, {longitud}")
                
                seleccion = input("Seleccione el número de la subestación correcta ('0' para buscar más o exit para ingreso manual al final): ")
                
                if seleccion.isdigit() and 0 <= int(seleccion) <= len(placemarks):
                    seleccion = int(seleccion)
                    if seleccion == 0:
                        placemarks = search_subestaciones(folder, nombre_subestacion_referencia, ns)
                        if not placemarks:
                            raise ValueError("No se encontraron más coincidencias con el nombre de la subestación")
                    else:
                        return extract_coordinates(placemarks[seleccion-1][0], ns)
                    
                elif seleccion.lower() == 'exit':
                    return "manual", "manual"
                else:
                    print("Selección inválida, por favor intente nuevamente.")
        else:
            raise ValueError("No se encontraron coincidencias con el nombre de la subestación")
    
    except ValueError as e:
        print(e)
        return None

def identificar_disenos(diccionarios):
    """
    Identifica los diseños únicos necesarios a partir de una lista de diccionarios.
    
    :param diccionarios: Lista de diccionarios con las claves 'patios', 'trafos', y 'otros'.
    :return: Lista de combinaciones únicas de diseños necesarios.
    """
    disenos_unicos = set()

    for diccionario in diccionarios:
        combinacion = (diccionario['patios'], diccionario['trafos'], diccionario['otros'])
        disenos_unicos.add(combinacion)

    return list(disenos_unicos)

def agregar_proyecto_ampliacion(proyecto, kml_write):
    print("\n")
    print(proyecto.imprimir_resumen_atributos_proyecto())
    print("\n")

    kml_file_consultas = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "KMZs", "SEN_coordinador", "doc_coordinador.kml"))

    latitud, longitud = buscar_subestacion_por_nombre_v3(kml_file_consultas, unidecode(proyecto.diccionario_proyecto["nombre_se"]))

    if latitud == "manual" or longitud == "manual":
        print("El proyecto se manejara manualmente al final de la ejecucion")
        return "manual"

    elif latitud and longitud:
        print(f"Coordenadas de la subestación: {latitud}, {longitud}")
        proyecto.diccionario_proyecto["coordenadas"] = (float(latitud), float(longitud))

        esquema = f"Amp_{proyecto.diccionario_proyecto['n_patios']}{proyecto.diccionario_proyecto['n_trafos']}{proyecto.diccionario_proyecto['n_otros']}"
        print(f"Esquema: {esquema}")
        try:
            print(proyecto.diccionario_proyecto["licitacion"])
            if proyecto.licitacion:
                agregar_proyecto_ampliacion_licitacion_v2(kml_write, proyecto.diccionario_proyecto, esquema)
            
            else:
                agregar_proyecto_ampliacion_v2(kml_write, proyecto.diccionario_proyecto, esquema)
        
        except Exception as e:
            print("Error al agregar proyecto al KMZ: ", e)
            return agregar_proyecto_ampliacion(proyecto)

        print("Proyecto agregado exitosamente al archivo KML.")
        return
    
    else:
        print("No se encontraron coordenadas para la subestación.")
        print(("El proyecto se manejara manualmente al final de la ejecucion"))
        return "manual"

def menu_opciones_proyectos(l_proyectos, kml_write):

    l_proy_manual = []
    
    for proyecto in l_proyectos:
        print("\n")
        print("Informacion del Proyecto: \n")

        for key, value in proyecto.diccionario_proyecto.items():
            print(f"{key}: {value}")

        print("\n")
        print("¿Qué desea hacer?")
        print("1. Agregar proyecto al KMZ")
        print("2. Manejar Manualmente y Continuar con el siguiente proyecto")
        print("3. Salir del programa")
        print("\n")
        opcion = input("Ingrese el número de la opción deseada: ")

        if opcion == "1":
            print("Implementar función para agregar proyecto al KMZ")
            qtal = agregar_proyecto_ampliacion(proyecto, kml_write)

            if qtal == "manual":
                l_proy_manual.append(proyecto)
                l_proyectos.remove(proyecto)
                continue

            else:
                l_proyectos.remove(proyecto)
                continue
        

        elif opcion == "2":
            l_proy_manual.append(proyecto)
            l_proyectos.remove(proyecto)
            continue
        
        elif opcion == "3":
            print("Saliendo del programa...")
            exit()


        elif opcion == "123":
            breakpoint()
            

        else:
            print("Opción inválida. Por favor, ingrese una opción válida.")
            return menu_opciones_proyectos(l_proyectos)
    

    return l_proy_manual

def informe_proyectos_no_procesados(l_proyectos):
    print("Proyectos no procesados: \n")
    for proyecto in l_proyectos:
        print(proyecto.imprimir_resumen_atributos_proyecto())

    print("\n")

    # Implementar función para guardar los proyectos no procesados en un archivo de texto
    print("Guardando proyectos no procesados en un archivo de texto...")
    with open("proyectos_no_procesados.txt", "w") as file:
        for proyecto in l_proyectos:
            file.write(proyecto.imprimir_resumen_atributos_proyecto())
            file.write("\n")

    print("Proyectos no procesados guardados exitosamente.")
    return


def main():
    pdf_file = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "PDFs", "plan_expansion_final_2023.pdf"))
    kml_write = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "KMZs", "archivo_en_blanco.kml"))

    dic_amp = generar_diccionario_ampliaciones(pdf_file)
    dic_desc_amp = generar_diccionario_descripciones_amp(pdf_file, dic_amp)

    conteo_casos = []

    lista_proyectos = []
    lista_proyectos_manuales = []

    for titulo, descripcion in dic_desc_amp.items():
        try:
            proyecto = Proyecto_ampliacion(titulo, descripcion)
            proyecto.procesar_proyecto()
            print(proyecto.nombre_proyecto)
            print(proyecto.licitacion)
            conteo_casos.append(proyecto.resultado)
            lista_proyectos.append(proyecto)

        
        except Exception as e:
            print(f"Error: {e}")
            continue

    print("\n")
    disenos_unicos = identificar_disenos(conteo_casos)
    print(disenos_unicos)
    print("\n")
    lista_proyectos_manuales = menu_opciones_proyectos(lista_proyectos, kml_write)
    print("\n")
    print("Proyectos procesados, vamos con los manuales: \n")
    print("\n")


    if lista_proyectos_manuales:
        informe_proyectos_no_procesados(lista_proyectos_manuales)
        print("Proyectos manuales: \n")
        for proyecto in lista_proyectos_manuales:
            print(proyecto.imprimir_resumen_atributos_proyecto())
            print("\n")
            print("Continuar implementacion...")




    # print(conteo_casos)
    # print("\n")
    # disenos_unicos = identificar_disenos(conteo_casos)
    # print(disenos_unicos)
    # print("\n")
    # print(lista_proyectos)
    

        


if __name__ == "__main__":
    main()

