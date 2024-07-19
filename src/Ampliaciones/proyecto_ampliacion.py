import spacy
from spacy import displacy
from spacy.matcher import Matcher
import re
import time
import pdfplumber
from openpyxl import Workbook
from funciones_extra import extraer_texto_entre_delimitadores_v2, remove_stopwords
from patio import Patio, Trafo, AmpBarraPatio
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



class Proyecto_ampliacion:
    def __init__(self, titulo, texto):
        self.texto = texto
        self.indices = None

        self.nombre_proyecto = titulo
        self.nombre_se = None
        self.tipo = "Ampliación"
        self.ubicacion = None
        self.patios = [] #a partir del resumen, podemos extraer el resumen de cada patio y extraer la informacion necesaria: Tension, Config, N_posiciones, Conexiones. Pos_disp.

        self.parrafos = None
        self.diccionario_patios = None

        self.valor_inversion = None
        self.entrada_operacion = None
        self.licitacion = None

        self.decreto =  "PET Final 2023"
        self.resumen = ""
        self.diccionario_kmz = {}        
        
        self.diccionario_patios = {}
        self.diccionario_trafos = {}
        self.diccionario_otros = {}


    def __str__(self):
        return f"Nombre: {self.nombre}\nTipo: {self.tipo}"


    def extraer_nombre_subestacion(self):
        # Define la expresión regular para extraer el nombre de la subestación
        patron  = r"S/E\s+([^0-9\(\),]+)"
        match = re.search(patron, self.nombre_proyecto)

        if match:
            nombre = match.group(1).strip()
            return f"S/E {nombre}"
        
        else:
            return None

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

    def extraer_licitacion(self):
        # Vamos a corroborar si la palabra "licitación" aparece en el texto
        patron = re.compile(r"licitación", re.IGNORECASE)

        match = patron.search(self.texto)

        if match:
            desc_licitacion = extraer_texto_entre_delimitadores_v2(self.texto, "La adjudicación", "Ministerio de Energía")

            if desc_licitacion == "ERROR EXTRAYENDO TEXTO":
                desc_licitacion = extraer_texto_entre_delimitadores_v2(self.texto, "La adjudicación", "presente Informe")

            return desc_licitacion if desc_licitacion != "ERROR EXTRAYENDO TEXTO" else None
        
        else:
            return None

    def clasificar_parrafo(self, parrafo):
        tipo_aumento_capacidad = ["instalación nuevo transformador", "reemplazo actual transformador"] #caso inst o const trafo
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
            
        if "deberá emplazar" in parrafo:
            tipo = "UBICACION"
            return tipo
        


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

        self.nombre_se = self.extraer_nombre_subestacion()
        self.resumen = self.extraer_resumen()
        self.entrada_operacion = self.extraer_entrada_operacion()
        self.valor_inversion = self.extraer_valor_inversion()
        self.licitacion = self.extraer_licitacion()

        
        
        self.parrafos = sent_tokenize(self.texto)
        patios = []
        trafos = []
        otros = []


        for parrafo in self.parrafos:
            parrafo_limpio = remove_stopwords(parrafo)
            tipo, elemento = self.clasificar_parrafo(parrafo_limpio)

            if tipo == "no_interesa":
                pass

            elif tipo == "construccion_instalacion_trafo":
                #Los atributos procesados del trafo son:
                # - tension_trafo_reemplazado
                # - tension_trafo_nuevo
                # Con eso, tenemos todo lo necesario para escribir su estructura en el XML
                trafo = Trafo(parrafo, tipo, elemento)
                trafo.procesar()
                trafos.append(trafo)


            elif tipo == "ampliacion_construccion_patio":
                patio = AmpBarraPatio(parrafo, tipo, elemento)
                patio.procesar()
                patios.append(patio)

            elif tipo == "otro":
                # Este es el caso donde vamos a chantar el parrafo nomas en la trajeta de XML
                otros.append(parrafo)
                pass         

            elif tipo == "UBICACION":
                self.ubicacion = parrafo


        #self.imprimir_resumen_atributos_proyecto()

        for patio in patios: #la listapatios tiene los distintos tipos de proyectos (patio, trafo, otros)
            patio.procesar()
            #patio.imprimir_resumen()
            nombre_patio = f"patio{patios.index(patio)+1}"
            self.diccionario_patios[nombre_patio] = patio.diccionario
        

        for trafo in trafos:
            trafo.procesar()
            #trafo.imprimir_resumen()
            nombre_trafo = f"trafo{trafos.index(trafo)+1}"
            self.diccionario_trafos[nombre_trafo] = trafo.diccionario

        for otro in otros:
            self.diccionario_otros[f"parrafo{otros.index(otro)+1}"] = otro


        self.resultado = {"patios": len(patios), "trafos": len(trafos), "otros": len(otros)}

        self.generar_diccionario_proyecto(patios, trafos, otros)




    def imprimir_resumen_atributos_proyecto(self):
        print(f"Nombre del proyecto: {self.nombre_proyecto}")
        print(f"Tipo de proyecto: {self.tipo}")
        print(f"Resumen del proyecto: {self.resumen}")
        print(f"Valor de inversión: {self.valor_inversion}")
        print(f"Entrada en operación: {self.entrada_operacion}")
        print("\n")

    def generar_diccionario_proyecto(self, l_patios, l_trafos, l_otros):
        self.diccionario_proyecto = {
            "nombre_se": self.nombre_se,
            "obra": self.nombre_proyecto,
            "decreto": self.decreto,
            "tipo": self.tipo,
            "vi": self.valor_inversion,
            "entrada_op": self.entrada_operacion,
            "licitacion": self.licitacion,
            "resumen": self.resumen,
            "patios": self.diccionario_patios,
            "n_patios": len(l_patios),
            "trafos": self.diccionario_trafos,
            "n_trafos": len(l_trafos),
            "otros": self.diccionario_otros,
            "n_otros": len(l_otros)
        }

        self.diccionario_proyecto["diseño"] = f"Amp_{len(l_patios)}{len(l_trafos)}{len(l_otros)}"

        if self.licitacion:
            self.diccionario_proyecto["diseño"] += "_l"

        
        return self.diccionario_proyecto
        

