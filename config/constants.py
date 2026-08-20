"""
Listas de valores FIJOS y EXACTOS para los menús desplegables del formulario.
Esta es la única fuente de verdad para estas listas: si algún día hay que
agregar, quitar o corregir un valor, se edita ÚNICAMENTE este archivo — no
hace falta tocar la base de datos.
"""

AREAS_DESTINO = [
    "ARCHIVO",
    "ATENCIÓN AL CLIENTE",
    "CARTERA Y COBRANZAS",
    "CATASTRO DE CLIENTES",
    "CONTROL OPERATIVO DE CONEXIONES",
    "CONTROL DE CONSUMOS",
    "LABORATORIO DE MEDIDORES",
    "LECTURAS Y FACTURACIÓN",
    "RECLAMOS",
]

# Detalle depende del Área destino elegida. La clave es el Área destino
# (debe existir en AREAS_DESTINO); el valor es la lista de Detalles
# permitidos para esa área.
AREA_DETALLE_MAP = {
    "ARCHIVO": ["DATOS CORRECTOS", "NO HAY QUIEN ATIENDA", "FUGAS", "SERVICIO SUSPENDIDO"],
    "CATASTRO DE CLIENTES": ["TIPO DE TARIFA", "ACTUALIZAR DATOS CATASTRALES"],
    "CONTROL OPERATIVO DE CONEXIONES": [
        "INSTALACIÓN DEL MEDIDOR", "ACTUALIZAR DATOS/ESTADO DEL MEDIDOR",
        "GARANTIA DE MEDIDOR", "CERTIFICAR ESTADO DE LA CONEXION",
    ],
    "LABORATORIO DE MEDIDORES": ["REVISIÓN TECNICA"],
    "ATENCIÓN AL CLIENTE": ["TAPONAMIENTO"],
    "RECLAMOS": ["REGULACION"],
    "LECTURAS Y FACTURACIÓN": ["REGULACION", "ACTUALIZACIÓN FLAG AP/ ALC"],
    "CONTROL DE CONSUMOS": ["CONEXIÓN/DERIVACION NO REGISTRADA"],
    "CARTERA Y COBRANZAS": ["CERTIFICAR ESTADO DE LA CONEXION"],
}

# Lista plana de todos los Detalles posibles (unión de todas las áreas).
# Se usa para la columna de edición en Base Consolidada, donde no es
# posible filtrar dinámicamente por fila.
ALL_DETALLES = sorted({d for lista in AREA_DETALLE_MAP.values() for d in lista})

INSPECTORES = [
    "ANGEL ZAMBRANO",
    "ANIBAL QUISILEMA",
    "CESAR AGUILERA",
    "DARWIN ULQUIANGO",
    "HOLGER MERA",
    "GALO BENALCAZAR",
    "WAGNER VIVAS",
    "XAVIER ZAMBRANO",
]

# Campo único "Analista" (unifica lo que antes eran "Autor" + "Analista responsable")
ANALISTAS = [
    "ANDRES RUEDA",
    "DIEGO ORTIZ",
    "FERNANDA VALLEJOS",
    "GUICELA GAIBOR",
    "KAROLINA VILLARREAL",
    "MARCO MARTINEZ",
    "RICARDO ORTEGA",
]

