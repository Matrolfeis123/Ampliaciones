from proyecto_ampliacion import *
from difflib import get_close_matches
import xml.etree.ElementTree as ET

#### Funciona para todo proyecto que posee un solo parrafo. 
### Cuando maneje como estructurar los de mas parrafos, va a funcionar tambien
### Tambien, me falta ver que hacer con los proyectos del tipo nuevas lineas e integrar las coordenadas de la misma.



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

# Uso de la función
# resultado = buscar_subestacion_por_nombre('ruta_al_archivo.kml', 'Nombre de la Subestacion')
# print(resultado)



def buscar_subestacion_por_nombre(kml_file, nombre_subestacion):

    tree = ET.parse(kml_file)
    root = tree.getroot()

    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    folders = root.findall(".//kml:Folder", ns)

    for folder in folders:
        name = folder.find("kml:name", ns).text
        if name == "Subestaciones":
            for placemark in folder.findall(".//kml:Placemark", ns):
                placemark_name = placemark.find("kml:name", ns).text.lower()
                nombre_subestacion = nombre_subestacion.lower()
                coincidencias = get_close_matches(nombre_subestacion, [placemark_name], n=1, cutoff=0.7) # si me esta encontrando mal segun el nombre de la subestacion, puedo cambiar el cutoff 
                
                if coincidencias:
                    print("Nombre: ", placemark.find("kml:name", ns).text)
                    longitud, latitud = placemark.find(".//kml:coordinates", ns).text.split(",")[0:2]
                    print("Coordenadas: ", placemark.find(".//kml:coordinates", ns).text.split(",")[0:2]) # Aca tenemos las coordenadas de la subestacion
                    print("Latitud: ", latitud)
                    print("Longitud: ", longitud)
                    return latitud, longitud #ver si entrego como tupla

def agregar_proyecto_ampliacion(kml_file, diccionario_proyecto):

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
        #Buscar la carpeta de ampliaciones, denominada: "Ampliaciones a S/E"
        folders = root.findall(".//kml:Folder", ns)
        targer_folder = None

        for folder in folders:
            name = folder.find("kml:name", ns).text
            if name == "Pruebas Desarrollo PET":
                target_folder = folder
                #crear un nuevo placemark
                placemark = ET.SubElement(folder, "{http://www.opengis.net/kml/2.2}Placemark")

                #crear un nombre para el placemark
                name = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}name")
                name.text = diccionario_proyecto["obra"]

                # Agregar el estilo del Placemark
                style_url = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}styleUrl")
                style_url.text = "#Ampli0"

                # Agregar los datos extendidos del Placemark
                extended_data = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}ExtendedData")
                schema_data = ET.SubElement(extended_data, "{http://www.opengis.net/kml/2.2}SchemaData", schemaUrl="#Ampli")

                simple_data_list = [
                    ("OBRA", diccionario_proyecto["obra"]),
                    ("DECRETO", diccionario_proyecto["decreto"]),
                    ("TIPO", diccionario_proyecto["tipo"]),
                    ("POSICIONES", diccionario_proyecto["pos_disp"]),
                    ("RESUMEN", diccionario_proyecto["resumen"] if diccionario_proyecto["resumen"] else "N/A")
                ]

                for key, value in simple_data_list:
                    data = ET.SubElement(schema_data, "{http://www.opengis.net/kml/2.2}SimpleData", {"name": key})
                    data.text = str(value)

                


                #Agregar las coordenadas del placemark
                point = ET.SubElement(placemark, "{http://www.opengis.net/kml/2.2}Point")
                coordinates = ET.SubElement(point, "{http://www.opengis.net/kml/2.2}coordinates")
                coordinates.text = f"{diccionario_proyecto["coordenadas"][1]},{diccionario_proyecto["coordenadas"][0]},0"

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


def main():


    file = "Codigos Definitivos\plan_expansion_final_2023.pdf"
    diccionario = generar_diccionario_ampliaciones(file)
    n_total_proyectos = len(diccionario)

    kml_file_consultas = "Codigos Definitivos\doc_coordinador.kml"
    kml_file_write = "Codigos Definitivos\SEN\doc.kml"

    lista_proyectos = ejecutar_analisis_2(diccionario, file)

    for proyecto in lista_proyectos:
        print(proyecto["Nombre S/E"])
        nombre = proyecto["Nombre S/E"]
        latitud, longitud = buscar_subestacion_por_nombre_v2(kml_file_consultas, proyecto["Nombre S/E"])
        proyecto["coordenadas"] = (float(latitud), float(longitud))
        print("\n")
        agregar_proyecto_ampliacion(kml_file_write, proyecto)
        breakpoint()


if __name__ == "__main__":
    main()