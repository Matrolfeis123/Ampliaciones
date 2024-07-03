from funciones_extra import generar_diccionario_ampliaciones, generar_diccionario_descripciones_amp
from proyecto_ampliacion import Proyecto_ampliacion
import os

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




def main():
    pdf_file = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "PDFs", "plan_expansion_final_2023.pdf"))  
    

    dic_amp = generar_diccionario_ampliaciones(pdf_file)
    dic_desc_amp = generar_diccionario_descripciones_amp(pdf_file, dic_amp)

    conteo_casos = []

    lista_proyectos = []

    for titulo, descripcion in dic_desc_amp.items():
        try:
            proyecto = Proyecto_ampliacion(titulo, descripcion)
            proyecto.procesar_proyecto()
            conteo_casos.append(proyecto.resultado)
            lista_proyectos.append(proyecto.diccionario_proyecto)

            # Desde aca, puedo armar el diccionario de salida con los datos del proyecto
        
        except Exception as e:
            print(f"Error: {e}")
            continue

    print(conteo_casos)
    print("\n")
    disenos_unicos = identificar_disenos(conteo_casos)
    print(disenos_unicos)
    print("\n")
    print(lista_proyectos)
    

        




# diccionario_output_proyecto = {
#     "obra": proyecto.nombre_proyecto,
#     "decreto": "PET Final 2023",
#     "tipo": proyecto.tipo,
#     "pos_disp": proyecto.posiciones_disponibles,
#     "Nombre Proyecto": proyecto.nombre_proyecto,
#     "Nombre S/E": proyecto.nombre,
#     "Tipo": proyecto.tipo,
#     "Posiciones": proyecto.posiciones_disponibles,
#     "resumen": proyecto.resumen_proyecto
# }

# lista_proyectos.append(diccionario_output_proyecto)


# diccio_proy = {
#     "Nombre Proyecto": titulo,s
#     "Nombre S/E": "No se pudo extraer",
#     "Tipo": "Ampliacion",
#     "Posiciones": "No se pudo extraer",
#     "Resumen": "No se pudo extraer"
# }

# lista_proyectos.append(diccio_proy)


if __name__ == "__main__":
    main()

