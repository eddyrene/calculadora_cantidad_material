# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError

class SaleCalculatorType(models.Model):
    _name = 'sale.calculadora.type'

    codigo = fields.Char(u"Código")
    modelo = fields.Char(u"Modelo")
    descripcion = fields.Char(u"Descripcion")
    unidad_kardex = fields.Char(u"Unidad Kardex")
    precio = fields.Float(u"Precio")
    cantidad= fields.Char(u"Cantidad")
    dato = fields.Char(u"Datos Fijo")
    base = fields.Integer(u"Base")
    inc = fields.Integer(u"INC(B)")
    altura = fields.Integer(u"Altura")

class SaleCalculatorProformaLine(models.Model):
    _name = 'sale.calculadora.proforma.line'

    proforma_id = fields.Many2one('sale.calculadora.proforma',"Lineas")

    cantidad = fields.Integer(u"Cantidad",size=3)
    nro_cristal = fields.Char("Numero de Cristal",size=10,readonly=True)
    base1 = fields.Integer("Base1 (L 4)",size=6)
    base2 = fields.Integer("Base2 (L 2)",size=6)
    altura1 = fields.Integer("Altura1 (L 1)",size=6)
    altura2 = fields.Integer("Altura2 (L 3)",size=6)
    descuadre = fields.Char("Descuadre",size=6,inverse="_grafico")
    perimetro = fields.Integer("Perimetro (mm)",compute="_medidas",size=6)
    area = fields.Float("Area m2",digits=(12,4),compute="_medidas", inverse="_grafico",size=6)
    peso = fields.Float("peso",size=6)
    min_vend = fields.Float(u"Mínimo Vendible",size=6)
    pulido = fields.Char("Pulido",size=6)
    entalle = fields.Boolean("Entalle")
    biselado = fields.Boolean("Biselado")
    lavado = fields.Boolean("Lavado")
    perforaciones = fields.Boolean("Perforaciones")
    plantilla = fields.Boolean("Plantilla")
    embalado = fields.Boolean("Embalado")
    insulado = fields.Boolean("Insulado")
    arenado = fields.Boolean("Arenado")
    image = fields.Binary("imagen")

    @api.depends('base1','base1','altura1','altura2','cantidad')
    def _medidas(self):
        from decimal import *
        t_area=0.0
        t_per =0.0
        for prof in self:
            t_area = (Decimal(prof.base1 * prof.altura1)*prof.cantidad)/(1000000)
            t_per = prof.base1 + prof.altura1 + prof.base2 + prof.altura2
            prof.update({
                'area':t_area,
                'perimetro':t_per,
            })

    @api.onchange('descuadre')
    def run1(self):
        self._grafico()
    @api.onchange('area')
    def run2(self):
        self._grafico()
    #@api.depends('descuadre','area')
    #@api.onchange('descuadre','area')
    def _grafico(self):
        import PIL.ImageDraw as ImageDraw
        import PIL.Image as Image
        from PIL import ImageFont
        for prof in self:
            if prof.altura2>0:
                w=1000
                h=1000
                image = Image.new("RGB", (w, h),color=(255,255,255))
                draw = ImageDraw.Draw(image)
                left= 200
                top=150
                h1=prof.altura1
                h2=prof.altura2
                b1=prof.base1
                b2=prof.base2

                dcd=[]
                if prof.descuadre:
                    dcd = [int(x) for x in prof.descuadre.split(',')]

                l = [b1,b2,h1,h2]
                e_max = max(l)
                size = [x*500 /e_max for x in l]

                points =(
                    (0.+left ,h/2+top),
                    (0.+left, h/2-size[2]+top),
                    (size[1]+left, h/2-size[3]+top),
                    (size[0]+left, h/2-0.+top),
                    (0.+left ,h/2- 0.+top),
                        )
                font = ImageFont.truetype("arial.ttf", 36)

                y=30
                draw.text((20, size[2]/3+top), "LADO 1",font=font,fill=(255, 43, 0,128))
                draw.text((size[0]+250, size[2]/3+top), "LADO 3",font=font,fill=(255, 43, 0,128))
                draw.text((size[0]/3+left,20), "LADO 2",font=font,fill=(255, 43, 0,128))
                draw.text((size[0]/3+left,size[3]+200), "LADO 4",font=font,fill=(255, 43, 0,128))

                draw.text((20, size[2]/3+top+y), str(h1)+" mm",font=font,fill=(51, 123, 164))
                draw.text((size[0]+250, size[2]/3+top+y), str(h2)+" mm",font=font,fill=(51, 123, 164))
                draw.text((size[0]/3+left,20+y), str(b2)+" mm",font=font,fill=(51, 123, 164))
                draw.text((size[0]/3+left,size[3]+200+y), str(b1)+" mm",font=font,fill=(51, 123, 164))

                draw.polygon((points), fill=(78, 121, 64))

                for d in dcd:
                    if d not in [1,2,3,4]:
                        raise UserError(_(u"Descuadre: Sólo válido número de lados: 1,2,3,4"))
                    else:
                        draw.line((points[d-1][0],points[d-1][1],points[d][0],points[d][1]),fill=128,width=15)

                import os
                direccion=self.env['main.parameter'].search([])[0].dir_create_file
                print "***********imprimio"
                image.save(direccion+'vidrio.png')
                prof.update({
                    'image':open(str(direccion)+"vidrio.png", "rb").read().encode("base64"),
                })

class SaleCalculatorProforma(models.Model):
    _name = 'sale.calculadora.proforma'
    #id_line = fields.Many2many('sale.calculadora.proforma.line')
    id_line = fields.One2many('sale.calculadora.proforma.line','proforma_id','lista de items')
    total_perimetro = fields.Char("Perimetro Total",compute='_totales',track_visibility='always')
    total_area = fields.Char("Area Total",compute='_totales',track_visibility='always')

    @api.multi
    def cantidad(self):
        ini = 1
        fin = 0
        for prof in self:
            for line in prof.id_line:
                ini = ini
                fin = ini+line.cantidad-1
                print line
                print line.id
                line.write({
                    'nro_cristal': str(ini)+" - " +str(fin),
                })
                ini = fin+1
        self.tipo = str(ini)

    @api.depends('id_line.cantidad','id_line.area','id_line.perimetro')
    def _totales(self):
        for prof in self:
            t_area=0.0
            t_per =0.0
            for line in prof.id_line:
                t_area += line.area
                t_per += line.perimetro
            prof.update({
                'total_area':t_area,
                'total_perimetro':t_per,
            })

class SaleLineCalculadora(models.Model):
    _inherit = 'sale.order.line'
    id_type = fields.Many2one('sale.calculadora.proforma',string="Calculadora")
    id_type_line = fields.One2many(related='id_type.id_line')
    #id_type_line = fields.Many2many(related='id_type.id_line')
    product_uom_qty = fields.Float(string='Quantity',required=True, default=1.0,digits=(12,4))

    @api.onchange('id_type')
    def _get_q(self):
        for line in self:
            line.update({
            'product_uom_qty': line.id_type.total_area,
            })

