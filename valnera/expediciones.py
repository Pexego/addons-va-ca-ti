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

from datetime import datetime, timedelta
from osv import fields, osv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools.translate import _
import decimal_precision as dp

class account_move(osv.osv):

    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):

        if context is None:
            context = {}

        if type(ids) != list:
            ids[0] = ids

        gastos = self.pool.get('gastos.gastos')
     
        gs = gastos.search(cr, uid,[('asiento_contable','=',ids[0])])
        if len(gs) > 0:
                gastos.write(cr, uid, gs, {'asentado':True})

        res = super(account_move,self).post(cr, uid, ids, context)

        return res

account_move()

class gastos_gastos(osv.osv):
    _name= 'gastos.gastos'


    def unlink(self, cr, uid, ids, context={}):

        exp = self.browse(cr, uid, ids[0])

        if exp.asiento_contable:
            raise osv.except_osv(_('Aviso'),_('No se puede eliminar gastos/recuperaciones con un asiento contable referenciado'))   

        res = super(gastos_gastos,self).unlink(cr, uid, ids, context=context)
       

        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}



        if type(ids) == list:
            ids = ids[0]   

        gasto = self.browse(cr, uid, ids)

        fsplit = str(gasto.fecha).split('-')
        if len(fsplit)>1:
            vals['ffecha'] = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]
                    
        qty =  gasto.qty               
        if 'qty' in vals:
            qty = vals['qty']

        estado =  gasto.estado               
        if 'estado' in vals:
            estado = vals['estado']

        if estado == 'recibido':
            vals['recibido'] = qty
            vals['emitido'] = 0
        else:
            vals['emitido'] = qty
            vals['recibido'] = 0

        res = super(gastos_gastos,self).write(cr, uid, ids, vals, context=context)

        if type(ids) == list:
            ids = ids[0]

        

        exp_s = self.pool.get('expediciones.expediciones')
        cli = self.pool.get('res.partner')

        if not 'ana_line' in vals and not ( ( 'recibido' in vals) or ( 'emitido' in vals)):
            raise osv.except_osv(_('Aviso'),_('No se puede modificar una entrada de contabilidad'))      
            exp = exp_s.browse(cr, uid, gasto.expedicion_id.id)
     
            if len(self.pool.get('expedicion.contabilidad').search(cr, uid, [])) <1:   
                raise osv.except_osv(_('Error'),_('Tienes que configurar la contabilidad antes de poder asignar costes)'))               
            
            analytic_line = self.pool.get('account.analytic.line')
            conta = self.pool.get('expedicion.contabilidad').browse(cr, uid,self.pool.get('expedicion.contabilidad').search(cr, uid, []) )[0]
            print 'apsa '+str(gasto.cliente)
            values = {
                        'name':gasto.name,
                        'amount':gasto.qty,
                        'account_id':conta.name.id,
                        'general_account_id':gasto.cliente.property_account_receivable.id,
                        'date':datetime.now(),
                        'journal_id':conta.diario.id,
                      }

            line_id = analytic_line.write(cr, gasto.ana_line.id, uid, values)

  

        if gasto.expedicion_id:
            gasto.expedicion_id.recalcular()      

        return res 

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        exp_s = self.pool.get('expediciones.expediciones')
        cli = self.pool.get('res.partner')

        exp = exp_s.browse(cr, uid, vals['expedicion_id'])
        if not 'cliente' in vals or not vals['cliente'] :
            vals['cliente'] = exp.cliente_id.id
            print 'exp.cliente_id.id   '+str(exp.cliente_id.id)

        vals['recibido'] = 0
        vals['emitido'] = 0

        if vals['estado'] == 'recibido':
            vals['recibido'] = vals['qty']
        else:
            vals['emitido'] = vals['qty']

        res = super(gastos_gastos,self).create(cr, uid, vals, context=context)
        
        

        if len(self.pool.get('expedicion.contabilidad').search(cr, uid, [])) <1:
                    raise osv.except_osv(_('Aviso'),_('Tienes que configurar contabilidad antes de poder asignar costes)'))        


        cl = cli.browse(cr, uid, vals['cliente'])

