# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

import wizard
import pooler
import time
from tools.translate import _

account_form = '''<?xml version="1.0"?>
<form string="Select parent account">
    <field name="account" colspan="4"/>
</form>'''

account_fields = {
    'account': {'string':'Account', 'type':'many2one', 'relation':'account.account', 'required':True},
}


class wizard_report(wizard.interface):

    def _check_state_xml(self, cr, uid, data, context):
           
            data['form']['xls'] = 'xls'
    #           data['form']['fiscalyear'] = 0
    #        else :
    #           data['form']['fiscalyear'] = 1
            return data['form']

    states = {
        
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch':account_form,'fields':account_fields, 'state':[('end','Cancel'),('report','Print'),('report_xml','Print XLS','gtk-print')]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.account.chart.report', 'state':'end'}
        },
        'report_xml': {
            'actions': [_check_state_xml],
            'result': {'type':'print', 'report':'account.account.chart.report', 'state':'end'}
        },
    }
wizard_report('account.account.chart.report')


