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


######  INFORME FACTURAS RECIBIDAS/EMITIDAS

class lin_imp_acu(osv.osv):
    _name = 'lin.imp.acu'



    def create(self, cr, uid, vals, context=None):

        if context is None:
            context = {}

        fact = self.pool.get('account.invoice')

        if 'base' in vals:
            vals['bases'] = fact.estruct_dig(cr, uid, str(vals['base'] ))+'€'
            vals['cuotas'] = fact.estruct_dig(cr, uid, str(vals['cuota'] ))+'€'
            vals['totals'] = fact.estruct_dig(cr, uid, str(vals['total'] ))+'€'

   
        res = super(lin_imp_acu,self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):

        if context is None:
            context = {}

        fact = self.pool.get('account.invoice')

        if 'base' in vals:
            vals['bases'] = fact.estruct_dig(cr, uid, str(vals['base'] ))+'€'
            vals['totals'] = fact.estruct_dig(cr, uid, str(vals['total'] ))+'€'

        if 'cuota' in vals:
            vals['cuotas'] = fact.estruct_dig(cr, uid, str(vals['cuota'] ))+'€'
   
        res = super(lin_imp_acu,self).write(cr, uid, ids, vals, context)
        return res

    _columns = {
                'informe':fields.many2one('informe.facturas','Informe'),

                'impuesto':fields.many2one('account.tax.code','Impuesto'),
                'name':fields.char('Nombre del impuesto', size=256),
                'base':fields.float('Base imponible'),
                'cuota':fields.float('Cuota Impuesto'),
                'total':fields.float('Total'),

                'bases':fields.char('Base imponible', size=256),
                'cuotas':fields.char('Cuota Impuesto', size=256),
                'totals':fields.char('Total', size=256),
                }

lin_imp_acu()

class lineas_emire_aux(osv.osv):
    _name = 'lineas.emire.aux'

    def borrar(self, cr, uid, ids = False, context = None):

        objb = self.pool.get('lineas.emire.aux')
        objb.unlink(cr,uid, objb.search(cr, uid, []))  

        objb = self.pool.get('expediciones.aux.cabecera')
        objb.unlink(cr,uid, objb.search(cr, uid, []))

        objb = self.pool.get('expediciones.aux')
        objb.unlink(cr,uid, objb.search(cr, uid, []))  

        objb = self.pool.get('lineas.aux')
        objb.unlink(cr,uid, objb.search(cr, uid, []))  

     
        return True

    _columns = {
                'informe_ids':fields.many2one('informe.facturas', 'Informe'),
    
                'ffactura':fields.char('Fecha', size=256),
                'fffactura':fields.date('Fecha'),
                'subcuenta':fields.char('Empresa', size=256),
                'descripcion':fields.char('Descripción', size=256),
                'nif':fields.char('NIF', size=256),
                'asiento':fields.char('Factura', size=256),
                'documento':fields.char('Documento', size=256),
                'base':fields.char('Base Imponible', size=256),
                'iva':fields.char('%IVA', size=256),
                'civa':fields.char('Cuota de IVA', size=256),
                'total':fields.char('Total', size=256),
                }
    

    _order = 'fffactura ,asiento'

lineas_emire_aux()


class informe_facturas(osv.osv):
    _name = 'informe.facturas'

########################## On - changes

    def chmes(self, cr, uid, ids, context=None):
        value = {'fecha1': False,'fecha2': False,'opcion':True}
        return {'value': value}

    def chfec(self, cr, uid, ids, context=None):
        value = {'mes': ' ','anio': ' ','opcion':False}
        return {'value': value}

    def chop(self, cr, uid, ids, op, context=None):

        if op == 'recibido':
            value = {'op_diarios':"['purchase','purchase_refund']"}

        else:
            value = {'op_diarios':"['sale','sale_refund']"}

        return {'value': value}

