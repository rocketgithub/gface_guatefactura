# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

import odoo.addons.l10n_gt_extra.a_letras

from datetime import datetime
from lxml import etree
import base64
import logging
from requests import Session
from requests.auth import HTTPBasicAuth
import zeep
from zeep.transports import Transport

# import logging.config
# logging.config.dictConfig({
#     'version': 1,
#     'formatters': {
#         'verbose': {
#             'format': '%(name)s: %(message)s'
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'zeep.transports': {
#             'level': 'DEBUG',
#             'propagate': True,
#             'handlers': ['console'],
#         },
#     }
# })

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    firma_gface = fields.Char('Firma GFACE', copy=False)
    pdf_gface = fields.Binary('PDF GFACE', copy=False)

    def invoice_validate(self):
        detalles = []
        subtotal = 0
        for factura in self:
            if factura.journal_id.usuario_gface and not factura.firma_gface:

                DocElectronico = etree.Element("DocElectronico")

                Encabezado = etree.SubElement(DocElectronico, "Encabezado")

                Receptor = etree.SubElement(DocElectronico, "Receptor")
                NITReceptor = etree.SubElement(Receptor, "NITReceptor")
                NITReceptor.text = factura.partner_id.vat.replace('-','')
                if factura.partner_id.vat == "C/F":
                    Nombre = etree.SubElement(Receptor, "Nombre")
                    Nombre.text = factura.partner_id.name
                    Direccion = etree.SubElement(Receptor, "Direccion")
                    Direccion.text = factura.partner_id.street or "."

                InfoDoc = etree.SubElement(Encabezado, "InfoDoc")

                TipoVenta = etree.SubElement(InfoDoc, "TipoVenta")
                TipoVenta.text = "B" if factura.tipo_gasto == "compra" else "S"
                DestinoVenta = etree.SubElement(InfoDoc, "DestinoVenta")
                DestinoVenta.text = "1"
                Fecha = etree.SubElement(InfoDoc, "Fecha")
                Fecha.text = fields.Date.from_string(factura.date_invoice).strftime("%d/%m/%Y")
                Moneda = etree.SubElement(InfoDoc, "Moneda")
                Moneda.text = "1"
                Tasa = etree.SubElement(InfoDoc, "Tasa")
                Tasa.text = "1"
                Referencia = etree.SubElement(InfoDoc, "Referencia")
                Referencia.text = str(10000+factura.id)

                Totales = etree.SubElement(Encabezado, "Totales")

                Bruto = etree.SubElement(Totales, "Bruto")
                Bruto.text = "%.2f" % factura.amount_total
                Descuento = etree.SubElement(Totales, "Descuento")
                Descuento.text = "0"
                Exento = etree.SubElement(Totales, "Exento")
                Exento.text = "0"
                Otros = etree.SubElement(Totales, "Otros")
                Otros.text = "0"
                Neto = etree.SubElement(Totales, "Neto")
                Neto.text = "%.2f" % factura.amount_untaxed
                Isr = etree.SubElement(Totales, "Isr")
                Isr.text = "0"
                Iva = etree.SubElement(Totales, "Iva")
                Iva.text = "%.2f" % (factura.amount_total - factura.amount_untaxed)
                Total = etree.SubElement(Totales, "Total")
                Total.text = "%.2f" % factura.amount_total

                subtotal = 0
                total = 0
                Detalles = etree.SubElement(DocElectronico, "Detalles")
                for linea in factura.invoice_line_ids:
                    if linea.price_unit != 0 and linea.quantity != 0:
                        precio_unitario = linea.price_unit * (100-linea.discount) / 100
                        precio_unitario_base = linea.price_subtotal / linea.quantity

                        total_linea = precio_unitario * linea.quantity
                        total_linea_base = precio_unitario_base * linea.quantity

                        total_impuestos = total_linea - total_linea_base
                        tasa = "12" if total_impuestos > 0 else "0"

                        Productos = etree.SubElement(Detalles, "Productos")

                        Producto = etree.SubElement(Productos, "Producto")
                        # Producto.text = linea.product_id.default_code or "-"
                        Producto.text = 'P'+str(linea.product_id.id)
                        Descripcion = etree.SubElement(Productos, "Descripcion")
                        Descripcion.text = linea.name
                        Medida = etree.SubElement(Productos, "Medida")
                        Medida.text = "1"
                        Cantidad = etree.SubElement(Productos, "Cantidad")
                        Cantidad.text = str(linea.quantity)
                        Precio = etree.SubElement(Productos, "Precio")
                        Precio.text = "%.2f" % precio_unitario
                        PorcDesc = etree.SubElement(Productos, "PorcDesc")
                        PorcDesc.text = "0"
                        ImpBruto = etree.SubElement(Productos, "ImpBruto")
                        ImpBruto.text = "%.2f" % total_linea
                        ImpDescuento = etree.SubElement(Productos, "ImpDescuento")
                        ImpDescuento.text = "0"
                        ImpExento = etree.SubElement(Productos, "ImpExento")
                        ImpExento.text = "0"
                        ImpOtros = etree.SubElement(Productos, "ImpOtros")
                        ImpOtros.text = "0"
                        ImpNeto = etree.SubElement(Productos, "ImpNeto")
                        ImpNeto.text = "%.2f" % total_linea_base
                        ImpIsr = etree.SubElement(Productos, "ImpIsr")
                        ImpIsr.text = "0"
                        ImpIva = etree.SubElement(Productos, "ImpIva")
                        ImpIva.text = "%.2f" % (total_linea - total_linea_base)
                        ImpTotal = etree.SubElement(Productos, "ImpTotal")
                        ImpTotal.text = "%.2f" % total_linea

                        total += total_linea
                        subtotal += total_linea_base

                if factura.journal_id.tipo_documento_gface > 1:
                    DocAsociados = etree.SubElement(Detalles, "DocAsociados")
                    DASerie = etree.SubElement(DocAsociados, "DASerie")
                    DASerie.text = factura.numero_viejo.split("|")[0]
                    DAPreimpreso = etree.SubElement(DocAsociados, "DAPreimpreso")
                    DAPreimpreso.text = factura.numero_viejo.split("|")[1]

                xmls = etree.tostring(DocElectronico, xml_declaration=True, encoding="UTF-8", pretty_print=True)
                logging.warn(xmls)

                session = Session()
                session.verify = False
                session.auth = HTTPBasicAuth('usr_guatefac', 'usrguatefac')
                session.http_auth = HTTPBasicAuth('usr_guatefac', 'usrguatefac')
                session.headers.update({'Authorization': 'Basic dXNyX2d1YXRlZmFjOnVzcmd1YXRlZmFj'})
                transport = Transport(session=session)
                wsdl = 'https://usr_guatefac:usrguatefac@pdte.guatefacturas.com/webservices63/produccion/svc01/Guatefac?WSDL'
                client = zeep.Client(wsdl=wsdl, transport=transport)

                resultado = client.service.generaDocumento(factura.journal_id.usuario_gface, factura.journal_id.clave_gface, factura.journal_id.nit_gface, factura.journal_id.establecimiento_gface, factura.journal_id.tipo_documento_gface, factura.journal_id.id_maquina_gface, "R", xmls)
                resultado = resultado.replace("&", "&amp;")
                logging.warn(resultado)
                resultadoXML = etree.XML(resultado)

                if len(resultadoXML.xpath("//Firma")) > 0:
                    firma = resultadoXML.xpath("//Firma")[0].text
                    numero = resultadoXML.xpath("//Serie")[0].text+'-'+resultadoXML.xpath("//Preimpreso")[0].text
                    factura.firma_gface = firma
                    factura.name = numero
                else:
                    raise UserError(resultadoXML.xpath("//Resultado")[0].text)

        return super(AccountInvoice,self).invoice_validate()

class AccountJournal(models.Model):
    _inherit = "account.journal"

    usuario_gface = fields.Char('Usuario GFACE', copy=False)
    clave_gface = fields.Char('Clave GFACE', copy=False)
    nit_gface = fields.Char('NIT GFACE', copy=False)
    establecimiento_gface = fields.Char('Establecimiento GFACE', copy=False)
    tipo_documento_gface = fields.Integer('Tipo de Documento GFACE', copy=False)
    id_maquina_gface = fields.Integer('ID Maquina GFACE', copy=False)
    serie_gface = fields.Char('Serie GFACE', copy=False)
    numero_resolucion_gface = fields.Char('Numero Resolución GFACE', copy=False)
    fecha_resolucion_gface = fields.Date('Fecha Resolución GFACE', copy=False)
    rango_inicial_gface = fields.Integer('Rango Inicial GFACE', copy=False)
    rango_final_gface = fields.Integer('Rango Final GFACE', copy=False)
    dispositivo_gface = fields.Char('Dispositivo GFACE', copy=False)
    nombre_documento_gface = fields.Selection([('Factura', 'Factura'), ('Nota de crédito', 'Nota de crédito'), ('Nota de débito', 'Nota de débito')], 'Tipo de Documento GFACE', copy=False)
