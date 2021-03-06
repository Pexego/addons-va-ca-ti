# -*- encoding: utf-8 -*-
# Copyright (c) 2005-2006 TINY SPRL. (http:__tiny.be) All Rights Reserved.
#
# $Id: product_expiry.py 4304 2006-10-25 09:54:51Z ged $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and_or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import datetime
from osv import fields,osv
import pooler
import netsvc
import time
from xml import dom
from xml.parsers import expat

#BASE

class account_aux(osv.osv):
    
    _name = "account.aux"
    _columns = {
                'name':fields.char('Nombre', size=256),
                'id_aux':fields.integer('Id'),
                }
    

    def contrastar(self, cr, uid, ids, context = None):

	acc_obj = self.pool.get('account.account')
	
	for acc in acc_obj.browse(cr, uid, acc_obj.search(cr, uid, [])):
		ser = self.search(cr, uid, [('id_aux','=',acc.id)])
		if acc.id < 2322:
		  if len(ser)<1:
			acc.unlink()
		  else:
		     nam = self.browse(cr, uid, ser[0])
		     acc.write( {'name':nam.name})

	return True

account_aux()

