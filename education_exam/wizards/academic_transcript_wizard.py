# -*- coding: utf-8 -*-


from eagle import models, fields, api, _
from eagle.exceptions import UserError
from datetime import datetime

class academicTranscript(models.Model):
    _name ='academic.transcript'
    _description='print academic transcript for selected exams'
    academic_year=fields.Many2one('education.academic.year',"Academic Year")
    level=fields.Many2one('education.class',"Level")
    exams=fields.Many2many('education.exam','transcript_id')
    specific_section = fields.Boolean('For a specific section')
    section=fields.Many2one('education.class.division')
    specific_student=fields.Boolean('For a specific Student')
    student=fields.Many2one('education.student','Student')
    state=fields.Selection([('draft','Draft'),('done','Done')],compute='calculate_state')
    @api.multi
    def del_generated_results(self):
        for exam in self.exams:
            records=self.env['education.exam.results.new'].search([('exam_id','=',exam.id)]).unlink()

    @api.multi
    def calculate_state(self):
        results=self.env[('education.exam.results')].search([('academic_year','=',self.academic_year.id),('class_id','=','level')])
        for exam in self.exams:
            rec=results.search([('exam_id','=',exam.id)])
            for line in rec:
                if line.state!='done':
                    self.state='draft'
                    return True
        self.state='done'

    @api.multi
    def get_merit_list(self):
        for rec in self:
            level=rec.level
            for exam in rec.exams:
                self.env['education.exam.results.new'].calculate_merit_list(exam,level)


    @api.multi
    @api.onchange('level', 'section')
    def get_student_domain(self):
        for rec in self:
            domain = []
            if rec.section:
                domain.append(('class_id','=',rec.section.id))
            else:
                domain.append(('class_id.class_id.id', '=', rec.level.id))

        return {'domain': {'student':domain}}
    @api.multi
    @api.onchange('specific_section')
    def onchange_specific_section(self):
        for rec in self:
            if rec.specific_section==False:
                rec.specific_student=False
                rec.section=False
    @api.multi
    def generate_results(self):
        for rec in self:
            for exam in self.exams:
                results_new_list=[]
                result_subject_line_list=[]
                result_paper_line_list=[]
                new_results=self.env['education.exam.results.new'].search([('exam_id', '=', exam.id)])
                results = self.env['education.exam.results'].search([('exam_id', '=', exam.id)])
                for rec in new_results:
                    if rec.result_id not in results:
                        rec.unlink
                for result in results:
                    subject_list = {}
                    new_result=new_results.search([('result_id','=',result.id)])
                    if len(new_result)==0:
                        result_data = {
                            "name": exam.name,
                            "exam_id": exam.id,
                            "student_id": result.student_id.id,
                            "result_id": result.id,
                            "academic_year": exam.academic_year.id,
                            "student_name": result.student_name,
                            "class_id": result.division_id.id,
                            "section_id": result.division_id.section_id.id,
                            "generate_date": datetime.now()
                        }

                        new_result = self.env['education.exam.results.new'].create(result_data)
                        results_new_list.append(new_result)
                    else:   # edit new result data
                        for result_to_edit in new_result:
                            result_to_edit.name= exam.name,
                            result_to_edit.exam_id=exam.id,
                            result_to_edit.student_id= result.student_id.id,
                            result_to_edit.academic_year= exam.academic_year.id,
                            result_to_edit.student_name= result.student_name
                            result_to_edit.class_id=result.division_id.id,
                            result_to_edit.section_id= result.division_id.section_id.id
                            result_to_edit.generate_date= datetime.now()
                            results_new_list.append(result_to_edit)
                    #calculate paper and subject datas
                    for paper in result.subject_line_ids:
                        present_subject_rules = self.env['exam.subject.pass.rules'].search(
                            [('exam_id', '=', exam.id), ('subject_id', '=', paper.subject_id.subject_id.id)])
                        if len(present_subject_rules) == 0:
                            values = {
                                'subject_id': paper.subject_id.subject_id.id,
                                'exam_id': exam.id,
                                'class_id': paper.subject_id.class_id.id
                            }
                            present_subject_rules = present_subject_rules.create(values)
                        present_paper_rules = self.env['exam.paper.pass.rules'].search(
                            [('subject_rule_id', '=', present_subject_rules.id),
                             ('paper_id', '=', paper.subject_id.id)])
                        if len(present_paper_rules) == 0:
                            paper_values = {
                                'subject_rule_id': present_subject_rules.id,
                                'paper_id': paper.subject_id.id,
                                'tut_mark': paper.subject_id.tut_mark,
                                'subj_mark': paper.subject_id.subj_mark,
                                'obj_mark': paper.subject_id.obj_mark,
                                'prac_mark': paper.subject_id.prac_mark
                            }
                            present_paper_rules = present_paper_rules.create(paper_values)
                        subjectId = paper.subject_id.subject_id
                        if subjectId not in subject_list:
                            newSubject=self.env['results.subject.line.new'].search([("subject_id","=",subjectId.id),
                                                                                    ('result_id','=',new_result.id),
                                                                                    ('pass_rule_id','=',present_subject_rules.id)])
                            if len(newSubject)==0:
                                subject_data = {
                                    "subject_id": subjectId.id,
                                    "result_id": new_result.id,
                                    "pass_rule_id": present_subject_rules.id
                                }
                                newSubject = self.env["results.subject.line.new"].create(subject_data)
                            result_subject_line_list.append(newSubject)
                            subject_list[subjectId] = newSubject
                        else:
                            newSubject = subject_list[subjectId]
                        new_paper = self.env["results.paper.line"].search([('subject_line','=',newSubject.id),
                                                                           ('paper_id','=',paper.subject_id.id),
                                                                           ('pass_rule_id','=',present_paper_rules.id)])
                        if len(new_paper)==0:
                            paper_data = {
                                "subject_line": newSubject.id,
                                "paper_id": paper.subject_id.id,
                                "pass_rule_id": present_paper_rules.id,
                                "tut_obt": paper.tut_obt,
                                "subj_obt": paper.subj_obt,
                                "obj_obt": paper.obj_obt,
                                "prac_obt": paper.prac_obt,
                                "tut_pr": paper.tut_pr,  # pr for present/Absent data
                                "subj_pr": paper.subj_pr,
                                "obj_pr": paper.obj_pr,
                                "prac_pr": paper.prac_pr,
                            }
                            new_paper = self.env["results.paper.line"].create(paper_data)
                        else:
                            new_paper.tut_obt= paper.tut_obt
                            new_paper.subj_obt= paper.subj_obt
                            new_paper.obj_obt= paper.obj_obt
                            new_paper.prac_obt= paper.prac_obt
                            new_paper.tut_pr= paper.tut_pr
                            new_paper.subj_pr= paper.subj_pr
                            new_paper.obj_pr=paper.obj_pr
                            new_paper.prac_pr=paper.prac_pr

                        result_paper_line_list.append(new_paper)
            self.calculate_subject_rules(subject_list,exam)
            # self.calculate_result_paper_lines(result_paper_line_list)
            #self.calculate_result_subject_lines(result_subject_line_list)
            self.get_result_type_count(exam)
            self.calculate_subjects_results(exam)
    @api.multi
    def calculate_subject_rules(self,subject_list,exam):
        for subjects in subject_list:
            subjectRules= self.env['exam.subject.pass.rules'].search(
                    [('exam_id', '=', exam.id), ('subject_id', '=', subjects.id)])
            for line in subjectRules:
                for paper_rule in line.paper_ids:
                    paper_rule.name = paper_rule.paper_id.paper
                    paper_rule.paper_marks = paper_rule.tut_mark + paper_rule.subj_mark + paper_rule.obj_mark + paper_rule.prac_mark
                line.academic_year = line.exam_id.academic_year.id
                line.name = line.subject_id.name + " for " + line.class_id.name + "-" + line.academic_year.name
                subject_full_marks = 0
                subjective_mark = 0
                objective_mark = 0
                tutorial_mark = 0
                practical_mark = 0
                for paper in line.paper_ids:
                    subject_full_marks = subject_full_marks + paper.paper_marks
                    subjective_mark = subjective_mark + paper.subj_mark
                    objective_mark = objective_mark + paper.obj_mark
                    tutorial_mark = tutorial_mark + paper.tut_mark
                    practical_mark = practical_mark + paper.prac_mark
                line.subject_marks = subject_full_marks
                line.prac_mark = practical_mark
                line.obj_mark = objective_mark
                line.subj_mark = subjective_mark
                line.tut_mark = tutorial_mark

    @api.multi
    def calculate_subjects_results(self, exam):
        student_lines = self.env['education.exam.results.new'].search([('exam_id', '=', exam.id)])
        for student in student_lines:
            obtained_general = 0
            obtained_general_converted = 0
            count_general_subjects = 0
            count_general_paper = 0
            count_general_fail = 0
            student.general_fail_count=0
            full_general_mark=0
            full_general_mark_converted=0
            gp_general = 0
            obtained_optional = 0
            obtained_optional_converted = 0
            count_optional_subjects = 0
            count_optional_paper = 0
            count_optional_fail = 0
            optional_full_mark = 0
            optional_full_mark_converted = 0
            gp_optional = 0
            obtained_extra = 0
            obtained_extra_converted = 0
            count_extra_subjects = 0
            count_extra_paper = 0
            count_extra_fail = 0
            extra_full_mark = 0
            extra_full_mark_converted = 0
            gp_extra = 0
            res_type_count=0
            for subject in student.subject_line:
                paper_count = 0
                PassFail = True
                optional = False
                extra = False
                obt_tut=0
                obt_prac=0
                obt_subj=0
                obt_obj=0
                mark_tut=0
                mark_prac=0
                mark_subj=0
                mark_obj=0
                subject_obtained=0
                subject_obtained_converted=0
                subject_full=0
                subject_full_converted=0
                count_fail=0
                for paper in subject.paper_ids:
                    paper_obtained=0
                    paper_obtained_converted=0
                    paper_full=0
                    paper_full_converted=0
                    paper_count = paper_count + 1
                    if paper.paper_id in student.student_history.optional_subjects:
                        optional = True
                    elif paper.paper_id.evaluation_type == 'extra':
                        extra = True
                    if paper.pass_rule_id.tut_mark > 0:
                        student.show_tut = True
                        if paper.tut_pr==True:
                            paper_obtained=paper_obtained+paper.tut_obt
                            obt_tut=obt_tut+paper.tut_obt
                            paper_full=paper_full+paper.pass_rule_id.tut_mark
                            mark_tut=mark_tut+paper.pass_rule_id.tut_mark
                        else:
                            PassFail=False
                    if paper.pass_rule_id.subj_mark > 0:
                        student.show_subj = True
                        if paper.subj_pr == True:
                            paper_obtained = paper_obtained + paper.subj_obt
                            paper_full = paper_full + paper.pass_rule_id.subj_mark
                            obt_subj = obt_subj + paper.subj_obt
                            mark_subj = mark_subj + paper.pass_rule_id.subj_mark
                        else:
                            PassFail = False
                    if paper.pass_rule_id.obj_mark > 0:
                        student.show_obj =True
                        if paper.obj_pr==True:
                            paper_obtained = paper_obtained + paper.obj_obt
                            paper_full = paper_full + paper.pass_rule_id.obj_mark
                            obt_obj = obt_obj + paper.obj_obt
                            mark_obj = mark_obj + paper.pass_rule_id.obj_mark
                        else:
                            PassFail=False
                    if paper.pass_rule_id.prac_mark > 0:
                        student.show_prac = True
                        if paper.prac_pr==True:
                            paper_obtained = paper_obtained + paper.prac_obt
                            paper_full = paper_full + paper.pass_rule_id.prac_mark
                            obt_prac = obt_prac + paper.prac_obt
                            mark_prac = mark_prac + paper.pass_rule_id.prac_mark
                        else:
                            PassFail=False

                    if paper.pass_rule_id.tut_pass > paper.tut_obt:
                        PassFail = False
                    elif paper.pass_rule_id.subj_pass > paper.subj_obt:
                        PassFail = False
                    elif paper.pass_rule_id.obj_pass > paper.obj_obt:
                        PassFail = False
                    elif paper.pass_rule_id.prac_pass > paper.prac_obt:
                        PassFail = False

                    paper.paper_obt=paper_obtained
                    paper.passed=PassFail
                    paper.paper_marks=paper_full
                    if paper_full>=100:
                        paper.paper_marks_converted=100
                    else:
                        paper.paper_marks_converted = 50
                    paper.paper_obt_converted=self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up((paper_obtained/paper_full)*paper.paper_marks_converted)
                    subject_obtained=subject_obtained+paper.paper_obt
                    subject_obtained_converted=subject_obtained_converted+paper.paper_obt_converted
                    subject_full=subject_full+paper_full
                    subject_full_converted=subject_full_converted+paper.paper_marks_converted
                subject.obj_obt=obt_obj
                subject.tut_obt=obt_tut
                subject.subj_obt=obt_subj
                subject.prac_obt=obt_prac
                subject.subject_obt=subject_obtained
                subject.subject_obt_converted=subject_obtained_converted
                subject.subject_marks=subject_full
                subject.subject_marks_converted=subject_full_converted
                if subject.pass_rule_id.tut_pass > subject.tut_obt:
                    PassFail = False
                elif subject.pass_rule_id.subj_pass > subject.subj_obt:
                    PassFail = False
                elif subject.pass_rule_id.obj_pass > subject.obj_obt:
                    PassFail = False
                elif subject.pass_rule_id.prac_pass > subject.prac_obt:
                    PassFail = False
                subject.pass_or_fail=PassFail
                if PassFail==False:
                    count_fail=1
                    subject_grade_point=0
                    subject_letter_grade='F'
                else:
                    count_fail = 0
                    subject_grade_point = self.env['education.result.grading'].get_grade_point(
                            subject_full,subject_obtained)
                    subject_letter_grade = self.env['education.result.grading'].get_letter_grade(
                        subject_full, subject_obtained)
                if subject_letter_grade=='F':
                    count_fail=1
                subject.grade_point=subject_grade_point
                subject.letter_grade=subject_letter_grade
                if extra == True:
                    subject.extra_for = student.id
                    obtained_extra = obtained_extra+subject.subject_obt
                    obtained_extra_converted = obtained_extra_converted+subject.subject_obt_converted
                    count_extra_subjects =count_extra_subjects+1
                    count_extra_paper = count_extra_paper+paper_count
                    extra_full_mark = extra_full_mark+subject_full
                    extra_full_mark_converted = extra_full_mark_converted+subject_full_converted
                    gp_extra = gp_extra + subject_grade_point
                    count_extra_fail = count_extra_fail + count_fail
                elif optional == True:
                    subject.optional_for = student.id
                    obtained_optional = obtained_optional + subject.subject_obt
                    obtained_optional_converted = obtained_optional_converted + subject.subject_obt_converted
                    count_optional_subjects = count_optional_subjects + 1
                    count_optional_paper = count_optional_paper + paper_count
                    optional_full_mark = optional_full_mark + subject.pass_rule_id.subject_marks
                    optional_full_mark_converted = optional_full_mark_converted + subject.pass_rule_id.subject_marks_converted
                    gp_optional = gp_optional + subject_grade_point
                    count_optional_fail = count_optional_fail + count_fail
                else:
                    full_general_mark = full_general_mark + subject_full
                    full_general_mark_converted = full_general_mark_converted + subject_full_converted
                    subject.general_for = student.id
                    count_general_subjects = count_general_subjects + 1
                    obtained_general=obtained_general+ subject.subject_obt
                    obtained_general_converted=obtained_general_converted+ subject.subject_obt_converted
                    count_general_paper = count_general_paper + paper_count
                    gp_general = gp_general + subject_grade_point
                    count_general_fail =count_general_fail + count_fail
                subject.paper_count= paper_count
                if paper_count > 1:
                    student.show_paper = True
            if student.show_tut==True:
                res_type_count=res_type_count+1
            if student.show_subj==True:
                res_type_count=res_type_count+1
            if student.show_obj==True:
                res_type_count=res_type_count+1
            if student.show_prac==True:
                res_type_count=res_type_count+1
            student.result_type_count=res_type_count
            student.extra_row_count = count_extra_paper
            student.extra_count = count_extra_subjects
            student.extra_obtained = obtained_extra
            student.extra_obtained_converted = obtained_extra_converted
            student.extra_fail_count=count_extra_fail
            student.extra_full_mark=extra_full_mark
            student.extra_full_mark_converted=extra_full_mark_converted

            student.general_row_count = count_general_paper
            student.general_count = count_general_subjects
            student.general_obtained = obtained_general
            student.general_obtained_converted = obtained_general_converted
            student.general_fail_count=count_general_fail
            student.general_gp=gp_general
            student.general_full_mark = full_general_mark
            student.general_full_mark_converted = full_general_mark_converted

            student.optional_row_count = count_optional_paper
            student.optional_count = count_optional_subjects
            student.optional_obtained = obtained_optional
            student.optional_obtained_converted = obtained_optional_converted
            student.optional_fail_count=count_optional_fail
            student.optional_gp = gp_optional
            student.optional_full_mark = optional_full_mark
            student.optional_full_mark_converted = optional_full_mark_converted
            if student.general_count > 0:
                student.general_gpa = student.general_gp / student.general_count
            else:
                student.general_gpa = 0

            if student.optional_count > 0:
                student.optional_gpa = student.optional_gp / student.optional_count
                if student.optional_gpa > 2:
                    student.optional_gpa_above_2 = student.optional_gpa - 2
                else:
                    student.optional_gpa = 0
            if student.optional_gpa > 0:
                optional_40_perc = student.optional_full_mark * 40 / 100
                optional_40_perc_converted = student.optional_full_mark_converted * 40 / 100
                student.optional_obtained_above_40_perc = student.optional_obtained - optional_40_perc
                student.optional_obtained_above_40_perc_converted = student.optional_obtained_converted - optional_40_perc_converted
            student.net_obtained = student.general_obtained + student.optional_obtained_above_40_perc
            student.net_obtained_converted = student.general_obtained_converted + student.optional_obtained_above_40_perc_converted
            if student.general_count > 0:
                if student.optional_gpa_above_2 < 0:
                    student.optional_gpa_above_2 = 0
                netGPA=student.general_gpa + (student.optional_gpa_above_2 / student.general_count)
                if netGPA<5:
                    student.net_gpa = round(netGPA,2)
                else:student.net_gpa=5
                student.net_lg = self.env['education.result.grading'].get_lg(student.net_gpa)
            if student.extra_count > 0:
                if student.extra_fail_count < 1:
                    student.extra_gpa = student.extra_gp / student.extra_count

        #   TODO   Here to genrate Merit List
        # result_lines=self.env['education.exam.results.new'].sorted(key=lambda r: (r.name, r.country_id.name))
        #

        # ############# TODO get subject Highest

        subject_rule_lines=self.env['exam.subject.pass.rules'].search([('exam_id','=',exam.id)])
        for subject_rule_line in subject_rule_lines:
            subject_result_lines=self.env['results.subject.line.new'].search([('pass_rule_id','=',subject_rule_line.id)], limit=1, order='subject_obt DESC')
            subject_rule_line.subject_highest=subject_result_lines.subject_obt
            for paper_rule_line in subject_rule_line.paper_ids:
                paper_result_line=self.env['results.paper.line'].search([('pass_rule_id','=',paper_rule_line.id)], limit=1, order='paper_obt DESC')
                paper_rule_line.paper_highest=paper_result_line.paper_obt




        # subjectLines=self.env['results.subject.line.new'].search([('result_id.exam_id','=',exam.id)])
        # ##### distinct values search
        # subject=subjectLines.mapped('subject_id')
        # for value in set(subject):
        #     lines=subjectLines.search([('subject_id','=',value.id)],  order='subject_mark DESC')
        #     highest_set=False
        #     for line in lines:
        #         if highest_set==False:
        #             highest=line.subject_mark
        #             highest_set=True
        #         line.subject_highest=highest

    @api.multi
    def calculate_result_paper_lines(self,result_paper_lines):
        for rec in result_paper_lines:
            passFail = True
            if rec.pass_rule_id.tut_pass > rec.tut_obt:
                passFail = False
            elif rec.pass_rule_id.subj_pass > rec.subj_obt:
                passFail = False
            elif rec.pass_rule_id.obj_pass > rec.obj_obt:
                passFail = False
            elif rec.pass_rule_id.prac_pass > rec.prac_obt:
                passFail = False
            elif rec.pass_rule_id.tut_mark > 0:
                if rec.tut_pr == False:
                    passFail = False
            elif rec.pass_rule_id.subj_mark > 0:
                if rec.subj_pr == False:
                    passFail = False
            elif rec.pass_rule_id.obj_mark > 0:
                if rec.obj_pr == False:
                    passFail = False
            elif rec.pass_rule_id.prac_mark > 0:
                if rec.prac_pr == False:
                    passFail = False
            paper_obtained = 0
            if rec.pass_rule_id.tut_mark > 0:
                paper_obtained = paper_obtained + rec.tut_obt
            if rec.pass_rule_id.subj_mark > 0:
                paper_obtained = paper_obtained + rec.subj_obt
            if rec.pass_rule_id.obj_mark > 0:
                paper_obtained = paper_obtained + rec.obj_obt
            if rec.pass_rule_id.prac_mark > 0:
                paper_obtained = paper_obtained + rec.prac_obt
            rec.paper_obt = paper_obtained
            rec.passed = passFail
            if passFail == True:
                rec.gp = self.env['education.result.grading'].get_grade_point(rec.pass_rule_id.paper_marks,
                                                                              rec.paper_obt)
                rec.lg = self.env['education.result.grading'].get_letter_grade(rec.pass_rule_id.paper_marks,
                                                                               rec.paper_obt)
            else:
                rec.gp = 0
                rec.lg = 'F'

    @api.multi
    def calculate_result_subject_lines(self,result_subject_lines):
        for rec in result_subject_lines:
            practical_obt = 0
            subjective_obt = 0
            objective_obt = 0
            tutorial_obt = 0
            practical_mark = 0
            subjective_mark = 0
            objective_mark = 0
            tutorial_mark = 0
            PassFail = True
            for line in rec.paper_ids:
                practical_obt = practical_obt + line.prac_obt
                subjective_obt = subjective_obt + line.subj_obt
                objective_obt = objective_obt + line.obj_obt
                tutorial_obt = tutorial_obt + line.tut_obt
                practical_mark = practical_mark+line.pass_rule_id.tut_mark
                subjective_mark = subjective_mark+line.pass_rule_id.subj_mark
                objective_mark = objective_mark+line.pass_rule_id.obj_mark
                tutorial_mark = tutorial_mark+line.pass_rule_id.tut_mark
                if line.passed == False:
                    PassFail = False
            rec.tut_obt = tutorial_obt
            rec.prac_obt = practical_obt
            rec.subj_obt = subjective_obt
            rec.obj_obt = objective_obt
            rec.tut_mark=tutorial_mark
            rec.prac_mark=practical_mark
            rec.subj_mark=subjective_mark
            rec.obj_mark=objective_mark

            if PassFail == False:
                PassFail = False
            elif rec.pass_rule_id.tut_pass > rec.tut_obt:
                PassFail = False
            elif rec.pass_rule_id.subj_pass > rec.subj_obt:
                PassFail = False
            elif rec.pass_rule_id.obj_pass > rec.obj_obt:
                PassFail = False
            elif rec.pass_rule_id.prac_pass > rec.prac_obt:
                PassFail = False

            rec.mark_scored = 0
            if rec.pass_rule_id.tut_mark > 0:
                rec.mark_scored = rec.mark_scored + rec.tut_obt
            if rec.pass_rule_id.subj_mark > 0:
                rec.mark_scored = rec.mark_scored + rec.subj_obt
            if rec.pass_rule_id.obj_mark > 0:
                rec.mark_scored = rec.mark_scored + rec.obj_obt
            if rec.pass_rule_id.prac_mark > 0:
                rec.mark_scored = rec.mark_scored + rec.prac_obt
            if PassFail == True:
                rec.grade_point = rec.env['education.result.grading'].get_grade_point(
                    rec.pass_rule_id.subject_marks,
                    rec.mark_scored)
                rec.letter_grade = rec.env['education.result.grading'].get_letter_grade(
                    rec.pass_rule_id.subject_marks,
                    rec.mark_scored)
            else:
                rec.grade_point = 0
                rec.letter_grade = 'F'

    @api.multi
    def get_result_type_count(self,exam):
        result_lines=self.env['education.exam.results.new'].search([('exam_id','=',exam.id)])
        for rec in result_lines:
            res_type_count = 0
            if rec.show_tut == True:
                res_type_count = res_type_count + 1
            if rec.show_subj == True:
                res_type_count = res_type_count + 1
            if rec.show_obj == True:
                res_type_count = res_type_count + 1
            if rec.show_prac == True:
                res_type_count = res_type_count + 1
            rec.result_type_count = res_type_count
