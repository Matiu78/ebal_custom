from odoo import models, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    # -------------------------
    # NOTIFICAR REFRESH
    # -------------------------
    def _notify_workorder_refresh(self, workorder_ids):
        bus = self.env["bus.bus"]

        for wid in workorder_ids:
            bus._sendone(
                "web_refresher",
                "notification",
                {
                    "type": "refresh",
                },
            )

    # -------------------------
    # CREATE
    # -------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_workorder_lines()
        return records

    # -------------------------
    # WRITE (IMPORTANTE CHATTER)
    # -------------------------
    def write(self, vals):
        res = super().write(vals)

        if "res_model" in vals or "res_id" in vals:
            self._sync_workorder_lines()

        return res

    # -------------------------
    # UNLINK
    # -------------------------
    def unlink(self):
        workorder_ids = self.filtered(
            lambda a: a.res_model == "mechanic.workorder" and a.res_id
        ).mapped("res_id")

        res = super().unlink()

        if workorder_ids:
            self._notify_workorder_refresh(workorder_ids)

        return res

    # -------------------------
    # SYNC CENTRAL
    # -------------------------
    def _sync_workorder_lines(self):
        Line = self.env["mechanic.workorder.attachment.line"]
        workorder_ids = []

        for att in self:
            if (
                att.res_model == "mechanic.workorder"
                and att.res_id
            ):
                exists = Line.search([
                    ("workorder_id", "=", att.res_id),
                    ("attachment_id", "=", att.id),
                ], limit=1)

                if not exists:
                    Line.create({
                        "workorder_id": att.res_id,
                        "attachment_id": att.id,
                    })

                workorder_ids.append(att.res_id)

        if workorder_ids:
            self._notify_workorder_refresh(list(set(workorder_ids)))