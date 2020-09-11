# Frappe 
from __future__ import unicode_literals
import frappe
import requests
import json
import pprint
from frappe import _
from frappe.utils import now_datetime


def tcc_fetch(packages: list):
    '''Main function that calls get_data, and then calls process data'''
    names = [p.name for p in packages]
    print(f"Fetching TCC packages {names}")
    return tcc_get_data(packages)


def tcc_get_data(packages: list):
    endpoint = 'https://tccrestify-dot-tcc-cloud.appspot.com/tracking/wid'
    docs = []
    for packages_chunk in chunks(packages, 10):
        r = requests.post(endpoint, json=tcc_format_body(packages_chunk))
        print("Status Code: ", r.status_code, "Response: ", r.json())
        data = r.json()
        if any(data):
            docs_chunk = tcc_process_data(packages_chunk, data)
            docs = docs + docs_chunk

    # Save the results.
    [d.save() for d in docs]

    # TODO: Validation that all ot the items are documents.
    # then save them.
    return docs


def tcc_process_data(packages, data):
    """Process the data response from tcc

    :packages: list of package objects.
    :data: data returned from tcc
    :returns: packages with updated values

    """
    updated_packages = []
    packages_info = data.get('remesas')['remesa']
    if any(packages_info):
        for pinfo in packages_info:
            package = next(filter(lambda p: p.guide == pinfo["numeroremesa"],
                           packages))
            if package:
                update = {
                    'origin_real': find_location(pinfo['ciudadorigen']['codigodane']),
                    'destination': find_location(pinfo['ciudaddestino']['codigodane']),
                    'address': pinfo['direcciondestinatario'].title(),
                    'observation': pinfo['observaciones'].title(),
                    'sender_name': pinfo['nombreremitente'].title(),
                    'sender_id': pinfo['identificacionremitente'].title(),
                    'receiver_name': pinfo['nombredestinatario'].title(),
                    'receiver_id': pinfo['identificaciondestinatario'],
                    'receiver_phone': pinfo['telefonodestinatario'],
                    'weight': pinfo['pesoreal'],
                    'weight_vol': pinfo['pesovolumen'],
                    'weight_charged': pinfo['pesofacturado'],
                    'type': 'package' if pinfo['unidadnegocio']['abreviatura'] == 'PQ' else 'envelope',
                    # TODO: Implement to_collect
                    # "to_collect": '',
                    "to_fetch": False
                }
                # Update the data from the package
                package.update(update)
                package.append('fetches', {
                            'doctype': 'Package Information Fetch',
                            'succesful': True,
                            'note': f'Received Information: \n{pprint.pformat(pinfo)}'
                            })
                updated_packages.append(package)

        # Packages that information wasn't received
        not_updated = {p.name for p in packages} - {p.name for p in updated_packages}
        for package in not_updated:
            package.append('fetches', {
                'doctype': 'Package Information Fetch',
                'succesful': False,
                'note': f'Did not receive any information for this package.'
                })
            updated_packages.append(package)
    else:
        updated_packages = packages

    return updated_packages


def tcc_format_guide(guide):
    return {
            "remesa": {
                "numero": guide,
                "esrelacion": ""
                }
            }


def tcc_format_body(packages):
    remesas = []
    for package in packages:
        remesas.append(tcc_format_guide(package.guide))

    body = {
            "tipodocumento": None,
            "numerodocumento": None,
            "remesas": remesas
            }

    return body


def find_location(value):
    """ Find the associated location from value
    :returns: location name
    """
    # Remove the last three digits and change for 000
    value = str(value)[:-3] + '000'
    location = frappe.get_all(
            'Package Location',
            filters={
                "dane_code": value
            },
            fields=['name'])

    if len(location) == 1:
        location = location[0].name
    else:
        location = None

    return location


def chunks(li: list, n: int):
    for i in range(0, len(li), n):
        yield li[i: i+n]