#############################################

    def generar_informe(self, cr, uid, ids, context=None):
        expediciones = self.pool.get('expediciones.expediciones')
        
        lines = self.pool.get('account.invoice.line')
        fact = self.pool.get('account.invoice')

        tx_aux = self.pool.get('lin.imp.acu')    

        gast = self.pool.get('gastos.gastos')

        inf = self.browse(cr, uid, ids)[0]

        for ex in inf.lineas:
            ex.unlink()
        
        for imp in inf.impuestos:
            imp.unlink()

        fact_ids = fact.search(cr, uid, [])
        gast_ids = gast.search(cr, uid, [])       

        escribir = True            

        nm = 'Resumen de facturas'        


        ########################  Emitidas/Recibidas

        fact_ids  = fact.search(cr, uid, [('type','in',('out_invoice','out_refund')),('state','!=','cancel'),('state','!=','draft')])

        if inf.opcion == 'recibido':
            fact_ids = fact.search(cr, uid, [('type','in',('in_invoice','in_refund')),('state','!=','cancel'),('state','!=','draft')])
            nm = nm+' Recibidas'
        else:
            nm = nm+' Emitidas'

        ########################  Diario

        if inf.diario :  
            fact_ids = fact.search(cr, uid, [('journal_id','=',inf.diario.id),('id','in',fact_ids)] )
        
        ########################  FECHAS




        if inf.fecha1 and inf.fecha2:    
             
            fexp1 = ' '
            fsplit = str(inf.fecha1).split('-')
            if len(fsplit)>1:
                 fexp1 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

            fexp2 = ' '
            fsplit = str(inf.fecha2).split('-')
            if len(fsplit)>1:
                 fexp2 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]


            fact_ids = fact.search(cr, uid, [('date_invoice','>=',inf.fecha1),('date_invoice','<=',inf.fecha2),('id','=',fact_ids)] )
            nm = nm + ', entre las fechas '+str( fexp1)+' y '+str(fexp2)
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

            fact_ids = fact.search(cr, uid, [('date_invoice','>=',fecha1),('date_invoice','<',fecha2),('id','in',fact_ids),('id','=',fact_ids)] )
           
            nm = nm + ', del mes '+str(inf.mes)+'-'+str(inf.anio) 

     

        ########################  TOTALES

        tot_base = 0
        tot_iva = 0  
        tot_total = 0  

        if escribir:
        
            aux_lines = self.pool.get('lineas.emire.aux')
            for ex in fact.browse(cr, uid, fact_ids):   
                amunt = ex.amount_untaxed

                nesc = str(ex.nescala and ex.nescala or ' ')

                if nesc == 'False':    
                    nesc = ' '


                signo = True
                if ex.type in ('out_invoice','in_invoice'):
                        signo = False



                #Fecha expedicion
                fexp = ' '
                fsplit = str(ex.date_invoice).split('-')
                if len(fsplit)>1:
                    fexp = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]
                
                if len(ex.tax_line) == 0:

                        ivan = '0'

                        values = {

                                        'ffactura':fexp,
                                        'fffactura':ex.date_invoice,
                                        'subcuenta':ex.account_id.name,
                                        'descripcion':ex.name,
                                        'nif':ex.partner_id.vat,
                                        'asiento':ex.move_id.name,
                                        'documento':ex.origin,
                                        'base':fact.estruct_dig(cr, uid, str(amunt))+'€',
                                        'iva':ivan,
                                        'civa':'0,00€',
                                        'total':fact.estruct_dig(cr, uid, str(amunt) )+'€',

                                        'informe_ids':inf.id,    
                                       }
                     
                        aux_lines.create(cr, uid, values)

                        if signo:
                             amunt = -amunt

                        tot_base = tot_base + amunt   
                        tot_iva = tot_iva + 0   
                        tot_total = tot_total + amunt


                        #Agrupacion de ivas

                        tax_s = tx_aux.search(cr,uid,[('name','=','IVA 0%'),('informe','=',inf.id)]) 

                        if len(tax_s) > 0:
                            tx = tx_aux.browse(cr, uid, tax_s[0])

                            tx.write({'base':tx.base + amunt,'total':tx.total + amunt})
                            print ' suma impuesto 20  '+str(tx.base)+'  --   '+str(amunt)

                        else:
                            values = {      
                                        'informe':inf.id,
                                        'name':'IVA 0%',
                                        'base':amunt,
                                        'cuota':0,
                                        'total': amunt,
                                     }
                            tx_aux.create(cr, uid, values)

                
                else:

                    for lin in ex.invoice_line:
    
                        if len(lin.invoice_line_tax_id) == 0:

                            ivan = '0'

                            values = {

                                        'ffactura':fexp,
                                        'fffactura':ex.date_invoice,
                                        'subcuenta':ex.account_id.name,
                                        'descripcion':ex.name,
                                        'nif':ex.partner_id.vat,
                                        'asiento':ex.move_id.name,
                                        'documento':ex.origin,
                                        'base':fact.estruct_dig(cr, uid, str(lin.price_subtotal))+'€',
                                        'iva':ivan,
                                        'civa':'0,00€',
                                        'total':fact.estruct_dig(cr, uid, str(lin.price_subtotal) )+'€',

                                        'informe_ids':inf.id,    
                                       }
                     
                            aux_lines.create(cr, uid, values)

                            amunt = lin.price_subtotal

                            if signo:
                                 amunt = -amunt

                            tot_base = tot_base + amunt   
                            tot_iva = tot_iva + 0   
                            tot_total = tot_total + amunt

                            #Agrupacion de ivas

                            tax_s = tx_aux.search(cr,uid,[('name','=','IVA 0%'),('informe','=',inf.id)]) 

                            if len(tax_s) > 0:
                                tx = tx_aux.browse(cr, uid, tax_s[0])                                                             

                                tx.write({'base':tx.base + amunt,'total':tx.total + amunt})

                            else:
                                values = {      
                                            'informe':inf.id,
                                            'name':'IVA 0%',
                                            'base':amunt,
                                            'cuota':0,
                                            'total': amunt,
                                         }
                                tx_aux.create(cr, uid, values)

                for tax in ex.tax_line:

                    if len(tax.name.split('IVA'))>1:

                        tbase = tax.base
                        tamount = tax.amount

                        ivan = tax.name.split('%')[0]
    
                     
                        if len(ivan.split(' ') ) > 1:
                            ivan = ivan.split(' ')[len(ivan.split(' '))-1]
                        values = {

                                        'ffactura':fexp,
                                        'fffactura':ex.date_invoice,
                                        'subcuenta':ex.account_id.name,
                                        'descripcion':ex.name,
                                        'nif':ex.partner_id.vat,
                                        'asiento':ex.move_id.name,
                                        'documento':ex.origin,
                                        'base':fact.estruct_dig(cr, uid, str(tbase))+'€',
                                        'iva':ivan,
                                        'civa':fact.estruct_dig(cr, uid, str(tamount))+'€',
                                        'total':fact.estruct_dig(cr, uid, str(tbase + tamount))+'€',

                                        'informe_ids':inf.id,    
                                       }
                     
                        aux_lines.create(cr, uid, values)
                    
                        if signo:
                            tbase = -tbase
                            tamount = -tax.amount

        
                        tot_base = tot_base + tbase    
                        tot_iva = tot_iva + tamount   
                        tot_total = tot_total + tbase + tamount
            
                        #Agrupacion de ivas

                        tax_s = tx_aux.search(cr,uid,[('name','=',tax.base_code_id.name),('informe','=',inf.id)]) 

                        if len(tax_s) > 0:
                            tx = tx_aux.browse(cr, uid, tax_s[0])

                            tx.write({'base':tx.base + tbase,'cuota':tx.cuota + tamount,'total':tx.total + tbase + tamount,})

                        else:
                
                            values = {      
                                        'informe':inf.id,
                                        'impuesto':tax.base_code_id.id,
                                        'name':tax.base_code_id.name,
                                        'base':tbase,
                                        'cuota':tamount,
                                        'total': tbase + tamount,
                                     }
                            tx_aux.create(cr, uid, values)
    


            tot_base = fact.estruct_dig(cr, uid, str(tot_base) ) +'€'
            tot_iva = fact.estruct_dig(cr, uid, str(tot_iva) ) +'€'
            tot_total = fact.estruct_dig(cr, uid, str(tot_total) ) +'€'

            inf.write({'name':nm,'tot_bases':tot_base,'tot_ivas':tot_iva,'tot_totals':tot_total})	
    
        return True

   

    _columns = {
                    'name':fields.char('Nombre informe', size=256),
                    'fecha1':fields.date('Desde'),
                    'fecha2':fields.date('Hasta'),

                    'tot_base':fields.float('Total base',size=256),
                    'tot_civa':fields.float('Total Cuota IVA',size=256),
                    'tot':fields.float('Total Factura',size=256),

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

                    'opcion': fields.selection([('emitido', 'Emitido'),
                                    ('recibido', 'Recibido'),
                                    ],'Mostrar'),

                    'op_diarios': fields.char('Op diario',size=256),

                    'diario':fields.many2one('account.journal','Diario'),

                    'lineas':fields.one2many('lineas.emire.aux','informe_ids', 'Facturas'),
                    'impuestos':fields.one2many('lin.imp.acu','informe', 'Impuestos'),

                    'tot_totals':fields.char('Total',size=256),
                    'tot_ivas':fields.char('Total IVA', size=256),
                    'tot_bases':fields.char('Total Base', size=256),
                }
    