# Diccionario Sector -> Lugar. La clave es lo que se muestra en el
# desplegable "Sector"; el valor es lo que se autocompleta en "Lugar".
SECTOR_LUGAR = {
    "1": "CENTRO HISTORICO", "2": "SAN JUAN", "3": "AMERICA- ANTIGUO H. MILITAR", "4": "AMERICA- ANTIGUO H. MILITAR", "5": "AMERICA- ANTIGUO H. MILITAR", "6": "EL EJIDO-ALAMEDA", "7": "VICENTINA", "8": "ITCHIMBIA", "9": "ITCHIMBIA", "10": "LA TOLA", "11": "CENTRO HISTORICO", "12": "LA GASCA", "13": "LA RONDA", "14": "LA MARISCAL", "15": "EL PANECILLO",
    "16": "LA FLORESTA", "17": "SAN ROQUE", "18": "GUAPULO- HOTEL QUITO",
    "19": "COLMENA - DOS PUENTES", "20": "LA PAZ", "21": "LOS DOS PUENTES",
    "22": "LA COLON", "23": "CHIMBACALLE", "24": "MARIANA DE JESUS-LA PRADERA",
    "25": "CHIMBACALLE", "26": "BELISARIO QUEVEDO- LAS CASAS", "27": "ALPAHUASI",
    "28": "RUMIPAMBA-COLINAS DEL PICHINCHA", "29": "LOMA DE PUENGASI", "30": "CAROLINA",
    "31": "CHIRIYACU - ARGELIA", "32": "BELLAVISTA", "33": "FERROVIARIA",
    "34": "EL BATAN", "35": "VILLFLORA", "36": "IÑAQUITO", "37": "LA MAGDALENA", "39": "LA MAGDALENA", 
    "38": "CHAUPICRUZ-EL BOSUQE", "40": "COCHAPAMBA- LA PULIDA", "41": "CHILIBULO",
    "42": "ANTIGUO AEROPUERTO- CONCEPCION", "43": "ATAHUALPA BARRIO NUEVO",
    "44": "EL INCA", "45": "IEES FUT-GATAZO", "46": "EL INCA","47": "EL CALZADO", "48": "LA KENEDDY", "49": "GUAJALO", "50": "SAN CARLOS", "51": "LUCHA DE LOS POBRES-TURUBAMBA",
    "52": "COTOCOLLAO", "53": "SOLANDA", "54": "EL ROSARIO- SABANILLA", "55": "MENA DOS",
    "56": "COLLALOMA-FRENTE COMITE DEL PUEBLO", "57": "POTRERILLOS-SANTA BARBARA",
    "58": "COMITE DEL PUEBLO-LA BOTA", "59": "SANTA RITA", "60": "CONDADO BAJO",
    "61": "CHILLOGALLO-BUENA VENTURA", "62": "COTOCOLLAO- ESTADIO LDU",
    "63": "QUITUMBE- TERMINAL TERRESTRE", "64": "ANANSAYAS- ELOY ALFARO",
    "65": "QUITUMBE-PLATAFORMA GUBERNAMMENTAL SUR",
    "66": "CARRETAS- EXTENSION SIMON BOLIVAR NORTE",
    "67": "MUSCULOS Y RIELES-DIVINO NIÑO", "68": "LA VICTORI- COLEGO EINSTEIN",
    "69": "NUEVA AURORA", "70": "CARCELEN- CARCELEN BAJO",
    "71": "VENDEDORES AMBULANTES-HACIENDA IBARRA", "72": "CONDADO ALTO- ATUCUHO",
    "73": "GUAMANI- BALZAPAMBA", "75": "CAUPICHO", "305": "PUMBO", "310": "PIFO",
    "315": "TABABELA", "320": "YARUQUI", "325": "CHECA", "330": "QUINCHE",
    "335": "GUAYLLABAMBA", "405": "CUMBAYA", "410": "TUMBACO", "505": "GUANGOPOLO",
    "510": "CONOCOTO", "512": "CONOCOTO", "520": "ALANGASI", "525": "LA MERCED", "530": "AMAGUAÑA", "535": "PINTAG", "605": "SAN ANTONIO-MITAD DEL MUNDO", "610": "POMASQUI",
    "702": "CALDERON", "703": "CALDERON", "704": "CALDERON", "705": "CALDERON-CARAPUNGO",
    "710": "LLANO CHICO - LLANO GRANDE", "715": "ZAMBIZA", "720": "NAYON",
    "905": "PUELLARO", "910": "PERUCHO", "915": "CHAVEZPAMBA", "920": "ATAHUALPA",
    "925": "SAN JOSE DE MINAS", "930": "CALACALI", "935": "NONO", "940": "NANEGAL",
    "945": "NANEGALITO", "950": "GUALEA", "955": "PACTO", "990": "GUAMANI",
    "805": "LLOA",
}

SECTORES = list(SECTOR_LUGAR.keys())


def lugar_for_sector(sector: str) -> str:
    """Devuelve el Lugar correspondiente a un código de Sector, o '' si no existe."""
    return SECTOR_LUGAR.get(sector, "")


def detalles_for_area(area: str) -> list:
    """Devuelve la lista de Detalles válidos para un Área destino dada."""
    return AREA_DETALLE_MAP.get(area, [])


def is_valid_area_detalle(area: str, detalle: str) -> bool:
    return detalle in AREA_DETALLE_MAP.get(area, [])


# Encabezados obligatorios para la importación masiva (Excel/CSV).
# "Lugar" NO va en el archivo: se recalcula siempre a partir de "Sector".
IMPORT_REQUIRED_COLUMNS = [
    "Fecha", "Numero_cuenta", "Numero_orden", "Area_destino",
    "Detalle", "Sector", "Inspector", "Analista",
]
