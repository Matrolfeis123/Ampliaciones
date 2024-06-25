from funciones_extra import generar_diccionario_ampliaciones, ejecutar_analisis_amp

def main():
    file = "plan_expansion_final_2023.pdf"

    diccionario = generar_diccionario_ampliaciones(file)

    dic_proyectos = ejecutar_analisis_amp(file, diccionario)

if __name__ == "__main__":
    main()