informe_facturas()


######  INFORME CABECERAS EXPEDICIONES

class expediciones_aux_cabecera(osv.osv):
    _name = 'expediciones.aux.cabecera'
    
    _columns = {
                'informe_id':fields.many2one('expediciones.cabecera', 'Informe'),

                'nexpedicion':fields.char('Nº Exp.', size=256),
                'nescala':fields.char('Nº Escala.', size=256),
                'mercancia':fields.char('Mercancia', size=256),
                'fexpedicion':fields.char('Fecha Exp.', size=256),
                'ffexpedicion':fields.date('Fecha Exp.'),
                'rexpedicion':fields.char('Ref. Exp.', size=256),
                'kilos':fields.char('Kg', size=256),
                'cliente':fields.char('Cliente', size=256),
                }

    _order = 'nexpedicion ,nescala, ffexpedicion'

expediciones_aux_cabecera()



class expediciones_cabecera(osv.osv):
    _name = 'expediciones.cabecera'
    

    def chmes(self, cr, uid, ids, context=None):
        value = {'fecha1': False,'fecha2': False,'opcion':True}
        return {'value': value}

    def chfec(self, cr, uid, ids, context=None):
        value = {'mes': ' ','anio': ' ','opcion':False}
        return {'value': value}


    def cex1(self, cr, uid, ids, context=None):
        value = {'ex2': False,'ex3':False}
        return {'value': value}

    def cex2(self, cr, uid, ids, context=None):
        value = {'ex1': False,'ex3':False}
        return {'value': value}

    def cex3(self, cr, uid, ids, context=None):
        value = {'ex2': False,'ex1':False}
        return {'value': value}


    def generar_informe(self, cr, uid, ids, context=None):
        expediciones = self.pool.get('expediciones.expediciones')
        

        inf = self.browse(cr, uid, ids)[0]

        for ex in inf.lineas:
            ex.unlink()

        exp_ids = expediciones.search(cr, uid, [('name','!=',''),('name','!=','0')])

        if inf.ex2:
            exp_ids = expediciones.search(cr, uid, [('escala','!=','')])

        if inf.ex3:
            exp_ids = expediciones.search(cr, uid, [])


        escribir = True        
        
        nm = 'Informe de expediciones '        


        
        ########################  FECHAS

        if inf.fecha1 and inf.fecha2:    
            exp_ids = expediciones.search(cr, uid, [('fecha','>=',inf.fecha1),('fecha','<=',inf.fecha2),('id','in',exp_ids)] )

            ff1 = inf.fecha1
            fsplit = str(inf.fecha1).split('-')
            if len(fsplit)>1:
                ff1 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

            ff2 = inf.fecha2
            fsplit = str(inf.fecha2).split('-')
            if len(fsplit)>1:
                ff2 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

            nm = nm + 'entre las fechas '+str(ff1)+' y '+str(ff2)
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

            exp_ids = expediciones.search(cr, uid, [('fecha','>=',fecha1),('fecha','<',fecha2),('id','in',exp_ids)] )

            nm = nm + ', del mes '+str(inf.mes)+'-'+str(inf.anio) 



   
       ##########Crear resultados

        if escribir:
        
            aux_lines = self.pool.get('expediciones.aux.cabecera')
            fact = self.pool.get('account.invoice')

            for ex in expediciones.browse(cr, uid, exp_ids):   
                if ex.name != '0':
                    #Fecha expedicion
                    fexp = ' '
                    fsplit = str(ex.fecha).split('-')
                    if len(fsplit)>1:
                        fexp = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]


                    values = {
                                'nescala':ex.escala   and ex.escala or ' ',
                                'nexpedicion':ex.name   and ex.name or ' ',
                                'ffexpedicion':ex.fecha ,
                                'fexpedicion':fexp,
                                'rexpedicion':ex.refe ,
                                'mercancia':ex.mercanciass or ' ' ,
                                'kilos':ex.kilos,
                                'cliente':ex.cliente_id.name or ' ' ,
                
                                'informe_id':inf.id,    
                               }
             
                    aux_lines.create(cr, uid, values)
    
            inf.write({'name':nm})
    
        return True



    _columns = {
                    'name':fields.char('Nombre informe', size=256),
                    'fecha1':fields.date('Desde'),
                    'fecha2':fields.date('Hasta'),

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

                    'ex1':fields.boolean('Expediciones'),
                    'ex2':fields.boolean('Escalas'),
                    'ex3':fields.boolean('Expediciones y escalas'),

                    'lineas':fields.one2many('expediciones.aux.cabecera','informe_id', 'Cabeceras Expediciones'),


                }


