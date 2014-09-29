# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Francisco Pascual Gonzalez (<http://ting.es>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Expediciones valnera",
    "version" : "1.1",
    "author" : "Francico Pascual(Ting)",
    'complexity': "easy",
    "description" : """
        Modulo personalizado para la gestion de expediciones en la empresa Valnera.
    """,
    "website" : "http://www.ting.es",
    "images" : [],
    "depends" : ["sale"],
    "category" : "Modulos Ting",
    "sequence": 16,
    "init_xml" : [],
    "demo_xml" : [
    ],
    "update_xml" : [
        "expediciones_view.xml",
        "facturas_view.xml",
        "partner_view.xml",
        "informes_view.xml"
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
