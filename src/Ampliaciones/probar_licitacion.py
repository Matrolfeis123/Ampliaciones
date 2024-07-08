import re
import pdfplumber
from unidecode import unidecode

# def generar_diccionario_ampliaciones(file):
#     diccionario_obras_ampliacion = {}

#     paginas = [1, 2]

#     with pdfplumber.open(file) as pdf:
#         text = ""
#         for i in paginas:
#             text += pdf.pages[i].extract_text()

#         matches = re.finditer(r'((Ampliación en S/E).*?)(?=\n\S)', text, re.DOTALL)
#         for match in matches:
#             line = match.group(0)
#             if not re.match(r".*[0-9]{2}$", line):
#                 print("Título largo: ", line)
#                 titulo = input("Ingrese el título del proyecto según el índice del pdf: ")
#                 pag_inicio = int(input("Ingrese la página de inicio del proyecto según el índice del pdf: ")) - 1
#                 pag_final = pag_inicio + 3

#             else:
#                 match = re.match(r'^(.*?)\s+(\d+)$', line)
#                 if match:
#                     titulo = match.group(1).replace(".", "").strip()
#                     pag_inicio = int(match.group(2)) - 1
#                     pag_final = pag_inicio + 3

            
#             diccionario_obras_ampliacion[titulo] = (pag_inicio, pag_final)


#     return diccionario_obras_ampliacion


# def extraer_texto_entre_delimitadores_v2(texto, delimitador_inicial, delimitador_final, delimitador_opcional=None):
#     if delimitador_opcional:
#         pattern = re.compile(
#             rf"{re.escape(delimitador_inicial)}(.*?)(?:{re.escape(delimitador_final)}|{re.escape(delimitador_opcional)}).*?\.",
#             re.DOTALL
#         )
#     else:
#         pattern = re.compile(
#             rf"{re.escape(delimitador_inicial)}(.*?){re.escape(delimitador_final)}.*?\.",
#             re.DOTALL
#         )
#     match = pattern.search(texto)
#     return match.group(0) if match else "ERROR EXTRAYENDO TEXTO"


# def generar_diccionario_descripciones_amp(file, diccionario):
#     dic_descripciones = {}
#     titulos_proyectos = list(diccionario.keys())
#     print(titulos_proyectos)
#     try:

#         with pdfplumber.open(file) as pdf:
#             for titulo, paginas in diccionario.items():
#                 indice_titulo_actual = titulos_proyectos.index(titulo)
#                 indice_titulo_sig = indice_titulo_actual + 1
#                 print(f"Procesando proyecto {indice_titulo_actual} de {len(titulos_proyectos)}: {titulo}")

#                 text = ""
#                 for i in range(paginas[0], paginas[1] + 1):
#                     text += pdf.pages[i].extract_text()

#                 text = text.replace("\n", " ").replace("  ", " ")
#                 texto_limpio = re.sub(r'\d{1,2}—–——–', "", text)
#                 texto_limpio = re.sub(r'—–——–', "", texto_limpio).replace("  ", " ")

#                 descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación de la obra", titulos_proyectos[indice_titulo_sig], "La adjudicación de esta obra quedará")
#                 if unidecode(titulos_proyectos[indice_titulo_sig].lower()) in unidecode(descripcion_def.lower()):
#                     #vamos a buscar el indice del split
#                     descripcion_minuscula = unidecode(descripcion_def.lower())
#                     titulo_sig_minuscula = unidecode(titulos_proyectos[indice_titulo_sig].lower())
#                     indice_separar = descripcion_minuscula.index(titulo_sig_minuscula)
#                     descripcion_def = descripcion_def[:indice_separar]
                    

#                 else:
#                     descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación de la obra", "moneda de los Estados Unidos de América")
                
#                 breakpoint()

#                 if titulo.strip() == "Ampliación en S/E Las Arañas (RTR ATMT)":
#                     texto_limpio = re.sub(r'\d{1,2}—–——–', "", text)
#                     texto_limpio = re.sub(r'—–——–', "", texto_limpio)
#                     texto_limpio = texto_limpio.replace("  ", " ")
#                     descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación de la obra El proyecto consiste en el aumento de capacidad de la subestación Las Arañas", "moneda de los Estados Unidos de América")

#                 dic_descripciones[titulo] = descripcion_def
                    


#     except Exception as e:
#         print(f"Error en la ejecución del análisis: {e}")


#     return dic_descripciones


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
                    titulo = match.group(1).replace(".", "").strip()
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

                text = text.replace("\n", " ").replace("  ", " ")
                texto_limpio = re.sub(r'\d{1,2}—–——–', "", text)
                texto_limpio = re.sub(r'—–——–', "", texto_limpio).replace("  ", " ")
                descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación", "Ministerio de Energía.")
                # Si en descripcion def se encuentra mas de dos veces la frase "Descripción general y ubicación", cambiamos la busqueda
                if descripcion_def.count("Descripción general y ubicación") >= 2 or descripcion_def == "ERROR EXTRAYENDO TEXTO":
                    descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación", "del presente Informe")
                    print("Caso Descrpcion general y ubicación > 2 veces")

                    if descripcion_def.count("Descripción general y ubicación") >= 2 or descripcion_def == "ERROR EXTRAYENDO TEXTO":
                        descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación", "moneda de los Estados Unidos de América")
                        print("Caso Descrpcion general y ubicación > 2 veces")
                

                if titulo.strip() == "Ampliación en S/E Las Arañas (RTR ATMT)":
                    texto_limpio = re.sub(r'\d{1,2}—–——–', "", text)
                    texto_limpio = re.sub(r'—–——–', "", texto_limpio)
                    texto_limpio = texto_limpio.replace("  ", " ")
                    descripcion_def = extraer_texto_entre_delimitadores_v2(texto_limpio, "Descripción general y ubicación de la obra El proyecto consiste en el aumento de capacidad de la subestación Las Arañas", "moneda de los Estados Unidos de América")

                dic_descripciones[titulo] = descripcion_def
                breakpoint()

    except Exception as e:
        print(f"Error en la ejecución del análisis: {e}")


    return dic_descripciones



if __name__ == "__main__":

    file = "src\Ampliaciones\plan_expansion_final_2023.pdf"
    dic_amp = generar_diccionario_ampliaciones(file)
    dic_desc_amp = generar_diccionario_descripciones_amp(file, dic_amp)