expediciones_cabecera()







######  INFORME Anual

class expediciones_aux(osv.osv):
    _name = 'expediciones.aux'
    
    _columns = {
                'informe_id':fields.many2one('expediciones.informe', 'Informe'),

                'nexpedicion':fields.char('Nº Exp.', size=256),
                'nescala':fields.char('Nº Escala', size=256),
                'fexpedicion':fields.char('Fecha Exp.', size=256),
                'ffexpedicion':fields.date('Fecha Exp.'),
                'rexpedicion':fields.char('Ref. Exp.', size=256),
                'be':fields.char('Buques estimado', size=256),
                'br':fields.char('Buques real', size=256),
                'me':fields.char('Mercancias estimado', size=256),
                'mr':fields.char('Mercancias real', size=256),
                'te':fields.char('Total estimado', size=256),
                'tr':fields.char('Total real', size=256),

                    'ex1':fields.boolean('Mercancias'),
                    'ex2':fields.boolean('Buques'),
                    'ex3':fields.boolean('Mercancias y buques'),

                'estado':fields.char('Estado',size=56),

                }

    _order = 'nexpedicion, nescala'

expediciones_aux()

class expediciones_informe(osv.osv):
    _name = 'expediciones.informe'

########################## On - changes

    def chmes(self, cr, uid, ids, context=None):
        value = {'fecha1': False,'fecha2': False,'opcion':True}
        return {'value': value}

    def chfec(self, cr, uid, ids, context=None):
        value = {'mes': ' ','anio': ' ','opcion':False}
        return {'value': value}

    def cex1(self, cr, uid, ids, context=None):
        value = {'ex2': False,'ex3':False}
        return {'value': value}

    def cex2(self, cr, uid, ids, context=None):
        value = {'ex1': False,'ex3':False}
        return {'value': value}

    def cex3(self, cr, uid, ids, context=None):
        value = {'ex2': False,'ex1':False}
        return {'value': value}

