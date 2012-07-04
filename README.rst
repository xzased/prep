Introduccion
============

Esta herramienta te permite contar los datos del PREP por entidad o seccion
con la finalidad de compararlos con los datos del IFE. Usando esta herramienta
descubri que alrededor de 1 de cada 8 secciones presentaba anomalias como
resultados "ilegibles", "sin acta" o "sin dato". Te regresa un diccionario
con los resultados de los 3 partidos principales -PAN, PRI, PRD (lo siento Quadro)
y los errores que se hallaron detallando la entidad, seccion y tipo de error.

Esta herramienta NO hackea el IFE, simplemente obtiene los resultados de la pagina
en forma programatica y cuenta los resultados.

Ejemplos
========

Asi es como se usa esta herramienta::

    from prep import *

    p = PREP()

    # Obtener resultado por seccion
    seccion = p.conteo_por_seccion("chihuahua", 1678)

    # Obtener resultado por entidad
    chihuahua = p.conteo_por_entidad("chihuahua")

    # Obtener todo!
    todo = p.conteo_total()


Esta herramienta imprime los resultados cada vez que pasa por una seccion (me gusta
ver que esta haciendo algo) si no les agrada solo modifiquen el print statement
en la funcion procesar_pagina.
