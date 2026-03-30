from odoo import models


class IncomeLaborAndPartsXlsx(models.AbstractModel):
    _name = 'report.ebal_mechanic.income_labor_and_parts_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        date_from = wizard.date_from
        date_to = wizard.date_to

        if not date_from or not date_to:
            return

        # ===============================
        # LINEAS DE FACTURA
        # ===============================
        lines = self.env['account.move.line'].search([
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.state', '=', 'posted'),
            ('product_id', '!=', False),
            ('move_id.invoice_date', '>=', date_from),
            ('move_id.invoice_date', '<=', date_to),
        ])

        labor_lines = lines.filtered(lambda l: l.product_id.type == 'service')
        product_lines = lines.filtered(lambda l: l.product_id.type != 'service')

        # ===============================
        # FORMATOS
        # ===============================
        title = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
        })

        subtitle = workbook.add_format({
            'bold': True,
            'align': 'center'
        })

        header = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center'
        })

        money = workbook.add_format({
            'border': 1,
            'num_format': '$#,##0.00'
        })

        text = workbook.add_format({'border': 1})

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd/mm/yyyy'
        })

        # ======================================================
        # HOJA 1 — MANO DE OBRA
        # ======================================================
        sheet = workbook.add_worksheet('Mano de Obra')

        sheet.merge_range('A1:G1', 'INGRESOS POR MANO DE OBRA', title)
        sheet.merge_range(
            'A2:G2',
            f'Desde: {date_from.strftime("%d/%m/%Y")} | Hasta: {date_to.strftime("%d/%m/%Y")}',
            subtitle
        )

        sheet.write_row(
            'A4',
            ['Fecha', 'Servicio', 'Mecánico', 'Marca', 'Modelo', 'Placa', 'Valor'],
            header
        )

        row = 4
        total_labor = 0.0

        for line in labor_lines:
            move = line.move_id
            vehicle = getattr(move, 'vehicle_id', False)

            brand = vehicle.brand_id.name if vehicle and vehicle.brand_id else ''
            model = vehicle.model_id.name if vehicle and vehicle.model_id else ''
            plate = vehicle.name if vehicle else ''

            mechanics = line.mechanic_ids or self.env['res.users']
            split_value = line.price_subtotal / max(len(mechanics), 1)

            for mechanic in mechanics:
                sheet.write_datetime(row, 0, move.invoice_date, date_format)
                sheet.write(row, 1, line.product_id.name, text)
                sheet.write(row, 2, mechanic.name if mechanic else '', text)
                sheet.write(row, 3, brand, text)
                sheet.write(row, 4, model, text)
                sheet.write(row, 5, plate, text)
                sheet.write(row, 6, split_value, money)

                total_labor += split_value
                row += 1

        sheet.merge_range(row, 0, row, 5, 'TOTAL', header)
        sheet.write(row, 6, total_labor, money)

        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:C', 22)
        sheet.set_column('D:F', 18)
        sheet.set_column('G:G', 15)

        # ======================================================
        # HOJA 2 — REPUESTOS (CON MARGEN)
        # ======================================================
        sheet = workbook.add_worksheet('Repuestos')

        sheet.merge_range('A1:H1', 'INGRESOS POR REPUESTOS', title)
        sheet.merge_range(
            'A2:H2',
            f'Desde: {date_from.strftime("%d/%m/%Y")} | Hasta: {date_to.strftime("%d/%m/%Y")}',
            subtitle
        )

        sheet.write_row(
            'A4',
            ['Fecha', 'Producto', 'Marca', 'Modelo', 'Placa', 'Precio', 'Costo', 'Margen'],
            header
        )

        row = 4
        total_price = 0.0
        total_cost = 0.0
        total_margin = 0.0

        for line in product_lines:
            move = line.move_id
            vehicle = getattr(move, 'vehicle_id', False)

            brand = vehicle.brand_id.name if vehicle and vehicle.brand_id else ''
            model = vehicle.model_id.name if vehicle and vehicle.model_id else ''
            plate = vehicle.name if vehicle else ''

            qty = line.quantity
            price = line.price_unit * qty

            cost_unit = line.product_id.standard_price or 0.0
            cost = cost_unit * qty
            margin = price - cost

            sheet.write_datetime(row, 0, move.invoice_date, date_format)
            sheet.write(row, 1, line.product_id.name, text)
            sheet.write(row, 2, brand, text)
            sheet.write(row, 3, model, text)
            sheet.write(row, 4, plate, text)
            sheet.write(row, 5, price, money)
            sheet.write(row, 6, cost, money)
            sheet.write(row, 7, margin, money)

            total_price += price
            total_cost += cost
            total_margin += margin
            row += 1

        sheet.merge_range(row, 0, row, 4, 'TOTAL', header)
        sheet.write(row, 5, total_price, money)
        sheet.write(row, 6, total_cost, money)
        sheet.write(row, 7, total_margin, money)

        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:E', 18)
        sheet.set_column('F:H', 18)