#########################################################

    def generar_informe(self, cr, uid, ids, context=None):
        expediciones = self.pool.get('expediciones.expediciones')
        

        inf = self.browse(cr, uid, ids)[0]

        for ex in inf.lineas:
            ex.unlink()

        exp_ids = expediciones.search(cr, uid, [])

        escribir = True        
        
        nm = 'Informe de expediciones '        


        
        ########################  FECHAS

        if inf.fecha1 and inf.fecha2:    
            exp_ids = expediciones.search(cr, uid, [('fecha','>=',inf.fecha1),('fecha','<=',inf.fecha2)] )

            ff1 = inf.fecha1
            fsplit = str(inf.fecha1).split('-')
            if len(fsplit)>1:
                ff1 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

            ff2 = inf.fecha2
            fsplit = str(inf.fecha2).split('-')
            if len(fsplit)>1:
                ff2 = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

            nm = nm + 'entre las fechas '+str(ff1)+' y '+str(ff2)
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

            exp_ids = expediciones.search(cr, uid, [('fecha','>=',fecha1),('fecha','<',fecha2),('id','in',exp_ids)] )

            nm = nm + ', del mes '+str(inf.mes)+'-'+str(inf.anio) 


   
        #################### Mercancias o buques

        if inf.ex1:
            exp_ids = expediciones.search(cr, uid, [('name','>=',''),('id','in',exp_ids)] )
            nm = nm + ', de Mercancias'
        else:
          if inf.ex2:
            exp_ids = expediciones.search(cr, uid, [('escala','>',''),('id','in',exp_ids)] )
            nm = nm + ', de Buques'
          else:
            nm = nm + ', de Mercancias y Buques'
        ########################  TOTALES

        me = 0
        mr = 0
        be = 0
        br = 0
        te = 0
        tr = 0

        if escribir:
        
            aux_lines = self.pool.get('expediciones.aux')
            fact = self.pool.get('account.invoice')

            for ex in expediciones.browse(cr, uid, exp_ids):   
    
                nesc = str(ex.escala and ex.escala or ' ')

                if nesc == 'False':    
                    nesc = ' '

                #Fecha expedicion
                fexp = ' '
                fsplit = str(ex.fecha).split('-')
                if len(fsplit)>1:
                    fexp = fsplit[2]+'/'+fsplit[1]+'/'+fsplit[0]

                est = 'A'
                if ex.state == 'cerrada':
                      est = 'C'

                values = {
                            'nexpedicion':ex.name   and ex.name or ' ',
                            'nescala':nesc  ,
                            'ffexpedicion':ex.fecha ,
                            'fexpedicion':fexp,
                            'rexpedicion':ex.refe or ' ' ,
                            'me':fact.estruct_dig(cr, uid, str(ex.est_mercaf ) )+'€' or '0,00€',
                            'mr':fact.estruct_dig(cr, uid, str(ex.resultado_mercaf ) )+'€',
                            'be':fact.estruct_dig(cr, uid, str(ex.est_buquesf) )+'€',
                            'br':fact.estruct_dig(cr, uid, str(ex.resultado_buquesf) )+'€',
                            'te':fact.estruct_dig(cr, uid, str( (ex.est_mercaf + ex.est_buquesf) ) )+'€',
                            'tr':fact.estruct_dig(cr, uid, str( (ex.resultado_mercaf + ex.resultado_buquesf ))) +'€',

                            'ex1':inf.ex1,
                            'ex2':inf.ex2,
                            'ex3':inf.ex3,

                            'estado':est,
            
                            'informe_id':inf.id,    
                           }
         
                aux_lines.create(cr, uid, values)
        
                me = me + ex.est_mercaf   
                mr = mr + ex.resultado_mercaf  

                be = be + ex.est_buquesf   
                br = br + ex.resultado_buquesf  

                te = te + ex.est_mercaf + ex.est_buquesf   
                tr = tr + ex.resultado_mercaf  + ex.resultado_buquesf  


            tot = fact.estruct_dig(cr, uid, str(tr) ) 
            totm = fact.estruct_dig(cr, uid, str(mr) ) 
            totb = fact.estruct_dig(cr, uid, str(br) ) 


            tote = fact.estruct_dig(cr, uid, str(te) ) 
            totme = fact.estruct_dig(cr, uid, str(me) ) 
            totbe = fact.estruct_dig(cr, uid, str(be) ) 

            inf.write({'name':nm,'tot':tot+'€','totm':totm+'€','totb':totb+'€','tote':tote+'€','totme':totme+'€','totbe':totbe+'€'})
    
        return True

    _columns = {
                    'name':fields.char('Nombre informe', size=256),
                    'fecha1':fields.date('Desde'),
                    'fecha2':fields.date('Hasta'),

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


                    'ex1':fields.boolean('Mercancias'),
                    'ex2':fields.boolean('Buques'),
                    'ex3':fields.boolean('Mercancias y buques'),
           
                    'tote':fields.char('Total',size=256),
                    'totbe':fields.char('Total Buques',size=256),
                    'totme':fields.char('Total mercancias',size=256),

                    'tot':fields.char('Total',size=256),
                    'totb':fields.char('Total Buques',size=256),
                    'totm':fields.char('Total mercancias',size=256),

                    'expediciones':fields.one2many('expediciones.expediciones','informe_id', 'Expediciones'),
                    'lineas':fields.one2many('expediciones.aux','informe_id', 'Expediciones'),
                    'lineas2':fields.one2many('expediciones.aux','informe_id', 'Expediciones'),
                    'lineas3':fields.one2many('expediciones.aux','informe_id', 'Expediciones'),
                }