#Conta analitica

        analytic_line = self.pool.get('account.analytic.line')
        conta = self.pool.get('expedicion.contabilidad').browse(cr, uid,self.pool.get('expedicion.contabilidad').search(cr, uid, []) )[0]

        if vals['estado'] == 'recibido':
            vals['qty'] = vals['qty'] * (-1)

        cuenta = conta.cuentam

        if vals['categ'] == 'buque':
            cuenta = conta.cuentab
          
        if vals['estado'] == 'emitido':
            cuenta = conta.cuentamr
            if vals['categ'] == 'buque':
                cuenta = conta.cuentabr

        values = {
                    'name':vals['name'],
                    'amount':vals['qty'],
                    'account_id':conta.name.id,
                    'general_account_id':cuenta.id,
                    'date':datetime.now(),
                    'journal_id':conta.diario.id,
                  }

        line_id = analytic_line.create(cr, uid, values)

        gasto = self.browse(cr, uid, res)

#Conta financiera

        mvl = self.pool.get('account.move.line')
        mv = self.pool.get('account.move')

        per = self.pool.get('account.period')

        mv_id = False
        asentado = True

        fsplit = str(vals['fecha']).split('-')
        if len(fsplit)>1:
                    ffactura = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]
                    vals['ffecha'] = ffactura

        if gasto.asiento_contableb:

            if vals['emitido'] < 0:
                vals['recibido'] = vals['emitido'] * (-1) 
                vals['emitido'] = 0

            if vals['recibido'] < 0:
                vals['emitido'] = vals['recibido'] * (-1) 
                vals['recibido'] = 0

            asentado = False
            per = per.search(cr, uid,[('date_start','<=',vals['fecha']),('date_stop','>=',vals['fecha']),('state','=','draft')])

            if len(per)<1:
                  raise osv.except_osv(_('Error !'),
                        _('No hay ningun periodo contable abierto creado para asignar este asiento de expedición en la fecha definida'))

            per = per[0]

            values = {
                        'ref':vals['name'],
                        'period_id': per,
                        'journal_id':conta.diariof.id,
                        'date':vals['fecha'],
                      }

            mv_id = mv.create(cr, uid, values)

            values = {
                        'name':vals['name'],
                        'credit':vals['emitido'],
                        'debit':vals['recibido'],
                        'account_id':cuenta.id,
                        'date':vals['fecha'],
                        'journal_id':conta.diariof.id,
                        'move_id':mv_id,
                        'period_id': per,
                      }

            lin_id = mvl.create(cr, uid, values)

        if gasto.expedicion_id:
            gasto.expedicion_id.recalcular()            

        self.write(cr, uid, res, {'asiento_contable':mv_id, 'asentado':asentado})


        return res 

    _columns = {
                'expedicion_id':fields.many2one('expediciones.expediciones','Expedición'),
                'cliente':fields.many2one('res.partner','Cliente'),
                'name':fields.char('Descripción', size=256),
                'qty':fields.float('Cantidad', size=256),
                'type':fields.selection([('gastos', 'Gastos'),
                                    ('recuperaciones', 'Recuperaciones'),
                                    ],'Tipo'),
                'categ':fields.selection([('buque', 'Buque'),
                                    ('mercancia', 'Mercancia'),
                                    ],'Categoría'),
                'ana_line':fields.many2one('account.analytic.line','Linea Analitica'),

                'estado':fields.selection([('recibido', 'Recibido'),
                                    ('emitido', 'Emitido'),
                                    ],'Estado'),

                'emitido':fields.float('Emitido'),
                    
                'recibido':fields.float('Recibido'),

                'fecha':fields.date('Fecha'),
                'ffecha':fields.char('Fecha', size=256),

                'asiento_contable':fields.many2one('account.move','Asiento contable'),
                'asiento_contableb':fields.boolean('¿Crear asiento?'),
                
                'asentado':fields.boolean('Conciliado'),

                }

    _order = 'fecha desc'

gastos_gastos()



