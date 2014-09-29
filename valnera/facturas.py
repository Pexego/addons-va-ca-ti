# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
from tools.translate import _
from datetime import datetime
import netsvc

class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'


    def create_move_from_st_line(self, cr, uid, st_line_id, company_currency_id, next_number, context=None):
        voucher_obj = self.pool.get('account.voucher')
        wf_service = netsvc.LocalService("workflow")
        move_line_obj = self.pool.get('account.move.line')
        bank_st_line_obj = self.pool.get('account.bank.statement.line')
        st_line = bank_st_line_obj.browse(cr, uid, st_line_id, context=context)

        if st_line.voucher_id:
            st_line.voucher_id.write({'fecha':st_line.date or st_line.voucher_id.date})
            cr.commit()

        if st_line.voucher_id:
            voucher_obj.write(cr, uid, [st_line.voucher_id.id], {'number': next_number}, context=context)
            if st_line.voucher_id.state == 'cancel':
                voucher_obj.action_cancel_draft(cr, uid, [st_line.voucher_id.id], context=context)
            wf_service.trg_validate(uid, 'account.voucher', st_line.voucher_id.id, 'proforma_voucher', cr) 
  

            v = voucher_obj.browse(cr, uid, st_line.voucher_id.id, context=context)
            bank_st_line_obj.write(cr, uid, [st_line_id], {
                'move_ids': [(4, v.move_id.id, False)]
            })

            return move_line_obj.write(cr, uid, [x.id for x in v.move_ids], {'statement_id': st_line.statement_id.id}, context=context)
        return super(account_bank_statement, self).create_move_from_st_line(cr, uid, st_line.id, company_currency_id, next_number, context=context)

account_bank_statement()

class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    _columns = {
                    'fecha':fields.date('Fecha extracto'),
                }

    def account_move_get(self, cr, uid, voucher_id, context=None):
        seq_obj = self.pool.get('ir.sequence')
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        #FIX PXGO NO se puede poner en este punto el name del movimiento se cambia para dejarlo en '/'
        if voucher_brw.number:
            name = voucher_brw.number
        elif voucher_brw.journal_id.sequence_id:
            name = seq_obj.next_by_id(cr, uid, voucher_brw.journal_id.sequence_id.id, context)
        else:
            raise osv.except_osv(_('Error !'),
                        _('Please define a sequence on the journal !'))
        #name = "/"
        if not voucher_brw.reference:
            ref = name.replace('/', '')
        else:
            ref = voucher_brw.reference

        #print ' voucher_brw.fecha     '+str( voucher_brw.fecha)+'    '+str(voucher_brw.date)


        move = {
             'name': name,
             'journal_id': voucher_brw.journal_id.id,
             'narration': voucher_brw.narration,
             'date': voucher_brw.fecha or voucher_brw.date,
             'ref': ref,
             'period_id': voucher_brw.period_id and voucher_brw.period_id.id or False
        }
        return move




account_voucher()

class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        
        if 'amount' in vals:
            vals['samount']  = self.pool.get('account.invoice').estruct_dig(cr, uid, str(vals['amount']))
        
        if 'base' in vals:
            vals['sbase'] = self.pool.get('account.invoice').estruct_dig(cr, uid, str(vals['base']))
        

        res = super(account_invoice_tax, self).create(cr, uid, vals, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):

        
        
        iv = self.browse(cr, uid, ids[0])

        vals['samount']  = self.pool.get('account.invoice').estruct_dig(cr, uid, str(iv.amount))
        vals['sbase'] = self.pool.get('account.invoice').estruct_dig(cr, uid, str(iv.base))
    
        res = super(account_invoice_tax, self).write(cr, uid, ids, vals, context=context)
        return res

    _columns = {
                    'samount':fields.char('Cantidad', size=256),    
                    'sbase':fields.char('Cantidad', size=256),    
                }

