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
import time
import decimal_precision as dp



class exp_info_aux(osv.osv):
    _name = 'exp.info.aux'

    _columns = {
                'informe':fields.many2one('exp.info','Informe'),

                'nexpedicion':fields.char('Nº Exp.', size=256),
                'nescala':fields.char('Nº Escala', size=256),
                'fexpedicion':fields.char('Fecha Exp.', size=256),
                'ffexpedicion':fields.date('Fecha Exp.'),
                'rexpedicion':fields.char('Ref. Exp.', size=256),
                'ffactura':fields.char('Fecha Fact.', size=256),
                'factura':fields.date('Fecha Fact.'),
                'nfactura':fields.char('Nº Factura', size=256),
                'cliente':fields.char('Cliente', size=256),
                'cfactura':fields.char('Concepto Factura', size=256),
                'emitido':fields.char('Emitido', size=256),
                'recibido':fields.char('Recibido', size=256),
                'emitidoc':fields.float('Emitido'),
                'recibidoc':fields.float('Recibido'),
                }

    _order = 'nexpedicion desc,ffexpedicion desc,factura desc, nfactura'

exp_info_aux()


class exp_info(osv.osv):
    _name = 'exp.info'

    def generar_informe(self, cr, uid, ids, context=None):
        expediciones = self.pool.get('expediciones.expediciones')
        
        lines = self.pool.get('account.invoice.line')
        fact = self.pool.get('account.invoice')

        gast = self.pool.get('gastos.gastos')

        inf = self.browse(cr, uid, ids)

        for ex in inf.lineas:
            ex.unlink()

        fact_ids = fact.search(cr, uid, [])
        gast_ids = gast.search(cr, uid, [])       

        escribir = True        
        
        nm = 'Informe de expediciones '        


        
        ########################  FECHAS

        if inf.fecha1 and inf.fecha2:    
            fact_ids = fact.search(cr, uid, [('date_invoice','>=',inf.fecha1),('date_invoice','<=',inf.fecha2),('state','!=','cancel'),('state','!=','draft')] )
            gast_ids = gast.search(cr, uid, [('fecha','>=',inf.fecha1),('fecha','<=',inf.fecha2)] )

            fexp1 = ' '
            fsplit = str(inf.fecha1).split('-')
            if len(fsplit)>1:
                 fexp1 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

            fexp2 = ' '
            fsplit = str(inf.fecha2).split('-')
            if len(fsplit)>1:
                 fexp2 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

            nm = nm + 'entre las fechas '+str(fexp1)+' y '+str(fexp2)
            escribir = True

            


        if inf.mes and inf.anio and inf.mes !=' ' and inf.anio !=' ': 
            escribir = True   
    
            mes =   int(inf.mes) +1
            anio = inf.anio

            if mes == 13:
                mes = 1
                anio= int(anio) +1

            fecha1 = time.strftime(str(inf.anio)+'-'+str(inf.mes)+'-01'),
            fecha2 = time.strftime(str(anio)+'-'+str(int(mes) )+'-01'),

            fact_ids = fact.search(cr, uid, [('date_invoice','>=',fecha1),('date_invoice','<',fecha2),('id','in',fact_ids),('state','!=','cancel'),('state','!=','draft')] )
            gast_ids = gast.search(cr, uid, [('fecha','>=',fecha1),('fecha','<',fecha2),('id','in',gast_ids)] )

            nm = nm + ', del mes '+str(inf.mes)+'-'+str(inf.anio) 

        ########################  CLIENTE

       
        if inf.cliente: 
            escribir = True   
            fact_ids = fact.search(cr, uid, [('partner_id','=',inf.cliente.id),('id','in',fact_ids)] )
            gast_ids = gast.search(cr, uid, [('cliente','=',inf.cliente.id),('id','in',gast_ids)] )
            nm = nm + ', del cliente '+str(inf.cliente.name)


        lines_ids = lines.search(cr, uid, [('invoice_id','in',fact_ids)])

     ########################  Expedicion 

        if inf.nexpedicion:
            lines_ids = lines.search(cr, uid, [('expedicion_id','=',inf.nexpedicion.id),('id','in',lines_ids)] )
            gast_ids = gast.search(cr, uid, [('expedicion_id','=',inf.nexpedicion.id) ,('id','in',gast_ids)] )

        ########################  OPCION

        if inf.op1 or inf.op2 : 
            escribir = True   
            if inf.op1:
                lines_ids = lines.search(cr, uid, [('id','in',lines_ids),('emitido','!=',0)])
                gast_ids = gast.search(cr, uid, [('id','in',gast_ids),('emitido','!=',0)] )
                nm = nm + ', Emitidos '
            else:
                lines_ids = lines.search(cr, uid, [('id','in',lines_ids),('recibido','!=',0)])
                gast_ids = gast.search(cr, uid, [('id','in',gast_ids),('recibido','!=',0)] )
                nm = nm + ', Recibidos '


        ########################  EXPEDICION


        if inf.ex1 or inf.ex2 or inf.ex4 : 
            escribir = True   
            if inf.ex1:
                lines_ids = lines.search(cr, uid, [('id','in',lines_ids),('afecta','=','mercancias')])
                gast_ids = gast.search(cr, uid, [('id','in',gast_ids),('categ','=','mercancia')] )
                nm = nm + ', de Mercancias '

            else:
                if inf.ex2:
                    lines_ids = lines.search(cr, uid, [('id','in',lines_ids),('afecta','=','buques')])
                    gast_ids = gast.search(cr, uid, [('id','in',gast_ids),('categ','=','buque')] )
                    nm = nm + ', de Buques '

                else:
                    lines_ids = lines.search(cr, uid, [('id','in',lines_ids),('afecta','=','no')])
                    gast_ids = gast.search(cr, uid, [('id','in',gast_ids),('categ','=','no')] ) 
                    nm = nm + ', de No afecta '

   
      
            


        ########################  TOTALES

        tot = 0
        totr = 0
        tote = 0

        if escribir:
        
            aux_lines = self.pool.get('exp.info.aux')
            #AGRUPACION
            if inf.agrupar:
                for ex in lines.browse(cr, uid, lines_ids):   
            

                    ex_s = aux_lines.search(cr, uid, [('nfactura','=',ex.nfactura),('informe','=',inf.id)])
                    
                    if len(ex_s)>0:
                        auli = aux_lines.browse(cr, uid, ex_s[0])
                        rec = auli.recibidoc + ex.recibido
                        emi = auli.emitidoc + ex.emitido
                        auli.write({
                             'recibido':fact.estruct_dig(cr, uid, str(rec))+' €' or '0,00€',
                             'recibidoc':rec,
                             'emitido':fact.estruct_dig(cr, uid, str(emi))+' €' or '0,00€',
                             'emitidoc':emi,
                                })
                    else:
                        nesc = str(ex.nescala and ex.nescala or ' ')
                        if nesc == 'False':    
                            nesc = ' '

                        #Fecha expedicion
                        fexp = ' '
                        fsplit = str(ex.expedicion_id.fecha).split('-')
                        if len(fsplit)>1:
                            fexp = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]
            
             

                        values = {
                                    
                                    'nexpedicion':ex.expedicion_id.name   and ex.expedicion_id.name or ' ',
                                    'nescala':nesc  ,
                                    'fexpedicion':fexp ,
                                    'ffexpedicion':ex.expedicion_id.fecha ,
                                    'rexpedicion':ex.expedicion_id.refe or ' ' ,
                                    'ffactura':ex.ffactura,
                                    'factura':ex.invoice_id.date_invoice,
                                    'nfactura':ex.nfactura or ' ',
                                    'cliente':ex.partner_id.name or ' ',
                                    'cfactura':ex.invoice_id.partner_id and ex.invoice_id.partner_id.name or ' ',
                                    'recibido': fact.estruct_dig(cr, uid, str(ex.recibido))+' €' or '0,00€',
                                    'emitido': fact.estruct_dig(cr, uid, str(ex.emitido))+' €' or '0,00€',
                                    'emitidoc':ex.emitido,
                                    'recibidoc':ex.recibido,
                                    'informe':inf.id,    
                                   }
             
                        aux_lines.create(cr, uid, values)
        
                    totr = totr + ex.recibido    
                    tote = tote + ex.emitido

                #LINEAS NO AGRUPADAS

            else:
                for ex in lines.browse(cr, uid, lines_ids):   
                    nesc = str(ex.nescala and ex.nescala or ' ')
                    if nesc == 'False':    
                        nesc = ' '

                    #Fecha expedicion
                    fexp = ' '
                    fsplit = str(ex.expedicion_id.fecha).split('-')
                    if len(fsplit)>1:
                        fexp = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]
        
         

                    values = {
                                'nexpedicion':ex.expedicion_id.name   and ex.expedicion_id.name or ' ',
                                'nescala':nesc  ,
                                'fexpedicion':fexp ,
                                'ffexpedicion':ex.expedicion_id.fecha ,
                                'rexpedicion':ex.expedicion_id.refe or ' ' ,
                                'ffactura':ex.ffactura,
                                'factura':ex.invoice_id.date_invoice,
                                'nfactura':ex.nfactura or ' ',
                                'cliente':ex.partner_id and ex.partner_id.name or ' ',
                                'cfactura':ex.name or ' ',
                                'emitido': fact.estruct_dig(cr, uid, str(ex.emitido))+' €' or '0,00€',
                                'recibido':fact.estruct_dig(cr, uid, str(ex.recibido))+' €' or '0,00€',
                                'informe':inf.id,    
                               }
             
                    aux_lines.create(cr, uid, values)
        
                    totr = totr + ex.recibido    
                    tote = tote + ex.emitido

            for ex in gast.browse(cr, uid, gast_ids):   
    
                nesc = str(ex.expedicion_id.escala and ex.expedicion_id.escala or ' ')

                if nesc == 'False':    
                    nesc = ' '

                #Fecha expedicion
                fexp = ' '
                fsplit = str(ex.expedicion_id.fecha).split('-')
                if len(fsplit)>1:
                    fexp = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

                #Fecha factura
                fexp = ' '
                fff = str( ex.fecha).split('-')
                if len(fsplit)>1:
                    fff = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

   
      
                fact = self.pool.get('account.invoice')

                values = {
                            'nexpedicion':ex.expedicion_id.name   and ex.expedicion_id.name or ' ',
                            'nescala':nesc  ,
                            'ffexpedicion':ex.expedicion_id.fecha ,
                            'fexpedicion':fexp,
                            'rexpedicion':str(ex.expedicion_id.refe or ' ') ,
                            'ffactura':fff or ' ',
                            'nfactura':'Albaran',
                            'cliente':ex.cliente.name or ' ',
                            'cfactura':ex.name or ' ',
                            'emitido': fact.estruct_dig(cr, uid, str(ex.emitido))+' €' or '0,00€',
                            'recibido':fact.estruct_dig(cr, uid, str(ex.recibido))+' €' or '0,00€',
                            'informe':inf.id,    
                           }
         
                aux_lines.create(cr, uid, values)
    
                totr = totr + ex.recibido    
                tote = tote + ex.emitido

            tot = fact.estruct_dig(cr, uid, str(tote - totr) ) 
            totr = fact.estruct_dig(cr, uid, str(totr) ) 
            tote = fact.estruct_dig(cr, uid, str(tote) ) 

            inf.write({'name':nm,'totr':totr,'tote':tote,'tot':tot,})
