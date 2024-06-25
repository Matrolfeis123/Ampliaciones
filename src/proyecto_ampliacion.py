import spacy
from spacy import displacy
from spacy.matcher import Matcher
import re
import time
import pdfplumber
from openpyxl import Workbook


############################################################################################################
############################################# PROYECTO AMPLIACION ###########################################
############################################################################################################
### Estos comentarios nos serviran como guia para conectar el codigo con el resto de los modulos del proyecto
### y para entender el funcionamiento del codigo.

### Este modulo se encarga de extraer la informacion de los proyectos de ampliacion de subestaciones,
### a partir de los informes de planificacion de expansion. Para esto, se extrae la informacion de las ampliaciones
### de subestaciones, y se procesa la informacion de cada proyecto de ampliacion, para extraer la informacion
### relevante de cada proyecto, como el nombre, la configuracion del patio, el numero de posiciones, las conexiones
### y las posiciones disponibles.
############################################################################################################
############################################################################################################
############################################################################################################
################################ ¿Como necesito el output de cada proyecto? ################################
### Necesito un diccionario con la siguiente estructura:
### diccionario = {
###     "Nombre Proyecto": "Ampliacion XXXX",
###     "Nombre S/E": "Nombre de la subestacion",
###     "Tipo": "Ampliacion",
###     "Posiciones": Numero,
###     "Resumen": "Descripcion general del proyecto" 
###     }



# Cargar el modelo en español
nlp = spacy.load("es_core_news_lg")

def generar_diccionario_ampliaciones(file):


    diccionario = {}

    paginas = [1, 2]
    lista_titulos_problemas = []

    with pdfplumber.open(file) as pdf:
        for i in paginas:
            page = pdf.pages[i]
            text = page.extract_text()

            lines = text.split("\n")

            for line in lines:
                if "Ampliación en S/E" in line:
                    if not re.match(r".*[0-9]{1,2}$", line):
                        lista_titulos_problemas.append(line)
                        print("No se pudo extraer el número de problema de la línea: ", line)


                    else:
                        match = re.match(r'^(.*?)\s+(\d+)$', line)
                        if match:
                            titulo = match.group(1).replace(".", "").strip()
                            #print("Título: ", titulo)
                            pag_inicio = int(match.group(2)) - 1
                            #print("Página de inicio: ", pag_inicio)
                            pag_final = pag_inicio + 1

                            diccionario[titulo] = (pag_inicio, pag_final)

    return diccionario

