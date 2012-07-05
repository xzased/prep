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
    6: "PANAL",
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
    resultados = Counter()
    casillas = tabla.find_all("tr", "data")
    vuelta = None
    for casilla in casillas:
        celdas = casilla.find_all("td")[2:16]
        errores = list()
        valores = list()
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
        try:
            # Hasta comas hay en algunas... no comments
            get_num = str(casilla.find_all("td")[19].string).replace("%", "").replace(",", ".")
            participacion = float(get_num)
            if participacion > 100:
                error = {"partido": partidos.get(20), "valor": participacion,
                            "tipo": "PARTICIPACION", "seccion": seccion, "entidad": entidad}
                errores.append(error)
        except:
            # La participacion no esta registrada, es un row con falta de acta
            # o sin datos, para lo cual ya registramos errores
            pass
        pan = valores[0]
        pri = valores[1] + valores[3] + valores[7]
        prd = valores[2] + valores[4] + valores[5] + sum(valores[8:12])
        resultado = {"pan": pan, "pri": pri, "prd": prd, "error": errores,
                        "total": sum(valores)}
        resultados.update(resultado)
    print resultados
    return resultados

class PREP(object):
    def __init__(self):
        self.url = "http://prep.elecciones.terra.com.mx/prep/DetalleCasillas"

    def conteo_por_entidad(self, entidad):
        no_data = 0
        edid = entidades.get(entidad, None)
        if not edid:
            raise ValueError("La entidad %s no es valida." % entidad)
        resultados = Counter()
        i = 0
        for seccion in secciones:
            params = urllib.urlencode({"idEdo": edid, "seccion": seccion})
            post = urllib.urlopen(self.url, params)
            pagina = post.read()
            resultado = procesar_seccion(pagina, entidad, seccion)
            if resultado:
                no_data = 0
                resultados.update(resultado)
            else:
                # Seccion no existe, desafortunadamente hay secciones contiguas
                # a secciones invalidas asi que solo nos queda seguir con el
                # siguiente, esa logica no me agrada
                no_data += 1
                if no_data >= 100:
                    # Si van mas de 100 secciones invalidas contiguas
                    # creo que ya no hay mas secciones. Repito, esa logica
                    # no me agrada.
                    break
                else:
                    continue
            i += 1
            if i > 50:
                break
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
        return resultados

    def bonito(self, output):
        ilegibles = [item for item in output["error"] if item["tipo"] == "ILEGIBLE"]
        sin_dato = [item for item in output["error"] if item["tipo"] == "SIN DATO"]
        participacion = [item for item in output["error"] if item["tipo"] == "PARTICIPACION"]
        sin_acta = [item for item in output["error"] if item["tipo"] == "SIN ACTA"]
        pan = output["pan"]
        pri = output["pri"]
        prd = output["prd"]
        total = output["total"]
        out_str = "RESULTADOS\n\nVOTOS:\nPAN:\tPRI:\tPRD:\tTOTAL:\n%i\t%i\t%i\t%i\n\n"
        out_str = out_str % (pan, pri, prd, total)
        perc = float(100) / total
        perc_pan = pan * perc
        perc_pri = pri * perc
        perc_prd = prd * perc
        perc_str = "PORCENTAJE:\nPAN:\tPRI:\tPRD:\n%.2f\t%.2f\t%.2f\n\n"
        perc_str = perc_str % (perc_pan, perc_pri, perc_prd)
        err_str = "ERRORES:\nIlegibles: %i\tSin dato: %i\tSin acta: %i\tParticipacion: %i\n\n"
        err_str = err_str % (len(ilegibles), len(sin_dato), len(sin_acta), len(participacion))
        err_ileg = "Desglose de casillas ilegibles:\nPAN:\tPRI:\tPRD:\n%i\t%i\t%i\n\n"
        ileg_pan = [item for item in ilegibles if item["partido"] == "PAN"]
        ileg_pri = [item for item in ilegibles if item["partido"] == "PRI"]
        ileg_prd = [item for item in ilegibles if item["partido"] == "PRD"]
        err_ileg = err_ileg % (len(ileg_pan), len(ileg_pri), len(ileg_prd))
        err_ileg_secc = err_ileg + "Secciones afectadas:\n"
        secciones_ileg = set()
        for ileg in ilegibles:
            secciones_ileg.add((ileg["entidad"], ileg["seccion"]))
        for ent, secc in secciones_ileg:
            err_ileg_secc = err_ileg_secc + ("%i\t%s\n" % (secc, ent))
        err_part = "\nDesglose de casillas que superan el porcentaje de participacion:\n\n"
        err_part_secc = err_part + "Secciones afectadas:\n"
        secciones_part = set()
        for part in participacion:
            secciones_part.add((part["entidad"], part["seccion"]))
        for ent, secc in secciones_part:
            err_part_secc = err_part_secc + ("%i\t%s\n" % (secc, ent))
        err_sd = "\nDesglose de casillas sin dato:\nPAN:\tPRI:\tPRD:\n%i\t%i\t%i\n\n"
        sd_pan = [item for item in sin_dato if item["partido"] == "PAN"]
        sd_pri = [item for item in sin_dato if item["partido"] == "PRI"]
        sd_prd = [item for item in sin_dato if item["partido"] == "PRD"]
        err_sd = err_sd % (len(sd_pan), len(sd_pri), len(sd_prd))
        err_sd_secc = err_sd + "\nSecciones afectadas:\n"
        secciones_sd = set()
        for sd in sin_dato:
            secciones_sd.add((sd["entidad"], sd["seccion"]))
        for ent, secc in secciones_sd:
            err_sd_secc = err_sd_secc + ("%i\t%s\n" % (secc, ent))
        err_sa_secc = "\nDesglose de casillas sin acta:\n\nSecciones afectadas:\n"
        secciones_sa = set()
        for sa in sin_acta:
            secciones_sa.add((sa["entidad"], sa["seccion"]))
        for ent, secc in secciones_sa:
            err_sa_secc = err_sa_secc + ("%i\t%s\n" % (secc, ent))
        resultado = out_str + perc_str + err_str + err_ileg_secc + err_part_secc + err_sd_secc + err_sa_secc
        return resultado