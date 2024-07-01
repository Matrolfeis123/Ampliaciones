from funciones_extra import generar_diccionario_ampliaciones, generar_diccionario_descripciones_amp
from proyecto_ampliacion import Proyecto_ampliacion

def main():
    file = "plan_expansion_final_2023.pdf"

    dic_amp = generar_diccionario_ampliaciones(file)
    dic_desc_amp = generar_diccionario_descripciones_amp(file, dic_amp)

    for titulo, descripcion in dic_desc_amp.items():
        proyecto = Proyecto_ampliacion(titulo, descripcion)
        


if __name__ == "__main__":
    main()