# Vamos a probar la funcion ejecutar analisis
def ejecutar_analisis_2(diccionario_final, file):

    ### Esta ejecucion es una version en la cual los parrafos se ven mejor y mas legible en la consola, sin embargo 
    ### no estoy seguro si funcionaria con el resto del codigo. Me podria ser util para mas adelante identificar 
    ### los parametros que me falta extraer de los proyectos para su uso en el KML.

    #data = [['Nombre Proyecto', 'Nro patios', "N° Posiciones disponibles"]]

    lista_proyectos = []


    for titulo, paginas in diccionario_final.items():
        try:
            pagina_inicio = paginas[0]
            pagina_final = paginas[1] + 1

            # Extraer texto de las páginas seleccionadas
            with pdfplumber.open(file) as pdf:
                text = ' '.join([pdf.pages[i].extract_text() for i in range(pagina_inicio, pagina_final) if pdf.pages[i].extract_text()])

            # Filtrar el texto para obtener la descripción
            descripcion = ''
            descripcion_general = text[text.find("Descripción general y ubicación"):]


            if titulo == "4113 Ampliación en S/E Bollenar 110 kV (BS)":
                #Este caso es especial, ya que esta descripcion se encuentra en la misma pagina que el proyecto Bollenar. De esta forma, logramos extraer la descripcion de este caso especial de forma correcta.
                descripcion_general = descripcion_general[descripcion_general.find("\n4.1.14 AMPLIACIÓN EN S/E LAS ARAÑAS (RTR ATMT)\n4.1.14.1 Descripción general y ubicación de la obra"):]

            
            if descripcion_general:
                descripcion_general = descripcion_general[descripcion_general.find("\n"):]
                final_descripcion = descripcion_general.find("El proyecto incluye todas las obras")
                descripcion = descripcion_general[:final_descripcion]




            # # Procesar la descripción con SpaCy
            if descripcion:
                # vamos a reemplazar los "\n" que estan al interior de la descripcion por un espacio en blanco
                descripcion = descripcion.replace("\n", " ")

                proyecto = Proyecto_ampliacion(descripcion)
                proyecto.procesar_texto_v2()
                #proyecto.resumen_proyecto_por_patio()
                #vamos a reemplazar los digitos numericos del principio de cada titulo, para guardarlo como nombre del proyecto
                nombre_proyecto = re.sub(r'^\d+\s', '', titulo)
                proyecto.nombre_proyecto = nombre_proyecto

                proyecto.nombre = f"S/E {proyecto.nombre}"

                diccionario_output_proyecto = {
                    "obra": proyecto.nombre_proyecto,
                    "decreto": "PET Final 2023",
                    "tipo": proyecto.tipo,
                    "pos_disp": proyecto.posiciones_disponibles,
                    "Nombre Proyecto": proyecto.nombre_proyecto,
                    "Nombre S/E": proyecto.nombre,
                    "Tipo": proyecto.tipo,
                    "Posiciones": proyecto.posiciones_disponibles,
                    "resumen": proyecto.resumen_proyecto
                }

                lista_proyectos.append(diccionario_output_proyecto)

        except Exception as e:
            error_message = f"Error en el proyecto {titulo}: {str(e)}"
            print(error_message)
            #breakpoint()

            diccio_proy = {
                "Nombre Proyecto": titulo,
                "Nombre S/E": "No se pudo extraer",
                "Tipo": "Ampliacion",
                "Posiciones": "No se pudo extraer",
                "Resumen": "No se pudo extraer"
            }

            lista_proyectos.append(diccio_proy)



    return lista_proyectos
        


