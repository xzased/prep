from bs4 import BeautifulSoup
from collections import Counter
import urllib, re

entidades = {
    "aguascalientes" : 1,
    "baja california" : 2,
    "baja california sur" : 3,
    "campeche" : 4,
    "coahuila" : 5,
    "colima" : 6,
    "chiapas" : 7,
    "chihuahua" : 8,
    "distrito federal" : 9,
    "durango" : 10,
    "guanajuato" : 11,
    "guerrero" : 12,
    "hidalgo" : 13,
    "jalisco" : 14,
    "mexico" : 15,
    "michoacan" : 16,
    "morelos" : 17,
    "nayarit" : 18,
    "nuevo leon" : 19,
    "oaxaca" : 20,
    "puebla" : 21,
    "queretaro" : 22,
    "quintana roo" : 23,
    "san luis potosi" : 24,
    "sinaloa" : 25,
    "sonora" : 26,
    "tabasco" : 27,
    "tamaulipas" : 28,
    "tlaxcala" : 29,
    "veracruz" : 30,
    "yucatan" : 31,
    "zacatecas" : 32
}

partidos = {
    0: "PAN",
    1: "PRI",
    2: "PRD",
    3: "PRI",
    4: "PRD",
    5: "PRD",
    6: "QUADRO",
    7: "PRI",
    8: "PRD",
    9: "PRD",
    10: "PRD",
    11: "PRD",
    12: "CNR",
    13: "NULO",
    20: "TODOS"
}

secciones = range(1, 10000)

class CellError(Exception):
    pass

def procesar_seccion(pagina, entidad, seccion):
    sopa = BeautifulSoup(pagina)
    tabla = sopa.find_all("table", "resultados")[0]
    inv = tabla.find("strong")
    if inv and "no existe" in inv.string:
        # Ya no hay seccion valida
        return None
    pan = 0
    pri = 0
    prd = 0
    errores = list()
    valores = list()
    casillas = tabla.find_all("tr", "data")
    for casilla in casillas:
        celdas = casilla.find_all("td")[2:16]
        try:
            for celda in celdas:
                if not celda.string:
                    # Atrapamos un 'row' sin informacion, SIN ACTA!
                    error = {"partido": partidos.get(20), "tipo": "SIN ACTA",
                                "seccion": seccion, "entidad": entidad}
                    errores.append(error)
                    raise CellError("Bad Row.")
                elif "detalle" in celda.string.lower():
                    # Atrapamos un 'row' de texto, desafortunadamente
                    # la pagina del IFE agrega la misma clase a varios
                    # 'rows' que funcionan como encabezados, o un 'ilegible'
                    # verifiquemos
                    raise CellError("Bad Row.")
                elif "ilegible" in celda.string.lower():
                    error = {"partido": partidos.get(celdas.index(celda)),
                                "tipo": "ILEGIBLE", "seccion": seccion, "entidad": entidad}
                    errores.append(error)
                    valores.append(0)
                elif "sin dato" in celda.string.lower():
                    error = {"partido": partidos.get(celdas.index(celda)),
                                "tipo": "SIN DATO", "seccion": seccion, "entidad": entidad}
                    errores.append(error)
                    valores.append(0)
                else:
                    valores.append(int(re.sub(r"\D", "", celda.string)))
        except CellError:
            continue
        pan = valores[0]
        pri = valores[1] + valores[3] + valores[7]
        prd = valores[2] + valores[4] + valores[5] + sum(valores[8:12])
        resultado = {"pan": pan, "pri": pri, "prd": prd, "error": errores, "total": sum(valores)}
        print resultado
        return resultado

class PREP(object):
    def __init__(self):
        self.url = "http://prep.elecciones.terra.com.mx/prep/DetalleCasillas"

    def conteo_por_entidad(self, entidad):
        edid = entidades.get(entidad, None)
        if not edid:
            raise ValueError("La entidad %s no es valida." % entidad)
        resultados = Counter()
        for seccion in secciones:
            params = urllib.urlencode({"idEdo": edid, "seccion": seccion})
            post = urllib.urlopen(self.url, params)
            pagina = post.read()
            resultado = procesar_seccion(pagina, entidad, seccion)
            if resultado:
                resultados.update(resultado)
            else:
                # Seccion no existe, desafortunadamente hay secciones contiguas
                # a secciones invalidas asi que solo nos queda seguir con el
                # siguiente, esa logica no me agrada
                continue
        return resultados

    def conteo_por_seccion(self, entidad, seccion):
        edid = entidades.get(entidad, None)
        if not edid:
            raise ValueError("La entidad %s no es valida." % entidad)
        params = urllib.urlencode({"idEdo": edid, "seccion": seccion})
        post = urllib.urlopen(self.url, params)
        pagina = post.read()
        resultado = procesar_seccion(pagina, entidad, seccion)
        return resultado

    def conteo_total(self):
        resultados = Counter()
        for entidad, v in entidades:
            resultado = self.conteo_por_entidad(entidad)
            resultados.update(resultado)
