
from eagle import models, fields, api

class ExamSubjectPassRules(models.Model):
    _name = 'exam.subject.pass.rules'
    _description = 'This table contains subject wise pass and fail rules for levels'
    _order = 'sl asc'
    sl=fields.Integer("Serial")
    name = fields.Char(string='Name'  )
    result_exam_line=fields.Many2one('education.exam.result.exam.line',required=True,string='Result Exam Line',ondelete="cascade")
    exam_id = fields.Many2one('education.exam', string='Exam')
    class_id = fields.Many2one('education.class', string='Class')
    subject_id = fields.Many2one('education.subject', string='Subjects')
    paper_ids = fields.One2many('exam.paper.pass.rules','subject_rule_id', string='Subjects')
    academic_year = fields.Many2one('education.academic.year', string='Academic Year')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    tut_mark=fields.Float("Tutorial")
    tut_pass=fields.Float("Tut. Pass")
    subj_mark=fields.Float("Subjective")
    subj_pass=fields.Float("Subj. Pass")
    obj_mark=fields.Float("Objective")
    obj_pass=fields.Float("Obj. Pass")
    prac_mark=fields.Float("Practical")
    prac_pass=fields.Float("Prac. Pass")
    subject_marks = fields.Float(string='full Mark')
    subject_marks_converted = fields.Float(string='full Mark Converted')

    subject_highest=fields.Float('Highest')
    subject_highest_converted=fields.Float('Highest Converted')
    subject_pass_marks = fields.Float(string='Total Pass Mark')
    state = fields.Selection([('draft',"Draft"), ('done', "Done")], "State", default='draft')

    @api.model
    def calculate_subject_marks(self):
        for rec in self:
            rec.tut_mark=0
            rec.subj_mark =0
            rec.obj_mark =0
            rec.prac_mark=0
            for paper in rec.paper_ids:
                rec.tut_mark = rec.tut_mark+paper.tut_mark
                rec.subj_mark = rec.subj_mark+paper.subj_mark
                rec.obj_mark = rec.obj_mark+ paper.obj_mark
                rec.prac_mark = rec.prac_mark+paper.prac_mark

            rec.subject_marks=rec.tut_mark+rec.subj_mark+rec.obj_mark+rec.prac_mark

class ExamPaperPassRules(models.Model):
    _name = 'exam.paper.pass.rules'
    _description = 'This table contains paper wise pass and fail rules for levels'
    _order = 'sl asc'
    sl = fields.Integer("Serial")
    name = fields.Char(string='Name' )
    subject_rule_id = fields.Many2one('exam.subject.pass.rules', string='Subject Rules',ondelete="cascade")
    paper_id = fields.Many2one("education.syllabus", "Paper")
    subject_id=fields.Many2one("education.subject",'subject',related="paper_id.subject_id")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    tut_mark=fields.Float("Tutorial")
    tut_pass=fields.Float("Tut. Pass")
    subj_mark=fields.Float("Subjective")
    subj_pass=fields.Float("Subj. Pass")
    obj_mark=fields.Float("Objective")
    obj_pass=fields.Float("Obj. Pass")
    prac_mark=fields.Float("Practical")
    prac_pass=fields.Float("Prac. Pass")
    paper_marks = fields.Float(string='Total Mark')
    paper_marks_converted = fields.Float(string='Total Converted Mark')
    paper_highest=fields.Float('Highest')
    paper_highest_converted=fields.Float('Highest Converted')
    paper_pass_marks = fields.Float(string='Total Pass Mark')
    state=fields.Selection([('draft',"Draft"),('done',"Done")],"State",default='draft')

    @api.model
    @api.onchange('subj_mark','tut_mark','obj_mark','prac_mark')
    def calculate_paper_marks(self):
        for rec in self:
            rec.paper_marks=rec.tut_mark+rec.subj_mark+rec.obj_mark+rec.prac_mark