class expediciones_expediciones(osv.osv):
    _name = 'expediciones.expediciones'

    
    def informar(self, cr, uid, ids, context={}):
        if type(ids) == list:
            ids = ids[0]   

        exp = self.browse(cr, uid, ids)

        #Fecha cierre
        fcerr = ' '
        fsplit = str(exp.fcerrada).split('-')
        if len(fsplit)>1:
            fcerr = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

        values = {
                   'nexpedicion':ids,   
                   'op3':True,  
                   'ex3':True,    
                    'refe':exp.refe,
                    'name':exp.name,
                    'escala':exp.escala,
                    'fecha':exp.fecha,
                    'pas':exp.pas,
                    'mercanciass':exp.mercanciass,
                    'kilos':exp.kilos,
                    'cliente_id':exp.cliente_id.id,
                    'origen_id':exp.origen_id.id,
                    'destino_id':exp.destino_id.id,
                    'armador_id':exp.armador_id.id,
                    'fletador_id':exp.fletador_id.id,
                    'est_mercaf':exp.est_mercaf,
                    'est_buquesf':exp.est_buquesf,
                    'resultado_mercaf':exp.resultado_mercaf,
                    'resultado_buquesf':exp.resultado_buquesf,
                    'resultado_expedicionf':exp.resultado_expedicionf,     
                    'cerrada':exp.cerrada,       
                    'fcerrada':fcerr,
                    'texto_sup': 'Presentación de mercancías y buques con líneas no agrupadas'
                    }

        exp_obj = self.pool.get('exp.info')

        exp_id = exp_obj.create(cr, uid, values)
        ids = exp_id

        context.update( {'active_id': ids, 'active_ids': [exp_id], 'id_imp': [exp_id]})
        
        exp_obj.generar_informe(cr, uid, exp_id, context)



        return {
            'name': _('Imprimir informe'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'exp.info',
            'view_id': False,
            'res_id': exp_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        } 
        


    def informarfact(self, cr, uid, ids, context={}):
        if type(ids) == list:
            ids = ids[0]   

        exp = self.browse(cr, uid, ids)

        ex2 = (exp.afecta == 'buque')
        ex1 = (exp.afecta == 'expedicion')
        ex4 = (exp.afecta == 'no')

        presentacion = 'Presentación de mercancías y buques con lineas '
        if ex4 :
            presentacion = 'Presentación de No afecta con lineas '
        if ex2 :
            presentacion = 'Presentación de buques con lineas '
        if ex1 :
            presentacion = 'Presentación de mercancías con lineas '

        if exp.agrupar :
            presentacion = presentacion + 'agrupadas'
        else:
            presentacion = presentacion + 'no agrupadas'
        
        #Fecha cierre
        fcerr = ' '
        fsplit = str(exp.fcerrada).split('-')
        if len(fsplit)>1:
            fcerr = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]           
    
        values = {
                   'nexpedicion':ids,   
                   'op3':True,  
                   'ex1':ex1,
                   'ex2':ex2,
                   'ex4':ex4,    
                    'refe':exp.refe,
                    'name':exp.name,
                    'escala':exp.escala,
                    'fecha':exp.fecha,
                    'pas':exp.pas,
                    'mercanciass':exp.mercanciass,
                    'kilos':exp.kilos,
                    'cliente_id':exp.cliente_id.id,
                    'origen_id':exp.origen_id.id,
                    'destino_id':exp.destino_id.id,
                    'armador_id':exp.armador_id.id,
                    'fletador_id':exp.fletador_id.id,
                    'est_mercaf':exp.est_mercaf,
                    'est_buquesf':exp.est_buquesf,
                    'resultado_mercaf':exp.resultado_mercaf,
                    'resultado_buquesf':exp.resultado_buquesf,
                    'resultado_expedicionf':exp.resultado_expedicionf,     
                    'cerrada':exp.cerrada,       
                    'fcerrada':fcerr,
                    'texto_sup': presentacion,
                    'agrupar':exp.agrupar,
                    }

        exp_obj = self.pool.get('exp.info')

        exp_id = exp_obj.create(cr, uid, values)
        ids = exp_id

        context.update( {'active_id': ids, 'active_ids': [exp_id], 'id_imp': [exp_id]})
        
        exp_obj.generar_informe(cr, uid, exp_id, context)


        return {
            'name': _('Imprimir informe'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'exp.info',
            'view_id': False,
            'res_id': exp_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        } 
        

        

    def unlink(self, cr, uid, ids, context={}):

        exp = self.browse(cr, uid, ids[0])        
        invo = self.pool.get('account.invoice.line')
        gast = self.pool.get('gastos.gastos')

        invo_val = invo.search(cr, uid, [('expedicion_id','=',exp.id)])
        if len(invo_val) > 0:
            raise osv.except_osv(_('Aviso'),_('Tienes que desvincular las facturas de la expedición antes de poder borrarla'))        

        gast_val = gast.search(cr, uid, [('expedicion_id','=',exp.id)])
        if len(gast_val) > 0:
            raise osv.except_osv(_('Aviso'),_('Tienes que desvincular los gastos/recuperaciones de la expedición antes de poder borrarla'))      

        if exp.state == 'cerrada':
            raise osv.except_osv(_('Aviso'),_('No se puede eliminar una expedicion cerrada'))      

        res = super(expediciones_expediciones,self).unlink(cr, uid, ids, context=context)
       

        return res

    def recalcular(self, cr, uid, ids, context = None):
        if type(ids) == list:
            ids = ids[0] 

        
  
        factt = self.pool.get('account.invoice')
        exp = self.browse(cr, uid, ids)
    
        tot_merc = 0
        tot_buq  = 0
        tot_exp  = 0
 
        tot_merc_f = 0
        tot_merc_fe = 0
        tot_merc_fr = 0
        tot_buq_f = 0
        tot_buq_fe = 0
        tot_buq_fr = 0

        tot_merc_g = 0
        tot_merc_ge = 0
        tot_merc_gr = 0
        tot_buq_g = 0
        tot_buq_ge = 0
        tot_buq_gr = 0

        tot_fact_emi = 0
        tot_fact_reci = 0

        tot_no = 0
        tot_no_fe = 0
        tot_no_fr = 0

        for fact in exp.facturas_line:
            if fact.afecta == 'mercancias':
                tot_merc = tot_merc +  fact.emitido
                tot_merc = tot_merc -  fact.recibido
                tot_merc_fe = tot_merc_fe + fact.emitido
                tot_merc_fr = tot_merc_fr + fact.recibido
                tot_fact_emi =   tot_fact_emi + fact.emitido
                tot_fact_reci =   tot_fact_reci + fact.recibido
            if fact.afecta == 'buques':
                tot_buq = tot_buq + fact.emitido
                tot_buq = tot_buq - fact.recibido
                tot_buq_fe = tot_buq_fe + fact.emitido
                tot_buq_fr = tot_buq_fr + fact.recibido
                tot_fact_emi =   tot_fact_emi + fact.emitido
                tot_fact_reci =   tot_fact_reci + fact.recibido
            if fact.afecta == 'no':
                tot_no = tot_no + fact.emitido
                tot_no = tot_no - fact.recibido
                tot_no_fe = tot_no_fe + fact.emitido
                tot_no_fr = tot_no_fr + fact.recibido
                tot_fact_emi =   tot_fact_emi + fact.emitido
                tot_fact_reci =   tot_fact_reci + fact.recibido

        tot_merc_f = tot_merc
        tot_buq_f = tot_buq


        res_fact =  tot_merc_f + tot_buq_f

        tot_gast = 0
        tot_gast_reci = 0
        tot_gast_emi = 0

        tot_gast_merca = 0
        tot_gast_reci_merca = 0
        tot_gast_emi_merca = 0

        tot_gast_buque = 0
        tot_gast_reci_buque = 0
        tot_gast_emi_buque = 0

        tot_gast_no = 0
        tot_gast_reci_no = 0
        tot_gast_emi_no = 0

        for gast in exp.gastos_line:
            if gast.categ == 'buque':
                if gast.estado == 'emitido':
                    tot_gast_emi_buque = tot_gast_emi_buque + gast.qty
                    tot_buq = tot_buq + gast.qty
                    tot_buq_g = tot_buq_g + gast.qty
                    tot_buq_ge = tot_buq_ge + gast.qty
                else:
                    tot_gast_reci_buque = tot_gast_reci_buque + gast.qty
                    tot_buq = tot_buq - gast.qty
                    tot_buq_g = tot_buq_g - gast.qty
                    tot_buq_gr = tot_buq_gr + gast.qty


            if gast.categ == 'mercancia':
                if gast.estado == 'emitido':
                    tot_gast_emi_merca = tot_gast_emi_merca + gast.qty
                    tot_merc = tot_merc +  gast.qty
                    tot_merc_g = tot_merc_g + gast.qty
                    tot_merc_ge = tot_merc_ge + gast.qty
                else:
                    tot_gast_reci_merca = tot_gast_reci_merca + gast.qty
                    tot_merc = tot_merc -  gast.qty
                    tot_merc_g = tot_merc_g - gast.qty
                    tot_merc_gr = tot_merc_gr + gast.qty

            if gast.categ == 'no':
                if gast.estado == 'emitido':
                    tot_gast_emi_no = tot_gast_emi_no + gast.qty
                    tot_merc = tot_merc +  gast.qty
                    tot_merc_g = tot_merc_g + gast.qty
                    tot_merc_ge = tot_merc_ge + gast.qty
                else:
                    tot_gast_reci_no = tot_gast_reci_no + gast.qty
                    tot_merc = tot_merc -  gast.qty
                    tot_merc_g = tot_merc_g - gast.qty
                    tot_merc_gr = tot_merc_gr + gast.qty
    
        tot_gast_merca = tot_gast_emi_merca - tot_gast_reci_merca
        tot_gast_buque = tot_gast_emi_buque - tot_gast_reci_buque
        tot_gast_no = tot_gast_emi_buque - tot_gast_reci_no
                
        tot_gast_emi = tot_gast_emi_merca + tot_gast_emi_buque +tot_gast_emi_no 
        tot_gast_reci = tot_gast_reci_merca + tot_gast_reci_buque +tot_gast_reci_no 

        tot_gast = tot_gast_emi -tot_gast_reci

        values = {      'resultado_mercaf': tot_merc or 0,
                        'resultado_buquesf': tot_buq or 0,

                        'resultado_mercafc': factt.estruct_dig(cr, uid, str(tot_fact_emi))+ str('€') or '0,0€', #total emitido fact facturas
                        'resultado_buquesfc': factt.estruct_dig(cr, uid, str(tot_fact_reci))+ str('€') or '0,0€',#total reci  facturas
                        'tot_buq_f': factt.estruct_dig(cr, uid, str(tot_fact_emi - tot_fact_reci))+ str('€') or '0,0€',#total  facturas





                        'resultado_mercaff': factt.estruct_dig(cr, uid, str(tot_merc_f))+ str('€') or '0,0€',#total merca facturas
                        'resultado_buquesff': factt.estruct_dig(cr, uid, str(tot_buq_f))+ str('€') or '0,0€',#total buques facturas

                        'resultado_mercafr': factt.estruct_dig(cr, uid, str(tot_merc_fr))+ str('€') or '0,0€',#recibido merca fact   recibidos
                        'resultado_buquesfr': factt.estruct_dig(cr, uid, str(tot_buq_fr))+ str('€') or '0,0€',#recibido buques fact   recibidos
                        'resultado_mercafe': factt.estruct_dig(cr, uid, str(tot_merc_fe))+ str('€') or '0,0€',#emitido merca fact   emitido
                        'resultado_buquesfe': factt.estruct_dig(cr, uid, str(tot_buq_fe))+ str('€') or '0,0€',#emitido buques fact   emitido

                        'resultado_expedicionf': (tot_buq or 0) + (tot_merc or 0) or 0,


                        'tot_fact_no':factt.estruct_dig(cr, uid, str(tot_no))+ str('€') or '0,0€',
                        'tot_fact_no_emi':factt.estruct_dig(cr, uid, str(tot_no_fe))+ str('€') or '0,0€',
                        'tot_fact_no_reci':factt.estruct_dig(cr, uid, str(tot_no_fr))+ str('€') or '0,0€',

              #####   GASTOS

                        'tot_gast': factt.estruct_dig(cr, uid, str(tot_gast_reci))+ str('€') or '0,0€',#total gastos   recibidos
                        'tot_gast_emi': factt.estruct_dig(cr, uid, str(tot_gast_emi))+ str('€') or '0,0€',#total gastos   emitido
                        'tot_gast_reci': factt.estruct_dig(cr, uid, str(tot_gast))+ str('€') or '0,0€',#total  gastos

                        'tot_gast_reci_merca': factt.estruct_dig(cr, uid, str(tot_gast_reci_merca))+ str('€') or '0,0€',#total merca gastos   recibidos
                        'tot_gast_emi_merca': factt.estruct_dig(cr, uid, str(tot_gast_emi_merca))+ str('€') or '0,0€',#total merca gastos   emitido
                        'tot_gast_merca': factt.estruct_dig(cr, uid, str(tot_gast_emi_merca - tot_gast_reci_merca))+ str('€') or '0,0€',#total merca gastos

                        'tot_gast_reci_buque': factt.estruct_dig(cr, uid, str(tot_gast_reci_buque))+ str('€') or '0,0€',#total buques gastos   recibidos
                        'tot_gast_emi_buque': factt.estruct_dig(cr, uid, str(tot_gast_emi_buque))+ str('€') or '0,0€',#total buques gastos   emitido
                        'tot_gast_buque': factt.estruct_dig(cr, uid, str(tot_gast_emi_buque - tot_gast_reci_buque))+ str('€') or '0,0€',#total buques gastos


                        'tot_gast_no':factt.estruct_dig(cr, uid, str(tot_no))+ str('€') or '0,0€',
                        'tot_gast_emi_no':factt.estruct_dig(cr, uid, str(tot_no_fe))+ str('€') or '0,0€',
                        'tot_gast_reci_no':factt.estruct_dig(cr, uid, str(tot_no_fr))+ str('€') or '0,0€',

                    }

        exp.write(values)

        return True

    def cerrar(self, cr, uid, ids, context = None):        
        exp = self.browse(cr, uid, ids[0])

        '''for exp in self.browse(cr, uid,self.search(cr, uid, [])):
            exp.recalcular()
        
        line_obj = self.pool.get('account.invoice.line')

        for line in line_obj.browse(cr, uid, line_obj.search(cr, uid,[('afecta','=',False)])):
            line.write( {'afecta':'no'})'''

         #tx = self.pool.get('account.invoice.tax')
         #acc = self.pool.get('account.invoice')
         #lin = self.pool.get('account.invoice.line')
 
         #for tax in tx.browse(cr, uid, tx.search(cr, uid,[]) ):
 
         #    values = {
         #         #      'samount':acc.estruct_dig(cr, uid, str(tax.amount)),
         #         #      'sbase':acc.estruct_dig(cr, uid, str(tax.base)),
         #         #       }

         #    tax.write(values)

         #for line in lin.browse(cr, uid, lin.search(cr, uid,[]) ):

         #    values = {         #         #  
         #         #      'estado': str(line.invoice_id.state),
         #         #       }

         #    line.write(values)

         #for inv in acc.browse(cr, uid, acc.search(cr, uid,[]) ):

         #    values = {         #         #  
         #         #      'estado': acc.estructurar(cr, uid, [inv.id]),
         #         #       }

         #    inv.write(values)
      #-----------------------------------------------------------------------------------------------------------------------------

        if not exp.fcerrada:        
                    raise osv.except_osv(_('Aviso'),_('Tienes que rellenar la fecha de cierre antes de poder cerrarla'))       

        self.write(cr, uid, ids, {'cerrada':'Sí', 'state':'cerrada'})    
      #-----------------------------------------------------------------------------------------------------------------------------       
        '''models = self.pool.get('ir.model')
        models_acc = self.pool.get('ir.model.access')

        for mod in models.search(cr, uid,[]):

            values= {
                        'name':str('valnera_permiso'+str(mod)),
                        'group_id':23,
                        'model_id':mod,
                        'perm_create':True,
                        'perm_unlink':True,
                        'perm_read':True,
                        'perm_write':True,
                    }
            models_acc.create(cr, uid, values)'''
      #-----------------------------------------------------------------------------------------------------------------------------

        return True

    def abrir(self, cr, uid, ids, context = None):

        self.write(cr, uid, ids, {'cerrada':'No', 'fcerrada':False, 'state':'abierta'})        

        return True

    def ch_opg(self, cr, uid, ids,  op2, context= None):
                val = 0
                if op2 == 'todos':
                    val = 1
                if op2 == 'buque':
                    val = 2
                if op2 == 'expedicion':
                    val = 3
                if op2 == 'no':
                    val = 4
                vals = {}
                vals['opg'] = val
                return {'value': vals}

    def ch_op(self, cr, uid, ids, op1, op2, context= None):
           val = 0
           if op1 :
                if op2 == 'todos':
                    val = 4
                if op2 == 'buque':
                    val = 5
                if op2 == 'expedicion':
                    val = 6 
                if op2 == 'no':
                    val = 8           
           else :
                if op2 == 'todos':
                    val = 1
                if op2 == 'buque':
                    val = 2
                if op2 == 'expedicion':
                    val = 3
                if op2 == 'no':
                    val = 7
           vals = {}
           vals['op'] = val
           return {'value': vals}

    _columns = {
                    'ref':fields.many2one('expediciones.referencia','Referencia'),
                    'refe':fields.char('Referencia', size=256),
                    'name':fields.char('Nº expedicion', size=256),
                    'escala':fields.char('Nº de escala', size=256),
                    'fecha':fields.date('Fecha'),
                    'pas':fields.char('PAS', size=256),
                    'mercancias':fields.many2one('product.product','Mercancia'),
                    'mercanciass':fields.char('Mercancia',size=512),
                    'kilos':fields.char('Kilos',size=512),
                    'id_mercancias':fields.one2many('expediciones.mercancia','expedicion_id', 'Mercancias'),
                    'cliente_id':fields.many2one('res.partner', 'Cliente'),
                    'origen_id':fields.many2one('expediciones.puerto', 'Origen'),
                    'destino_id':fields.many2one('expediciones.puerto', 'Destino'),
                    'toperacion_id':fields.many2one('expediciones.toperacion', 'Tipo de operación'),
                    'tdesplazamiento_id':fields.many2one('expediciones.tdesplazamiento', 'Tipo de desplazamiento'),
                    'armador_id':fields.many2one('res.partner', 'Armador'),
                    'fletador_id':fields.many2one('res.partner', 'Fletador'),
                    'est_mercaf':fields.float('Estimación de mercancías',   digits_compute= dp.get_precision('Sale Price')),
                    'est_buquesf':fields.float('Estimación de Buques',  digits_compute= dp.get_precision('Sale Price')),
                    'resultado_mercaf':fields.float('Resultado de la expedición', digits_compute= dp.get_precision('Sale Price')),
                    'resultado_buquesf':fields.float('Resultado del buque', digits_compute= dp.get_precision('Sale Price')),
                    'resultado_expedicionf':fields.float('Resultado agregado', digits_compute= dp.get_precision('Sale Price')),
                
                ###########FACTURAS

                    'facturas':fields.one2many('account.invoice','expedicion_id', 'Facturas'),
                    'facturas_line':fields.one2many('account.invoice.line','expedicion_id', 'Facturas'),
                    'facturas_line2':fields.one2many('account.invoice.line','expedicion_id', 'Facturas', domain=[('afecta','=','buques')]),
                    'facturas_line3':fields.one2many('account.invoice.line','expedicion_id', 'Facturas', domain=[('afecta','=','mercancias')]),
                    'facturas_line4':fields.one2many('account.invoice.line','expedicion_id', 'Facturas'),
                    'facturas_line5':fields.one2many('account.invoice.line','expedicion_id', 'Facturas', domain=[('afecta','=','buques')]),
                    'facturas_line6':fields.one2many('account.invoice.line','expedicion_id', 'Facturas', domain=[('afecta','=','mercancias')]),
                    'facturas_line7':fields.one2many('account.invoice.line','expedicion_id', 'Facturas', domain=[('afecta','=','no')]),
                    'facturas_line8':fields.one2many('account.invoice.line','expedicion_id', 'Facturas', domain=[('afecta','=','no')]),
                   
                    'state': fields.selection([('abierta', 'Abierta'),
                                    ('cerrada', 'Cerrada'),
                                    ],'Estado'),

                    'afecta': fields.selection([                                 
                                    ('todos', 'Todos'),
                                    ('expedicion', 'Expedicion'),
                                    ('buque', 'Buque'),
                                    ('no', 'No afecta'),
                                    ],'Afecta'),



                    'op': fields.integer('Opcion de informe'),

                    'agrupar':fields.boolean('Agrupar líneas'),

                ##########GASTOS
                    'gastos_line':fields.one2many('gastos.gastos','expedicion_id', 'Gastos'),
                    'gastos_line2':fields.one2many('gastos.gastos','expedicion_id', 'Gastos', domain=[('categ','=','buque')]),
                    'gastos_line3':fields.one2many('gastos.gastos','expedicion_id', 'Gastos', domain=[('categ','=','mercancia')]),
                    'gastos_line4':fields.one2many('gastos.gastos','expedicion_id', 'Gastos', domain=[('categ','=','no')]),

                    'stateg': fields.selection([('abierta', 'Abierta'),
                                    ('cerrada', 'Cerrada'),
                                    ],'Estado'),

                    'afectag': fields.selection([                                 
                                    ('todos', 'Todos'),
                                    ('expedicion', 'Expedicion'),
                                    ('buque', 'Buque'),
                                    ],'Afecta'),



                    'opg': fields.integer('Opcion de informe'),

                    #Informe
                    'informe_id':fields.many2one('expediciones.informe','Informe'),
                    'informe2_id':fields.many2one('expediciones.informefil','Informe'),
                    'cerrada':fields.char('Cerrada', size=256),
                    'fcerrada':fields.date('Fecha Cierre', size=256),
            

                        'resultado_mercafr': fields.char('Total Recibido', size=256),
                        'resultado_buquesfr': fields.char('Total Recibido', size=256),
                        'resultado_mercafe': fields.char('Total Emitido', size=256),
                        'resultado_buquesfe': fields.char('Total Emitido', size=256),


                        'resultado_mercaff': fields.char('Total Resultado', size=256),
                        'resultado_buquesff': fields.char('Total Resultado', size=256),
                        'resultado_mercafg': fields.char('Total Emitido', size=256),
                        'resultado_buquesfg': fields.char('Total Emitido', size=256),

                        'resultado_mercafc': fields.char('Total Emitido', size=256), 
                        'resultado_buquesfc': fields.char('Total Recibido', size=256),
                        'tot_buq_f': fields.char('Total Resultado', size=256),


                        'tot_fact_no':fields.char('Total Resultado', size=256),
                        'tot_fact_no_emi':fields.char('Total Emitido', size=256),
                        'tot_fact_no_reci':fields.char('Total Recibido', size=256),

##GASTOS
            
                        
                        'tot_gast':fields.char('Total Resultado', size=256),
                        'tot_gast_emi':fields.char('Total Emitido', size=256),
                        'tot_gast_reci':fields.char('Total Recibido', size=256),

                        'tot_gast_reci_merca':fields.char('Total Recibido', size=256),
                        'tot_gast_emi_merca':fields.char('Total Emitido', size=256),
                        'tot_gast_merca': fields.char('Total Resultado', size=256),

                        'tot_gast_reci_buque': fields.char('Total Recibido', size=256),
                        'tot_gast_emi_buque': fields.char('Total Emitido', size=256),
                        'tot_gast_buque': fields.char('Total Resultado', size=256),


                        'tot_gast_no':fields.char('Total Resultado', size=256),
                        'tot_gast_emi_no':fields.char('Total Emitido', size=256),
                        'tot_gast_reci_no':fields.char('Total Recibido', size=256),


                }


    _order = 'fecha desc'

    _defaults = {
        'cerrada': 'No',
        'state':'abierta',
        'afecta':'todos',
        'op':1,
        'afectag':'todos',
        'opg':1,
                }
expediciones_expediciones()

class expediciones_referencia(osv.osv):
    _name='expediciones.referencia'
    _columns = {
                'name':fields.char('Referencia', size=264),
                }

expediciones_referencia()

class expediciones_mercancia(osv.osv):
    _name='expediciones.mercancia'
    _columns = {
                'name':fields.many2one('product.product','Producto'),
                'cantidad':fields.float('Cantidad'),
                'expedicion_id':fields.many2one('expediciones.expediciones','Expedición')
                }

expediciones_mercancia()

class expediciones_toperacion(osv.osv):
    _name='expediciones.toperacion'
    _columns = {
                'name':fields.char('Tipo de operación', size=256),
                }

expediciones_toperacion()

class expediciones_puerto(osv.osv):
    _name='expediciones.puerto'
    _columns = {
                'name':fields.char('Puerto', size=256),
                }

expediciones_puerto()

class expediciones_tdesplazamiento(osv.osv):
    _name='expediciones.tdesplazamiento'
    _columns = {
                'name':fields.char('Tipo de desplazamiento', size=256),
                }

expediciones_tdesplazamiento()


class expedicion_contabilidad(osv.osv):
    _name= 'expedicion.contabilidad'

    _columns = {
                'name':fields.many2one('account.analytic.account','Cuenta analítica a la que se asignan los gastos de expediciones'),
                'diario':fields.many2one('account.analytic.journal','Diario analítico'),
                'diariof':fields.many2one('account.journal','Diario financiero'),
                'cuentam':fields.many2one('account.account','Cuenta financiera para imputacion de gastos de Mercancias'),
                'cuentab':fields.many2one('account.account','Cuenta financiera para imputación de gastos de Buques'),
                'cuentamr':fields.many2one('account.account','Cuenta financiera para imputacion de recuperación de Mercancias'),
                'cuentabr':fields.many2one('account.account','Cuenta financiera para imputación de recuperación de Buques'),
                #Fecha para controlar que no se creen facturas anteriores a la fecha maxima
                'fmaxs':fields.date('Fecha última factura cliente'),
                'fmaxps':fields.date('Fecha última factura proveedor'),
                }


expedicion_contabilidad()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