account_invoice_tax()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'


    def ch_ex(self, cr, uid, ids, ex, context = None):

        if not ex:
            v = {'nescala': False}
            return {'value': v}

        ex_obj = self.pool.get('expediciones.expediciones')
        exp = ex_obj.browse(cr, uid, ex)

        v = {'nescala': exp.escala}

        return {'value': v}

    def ch_es(self, cr, uid, ids, es, context = None):

        if not es:
            v = {'expedicion_id': False}
            return {'value': v}

        ex_obj = self.pool.get('expediciones.expediciones')

        ex_s = ex_obj.search(cr, uid, [('escala','=',es)])

        if len(ex_s) < 1:
            raise osv.except_osv(_('Error'), _('No hay ninguna expedición con ese numero de escala'))

        v = {'expedicion_id': ex_s[0],'expedicion_aux': ex_s[0]}

        return {'value': v}

    _columns = {
                    'expedicion_id':fields.many2one('expediciones.expediciones','Nº Expedición'),
                    'expedicion_alm':fields.many2one('expediciones.expediciones','Expedición auxiliar'),

                    'nescala':fields.char('Nº de escala', size=256),

                    'recibido': fields.selection([('no', 'No'),
                                    ('si', 'Sí­'),
                                    ],'Recibido'),
                    'pagado': fields.selection([('no', 'No'),
                                    ('si', 'Sí­'),
                                    ],'Pagado'),
                    'afecta': fields.selection([                                 
                                    ('no', 'No'),
                                    ('mercancias', 'Mercancias'),
                                    ('buques', 'Buques'),
                                    ],'Afecta'),
                    'validar': fields.boolean('Validador de escritura'),

                #Fecha informe

                'fechainf':fields.char('fechainf', size=256),
                    
                #Campos referencia para el informe


                'texto':fields.char('Texto superior', size=512),
                'anexos':fields.char('Anexos', size=512),

                'ref1':fields.char('Referencia 1', size=32),
                'ref2':fields.char('Referencia 2', size=32),
                'ref3':fields.char('Referencia 3', size=32),
                'ref4':fields.char('Referencia 4', size=32),
                'ref5':fields.char('Referencia 5', size=32),
                'ref6':fields.char('Referencia 6', size=32),
                'ref7':fields.char('Referencia 7', size=32),
                'ref8':fields.char('Referencia 8', size=32),
                'ref9':fields.char('Referencia 9', size=32),
                'ref10':fields.char('Referencia 10', size=32),
                'ref11':fields.char('Referencia 11', size=32),
                'ref12':fields.char('Referencia 12', size=32),

                'samount_total':fields.char('Total', size=64),
                'samount_untaxed':fields.char('Total sin impuestos', size=64),
                'samount_tax':fields.char('Total impuestos', size=64),
                'val_s': fields.boolean('Validador'),   
                }


    def estruct_dig(self, cr, uid, dato, context=None):

        dec = '.00'
        neg = False

        if len(dato.split('-')) > 1:
            neg = True
            dato = dato.split('-')[1]

        dig_s = str(dato).split('.')

        if len(dig_s) > 1:
           if len(dig_s[1]) < 2:
                dec=','+dig_s[1]+'0'
           else:
                dec=','+dig_s[1]

        car = len(dig_s[0])
        
        dig = ''

        while car > 3:
            dig =  '.'+str(dig_s[0][(car-3):car])+ dig            
            car = car-3

        dig = str(dig_s[0][0:car])+ str(dig) + str(dec)

        if neg:
            dig = '-'+dig    

        return dig

    def estructurar(self, cr, uid, id_inv, context=None):

        inv = self.browse(cr, uid, id_inv)[0]
        
        total = self.estruct_dig(cr, uid, str(inv.amount_total))
        total_untaxed = self.estruct_dig(cr, uid, str(inv.amount_untaxed))
        total_tax = self.estruct_dig(cr, uid, str(inv.amount_tax))

        inv.write({
                    'samount_total':total,
                    'samount_untaxed':total_untaxed,
                    'samount_tax':total_tax,
                    'val_s': True,                    
                    })

        return True

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        print str(vals)

        per = 'period_id' in vals	 and vals['period_id'] or False

        if not 'expedicion_id' in vals:

            line = vals['invoice_line'][0]
            exp = str(line).split("'expedicion_id': (")
            if len(exp)>1:
                vals['expedicion_id'] = exp[1].split(',')[0]

            exp = str(line).split("'nescala': u'")
            if len(exp)>1:
                vals['nescala'] = exp[1].split("'")[0]

            exp = str(line).split("'afecta': u'")
            if len(exp)>1:
                vals['afecta'] = exp[1].split("'")[0]

        if 'date_invoice' in vals and len(str(vals['date_invoice']))>6:
            
            fsplit = str(vals['date_invoice']).split('-')

            vals['fechainf'] = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

        vals['validar'] = True

        #estructura decimales
        total = 'amount_total' in vals and self.estruct_dig(cr, uid, str(vals['amount_total'])) or False
        total_untaxed = 'inv.amount_untaxed' in vals and self.estruct_dig(cr, uid, str(vals['inv.amount_untaxed'])) or False
        total_tax ='inv.amount_tax' in vals and self.estruct_dig(cr, uid, str(['inv.amount_tax'])) or False

        vals['samount_total']=total,
        vals['samount_untaxed']=total_untaxed,
        vals['samount_tax']=total_tax,
        vals['val_s']= True,                    
                    

        res = super(account_invoice, self).create(cr, uid, vals, context=context)

        inv = self.browse(cr, uid, res)

        cont_ob = self.pool.get('expedicion.contabilidad')
        
        cont_s = cont_ob.browse(cr, uid, cont_ob.search(cr, uid, []))

        if len(cont_s)<1:
            raise osv.except_osv(_('Error'), _('Debes configurar la contabilidad en el menu de configuración de expediciones antes de realizar facturas'))
        cont = cont_s[0]

        if not inv.nescala and not inv.expedicion_id:
            raise osv.except_osv(_('Error'), _('Debe seleccionar una expedición'))    

        if inv.date_invoice:

            facs = self.search(cr, uid, [('period_id','=',inv.period_id.id),('type','=',inv.type),('date_invoice','>',inv.date_invoice)])

            if len(facs)>0:
				raise osv.except_osv(_('Error'), _('La factura que esta intentando crear tiene una fecha inferior a la ultima creada '))    
             
            if inv.period_id.date_start > inv.date_invoice or inv.period_id.date_stop < inv.date_invoice:
				raise osv.except_osv(_('Error'), _('La fecha de la factura no corresponde con el periodo'))    

           
           
        if inv.expedicion_id.cerrada != 'No':
                raise osv.except_osv(_('Error'), _('No se puede asignar una factura a una expedicion cerrada'))


        for line in inv.invoice_line:
            ffactura = inv.date_invoice
            fsplit = str(inv.date_invoice).split('-')
            if len(fsplit)>1:
                    ffactura = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]
            line.write( {'nfactura':str(inv.number),'ffactura':ffactura})
            if ( (not line.expedicion_id) and (not line.expedicion_id_aux) and (not line.nescala) )  and not line.noexp:
               line.write( {'expedicion_id':inv.expedicion_id.id,'expedicion_id_aux':inv.expedicion_id.id, 'nescala': str(inv.nescala)})
            if not line.afecta :
               line.write( {'afecta':inv.afecta, 'estado': str(inv.state)})
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        #FIX bug PXGO 15/05/2014
        if 'state' in vals and vals['state'] == 'paid':
            return super (account_invoice, self).write(cr, uid, ids, vals, context=context)

        inv = self.browse(cr, uid, ids[0])

        if 'date_invoice' in vals:
            
            fsplit = str(vals['date_invoice']).split('-')

            vals['fechainf'] = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]
            
       
            for lin in inv.invoice_line:
                lin.write({'ffactura':vals['fechainf']})


        if 'state' in vals and vals['state'] == 'cancel':
            vals['expedicion_alm'] = inv.expedicion_id.id

        res = super(account_invoice, self).write(cr, uid, ids, vals,  context=context)

        inv = self.browse(cr, uid, ids)[0]
        
        cont_ob = self.pool.get('expedicion.contabilidad')
        
        cont = cont_ob.browse(cr, uid, cont_ob.search(cr, uid, [])[0])

        idc = ids[0]
        
        buscar = True
        while buscar and idc > 0:        
             
            idc = idc - 1
            if  len(self.search(cr, uid, [('id','=',idc)]) )>0:                 
                invs =  self.pool.get('account.invoice').browse(cr, uid, idc)
                if  invs.date_invoice:
                    buscar = False
        if idc > 0:
            dmin = invs.date_invoice    
        else:
            dmin = False

        cont = 0
        idc = ids[0]
        buscar = True
        while buscar:
            idc = idc + 1
            if  len(self.search(cr, uid, [('id','=',idc)]) )>0:  
              invs =  self.browse(cr, uid, idc)
              if invs.date_invoice:
                buscar = False
              else:                
                cont = cont + 1
                if cont > 10:                    
                  buscar = False
            else:                
                cont = cont + 1
                if cont > 10:                    
                  buscar = False
        if cont <= 10:
            dmax = invs.date_invoice
        else:
            dmax = datetime.now().strftime('%Y-%m-%d')   
  
        ffactura = str(inv.date_invoice)             
   
        

        for line in inv.invoice_line:
                fsplit = str(inv.date_invoice).split('-')
                if len(fsplit)>1:
                    ffactura = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

                values = {}

                values['nfactura'] = str(inv.number)
                values['ffactura'] = ffactura
                values['fecha_factura'] = inv.date_invoice

                if ('state' in vals and (vals['state'] == 'cancel' or vals['state'] == 'draft')) or ('estado' in vals and (vals['estado'] == 'cancel')):
                   
                        values['estado'] = str(inv.state)
                        vals['val_s'] = True
                else:
                    values['estado'] = str(inv.state)
                    if (not line.expedicion_id and not line.noexp and not line.expedicion_id_aux) or (  (not 'expedicion_id_aux' in vals) and (not 'expedicion_id' in vals)  and (line.expedicion_id and line.expedicion_id_aux.id == inv.expedicion_alm.id  )):
                        values['expedicion_id'] = inv.expedicion_id.id  
                        values['expedicion_id_aux'] = inv.expedicion_id.id  
                        values['nescala'] =  str(inv.nescala)
                        values['afecta'] = inv.afecta
                        if inv.expedicion_id.cerrada != 'No':
                                    raise osv.except_osv(_('Error'), _('No se puede asignar una factura a una expedicion cerrada'))

                    else:
                        if  line.expedicion_id_aux:
                                values['expedicion_id'] = line.expedicion_id_aux.id                  
                    #if not line.afecta :
                         #values['afecta'] = inv.afecta  
            
                         
            
                
                line.write(values)

        if not 'val_s' in vals:
            self.estructurar(cr, uid, ids)

        return res


    def sobreescribir_exp(self, cr, uid, ids, context = None):
        
        inv = self.browse(cr, uid, ids)[0]
        for line in inv.invoice_line:
                line.write( {'expedicion_id_aux':inv.expedicion_id.id,'expedicion_id':inv.expedicion_id.id,  'afecta': str(inv.afecta), 'nescala': str(inv.nescala)})

        return True

