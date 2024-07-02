from funciones_extra import generar_diccionario_ampliaciones, generar_diccionario_descripciones_amp
from proyecto_ampliacion import Proyecto_ampliacion
import os

def main():
    pdf_file = os.path.abspath(os.path.join(os.getcwd(), "ArchivosConsultables", "PDFs", "plan_expansion_definitivo_2022.pdf"))  
    

    dic_amp = generar_diccionario_ampliaciones(pdf_file)
    dic_desc_amp = generar_diccionario_descripciones_amp(pdf_file, dic_amp)

    for titulo, descripcion in dic_desc_amp.items():
        try:
            print(titulo)
            proyecto = Proyecto_ampliacion(titulo, descripcion)
            proyecto.procesar_proyecto()
        
        except Exception as e:
            print(f"Error: {e}")
            continue

        




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

