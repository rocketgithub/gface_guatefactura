# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

#import odoo.addons.l10n_gt_extra.a_letras

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

class AccountMove(models.Model):
    _inherit = "account.move"

    firma_gface = fields.Char('Firma GFACE', copy=False)
    pdf_gface = fields.Binary('PDF GFACE', copy=False)
    nombre_cliente_gface = fields.Char('Nombre Cliente GFACE', copy=False)
    direccion_cliente_gface = fields.Char('Nombre Cliente GFACE', copy=False)


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
