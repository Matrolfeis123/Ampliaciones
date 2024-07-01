import spacy
from spacy import displacy
from spacy.matcher import Matcher
import re
import time
import pdfplumber
from openpyxl import Workbook
from patio import Patio
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk import FreqDist
import string

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
    def __init__(self, titulo, texto):
        self.nlp = nlp
        self.texto = texto
        self.doc = self.nlp(texto.strip())


        self.nombre_proyecto = titulo
        self.parrafos = None
        self.tipo = "Ampliación"
        self.patios = [] #a partir del resumen, podemos extraer el resumen de cada patio y extraer la informacion necesaria: Tension, Config, N_posiciones, Conexiones. Pos_disp.
        self.diccionario_patios = None


        self.valor_inversion = None
        self.entrada_operacion = None


        self.numero_posiciones = None
        self.patios = [] #??
        self.lista_conexiones = []
        self.posiciones_disponibles = "No procesed"

        self.resumen_proyecto = ""
        self.decreto =  "PET Final 2023"


    def __str__(self):
        return f"Nombre: {self.nombre}\nTipo: {self.tipo}"
    

    def procesar_descripcion(self):
        self.indices = self.encontrar_indices_parrafos()
        self.resumen_proyecto = self.extraer_resumen()
        self.numero_posiciones = self.extraer_numero_posiciones_v3(self.resumen_proyecto)
        self.entrada_operacion = self.extraer_entrada_operacion()
        self.valor_inversion = self.extraer_valor_inversion()

        self.diccionario_patios = self.separar_por_patios() # Este diccionario contiene los parrafos separados por categorias, para posteriormente procesar_parragos_patios
        self.procesar_parrafos_patios()

        self.imprimir_resumen_atributos_proyecto()



    def encontrar_indices_parrafos_v1(self):
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

        indices = self.encontrar_indices_parrafos_v1()

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


    def encontrar_indices_parrafos(self):

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
            "Por su parte",
            "La configuración del patio",
            "Adicionalmente, el proyecto considera",
            "Adicionalmente, el proyecto contempla",
            "Además, el proyecto contempla",
            "Además, el proyecto considera",
            "La capacidad de barras",
            "La subestación se deberá emplazar",
            "Finalmente, el proyecto"
        ]
    
        # Crear un patrón de expresión regular que busque todas las frases de inicio
        pattern = re.compile('|'.join(re.escape(frase) for frase in frases_inicio))

        # Encontrar todas las posiciones de inicio de las frases
        indices = [match.start() for match in pattern.finditer(self.texto)]
        
        return indices


    def extraer_texto_entre_delimitadores_v2(self, texto, delimitador_inicial, delimitador_final):
        pattern = re.compile(f"{delimitador_inicial}(.*?{delimitador_final}.*?)\.", re.DOTALL)
        match = pattern.search(texto)
        return match.group(0) if match else "ERROR EXTRAYENDO TEXTO"


    def extraer_resumen(self):
        # Definimos las frases de inicio y fin
        frase_inicio = "El proyecto consiste en"
        frase_fin = "El proyecto incluye todas las obras"
        
        # Utilizamos una expresión regular para encontrar el texto entre las frases
        patron = re.compile(re.escape(frase_inicio) + r'(.*?)(?=' + re.escape(frase_fin) + ')', re.DOTALL)
        
        # Buscamos el patrón en el string de entrada
        coincidencia = patron.search(self.texto)
        
        # Si encontramos una coincidencia, la devolvemos, de lo contrario devolvemos None
        if coincidencia:
            return coincidencia.group(0).strip()
        else:
            return None

  
    def extraer_valor_inversion(self):
        # Patrón de expresión regular para encontrar el valor de inversión
        patron = re.compile(r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?) dólares", re.IGNORECASE)

        # Buscar el valor de inversión en la descripción
        match = patron.search(self.texto)

        if match:
            # Extraer y devolver la frase completa encontrada
            valor_inversion = match.group(0)
            return valor_inversion
        else:
            return None  # Devolver None si no se encuentra el valor de inversión


    def extraer_entrada_operacion(self):
        # patron que identifique la frase: El proyecto deberá ser construido y entrar en operación, a más tardar, dentro de los dd meses siguientes a la fecha de publicación en el Diario Oficial del respectivo decreto

        patron = re.compile(r"a más tardar, dentro de los \d{1,2} meses siguientes a la fecha de publicación en el Diario Oficial del respectivo decreto", re.IGNORECASE)

        match = patron.search(self.texto)

        if match:
            entrada_operacion = match.group(0)
            return entrada_operacion
        else:
            return None # Devolver None si no se encuentra la fecha de entrada en operación


    def imprimir_resumen_atributos_proyecto(self):
        print(f"Nombre del proyecto: {self.nombre_proyecto}")
        print(f"Tipo de proyecto: {self.tipo}")
        print(f"Resumen del proyecto: {self.resumen_proyecto}")
        print(f"Valor de inversión: {self.valor_inversion}")
        print(f"Entrada en operación: {self.entrada_operacion}")
        print("\n")


    def extraer_numero_posiciones_v3(self):
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
        pattern1 = re.compile(r'\b(\d+|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)(?: (nueva|nuevas))? (posición|posiciones|diagonal|diagonales)\b', re.IGNORECASE)
        pattern2 = re.compile(r'\b(\d+|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez) (celda para alimentador|celdas para alimentadores)\b', re.IGNORECASE)
        pattern3 = re.compile(r'\b(\d+|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez) (paño|paños)\b', re.IGNORECASE)


        match1 = pattern1.search(self.texto)
        match2 = pattern2.search(self.texto)
        match3 = pattern3.search(self.texto)

        if match1:
            numero_str, _, tipo = match1.groups()
            numero = numeros.get(numero_str.lower(), int(numero_str) if numero_str.isdigit() else 0)

            if tipo.lower() == "diagonales" or tipo.lower() == "diagonal":
                return numero * 2
            elif tipo.lower() == "posiciones" or tipo.lower() == "posición":
                return numero
        
        elif match2:
            numero_str, tipo = match2.groups()
            numero = numeros.get(numero_str.lower(), int(numero_str) if numero_str.isdigit() else 0)
            return f"al menos {numero} celda(s) para alimentadores"


            
        elif match3:
            numero_str = match3.group(1)
            numero = numeros.get(numero_str.lower(), int(numero_str) if numero_str.isdigit() else 0)
            return f"al menos {numero} paño(s)"

        else:
            return False

    def separar_por_patios(self):
        """ 
        Esta funcion recibe la descripcion del proyecto y la separa en parrafos segun la informacion de los patios, celdas y paños.
        La funcion devuelve un diccionario con los parrafos separados en las siguientes categorias:
        - patios
        - celdas
        - paños
        - otros

        A cada categoria debe ejecutarse un procesamiento adicional para extraer la informacion necesaria, tal como la configuracion, numero de posiciones, etc.
        """


        parrafos = self.texto.split(".")
        palabras_clave_patios = ["patio"]
        palabras_clave_celdas = ["sala de celdas"]
        palabras_clave_paños = ["paño", "paños"]
        palabras_posiciones = ["diagonales", "posiciones", "posición", "diagonal"]
        parrafos_patios = [parrafo for parrafo in parrafos if any(palabra in parrafo for palabra in palabras_clave_patios) and "configuración" in parrafo and any(palabra in parrafo for palabra in palabras_posiciones)]
        parrafos_celdas = [parrafo for parrafo in parrafos if any(palabra in parrafo for palabra in palabras_clave_celdas) and "configuración" in parrafo and any(palabra in parrafo for palabra in palabras_posiciones)]
        parrafos_paños = [parrafo for parrafo in parrafos if any(palabra in parrafo for palabra in palabras_clave_paños) and "configuración" and any(palabra in parrafo for palabra in palabras_posiciones)]
        parrafos_otros = [parrafo for parrafo in parrafos if parrafo not in parrafos_patios and parrafo not in parrafos_celdas and parrafo not in parrafos_paños]
        
        diccionario_parrafos = {
            "patios": parrafos_patios,
            "celdas": parrafos_celdas,
            "paños": parrafos_paños,
            "otros": parrafos_otros
        }

        return diccionario_parrafos
    
    def procesar_parrafos_patios(self):
        """
        Esta funcion nos permitira procesar los parrafos separados por categorias, y extraer la informacion necesaria para cada una de ellas.
        La informacion necesaria de cada categoria es la siguiente:
        - Patio: Tension, Configuracion, numero de posiciones, conexiones, posiciones disponibles.
        - Paño: Tension, Configuracion, numero de posiciones, conexiones, posiciones disponibles.
        """
        for categoria, parrafos in self.diccionario_patios.items():
            if parrafos and categoria != "otros":
                if categoria == "patios":
                    for parrafo in parrafos:
                        patio = Patio(parrafo, proyecto_padre=self)
                        patio.procesar_patio()
                        patio.imprimir_resumen_patio()

                elif categoria == "celdas":
                    print("Caso procesamiento celdas")
                    pass

                elif categoria == "paños":
                    print("Caso procesamiento paños")




        print("\n")

    def remove_stopwords(self, texto):
        stop_words = set(stopwords.words('spanish'))
        tokens = nltk.word_tokenize(texto)
        tokens = [word for word in tokens if word.lower() not in stop_words]
        tokens = [word for word in tokens if word.lower() not in string.punctuation]
        return " ".join(tokens)

    def clasificar_parrafo(self, parrafo):
        tipo_aumento_capacidad = ["aumento capacidad", "instalación nuevo transformador", "reemplazo actual transformador"] #caso inst o const trafo
        tipo_ampliacion_construccion = ["ampliación barra", "construcción nueva sección barra", "ampliación galpón", "ampliación patio", "construcción nueva barra", "ampliación sala celdas", "construcción nueva sala celdas", "construcción nuevo paño"] # caso ampliacion construccion patio, paño, nva barra, etc
        tipo_otro = ["nuevos bancos condensadores", "nuevo banco condensadores", "banco autotransformadores existente nueva"]

        tipo_no_interesa = ["proyecto incluye todas obras modificaciones", "respectivas bases licitación", "contempla todas tareas labores obras", "caso definirse desarrollo", " producto del aumento de capacidad antes", "Entrada operación", "Valor inversión", "C.O.M.A", "referenciales V.I", "referencial proyecto"]

        tipo = "REVISAR!"
        elemento_encontrado = None

        #quizas, podria devolver directamente el elemento_encontrado y definir las listas en la otra funcion, tal que si elemento encontrado esta en la lista "tipo_aumento_capacidad", se utiliza el esquema de estilo xml correspondiente al aumento de capacidad de la s/e, y asi con los otros tipos de parrafos.
        
        for elemento in tipo_no_interesa:
            if elemento in parrafo:
                tipo = "no_interesa"
                elemento_encontrado = elemento
                return tipo, None

        for elemento in tipo_aumento_capacidad:
            if elemento in parrafo:
                tipo = "construccion_instalacion_trafo"
                elemento_encontrado = elemento
                return tipo, elemento_encontrado
        
        for elemento in tipo_ampliacion_construccion:
            if elemento in parrafo:
                tipo = "ampliacion_construccion_patio"
                elemento_encontrado = elemento
                return tipo, elemento_encontrado
        
        for elemento in tipo_otro:
            if elemento in parrafo:
                tipo = "otro"
                elemento_encontrado = elemento
                return tipo, elemento_encontrado
        


        return tipo, elemento_encontrado
    

    def procesar_proyecto(self):
        """
        Esta funcion nos debe permitir procesar la descripcion de los proyectos, con el objetivo de extraer los siguientes atributos:
        - Nombre del proyecto ("obra")
        - Estado ("decreto?")
        - Resumen del proyecto (Que hacer en el caso donde hay multiples parrafos?)
        - Valor de inversion
        - Entrada en operacion
        - Condicionado a Licitacion (?)

        Luego, se deben procesar los parrafos del proyecto, clasificarlos y generar el xml correspondiente al tipo de patio
        """
        self.resumen_proyecto = self.extraer_resumen()
        self.valor_inversion = self.extraer_valor_inversion()
        self.parrafos = sent_tokenize(self.texto)

        for parrafo in self.parrafos:
            parrafo_limpio = self.remove_stopwords(parrafo)
            tipo, elemento = self.clasificar_parrafo(parrafo_limpio)
            print(f"Tipo: {tipo}, Elemento: {elemento}")
            print("\n")
            
            patio = Patio(parrafo, tipo, elemento) # Entrego el parrafo completo, no el parrafo limpio
            


    def procesar_descripcion(self):
        self.indices = self.encontrar_indices_parrafos()
        self.resumen_proyecto = self.extraer_resumen()
        self.numero_posiciones = self.extraer_numero_posiciones_v3(self.resumen_proyecto)
        self.entrada_operacion = self.extraer_entrada_operacion()
        self.valor_inversion = self.extraer_valor_inversion()

        self.diccionario_patios = self.separar_por_patios() # Este diccionario contiene los parrafos separados por categorias, para posteriormente procesar_parragos_patios
        self.procesar_parrafos_patios()

        self.imprimir_resumen_atributos_proyecto()



if __name__ == "__main__":

    file = "Informes\plan_expansion_final_2023.pdf"
    diccionario = generar_diccionario_ampliaciones(file)
    n_total_proyectos = len(diccionario)


    ejecutar_analisis_2(diccionario, file)


