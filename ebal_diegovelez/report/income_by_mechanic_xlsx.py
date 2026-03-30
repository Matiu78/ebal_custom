from odoo import models
from datetime import date
from calendar import monthrange

class IncomeByMechanicXlsx(models.AbstractModel):
    _name = 'report.ebal_mechanic.income_by_mechanic_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        date_from = wizard.date_from
        date_to = wizard.date_to

        if not date_from or not date_to:
            return

        lines = self.env['account.move.line'].search([
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.state', '=', 'posted'),
            ('product_id.type', '=', 'service'),
            ('move_id.invoice_date', '>=', date_from),
            ('move_id.invoice_date', '<=', date_to),
            ('mechanic_ids', '!=', False),
        ])

        mechanic_data = {}

        for line in lines:
            move = line.move_id

            vehicle = move.vehicle_id if hasattr(move, 'vehicle_id') else False

            mechanics = line.mechanic_ids
            if not mechanics:
                continue

            split_value = (line.price_unit * line.quantity) / len(mechanics)

            for mechanic in mechanics:
                mechanic_data.setdefault(mechanic, []).append({
                    'date': move.invoice_date,
                    'product': line.product_id.name,
                    'brand': vehicle.brand_id.name if vehicle and vehicle.brand_id else '',
                    'model': vehicle.model_id.name if vehicle and vehicle.model_id else '',
                    'plate': vehicle.name if vehicle else '',
                    'value': split_value,
                })

        # ===== FORMATOS =====
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
        })

        subtitle_format = workbook.add_format({
            'bold': True,
            'align': 'center'
        })

        header = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center'
        })

        money_format = workbook.add_format({
            'num_format': '$#,##0.00',
            'border': 1
        })

        text_format = workbook.add_format({'border': 1})

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd/mm/yyyy'
        })

        # ===== HOJAS POR MECÁNICO =====
        for mechanic, rows in mechanic_data.items():
            sheet = workbook.add_worksheet(mechanic.name[:31])
            total_mechanic = sum(r['value'] for r in rows)

            # ---- ENCABEZADO SUPERIOR ----
            sheet.merge_range('A1:I1', 'INGRESOS POR TRABAJADOR', title_format)
            sheet.merge_range(
                'A2:I2',
                f'Desde: {date_from.strftime("%d/%m/%Y")}  |  Hasta: {date_to.strftime("%d/%m/%Y")}',
                subtitle_format
            )
            sheet.merge_range('A3:I3', f'Mecánico: {mechanic.name} | Total: ${total_mechanic:,.2f}', subtitle_format)

            # ---- CABECERA DE TABLA (fila 5) ----
            header_row = 4
            sheet.write(header_row, 0, 'FECHA', header)
            sheet.merge_range(header_row, 1, header_row, 4, 'DETALLE', header)
            sheet.write(header_row, 5, 'MARCA', header)
            sheet.write(header_row, 6, 'MODELO', header)
            sheet.write(header_row, 7, 'PLACA', header)
            sheet.write(header_row, 8, 'VALOR', header)

            # ---- DATOS ----
            row = header_row + 1
            for r in rows:
                sheet.write_datetime(row, 0, r['date'], date_format)
                sheet.merge_range(row, 1, row, 4, r['product'], text_format)
                sheet.write(row, 5, r['brand'], text_format)
                sheet.write(row, 6, r['model'], text_format)
                sheet.write(row, 7, r['plate'], text_format)
                sheet.write(row, 8, r['value'], money_format)
                row += 1
            
            sheet.merge_range(row, 0, row, 7, 'TOTAL', header)
            sheet.write(row, 8, total_mechanic, money_format)

            # ---- ANCHOS ----
            sheet.set_column('A:A', 12)
            sheet.set_column('B:E', 35)
            sheet.set_column('F:I', 18)