class Proyecto_ampliacion:
    def __init__(self, texto):
        self.nlp = nlp
        self.doc = self.nlp(texto.strip())
        self.nombre = None
        self.tipo = "Ampliación"
        #self.ubicacion = None
        self.nombre_proyecto = None
        self.numero_posiciones = None
        self.patios = [] #??
        self.lista_conexiones = []
        self.posiciones_disponibles = "No procesed"

        self.resumen_proyecto = ""
        self.cofiguracion = ""
        self.objetivo = ""


    def __str__(self):
        return f"Nombre: {self.nombre}\nTipo: {self.tipo}"
    

    def encontrar_indices_parrafos(self):
        indices = []
        for sent in self.doc.sents:
            if sent.text.startswith("El proyecto consiste en") or \
            sent.text.startswith("A su vez, el proyecto incluye") or \
            sent.text.startswith("A su vez, el proyecto considera") or \
            sent.text.startswith("A su vez, el proyecto consiste en") or \
            sent.text.startswith("A su vez, el proyecto contempla") or \
            sent.text.startswith("A su vez, el proyecto considera") or \
            sent.text.startswith("Adicionalmente, el proyecto considera") or \
            sent.text.startswith("Adicionalmente, el proyecto contempla") or \
            sent.text.startswith("Además, el proyecto contempla") or \
            sent.text.startswith("Además, el proyecto considera"):
                indices.append((sent.start, sent.end))

                # probar con  or \ sent.text.startswith("El proyecto contempla")
        
        return indices


    def extraer_nombre(self):
        name_pattern = [
        {"LOWER": "de"}, 
        {"LOWER": "la"}, 
        {"LOWER": "subestación"},    
        {"IS_ALPHA": True, "OP": "+"},
        {"IS_PUNCT": True, "OP": "*"}]

        matcher = Matcher(self.nlp.vocab)
        matcher.add("nombre", [name_pattern])

        matches = matcher(self.doc)

        for match_id, start, end in matches:
            span = self.doc[start:end]
            nombre = span.text
            nombre = nombre.replace("de la subestación", "").strip()
            nombre = nombre.replace(",", "")

            #si el nombre posee mas de 3 palabras, vamos a tomar solo la primera palabra
            if len(nombre.split()) > 3:
                #print("Nombre antes:", nombre)
                nombre = nombre.split()[0:2]
                nombre = " ".join(nombre)
                nombre = nombre.replace("mediante", "")
                #print("Nombre despues:", nombre)
                break

        return nombre
        
   
    def extraer_info_patio(self):
  

        matcher = Matcher(self.nlp.vocab)

        # Primero, creamos el patron para extraer el patio junto a su tension
        patron_patio = [{"LOWER": "patio"}, {"LOWER": "de"}, {"POS": "NUM"}, {"LOWER": "kv"}]
        matcher.add("patio", [patron_patio])


        # Ahora, vamos a extraer la configuracion del patio
        patron_configuracion = [{"LOWER": "cuya"}, {"LOWER": "configuración"}, {"LOWER": "corresponde"}, {"LOWER": "a"}, {"IS_ALPHA": True, "OP": "*"}, {"IS_PUNCT": True, "OP": "*"}]
        matcher.add("configuracion", [patron_configuracion])

        # Ahora, vamos a extraer las conexiones
        patron_conexiones = [{"LOWER": "de"}, {"LOWER": "manera"}, {"LOWER": "de"}, {"LOWER": "permitir"}, {"LOWER": "la"}, {"LOWER": "conexión"}]
        matcher.add("conexiones", [patron_conexiones])

        # Para el numero de posiciones, sabemos que siempre se encuentra un par de tokens antes del inicio de la descripcion de las conexiones
        # Por lo tanto, vamos a extraer el numero de posiciones a partir de la descripcion de las conexiones


        matches = matcher(self.doc)

        for match_id, start, end in matches:
            if self.nlp.vocab.strings[match_id] == "patio":
                span = self.doc[start:end]
                patio = span.text
                print("Patio:", patio)

            elif self.nlp.vocab.strings[match_id] == "configuracion":
                span = self.doc[start:end-1]
                configuracion = span.text
                print("Configuracion:", configuracion)

            elif self.nlp.vocab.strings[match_id] == "conexiones":
                # para este caso, vamos a extender el "end" del span hasta el siguiente punto, tal que podamos extraer las conexiones
                #para esto, vamos a buscar el siguiente punto a partir del end del span
                for token in self.doc[end:]:
                    if token.text == ".":
                        end_conexiones = token.i
                        break

                span = self.doc[start:end_conexiones] #podria reemplazar start por end, asi no incluyo la frase "de manera de permitir la conexion"
                conexiones = span.text
                print("Conexiones:", conexiones)




        #Ahora, vamos a ver que datos no fueron encontrados para evaluar caso a caso
        if not patio:
            print("No se encontró el patio")

        if not configuracion:
            print("No se encontró la configuración del patio")

        if not conexiones:
            print("No se encontraron las conexiones del patio")
   
    
    def extraer_configuracion(self, parrafo):
        l_configs = ["barra principal seccionada y barra de transferencia", "interruptor y medio", 
                     "doble barra principal y barra de transferencia", "doble barra principal y barra de transferencia", 
                     "doble barra principal con barra de transferencia", "barra simple", "barra principal con barra de transferencia"]
        configuracion = None
        #vamos a comprobar si la configuracion del patio se encuentra en el parrafo
        print(parrafo)
        for config in l_configs:
            if config in parrafo:
                return config
            
            else:
                configuracion = "No se encontró la configuración del patio"

        return configuracion


    def extraer_numero_posiciones(self, doc_parrafo):
        nro_posiciones = 0
        numeros = {
            "uno": 1,
            "una": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
            "siete": 7,
            "ocho": 8,
            "nueve": 9,
            "diez": 10
        }

        for token in doc_parrafo:
            if token.text == "posición" or token.text == "diagonal":
                numero = numeros.get(doc_parrafo[token.i - 1].text, doc_parrafo[token.i - 1].text)
                nro_posiciones = numero

                if token.text == "diagonal":
                    nro_posiciones *= 2

                return nro_posiciones

            if (token.text == "posiciones" or token.text == "diagonales") and doc_parrafo[token.i -2].like_num: #falta variar el caso de que sea el (token.i - 1)
                # Si encontramos la palabra "posiciones" o "diagonales", vamos a buscar el token anterior para ver si contiene un numero
                numero = numeros.get(doc_parrafo[token.i - 2].text, doc_parrafo[token.i - 2].text)

                if token.text == "diagonales":
                    nro_posiciones = numero * 2
                    return nro_posiciones
                    #print(f"El patio {self.nombre} tiene {self.numero_posiciones} posiciones")

                elif token.text == "posiciones":
                    nro_posiciones = numero
                    return nro_posiciones
                    #print(f"El patio {self.nombre} tiene {self.numero_posiciones} posiciones")

                else:
                    print("No se encontraron coincidencias")
                    nro_posiciones = None
                    return nro_posiciones
                
            elif (token.text == "posiciones" or token.text == "diagonales") and doc_parrafo[token.i - 1].like_num:
                numero = numeros.get(doc_parrafo[token.i - 1].text, doc_parrafo[token.i - 1].text)
                
                if token.text == "diagonales":
                    nro_posiciones = numero * 2
                    return nro_posiciones
                    #print(f"El patio {self.nombre} tiene {self.numero_posiciones} posiciones")

                elif token.text == "posiciones":
                    nro_posiciones = numero
                    return nro_posiciones
                    #print(f"El patio {self.nombre} tiene {self.numero_posiciones} posiciones")

                else:
                    print("No se encontraron coincidencias")
                    nro_posiciones = None
                    return nro_posiciones

            elif (token.text == "paños") and doc_parrafo[token.i -1].like_num:
                numero = numeros.get(doc_parrafo[token.i - 1].text, doc_parrafo[token.i - 1].text)
                nro_posiciones = str(numero)+" paño(s)"


        return nro_posiciones


    def extraer_conexiones(self, doc_parrafo):
        try:
            matcher = Matcher(self.nlp.vocab)
            patron_conexiones_inicio = [{"LOWER": "permitir"}, {"LOWER": "la"}, {"LOWER": "conexión"}]
            matcher.add("conexiones", [patron_conexiones_inicio])

            matches = matcher(doc_parrafo)

            if matches:
                end = matches[0][2]

                conexiones = doc_parrafo[end:].text.split(",")
                conexiones = [conexion.strip() for conexion in conexiones]
                return conexiones
            

        except Exception as e:
            print(f"Error: {e}")
            #Podria manejar un mensaje tipo N/A o None, para manejar el caso en otras funciones

        return "No se encontraron conexiones"
    

    def calcular_posiciones_disponibles(self):
        numeros = {
            "uno": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
            "siete": 7,
            "ocho": 8,
            "nueve": 9,
            "diez": 10
        }

        self.posiciones_disponibles = int(self.numero_posiciones)


        try:
            for conexion in self.lista_conexiones:
                            # Todas estas condiciones podria pasar a lower o lemma con spacy, tal que no tenga que hacer tantas comparaciones(?)

                if "seccionamiento" in conexion:
                    # En este caso, se debe buscar la configuracion de la linea seccionada, contenida en conexiones con un patron del tipo dxddd, donde nos interesa el digito antes de la x.
                    # Podriamos buscar el patron {"SHAPE": {"IN":["dxddd", "dxdd", "dxd", "ddxd", "ddxdd", "ddxddd", "dddxd", "dddxdd", "dddxddd"]}, "OP": "+"} con el matcher
                    patron = r'\b\d+x\d{2,3}\b'
                    match = re.findall(patron, conexion)
                    ## OJO EN ESTE CASO, TENGO QUE HACER LA DIFERENCIA ENTRE EL SECCIONAMIENTO Y UNA NUEVA LINEA UNICAMENTE??
                    # ES DECIR, ES DISTINTO "EL SECCIONAMIENTO DE ... 2x110 ..." QUE "la conexión de la nueva línea 2x110 "

                    if match:
                        for tension in match:
                            posic_ocup = int(tension[0])*2
                            self.posiciones_disponibles -= posic_ocup

                    else:
                        print("No se encontraron coincidencias")


                elif ("de la línea") in conexion:

                    patron = r'\b\d+x\d{2,3}\b'
                    match = re.search(patron, conexion)

                    if match:
                        #print("Configuracion de la linea seccionada:", match.group())
                        posic_ocup = int(match.group()[0])
                        self.posiciones_disponibles -= posic_ocup

                    else:
                        print("No se encontraron coincidencias")

                elif "de la nueva línea" in conexion:
                    patron = r'\b\d+x\d{2,3}\b'
                    match = re.search(patron, conexion)

                    if match:
                        #print("Configuracion de la linea seccionada:", match.group())
                        posic_ocup = int(match.group()[0])
                        self.posiciones_disponibles -= posic_ocup

                    else:
                        print("No se encontraron coincidencias")


                elif "de las líneas" in conexion:
                    patron = r'\b\d+x\d{2,3}\b'
                    match = re.search(patron, conexion)

                    if match:
                        #print("Configuracion de la linea seccionada:", match.group())
                        posic_ocup = int(match.group()[0])
                        self.posiciones_disponibles -= posic_ocup

                    else:
                        print("No se encontraron coincidencias")

                

                elif "de la obra" in conexion:

                    patron = r'\b\d+x\d{2,3}\b'
                    coincidencias = re.findall(patron, conexion)
                    

                    if coincidencias:
                        for coincidencia in coincidencias:
                            posic_ocup = int(coincidencia[0])
                            self.posiciones_disponibles -= posic_ocup

                    else:
                        print("Problemas posiciones nuevas obras, calculo posiciones.")
                        self.posiciones_disponibles = "REVISAR LOGICA!"

                elif "nuevas líneas" in conexion:
                    patron = r'\b\d+x\d{2,3}\b'
                    match = re.search(patron, conexion)

                    if match:
                        #print("Configuracion de la linea seccionada:", match.group())
                        posic_ocup = int(match.group()[0])
                        self.posiciones_disponibles -= posic_ocup

                    else:
                        print("No se encontraron coincidencias")


                elif "transformador" in conexion and "banco" not in conexion:
                    # un transformador utiliza una unica posicion
                    self.posiciones_disponibles -= 1



                elif "paño" in conexion:
                    if "paño acoplador" in conexion and "paño seccionador" in conexion:
                        self.posiciones_disponibles -= 2

                    elif "paño acoplador" in conexion:
                        #print("ACOPLADOR")
                        self.posiciones_disponibles -= 1

                    elif "paño seccionador" in conexion:
                        #print("SECCIONADOR")
                        self.posiciones_disponibles -= 1

                    else:
                        print("Revisar tipo de paño a conectar xdddd")
                        patron_tension = r'\b\d+x\d{2,3}\b'
                        match = re.findall(patron_tension, conexion)
                        
                        if match:
                            for tension in match:
                                posic_ocup = int(tension[0])
                                self.posiciones_disponibles -= posic_ocup

                        else:
                            print("No se encontraron coincidencias para paño, REVISAR!")


                else:
                    patron_tension = r'\b\d+x\d{2,3}\b'
                    match = re.findall(patron_tension, conexion)

                    if match:
                        for tension in match:
                            posic_ocup = int(tension[0])
                            self.posiciones_disponibles -= posic_ocup

                    else:
                        if "bancos" in conexion:
                            # vamos a buscar dentro de la descripcion del proyecto padre

                            doc = self.proyecto_padre.doc
                            #vamos a buscar la palabra banco o bancos, y si la palabra anterior a esta es un numero, entonces tomamos ese numero como la cantidad de bancos
                            for token in doc:
                                if token.text == "bancos" and doc[token.i - 1].like_num:

                                    numero = numeros.get(doc[token.i - 1].text, doc[token.i - 1].text)
                                    posic_ocup = int(numero)
                                    self.posiciones_disponibles -= posic_ocup
                                    #print("FUNCIONO BRODER")
                                    break

                        elif "banco" in conexion:
                            self.posiciones_disponibles -= 1
                            


                        else:
                            #print(f"No se encontraron coincidencias para {conexion}")
                            continue


            return ""

        except Exception as e:
            print(f"Error: {e}")
            return ""



    def procesar_texto_v2(self):
        descripcion = False
        configuracion = False
        objetivo = False
        patio = False


        indices = self.encontrar_indices_parrafos()

        self.nombre = self.extraer_nombre()
        #print("Nombre:", self.nombre)

        if len(indices) == 1:
            parrafo = self.doc[indices[0][0]:indices[0][1]]
            #print("Parrafo:", parrafo)
            self.cofiguracion  = self.extraer_configuracion(parrafo.text)
            #print("Configuracion:", self.cofiguracion )
            self.numero_posiciones = self.extraer_numero_posiciones(parrafo)
            #print("Numero de posiciones:", self.numero_posiciones)
            self.lista_conexiones = self.extraer_conexiones(parrafo)
            #print("Conexiones:", self.lista_conexiones)
            self.calcular_posiciones_disponibles()
            #print("Posiciones disponibles:", self.posiciones_disponibles)
            self.resumen_proyecto = parrafo.text
            pass

        else:
            # vamos a recorrer los indices de parrafos y vamos a imprimir el texto de cada parrafo
            #imprimir titulo del proyecto
            print(f"Proyecto: {self.nombre}")
            parrafo_final = ""
            for i, (start, end) in enumerate(indices):
                parrafo = self.doc[start:end]
                print(f"Parrafo {i}: {parrafo}")
                print("\n")
                parrafo_final += parrafo.text

            self.resumen_proyecto = parrafo_final
            self.cofiguracion  = self.extraer_configuracion(parrafo_final)
            self.numero_posiciones = "IMPLEMENTAR LOGICA DE CALCULO POR PATIO!"
            self.lista_conexiones = "IMPLEMENTAR LOGICA DE CALCULO POR PATIO!"
            self.posiciones_disponibles = "IMPLEMENTAR LOGICA DE CALCULO POR PATIO!"


                # if "posiciones" in parrafo.text or "posición" in parrafo.text or "diagonales" in parrafo.text or "diagonal" in parrafo.text:
                #     self.numero_posiciones = self.extraer_numero_posiciones(parrafo)
                #     print("Numero de posiciones:", self.numero_posiciones)

                # if i == 0:
                #     # vamos a hacer que el resumen del proyecto sea el primer parrafo
                #     self.resumen_proyecto = parrafo.text

                # #Vamos a imprimir la informacion extraida, y dar la opcion de ingresar el resto de informacion de forma manual:


              


                #PREGUNTAR A TUGA:
                #1. COMO INTERPRETO LOS PROYECTOS DE MULTIPLES PARRAFOS
                #2. COMO PUEDO EXTRAER LOS DATOS DE FORMA CORRECTA
                #3. COMO ARMO EL EXCEL DE OUTPUT DEL PROYECTO
                #4. COMO ARMO EL PROYECTO PARA EL KMZ


                # Vamos a escribir cosas auxiliares en estos casos





if __name__ == "__main__":

    file = "Informes\plan_expansion_final_2023.pdf"
    diccionario = generar_diccionario_ampliaciones(file)
    n_total_proyectos = len(diccionario)


    ejecutar_analisis_2(diccionario, file)


