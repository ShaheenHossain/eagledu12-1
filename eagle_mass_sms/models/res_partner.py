# -*- coding: utf-8 -*-
from eagle import api, fields, models

class ResPartnerMassSms(models.Model):

    _inherit = "res.partner"
    
    sms_opt_out = fields.Boolean(string="Mass SMS Opt Out")