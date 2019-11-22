# -*- coding: utf-8 -*-

from eagle import fields, models, api, _
from eagle.exceptions import ValidationError
from datetime import datetime,date
from calendar import monthrange

class AcademyRoomNo(models.Model):
    _name='education.rooms'
    name=fields.Char('Room Name')
    code=fields.Integer('Room No')
    capacity=fields.Integer('Capacity')
    amenities_ids = fields.One2many('education.class.amenities', 'room_id', string='Amenities')
class EducationAcademic(models.Model):
    _name = 'education.academic.year'
    _description = 'Academic Year'
    _order = 'sequence asc'
    _rec_name = 'name'
    name = fields.Char(string='Name', required=True, help='Name of academic year')
    ay_code = fields.Char(string='Code', required=True, help='Code of academic year')
    sequence = fields.Integer(string='Sequence', required=True)
    ay_start_date = fields.Date(string='Start date', required=True, help='Starting date of academic year')
    ay_end_date = fields.Date(string='End date', required=True, help='Ending of academic year')
    ay_description = fields.Text(string='Description', help="Description about the academic year")
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the Academic Year without removing it.")
    @api.onchange('ay_end_date')
    def generate_academic_months(self):
        month_list=self.env['education.month'].search([('id','>',0)],order='id')
        if self.ay_end_date:
            last_month_generated=self.env['education.academic.month'].search([('id','>','0')], order='end_date DESC',limit=1)
            if len(last_month_generated)>0:
                gen_year=last_month_generated.years
                gen_month=last_month_generated.months.id
            else:
                gen_year=2018
            for y in range(gen_year , datetime.strptime(self.ay_end_date,"%Y-%m-%d").year+1):
                for m in month_list:
                    data={'years':y,
                          'months':m.id,
                          'end_date': date(y, m.id, monthrange(y, m.id)[1]),
                            'start_date': date(y, m.id, 1),
                            'month_code':m.code + " " + str(y)

                    }
                    if len(self.env['education.academic.month'].search([('years', '=', y), ('months', '=', m.id)])) == 0:
                        new_month=self.env['education.academic.month'].create(data)

    @api.model
    def create(self, vals):
        """Over riding the create method and assigning the 
        sequence for the newly creating record"""
        vals['sequence'] = self.env['ir.sequence'].next_by_code('education.academic.year')
        res = super(EducationAcademic, self).create(vals)
        return res

    @api.multi
    def unlink(self):
        """return validation error on deleting the academic year"""
        for rec in self:
            raise ValidationError(_("Academic Year can not be deleted, You only can Archive it."))


    _sql_constraints = [
        ('ay_code', 'unique(ay_code)', "Code already exists for another academic year!"),
    ]

    @api.constrains('ay_start_date', 'ay_end_date')
    def validate_date(self):
        """Checking the start and end dates of the syllabus,
        raise warning if start date is not anterior"""
        for rec in self:
            if rec.ay_start_date >= rec.ay_end_date:
                raise ValidationError(_('Start date must be Anterior to End date'))

class EducationAcademicMonth(models.Model):
    _name = 'education.academic.month'
    _description = 'Academic month'
    _rec_name = 'month_code'
    name=fields.Char("Month")
    years=fields.Integer('Year')
    months = fields.Many2one('education.month',string='Name', required=True, help='Name of the Month')
    month_code=fields.Char('Month')
    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')
    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the Academic Year without removing it.")


    @api.depends('months')
    def calculate_details(self):
        for rec in self:
            rec.end_date=date(rec.years,rec.months.id,monthrange(rec.years,rec.months.id)[1])
            rec.start_date=date(rec.years,rec.months.id,1)
            rec.month_code=rec.months.code +" "+ str(rec.years)


class MonthNames(models.Model):
    _name='education.month'
    name=fields.Char("Month")
    code=fields.Char('Code')