#imprimir directamente (no funciona en gtk)
            '''action = self.pool.get('ir.actions.report.xml').read(cr, uid, 638, context=context)
            
            domain = [('id','=', ids)]
            action.update({'domain': domain})
            action.update({'target': 'new'})
            action.update({'context': context})
            action.update({'nodestroy': True})
            return action'''

            return True


    
      

########################## On - changes

    def chmes(self, cr, uid, ids, context=None):
        value = {'fecha1': False,'fecha2': False,'opcion':True}
        return {'value': value}

    def chfec(self, cr, uid, ids, context=None):
        value = {'mes': ' ','anio': ' ','opcion':False}
        return {'value': value}

    def cop1(self, cr, uid, ids, x1, x2, context=None):
        
        if x1:
           value =  {'op2': False,'op3':False,'most':9}
        else:
           if x2:
             value =  {'op2': False,'op3':False,'most':6}
           else:
             value = {'op2': False,'op3':False, 'most':3}

        return {'value': value}

    def cop2(self, cr, uid, ids, x1, x2, context=None):

        if x1:
           value = {'op1': False,'op3':False,'most':8}
        else:
           if x2:
             value = {'op1': False,'op3':False, 'most':5}
           else:
             value = {'op1': False,'op3':False, 'most':2}

        return {'value': value}

    def cop3(self, cr, uid, ids, x1, x2, context=None):

        if x1:
           value = {'op2': False,'op1':False,'most':7}
        else:
           if x2:
             value = {'op2': False,'op1':False,'most':4}
           else:
             value = {'op2': False,'op1':False,'most':1}
        
        return {'value': value}

    def cex1(self, cr, uid, ids, x1, x2, context=None):

        if x1:
           value = {'ex2': False,'ex3':False,'most':9}
        else:
           if x2:
             value = {'ex2': False,'ex3':False,'most':8}
           else:
             value = {'ex2': False,'ex3':False,'most':7}

        return {'value': value}

    def cex2(self, cr, uid, ids, x1, x2, context=None):
    
        if x1:
           value = {'ex1': False,'ex3':False,'most':6}
        else:
           if x2:
             value = {'ex1': False,'ex3':False,'most':5}
           else:
             value = {'ex1': False,'ex3':False,'most':4}

        return {'value': value}

    def cex3(self, cr, uid, ids, x1, x2, context=None):
       
        if x1:
           value = {'ex2': False,'ex1':False,'most':3}
        else:
           if x2:
             value = {'ex2': False,'ex1':False,'most':2}
           else:
             value = {'ex2': False,'ex1':False,'most':1}
            
        return {'value': value}

    ##########################

    def ch_ex(self, cr, uid, ids, ex, context = None):

        if not ex:
            v = {'nescala': False}
            return {'value': v}

        ex_obj = self.pool.get('expediciones.expediciones')
        exp = ex_obj.browse(cr, uid, ex)

        v = {'nescala': exp.escala}

        return {'value': v, 'fecha1': False,'fecha2': False,'opcion':True, 'mes': ' ','anio': ' ','opcion':False}

    def ch_es(self, cr, uid, ids, es, context = None):

        if not es:
            v = {'expedicion_id': False}
            return {'value': v}

        ex_obj = self.pool.get('expediciones.expediciones')

        ex_s = ex_obj.search(cr, uid, [('escala','=',es)])

        if len(ex_s) < 1:
            raise osv.except_osv(_('Error'), _('No hay ninguna expedición con ese numero de escala'))

        v = {'nexpedicion': ex_s[0], 'fecha1': False,'fecha2': False,'opcion':True, 'mes': ' ','anio': ' ','opcion':False}

        return {'value': v}