# {
#     "remesas": {
#         "remesa": [
#             {
#                 "numeroremesa": "133161454",
#                 "fecharemesa": "2020-07-24",
#                 "documentos": {
#                     "documento": [
#                         {
#                             "tipodocumento": {
#                                 "descripcion": "",
#                                 "abreviatura": ""
#                             },
#                             "numerodocumento": "133161454",
#                             "fechadocumento": ""
#                         }
#                     ]
#                 },
#                 "ciudadorigen": {
#                     "id": "1",
#                     "descripcion": "MEDELLÍN",
#                     "abreviatura": "MEDELLÍN",
#                     "codigodane": "05001000"
#                 },
#                 "ciudaddestino": {
#                     "id": "39",
#                     "descripcion": "ARJONA",
#                     "abreviatura": "ARJONA",
#                     "codigodane": "13052000"
#                 },
#                 "estadoremesa": {
#                     "id": "3000",
#                     "descripcion": "Entregada el 01/08/2020 12:00:00 AM",
#                     "abreviatura": ""
#                 },
#                 "tieneimagen": "FALSE",
#                 "tienenovedad": "TRUE",
#                 "nombreremitente": "MATTELSA S.A.S - MATTELSA S.A.S",
#                 "direccionremitente": "CL 35 46 63 MEDELLÍN ANTIOQUIA",
#                 "telefonoremitente": "2320913",
#                 "identificacionremitente": "830513441",
#                 "cuentaremitente": "5598300",
#                 "nombrecuentaremitente": "MATTELSA S.A.S 5598300",
#                 "nombredestinatario": "luis daniel ortega castro",
#                 "telefonodestinatario": "3233561346 - 32",
#                 "direcciondestinatario": "CL 43 03 01 Calle junin",
#                 "identificaciondestinatario": "222222222",
#                 "formapago": "CREDITO EN ORIGEN",
#                 "unidades": "1",
#                 "pesoreal": "1",
#                 "observaciones": "Santa lucia - Diagonal al parque santa luci",
#                 "fechaentrega": "2020-08-01T00:00:00.000-05:00",
#                 "diasentrega": "",
#                 "unidadnegocio": {
#                     "id": "2",
#                     "descripcion": "MENSAJERIA",
#                     "abreviatura": "ME"
#                 },
#                 "valormercancia": "35000",
#                 "ceoporigen": "MEDELLÍN",
#                 "ceopdestino": "CARTAGENA",
#                 "viajenacional": "343285",
#                 "movilnacional": "PRN01_AN - PRN002",
#                 "vannacional": "12104 - R13510",
#                 "viajelocal": "3",
#                 "movillocal": "14222 - VEL550",
#                 "flete": "6350",
#                 "zonalocal": "ZONA UNICA",
#                 "rutalocal": "RUTA 22 REEXPEDIDOR LOGINCARGO",
#                 "conductorlocal": "LOGISTICA INTEGRAL DE CARGA LOGINCARGO S",
#                 "fechapromesa": "2020-07-30",
#                 "licencia": "MENSAJERIA POSTAL",
#                 "idlicencia": "1",
#                 "pesovolumen": "0",
#                 "pesofacturado": "1",
#                 "codigobolsa": "",
#                 "tiposervicio": "NORMAL",
#                 "valorrecaudo": "",
#                 "codigopostaldestino": "",
#                 "novedades": {
#                     "novedad": [
#                         {
#                             "codigo": "74801446",
#                             "proceso": "3",
#                             "ciudadplantea": {
#                                 "id": "39",
#                                 "descripcion": "ARJONA",
#                                 "abreviatura": "ARJONA",
#                                 "codigodane": ""
#                             },
#                             "ciudadsoluciona": {
#                                 "id": "1",
#                                 "descripcion": "MEDELLIN",
#                                 "abreviatura": "MEDELLIN",
#                                 "codigodane": ""
#                             },
#                             "fechanovedad": "2020-07-27T14:40:00",
#                             "fechaplanteamiento": "2020-07-27T14:40:00",
#                             "usuarioplantea": "DMARTINEZA - DAVID MARTINEZ ARNEDO",
#                             "fechasolucion": "2020-07-27T14:47:52",
#                             "causa": "Mercancía No Sale A Distribución - Cliente Recibe En Fecha U Horario Específico",
#                             "codigocausa": "232",
#                             "estado": "Ejecutada",
#                             "tipodenovedad": "Normal",
#                             "comentarios": "EL REEXPEDIDOR VIAJARA EL DÍA 28-7-2020........",
#                             "definicion": "Su mercancía ya se encuentra en centro de operación destino. Aún no ha sido entregada porque el destinatario recibe en una fecha u hora específica, por lo tanto, nos encontramos a la espera de la asignación de la cita para ofrecer la mercancía o del cumplimiento de dicha cita.",
#                             "novedadprincipal": "Mercancía No Sale A Distribución",
#                             "complementonovedad": "Cliente Recibe En Fecha U Horario Específico",
#                             "seguimientos": {
#                                 "seguimiento": [
#                                     {
#                                         "fechaseguimiento": "2020-07-27T14:47:52",
#                                         "observaciones": "EL REEXPEDIDOR VIAJARA EL DÍA 28-7-2020........",
#                                         "seguimiento": "EL REEXPEDIDOR VIAJARA EL DÍA 28-7-2020........",
#                                         "fechasolucion": "2020-07-27T14:47:52",
#                                         "essolucion": "TRUE",
#                                         "usuarioseguimiento": "dmartineza",
#                                         "funcionariocliente": "",
#                                         "funcionariotcc": "dmartineza - David Martinez Arnedo",
#                                         "nuevadireccion": "",
#                                         "fechareofrecimiento": "",
#                                         "ventanahoraria": "",
#                                         "esrechazo": "FALSE",
#                                         "fecharechazo": "",
#                                         "usuariorechazo": "",
#                                         "observacionrechazo": "",
#                                         "tiposeguimiento": ""
#                                     }
#                                 ]
#                             }
#                         },
#                         {
#                             "codigo": "74775237",
#                             "proceso": "2",
#                             "ciudadplantea": {
#                                 "id": "39",
#                                 "descripcion": "ARJONA",
#                                 "abreviatura": "ARJONA",
#                                 "codigodane": ""
#                             },
#                             "ciudadsoluciona": {
#                                 "id": "1",
#                                 "descripcion": "MEDELLIN",
#                                 "abreviatura": "MEDELLIN",
#                                 "codigodane": ""
#                             },
#                             "fechanovedad": "2020-07-25T01:33:00",
#                             "fechaplanteamiento": "2020-07-25T01:33:00",
#                             "usuarioplantea": "DMCAVIEDES - DIANA MARCELA CAVIEDES ARBOLEDA",
#                             "fechasolucion": "2020-07-25T08:11:40",
#                             "causa": "Mercancía No Ha Llegado A Centro De Operación Destino Tcc - Restricción En Las Vías Nacionales",
#                             "codigocausa": "228",
#                             "estado": "Ejecutada",
#                             "tipodenovedad": "Normal",
#                             "comentarios": "Novedad Rutas Nacionales, Viaje UNIGIS: 309447, Deslizamiento de Tierra, Latitud: 7.2843487280238, Longitud: -75.392729895348",
#                             "definicion": "Su mercancía aún se encuentra en tránsito hacia el centro de operación destino, debido a restricción en las vías.",
#                             "novedadprincipal": "Mercancía No Ha Llegado A Centro De Operación Destino Tcc",
#                             "complementonovedad": "Restricción En Las Vías Nacionales",
#                             "seguimientos": {
#                                 "seguimiento": [
#                                     {
#                                         "fechaseguimiento": "2020-07-25T08:11:40",
#                                         "observaciones": "ESTA MERCANCÍA DEBE OFRECERSE AL SIGUIENTE DÍA HÁBIL",
#                                         "seguimiento": "ESTA MERCANCÍA DEBE OFRECERSE AL SIGUIENTE DÍA HÁBIL",
#                                         "fechasolucion": "2020-07-25T08:11:40",
#                                         "essolucion": "TRUE",
#                                         "usuarioseguimiento": "DMCAVIEDES - DIANA MARCELA CA",
#                                         "funcionariocliente": "PROCESO AUTOMÁTICO",
#                                         "funcionariotcc": "DMCAVIEDES - DIANA MARCELA CAVIEDES ARBOLEDA",
#                                         "nuevadireccion": "",
#                                         "fechareofrecimiento": "2020-07-27T00:00:00",
#                                         "ventanahoraria": "08:00:00 AM - 06:00:00 PM",
#                                         "esrechazo": "FALSE",
#                                         "fecharechazo": "",
#                                         "usuariorechazo": "",
#                                         "observacionrechazo": "",
#                                         "tiposeguimiento": ""
#                                     }
#                                 ]
#                             }
#                         }
#                     ]
#                 }
#             },
#             {
#                 "numeroremesa": "439476256",
#                 "fecharemesa": "2020-07-23",
#                 "documentos": {
#                     "documento": [
#                         {
#                             "tipodocumento": {
#                                 "descripcion": "",
#                                 "abreviatura": ""
#                             },
#                             "numerodocumento": "FH885",
#                             "fechadocumento": ""
#                         }
#                     ]
#                 },
#                 "ciudadorigen": {
#                     "id": "1",
#                     "descripcion": "MEDELLÍN",
#                     "abreviatura": "MEDELLÍN",
#                     "codigodane": "05001000"
#                 },
#                 "ciudaddestino": {
#                     "id": "39",
#                     "descripcion": "ARJONA",
#                     "abreviatura": "ARJONA",
#                     "codigodane": "13052000"
#                 },
#                 "estadoremesa": {
#                     "id": "3000",
#                     "descripcion": "Entregada el 14/08/2020 12:00:00 AM",
#                     "abreviatura": ""
#                 },
#                 "tieneimagen": "FALSE",
#                 "tienenovedad": "TRUE",
#                 "nombreremitente": "FAHILOS S.A.",
#                 "direccionremitente": "CLL. 79 B SUR #54-80",
#                 "telefonoremitente": "3092020",
#                 "identificacionremitente": "890900342",
#                 "cuentaremitente": "1932400",
#                 "nombrecuentaremitente": "FAHILOS (1) S.A. 1932400",
#                 "nombredestinatario": "DUARTE GALVAN MIGUEL DE JESUS",
#                 "telefonodestinatario": "3008867412",
#                 "direcciondestinatario": "AVENIDA PASTRANA N 23-72-ALMACEN SAIRATES",
#                 "identificaciondestinatario": "1043436166-3",
#                 "formapago": "CREDITO EN ORIGEN",
#                 "unidades": "1",
#                 "pesoreal": "10",
#                 "observaciones": "107243",
#                 "fechaentrega": "2020-08-14T00:00:00.000-05:00",
#                 "diasentrega": "",
#                 "unidadnegocio": {
#                     "id": "1",
#                     "descripcion": "PAQUETERIA",
#                     "abreviatura": "PQ"
#                 },
#                 "valormercancia": "560000",
#                 "ceoporigen": "MEDELLÍN",
#                 "ceopdestino": "CARTAGENA",
#                 "viajenacional": "343113",
#                 "movilnacional": "PRN01_AN - PRN002",
#                 "vannacional": "12032 - R05202",
#                 "viajelocal": "2",
#                 "movillocal": "14222 - VEL550",
#                 "flete": "13590",
#                 "zonalocal": "ZONA UNICA",
#                 "rutalocal": "RUTA 22 REEXPEDIDOR LOGINCARGO",
#                 "conductorlocal": "LOGISTICA INTEGRAL DE CARGA LOGINCARGO S",
#                 "fechapromesa": "2020-07-25",
#                 "licencia": "PAQUETERIA",
#                 "idlicencia": "3",
#                 "pesovolumen": "0",
#                 "pesofacturado": "30",
#                 "codigobolsa": "",
#                 "tiposervicio": "NORMAL",
#                 "valorrecaudo": "",
#                 "codigopostaldestino": "",
#                 "novedades": {
#                     "novedad": [
#                         {
#                             "codigo": "74801472",
#                             "proceso": "3",
#                             "ciudadplantea": {
#                                 "id": "39",
#                                 "descripcion": "ARJONA",
#                                 "abreviatura": "ARJONA",
#                                 "codigodane": ""
#                             },
#                             "ciudadsoluciona": {
#                                 "id": "1",
#                                 "descripcion": "MEDELLIN",
#                                 "abreviatura": "MEDELLIN",
#                                 "codigodane": ""
#                             },
#                             "fechanovedad": "2020-07-27T14:42:00",
#                             "fechaplanteamiento": "2020-07-27T14:42:00",
#                             "usuarioplantea": "DMARTINEZA - DAVID MARTINEZ ARNEDO",
#                             "fechasolucion": "2020-07-27T14:47:53",
#                             "causa": "Mercancía No Sale A Distribución - Cliente Recibe En Fecha U Horario Específico",
#                             "codigocausa": "232",
#                             "estado": "Ejecutada",
#                             "tipodenovedad": "Normal",
#                             "comentarios": "EL REEXPEDIDOR VIAJARA EL DÍA 28-7-2020........",
#                             "definicion": "Su mercancía ya se encuentra en centro de operación destino. Aún no ha sido entregada porque el destinatario recibe en una fecha u hora específica, por lo tanto, nos encontramos a la espera de la asignación de la cita para ofrecer la mercancía o del cumplimiento de dicha cita.",
#                             "novedadprincipal": "Mercancía No Sale A Distribución",
#                             "complementonovedad": "Cliente Recibe En Fecha U Horario Específico",
#                             "seguimientos": {
#                                 "seguimiento": [
#                                     {
#                                         "fechaseguimiento": "2020-07-27T14:47:53",
#                                         "observaciones": "EL REEXPEDIDOR VIAJARA EL DÍA 28-7-2020........",
#                                         "seguimiento": "EL REEXPEDIDOR VIAJARA EL DÍA 28-7-2020........",
#                                         "fechasolucion": "2020-07-27T14:47:53",
#                                         "essolucion": "TRUE",
#                                         "usuarioseguimiento": "dmartineza",
#                                         "funcionariocliente": "",
#                                         "funcionariotcc": "dmartineza - David Martinez Arnedo",
#                                         "nuevadireccion": "",
#                                         "fechareofrecimiento": "",
#                                         "ventanahoraria": "",
#                                         "esrechazo": "FALSE",
#                                         "fecharechazo": "",
#                                         "usuariorechazo": "",
#                                         "observacionrechazo": "",
#                                         "tiposeguimiento": ""
#                                     }
#                                 ]
#                             }
#                         },
#                         {
#                             "codigo": "74784903",
#                             "proceso": "3",
#                             "ciudadplantea": {
#                                 "id": "39",
#                                 "descripcion": "ARJONA",
#                                 "abreviatura": "ARJONA",
#                                 "codigodane": ""
#                             },
#                             "ciudadsoluciona": {
#                                 "id": "1",
#                                 "descripcion": "MEDELLIN",
#                                 "abreviatura": "MEDELLIN",
#                                 "codigodane": ""
#                             },
#                             "fechanovedad": "2020-07-25T13:34:00",
#                             "fechaplanteamiento": "2020-07-25T13:34:00",
#                             "usuarioplantea": "JALCALAR - JEFFREY ALCALA RUDA",
#                             "fechasolucion": "2020-07-25T13:35:28",
#                             "causa": "Mercancía No Sale A Distribución - Restricción En Las Vías Urbanas",
#                             "codigocausa": "301",
#                             "estado": "Ejecutada",
#                             "tipodenovedad": "Normal",
#                             "comentarios": "S EOFRECERA EL DIA  27 DE JULIO",
#                             "definicion": "Su mercancía se encuentra en centro de operación destino. Aún no ha sido entrega a destinatario por dificultades en las vías.  Estaremos dando continuidad al servicio lo más pronto posible.",
#                             "novedadprincipal": "Mercancía No Sale A Distribución",
#                             "complementonovedad": "Restricción En Las Vías Urbanas",
#                             "seguimientos": {
#                                 "seguimiento": [
#                                     {
#                                         "fechaseguimiento": "2020-07-25T13:35:28",
#                                         "observaciones": "ESTA MERCANCÍA DEBE OFRECERSE AL SIGUIENTE DÍA HÁBIL",
#                                         "seguimiento": "ESTA MERCANCÍA DEBE OFRECERSE AL SIGUIENTE DÍA HÁBIL",
#                                         "fechasolucion": "2020-07-25T13:35:28",
#                                         "essolucion": "TRUE",
#                                         "usuarioseguimiento": "JALCALAR - JEFFREY ALCALA RUD",
#                                         "funcionariocliente": "PROCESO AUTOMÁTICO",
#                                         "funcionariotcc": "JALCALAR - JEFFREY ALCALA RUDA",
#                                         "nuevadireccion": "",
#                                         "fechareofrecimiento": "2020-07-27T00:00:00",
#                                         "ventanahoraria": "08:00:00 AM - 06:00:00 PM",
#                                         "esrechazo": "FALSE",
#                                         "fecharechazo": "",
#                                         "usuariorechazo": "",
#                                         "observacionrechazo": "",
#                                         "tiposeguimiento": ""
#                                     }
#                                 ]
#                             }
#                         }
#                     ]
#                 }
#             }
#         ]
#     },
#     "respuesta": {
#         "codigo": "0",
#         "mensaje": "Consulta exitosa",
#         "codigointerno": "0",
#         "mensajeinterno": "Consulta exitosa"
#     }
# }