account_invoice()


class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'


    def ch_ex_aux(self, cr, uid, ids, ex,  context = None):

        if not ex:
            v = {'expedidicion_id': False,'marcada':False}
            return {'value': v}
        v = {'expedidicion_id': ex}

       
	
        if exp.cerrada != 'No':
                raise osv.except_osv(_('Error'), _('No se puede asignar una factura a una expedicion cerrada'))

        return {'value': v}

    def ch_ex(self, cr, uid, ids, ex, state, context = None):

        if not ex:
            v = {'nescala': False}

            return {'value': v}

        ex_obj = self.pool.get('expediciones.expediciones')
        exp = ex_obj.browse(cr, uid, ex)
        if exp.cerrada != 'No':
                raise osv.except_osv(_('Error'), _('No se puede asignar una factura a una expedicion cerrada'))
        v = {'nescala': exp.escala,'expedidicion_id': ex}

        return {'value': v}

    def ch_es(self, cr, uid, ids, es, context = None):

        if not es:
            v = {'expedicion_id': False}
            return {'value': v}

        ex_obj = self.pool.get('expediciones.expediciones')

        ex_s = ex_obj.search(cr, uid, [('escala','=',es)])

        exp = ex_obj.browse(cr, uid, ex)
        if exp.cerrada != 'No':
                raise osv.except_osv(_('Error'), _('No se puede asignar una factura a una expedición cerrada'))



        if len(ex_s) < 1:
            raise osv.except_osv(_('Error'), _('No hay ninguna expedición con ese numero de escala'))

        v = {'expedicion_id': ex_s[0],'expedicion_id_aux':ex_s[0]}

        return {'value': v}

    def write(self, cr, uid, ids, vals, context=None):
        ex_obj = self.pool.get('expediciones.expediciones')
        if context is None:
            context = {}
        #text = self.pool.get('account.invoice').estruct_dig(cr, uid, str(vals['price_subtotal']))
       # raise osv.except_osv(_('Aviso'),_(text))

        if 'emitido' in vals and vals['emitido'] != 0:
            vals['sprice_subtotal']  = self.pool.get('account.invoice').estruct_dig(cr, uid, str(vals['emitido']))
        else:
            if 'recibido' in vals and vals['recibido'] != 0:
                 vals['sprice_subtotal'] = self.pool.get('account.invoice').estruct_dig(cr, uid, str(vals['recibido']))    

        lin = self.browse(cr, uid, ids)[0]

        id_exp = lin.expedicion_id.id
        res = super(account_invoice_line,self).write(cr, uid, ids, vals, context=context)

        lin = self.browse(cr, uid, ids)[0]        

     #   if ('expedicion_id' in vals) and (str(vals['expedicion_id']) !='False') and ( ( not 'afecta' in vals) and (not lin.afecta)) :
      #      raise osv.except_osv(_('Aviso'),_('Tienes que rellenar el campo Afecta en todas las lineas con expediciÃ³n\n\n (Se asigna automÃ¡ticamente la expediciÃ³n de la factura a todas las lineas)'))

        if 'emitido' not in vals and 'recibido' not in vals:
            if (lin.invoice_id.type == 'out_invoice' or lin.invoice_id.type == 'in_refund') :
                lin.write({'emitido':lin.price_subtotal, 'nfactura':lin.invoice_id.number, 'recibido':0})
            else:
                lin.write({'recibido':lin.price_subtotal, 'nfactura':lin.invoice_id.number, 'emitido':0})


        if lin.expedicion_id : 
            lin.expedicion_id.recalcular()      
        else:   
            if 'expedicion_id' in vals and vals['expedicion_id'] == False and id_exp:
                ex_obj.recalcular(cr, uid, id_exp )

 
        return res

    def sacar_factura(self, cr, uid, ids, context=None):  
        
         
         cr.execute("select id from ir_ui_view where name='account.invoice.form'")
        
         view_id = cr.fetchall()[0]
         
         inv_id = self.browse(cr, uid, ids[0]).invoice_id.id

         value = {
                'name': 'Factura',
                'view_type': 'form',
                'res_model': 'account.invoice',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'res_id': inv_id,
                'nodestroy':True,
                }
         return value
        



    def create(self, cr, uid, vals, context=None):

        if context is None:
            context = {}

        if 'emitido' in vals:
            vals['sprice_subtotal']  = self.pool.get('account.invoice').estruct_dig(cr, uid, str(vals['emitido']))
        else:
            if 'recibido' in vals:
                 vals['sprice_subtotal'] = self.pool.get('account.invoice').estruct_dig(cr, uid, str(vals['recibido']))    


        if 'expedicion_id' in vals and type(vals['expedicion_id']) == tuple:
            vals['expedicion_id'] = vals['expedicion_id'][0]
            vals['expedicion_id_aux'] = vals['expedicion_id']   
        res = super(account_invoice_line,self).create(cr, uid, vals, context=context)
        lin = self.browse(cr, uid, res)
        
        if ('expedicion_id' in vals) and (str(vals['expedicion_id']) !='False')  and (not 'afecta' in vals) :
            raise osv.except_osv(_('Aviso'),_('Tienes que rellenar el campo Afecta en todas las lineas con expedición\n\n (Se asigna automáticamente la expedición de la factura a todas las lineas)'))

       

        if lin.expedicion_id:
            lin.expedicion_id.recalcular()        

        if lin.invoice_id.type == 'out_invoice' or lin.invoice_id.type == 'in_refund':
            lin.write({'emitido':lin.price_subtotal, 'nfactura':lin.invoice_id.number})
        else:
            lin.write({'recibido':lin.price_subtotal, 'nfactura':lin.invoice_id.number})
        return res



    _columns = {

                    'expedicion_id':fields.many2one('expediciones.expediciones','Expedición'),
                    'expedicion_id_aux':fields.many2one('expediciones.expediciones','Expedición'),

                    'nescala':fields.char('Nº de escala', size=256),


                    'pagado': fields.selection([('no', 'No'),
                                    ('si', 'Sí­'),
                                    ],'Pagado'),

                    'afecta': fields.selection([                                 
                                    ('no', 'No'),
                                    ('mercancias', 'Mercancias'),
                                    ('buques', 'Buques'),
                                    ],'Afecta'),

                    'emitido':fields.float('Emitido'),
                    
                    'recibido':fields.float('Recibido'),

                    'nfactura':fields.char('Numero de factura', size= 256),
                    'ffactura':fields.char('F. factura', size= 256),

                    'fecha_factura':fields.date('Fecha de factura(date)'),

                    'noexp':fields.boolean('No añadir expedición', size= 256),
                    
                    'estado':fields.char('Estado',size = 256),

                    'sprice_subtotal':fields.char('Total', size=256),
                
                    'informee_id':fields.many2one('expediciones.informefil','Informe'),
              
                    'marcada': fields.boolean('Marcada'),   

                }

    #_order = 'fecha_factura desc'

account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