expediciones_informe()


####################     INFORME Gastos expediciones


class lineas_aux(osv.osv):
    _name = 'lineas.aux'

    _columns = {
                'informe':fields.many2one('expediciones.informefil','Informe'),

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
                }

    _order = 'nexpedicion desc,ffexpedicion desc,factura desc, nfactura'

lineas_aux()


class expediciones_informefil(osv.osv):
    _name = 'expediciones.informefil'

    def generar_informe(self, cr, uid, ids, context=None):
        expediciones = self.pool.get('expediciones.expediciones')
        
        lines = self.pool.get('account.invoice.line')
        fact = self.pool.get('account.invoice')

        gast = self.pool.get('gastos.gastos')

        inf = self.browse(cr, uid, ids)[0]

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


        if inf.ex1 or inf.ex2 : 
            escribir = True   
            if inf.ex1:
                lines_ids = lines.search(cr, uid, [('id','in',lines_ids),('afecta','=','mercancias')])
                gast_ids = gast.search(cr, uid, [('id','in',gast_ids),('categ','=','mercancia')] )
                nm = nm + ', de Mercancias '

            else:
                lines_ids = lines.search(cr, uid, [('id','in',lines_ids),('afecta','=','buques')])
                gast_ids = gast.search(cr, uid, [('id','in',gast_ids),('categ','=','buque')] ) 
                nm = nm + ', de Buques '

   

        ########################  TOTALES

        tot = 0
        totr = 0
        tote = 0

        if escribir:
        
            aux_lines = self.pool.get('lineas.aux')

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
                            'cliente':ex.partner_id.name or ' ',
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

                    'lineas':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas2':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas3':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas4':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas5':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas6':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas7':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas8':fields.one2many('lineas.aux','informe','Lineas Informe'),
                    'lineas9':fields.one2many('lineas.aux','informe','Lineas Informe'),

                    'opcion':fields.boolean('Opción'),

                    'op1':fields.boolean('Emitido'),
                    'op2':fields.boolean('Recibido'),
                    'op3':fields.boolean('Completo'),

                    'ex1':fields.boolean('Mercancias'),
                    'ex2':fields.boolean('Buques'),
                    'ex3':fields.boolean('Mercancias y buques'),
           
                    'tot':fields.char('Total',size=256),
                    'tote':fields.char('Total Emitido',size=256),
                    'totr':fields.char('Total Recibido',size=256),

                    'nexpedicion':fields.many2one('expediciones.expediciones','Expedicion'),
                    'nescala':fields.char('Escala', size=256),

                    'most':fields.integer('Mostrar'),

                }

expediciones_informefil()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