##########################

    _columns = {
                    'name':fields.char('Nombre informe', size=256),
                    'cliente':fields.many2one('res.partner','Cliente'),
                    'mercancia':fields.many2one('product.product','Mercancia'),

                    'mes': fields.selection([(' ', ' '),
                                    ('1', 'Enero'),
                                    ('2', 'Febrero'),
                                    ('3', 'Marzo'),
                                    ('4', 'Abril'),
                                    ('5', 'Mayo'),
                                    ('6', 'Junio'),
                                    ('7', 'Julio'),
                                    ('8', 'Agosto'),
                                    ('9', 'Septiembre'),
                                    ('10', 'Octubre'),
                                    ('11', 'Noviembre'),
                                    ('12', 'Diciembre'),
                                    ],'Mes'),

                    'anio': fields.selection([(' ', ' '),
                                    ('2010', '2010'),
                                    ('2011', '2011'),
                                    ('2012', '2012'),
                                    ('2013', '2013'),
                                    ('2014', '2014'),
                                    ('2015', '2015'),
                                    ('2016', '2016'),
                                    ('2017', '2017'),
                                    ('2018', '2018'),
                                    ('2019', '2019'),
                                    ('2020', '2020'),
                                    ('2021', '2021'),
                                    ('2022', '2022'),
                                    ('2023', '2023'),
                                    ('2024', '2024'),
                                    ('2025', '2025'),
                                    ('2026', '2026'),
                                    ('2027', '2027'),
                                    ('2028', '2028'),
                                    ('2029', '2029'),
                                    ('2030', '2030'),
                                    ('2031', '2031'),
                                    ('2032', '2032'),
                                    ('2033', '2033'),
                                    ('2034', '2034'),
                                    ('2035', '2035'),
                                    ('2036', '2036'),
                                    ('2037', '2037'),
                                    ('2038', '2038'),
                                    ('2039', '2039'),
                                    ('2040', '2040'),
                                    ('2041', '2041'),
                                    ('2042', '2042'),
                                    ('2043', '2043'),
                                    ('2044', '2044'),
                                    ('2045', '2045'),
                                    ('2046', '2046'),
                                    ('2047', '2047'),
                                    ('2048', '2048'),
                                    ('2049', '2049'),
                                    ('2050', '2050'),
                                    ('2051', '2051'),
                                    ('2052', '2052'),
                                    ('2053', '2053'),
                                    ('2054', '2054'),
                                    ('2055', '2055'),
                                    ('2056', '2056'),
                                    ('2057', '2057'),
                                    ('2058', '2058'),
                                    ('2059', '2059'),
                                    ('2060', '2060'),
                                    ],'Año'),

                    'fecha1':fields.date('Desde'),
                    'fecha2':fields.date('Hasta'),

                    'expediciones':fields.one2many('expediciones.expediciones','informe2_id', 'Expediciones'),
                    'lin_ext':fields.one2many('account.invoice.line','informee_id', 'Lineas de expedicion'),

                    'lineas':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas2':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas3':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas4':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas5':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas6':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas7':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas8':fields.one2many('exp.info.aux','informe','Lineas Informe'),
                    'lineas9':fields.one2many('exp.info.aux','informe','Lineas Informe'),

                    'opcion':fields.boolean('Opción'),

                    'op1':fields.boolean('Emitido'),
                    'op2':fields.boolean('Recibido'),
                    'op3':fields.boolean('Completo'),

                    'ex1':fields.boolean('Mercancias'),
                    'ex2':fields.boolean('Buques'),
                    'ex4':fields.boolean('No'),
                    'ex3':fields.boolean('Mercancias y buques'),
           
                    'tot':fields.char('Total',size=256),
                    'tote':fields.char('Total Emitido',size=256),
                    'totr':fields.char('Total Recibido',size=256),

                    'nexpedicion':fields.many2one('expediciones.expediciones','Expedicion'),
                    'nescala':fields.char('Escala', size=256),

                    'most':fields.integer('Mostrar'),

                    
                    
                    'refe':fields.char('Referencia', size=256),
                    'name':fields.char('Nº expedicion', size=256),
                    'escala':fields.char('Nº de escala', size=256),
                    'fecha':fields.date('Fecha'),
                    'pas':fields.char('PAS', size=256),
                    'mercanciass':fields.char('Mercancia',size=512),
                    'kilos':fields.char('Kilos',size=512),
                    'id_mercancias':fields.one2many('expediciones.mercancia','expedicion_id', 'Mercancias'),
                    'cliente_id':fields.many2one('res.partner', 'Cliente'),
                    'origen_id':fields.many2one('expediciones.puerto', 'Origen'),
                    'destino_id':fields.many2one('expediciones.puerto', 'Destino'),
                    'armador_id':fields.many2one('res.partner', 'Armador'),
                    'fletador_id':fields.many2one('res.partner', 'Fletador'),
                    'est_mercaf':fields.float('Estimación de mercancías',   digits_compute= dp.get_precision('Sale Price')),
                    'est_buquesf':fields.float('Estimación de Buques',  digits_compute= dp.get_precision('Sale Price')),
                    'resultado_mercaf':fields.float('Resultado de la expedición', digits_compute= dp.get_precision('Sale Price')),
                    'resultado_buquesf':fields.float('Resultado del buque', digits_compute= dp.get_precision('Sale Price')),
                    'resultado_expedicionf':fields.float('Resultado agregado', digits_compute= dp.get_precision('Sale Price')),
                    'cerrada':fields.char('Cerrada', size=256),
                    'fcerrada':fields.char('Fecha Cierre', size=256),

                    'texto_sup':fields.char('Texto sup',size=512),

                    'agrupar':fields.boolean('Agrupar',size=512),

                }

exp_info()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
