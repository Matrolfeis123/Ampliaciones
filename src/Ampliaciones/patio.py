# En este script manejaremos todo lo relacionado con la clase patio. 
# Esta clase sera instanciada cada vez que se encuentre un patio en el texto extraido de los PDFs.

import re
from funciones_extra import extraer_texto_entre_delimitadores_v2

class Patio:
    def __init__(self, descripcion: str, patio_paño_alimentador: bool, proyecto_padre=None):
        self.texto = descripcion
        self.patio_paño_alimentador = patio_paño_alimentador
        self.proyecto_padre = proyecto_padre # Corresponde a la instancia de la clase Proyecto a la que pertenece el patio

        self.nombre = None
        self.tension = None
        self.configuracion = None
        self.posiciones = 0
        self.lista_conexiones = None
        self.posiciones_disponibles = 0
        self.objetivo_amp = None

    def __str__(self) -> str:
        return f"{self.nombre} de {self.tension} kV, con configuración {self.configuracion}. Número de posiciones: {self.posiciones_disponibles}"
    
    def __repr__(self) -> str:
        return f"{self.nombre}"
    
    def imprimir_resumen_patio(self):
        print(f"Nombre: {self.nombre}")
        print(f"Tensión: {self.tension}")
        print(f"Configuración: {self.configuracion}")
        print(f"Número de posiciones totales: {self.posiciones}")
        print(f"Posiciones disponibles: {self.posiciones_disponibles}")
        print(f"Conexiones: {self.lista_conexiones}")
    
    def procesar_patio(self):
        self.nombre = self.extraer_tension()
        self.tension = self.nombre
        self.configuracion = self.extraer_configuracion()
        self.posiciones = self.extraer_numero_posiciones()
        self.lista_conexiones = self.extraer_conexiones()
        self.calcular_posiciones_disponibles()
    
    def extraer_configuracion(self):
        l_configs = ["barra principal seccionada y barra de transferencia", "interruptor y medio", "doble barra principal y barra de transferencia", "doble barra principal y barra de transferencia", "doble barra principal con barra de transferencia", "barra simple"]
        l_configs2 = ["barra principal con barra de transferencia", "interruptor y medio", "barra principal seccionada y barra de transferencia", "barra simple", "doble barra principal y barra de transferencia", "barra principal más barra auxiliar", "barra simple seccionada", "barra principal más barra auxiliar", "barra principal y barra de transferencia", ]
        l_config_oficial = ['barra principal seccionada y barra de transferencia', 'interruptor y medio', 'doble barra principal y barra de transferencia', 'doble barra principal con barra de transferencia', 'barra simple', 'barra principal con barra de transferencia', 'barra principal más barra auxiliar', 'barra simple seccionada', 'barra principal y barra de transferencia']

        for config in l_config_oficial:
            if config in self.texto:
                return config
            
        return "No se pudo extraer la configuración"
            
    def extraer_tension(self):
        # vamos a buscar donde diga la frase "patio de X kV"
        pattern = re.compile(r'patio de \d+(?:,\d+)? kV')
        match = pattern.search(self.texto)

        if match:
            return match.group(0)
        
        else:
            # Vamos a buscar por tension de barras 
            pattern = re.compile(r'(barra|barras|sala de celdas|sección de barra|) de \d+(?:,\d+)? kV')
            match = pattern.search(self.texto)

            if match:
                return match.group(0)
            
            else:
                return "No se encontro tension de patio o barra o celda, por lo que se imprimira un resumen del proyecto directamente"
            

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


    def extraer_conexiones(self):

        def limpiar_conexion(conexion):
        # Eliminar artículos y preposiciones iniciales
            conexion = re.sub(r'^(el |la |los |las |del |de |a |en |para |la conexión de |la construcción de |del |un |una |)', '', conexion, flags=re.IGNORECASE).strip()
            return conexion
        
        try:
            patron_conexiones_inicio = re.compile(r'\bde manera de permitir la conexión\b(.*?)(\.\s|$)', re.IGNORECASE | re.DOTALL)
            patron_alternativo = re.compile(r'\bpaños para (alimentador|alimentadores)\b(.*?)(\.\s|$)', re.IGNORECASE | re.DOTALL)


            match_conexiones_inicio = patron_conexiones_inicio.search(self.texto)
            match_alternativo = patron_alternativo.search(self.texto)

            if match_conexiones_inicio:
                
                conexiones = match_conexiones_inicio.group(1).replace("y la", ",").split(",")
                lista_conexiones = [limpiar_conexion(conexion.strip()) for conexion in conexiones]
                return lista_conexiones

            elif match_alternativo:
                conexiones = match_alternativo.group(0).split(",")
                lista_conexiones = [limpiar_conexion(conexion.strip()) for conexion in conexiones]
                return lista_conexiones




        except Exception as e:
            print(f"Error extraccion conexiones: {e}")


        return "Revisar manualmente, al parecer no hay conexiones en el texto."
    
    def calcular_posiciones_disponibles(self):
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

        if isinstance(self.posiciones, str):
            self.posiciones_disponibles = self.posiciones
            return ""
        
        else:
            try:

                self.posiciones_disponibles = int(self.posiciones)

                for conexion in self.lista_conexiones:

                    if "seccionamiento" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.findall(patron, conexion)
                        if match:
                            for tension in match:
                                posic_ocup = int(tension[0])*2 #OJO ACA, pq [0]? 
                                self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")


                    elif ("la conexión de la línea") in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.search(patron, conexion)
                        if match:
                            posic_ocup = int(match.group()[0]) #Ojo aca tmb
                            self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")

                    elif "la conexión de la nueva línea" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.search(patron, conexion)
                        if match:
                            posic_ocup = int(match.group()[0])
                            self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")


                    elif "la conexión de las líneas" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.search(patron, conexion)

                        if match:
                            posic_ocup = int(match.group()[0])
                            self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")

                    elif "la conexión de la obra" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        coincidencias = re.findall(patron, conexion)

                        if coincidencias:
                            for coincidencia in coincidencias:
                                posic_ocup = int(coincidencia[0])
                                self.posiciones_disponibles -= posic_ocup

                        else:
                            print("Problemas posiciones nuevas obras, calculo posiciones.")


                    elif "transformador" in conexion and "banco" not in conexion:
                        self.posiciones_disponibles -= 1



                    elif "paño" in conexion:
                        if "paño acoplador" in conexion and "paño seccionador" in conexion:
                            self.posiciones_disponibles -= 2

                        elif "paño acoplador" in conexion:
                            self.posiciones_disponibles -= 1

                        elif "paño seccionador" in conexion:
                            self.posiciones_disponibles -= 1

                        else:
                            print("Revisar tipo de paño a conectar xdddd")
                            continue

                    else:
                        patron_tension = r'\b(\d+)x\d{2,3}\b'
                        match = re.findall(patron_tension, conexion)
                        if match:
                            for tension in match:
                                posic_ocup = int(tension)
                                self.posiciones_disponibles -= posic_ocup
                        else:
                            ####################################################
                            #### REVISAR ESTA LOGICA!!!! 05/06/2024

                            if "bancos de autotransformadores" in conexion:
                                # Vamos a buscar en la descripcion del texto la palabra bancos y si la palabra anterior a esta es un numero, entonces tomamos ese numero como la cantidad de bancos
                                doc = self.proyecto_padre.doc
                                for token in doc:
                                    if token.text == "bancos" and doc[token.i - 1].like_num:
                                        numero = numeros.get(doc[token.i - 1].text, doc[token.i - 1].text)
                                        posic_ocup = int(numero)
                                        self.posiciones_disponibles -= posic_ocup
                                        break
                            
                            elif "bancos" in conexion:
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
                                continue

                            ##################################



            except Exception as e:
                print(f"Error: {e}")
                return ""



if __name__ == "__main__":
    texto = 'Además, el proyecto considera la construcción de un patio de 13,8 kV, en configuración barra simple, contemplándose la construcción de, al menos, cuatro paños para alimentadores, el paño de conexión para el transformador de poder 110/13,8 kV antes mencionado y espacio en barra y plataforma para la construcción de dos paños futuros.'

    patio = Patio(texto, False)
    patio.procesar_patio()
    patio.imprimir_resumen_patio()

