
from eagle import models, fields, api
import pandas as pd
from datetime import datetime
import os
import numpy

class EducationExamResultsExamination(models.Model):
    _name='education.exam.result.exam.line'
    _description = 'this table contain exam information for results line that is first term, secound term or both average'
    name=fields.Char('Result For',compute='get_name',store="True" )
    student_line=fields.One2many('education.exam.results.new','exam_result_line',string="students")
    exam_ids=fields.Many2many('education.exam',string="exams")
    exam_count=fields.Integer('No of Exams')
    pass_rules=fields.One2many('exam.subject.pass.rules','result_exam_line',string="Subject Rules")
    return_date = fields.Date(string="Date Of Return")
    academic_year = fields.Many2one('education.academic.year', string='Academic Year')
    total_working_days = fields.Integer("Total Working Days")
    state=fields.Selection([('draft','Draft'),('done','Done')],string='State', default='draft')
    @api.onchange('exam_ids')
    def get_name(self):
        for rec in self:
            rec.exam_count=len(rec.exam_ids)
            name_str="result For "
            for exam in rec.exam_ids:
                name_str=name_str + exam.name
                if not exam_last:
                    name_str=name_str +','

    @api.multi
    def process_average_results(self,result_exam_line):
        collection={}
        exam_class=''
        exam_year=''
        exam_lines=self.env['education.exam.result.exam.line'].search([
            ('exam_count','=',1),('exam_ids','in',[exam.id for exam in result_exam_line.exam_ids])])
        for line in result_exam_line.exam_ids:
            exam_class = line.class_id
            exam_year = line.academic_year
        result_obj=self.env['education.exam.results.new']
        result_lines=result_obj.search([('exam_result_line','in',[exam_line.id for exam_line in exam_lines])])
        # student_id = result_lines.mapped('student_id')
        fields = self.env['education.exam.results.new'].fields_get()
        y=self.env['education.exam.results.new']._fields
        student_id=result_lines.mapped('student_id')
        subject_rule_lines=self.env['exam.subject.pass.rules'].search([
            ('result_exam_line','in',[exam_line.id for exam_line in exam_lines])])
        subject_ids=subject_rule_lines.mapped('subject_id')

        for subject in subject_ids:
            existing_subject_rules = self.env['exam.subject.pass.rules'].search(
                [('result_exam_line', '=', result_exam_line.id),
                 ('subject_id', '=', subject.id)])
            if len(existing_subject_rules)==0:
                subject_rules_data={
                    'result_exam_line':result_exam_line.id,
                    'class_id': exam_class.id,
                    'academic_year': exam_year.id,
                    'subject_id': subject.id,
                }
                new_subject_rules=self.env['exam.subject.pass.rules'].create(subject_rules_data)
        paper_rule_lines = self.env['exam.paper.pass.rules'].search([
            ('subject_rule_id.result_exam_line', 'in', [exam_line.id for exam_line in exam_lines])])
        paper_ids = paper_rule_lines.mapped('paper_id')
        for paper in paper_ids:
            existing_paper_rules = self.env['exam.paper.pass.rules'].search(
                [('subject_rule_id.result_exam_line', '=',result_exam_line.id),
                 ('paper_id', '=', paper.id)])
            if len(existing_paper_rules)==0:
                paper_rules_data = {
                    'subject_rule_id':self.env['exam.subject.pass.rules'].search([
                                            ('subject_id','=',paper.subject_id.id),
                                            ('result_exam_line','=',result_exam_line.id)]).id,
                    'subject_id': paper.subject_id.id,
                    'paper_id':paper.id,
                }
                new_paper_rules = self.env['exam.paper.pass.rules'].create(paper_rules_data)

        # process pass_rules
        #process paper_pass_rules_data
        paper_rules = self.env['exam.paper.pass.rules'].search([('subject_rule_id.result_exam_line', 'in', [exam_line.id for exam_line in exam_lines])])
        paper_rule_data = {}
        tut_mark = paper_rules.mapped('tut_mark')
        tut_pass = paper_rules.mapped('tut_pass')
        subj_mark = paper_rules.mapped('subj_mark')
        subj_pass = paper_rules.mapped('subj_pass')
        obj_mark = paper_rules.mapped('obj_mark')
        obj_pass = paper_rules.mapped('obj_pass')
        prac_mark = paper_rules.mapped('prac_mark')
        prac_pass = paper_rules.mapped('prac_pass')
        paper_marks = paper_rules.mapped('paper_marks')
        paper_pass_marks = paper_rules.mapped('paper_pass_marks')
        paper_marks_converted = paper_rules.mapped('paper_marks_converted')
        record_id = paper_rules.mapped('id')

        # convert above mapped tupples to list because dataframe only uses lists
        # insert list datas to dictionery
        paper_rule_data['record_id'] = list(self.env['exam.paper.pass.rules'].search([('id','in',record_id)]))
        paper_rule_data['tut_mark'] = list(tut_mark)
        paper_rule_data['tut_pass'] = list(tut_pass)
        paper_rule_data['subj_mark'] = list(subj_mark)
        paper_rule_data['subj_pass'] = list(subj_pass)
        paper_rule_data['obj_mark'] = list(obj_mark)
        paper_rule_data['obj_pass'] = list(obj_pass)
        paper_rule_data['prac_mark'] = list(prac_mark)
        paper_rule_data['prac_pass'] = list(prac_pass)
        # paper_rule_data['paper_marks'] = list(paper_marks)
        paper_rule_data['paper_pass_marks'] = list(paper_pass_marks)
        # paper_rule_data['paper_marks_converted'] = list(paper_marks_converted)
        df_paper_rules = pd.DataFrame(paper_rule_data)
        df_paper_rules['paper_id']='ppp'
        for i,row in df_paper_rules.iterrows():
            df_paper_rules.loc[i, 'paper_id'] = df_paper_rules.loc[i, 'record_id'].paper_id

        df_paper_rules_average=df_paper_rules.groupby('paper_id').mean()
        for r,row in df_paper_rules_average.iterrows():
            paper_rule_lines=self.env['exam.paper.pass.rules'].search([('subject_rule_id.result_exam_line', '=', result_exam_line.id),
                                                                       ('paper_id','=',r.id)])
            # todo to avoide singleton error len paper_rule_lines added
            if len(paper_rule_lines)>0:
                paper_rule_lines.tut_mark = row['tut_mark']
                paper_rule_lines.subj_mark = row['subj_mark']
                paper_rule_lines.obj_mark = row['obj_mark']
                paper_rule_lines.prac_mark = row['prac_mark']
                paper_rule_lines.tut_pass = row['tut_pass']
                paper_rule_lines.subj_pass = row['subj_pass']
                paper_rule_lines.obj_pass = row['obj_pass']
                paper_rule_lines.prac_pass = row['prac_pass']
                paper_rule_lines.paper_pass_marks = row['paper_pass_marks']
                paper_rule_lines.paper_marks = row['tut_mark']+row['subj_mark']+row['obj_mark']+row['obj_mark']
        #process subject Pass rules
        subject_rules=self.env['exam.subject.pass.rules'].search([('result_exam_line','in',[exam_line.id for exam_line in exam_lines])])

        subject_rule_data={}
        record_id=subject_rules.mapped('id')
        tut_mark = subject_rules.mapped('tut_mark')
        tut_pass = subject_rules.mapped('tut_pass')
        subj_mark = subject_rules.mapped('subj_mark')
        subj_pass = subject_rules.mapped('subj_pass')
        obj_mark = subject_rules.mapped('obj_mark')
        obj_pass = subject_rules.mapped('obj_pass')
        prac_mark = subject_rules.mapped('prac_mark')
        prac_pass = subject_rules.mapped('prac_pass')
        subject_marks = subject_rules.mapped('subject_marks')
        subject_pass_marks = subject_rules.mapped('subject_pass_marks')
        subject_marks_converted = subject_rules.mapped('subject_marks_converted')

        # convert above mapped tupples to list because dataframe only uses lists
        # insert list datas to dictionery
        subject_rule_data['tut_mark'] = list(tut_mark)
        subject_rule_data['tut_pass'] = list(tut_pass)
        subject_rule_data['subj_mark'] = list(subj_mark)
        subject_rule_data['subj_pass'] = list(subj_pass)
        subject_rule_data['obj_mark'] = list(obj_mark)
        subject_rule_data['obj_pass'] = list(obj_pass)
        subject_rule_data['prac_mark'] = list(prac_mark)
        subject_rule_data['prac_pass'] = list(prac_pass)
        subject_rule_data['subject_marks'] = list(subject_marks)
        subject_rule_data['subject_pass_marks'] = list(subject_pass_marks)
        subject_rule_data['subject_marks_converted'] = list(subject_marks_converted)
        subject_rule_data['record_id'] = list(self.env['exam.subject.pass.rules'].search([('id','in',record_id)]))

        df_subject_rules=pd.DataFrame(subject_rule_data)
        df_subject_rules['subject_id']='subjects'
        for index,row in df_subject_rules.iterrows():
            df_subject_rules.loc[index, 'subject_id'] = df_subject_rules.loc[index, 'record_id'].subject_id

        df_average_subject_rules=df_subject_rules.groupby('subject_id').mean()
        for r,rows in df_average_subject_rules.iterrows():
            subject_rule_lines = self.env['exam.subject.pass.rules'].search(
                [('result_exam_line', '=', result_exam_line.id),
                    ('subject_id', '=', r.id)])
            subject_rule_lines.tut_mark = row['tut_mark']
            subject_rule_lines.subj_mark = row['subj_mark']
            subject_rule_lines.obj_mark = row['obj_mark']
            subject_rule_lines.prac_mark = row['prac_mark']
            subject_rule_lines.tut_pass = row['tut_pass']
            subject_rule_lines.subj_pass = row['subj_pass']
            subject_rule_lines.obj_pass = row['obj_pass']
            subject_rule_lines.prac_pass = row['prac_pass']
            subject_rule_lines.subject_pass_marks = row['subject_pass_marks']
            subject_rule_lines.subject_marks =row['tut_mark']+row['subj_mark']+row['obj_mark']+row['prac_mark']

        #calculate obtained marks
        for student in student_id:
            new_result_line=self.env['education.exam.results.new'].search([('exam_result_line','=',result_exam_line.id),
                                                                           ('student_id','=',student.id)])
            if len(new_result_line)==0:
                new_result_line_data={
                    'exam_result_line':result_exam_line.id,
                    'student_id': student.id
                        }
                new_result_line=new_result_line.create(new_result_line_data)

            students_result_subject_lines=self.env['results.subject.line.new'].search([('result_id.student_id','=',student.id),
                                            ('result_id.exam_result_line','in',[line.id for line in exam_lines])])
            result_subject_line_subject=students_result_subject_lines.mapped('subject_id')
            resultSubjects=set(result_subject_line_subject)
            for subject in resultSubjects:
                new_subject_line=self.env['results.subject.line.new'].search([('result_id','=',new_result_line.id),('subject_id','=', subject.id)])
                if len(new_subject_line)==0:
                    data={
                        'result_id':new_result_line.id,
                        'subject_id': subject.id,
                        'pass_rule_id': self.env['exam.subject.pass.rules'].search([('result_exam_line','=',result_exam_line.id),
                                                                                    ('subject_id','=',subject.id)]).id,

                    }
                    new_subject_line=self.env['results.subject.line.new'].create(data)
                # # This part insert paper_line data without marks
                # subjec_result_paper_line=self.env['results.paper.line'].search([('subject_line.result_id.student_id','=',student.id),
                #                                 ('subject_line.result_id.exam_result_line','in',[line.id for line in exam_lines])])
                # result_paper_line_subject = subjec_result_paper_line.mapped('paper_id')
                # resultPapers = set(result_paper_line_subject)
                # for paper in resultPapers:
                #     new_paper_line=self.env['results.paper.line'].search([('subject_line.result_id.student_id','=',new_result_line.id),
                #                                                           ('paper_id','=', paper.id)])
                #     if len(new_paper_line)==0:
                #         data={
                #             'paper_id':paper.id,
                #             'subject_line': self.env['results.subject.line.new'].search([('result_id','=',new_result_line.id),
                #                                                                         ('subject_id','=',paper.subject_id.id)]).id,
                #             'pass_rule_id':self.env['exam.paper.pass.rules'].search([('paper_id','=',paper.id),
                #                                                                      ('subject_rule_id.result_exam_line','=',result_exam_line.id)]).id
                #
                #         }
                #         new_paper_line=self.env['results.paper.line'].create(data)


            paper_data={}
            students_result_paper_lines=self.env['results.paper.line'].search([('subject_line.result_id.student_id','=',student.id),
                                                    ('subject_line.result_id.exam_result_line','in',[line.id for line in exam_lines])])
            tut_obt = students_result_paper_lines.mapped('tut_obt')
            subj_obt = students_result_paper_lines.mapped('subj_obt')
            prac_obt = students_result_paper_lines.mapped('prac_obt')
            obj_obt = students_result_paper_lines.mapped('obj_obt')
            id_no = students_result_paper_lines.mapped('id')
            paper_data['tut_obt']=list(tut_obt)
            paper_data['subj_obt']=list(subj_obt)
            paper_data['obj_obt']=list(obj_obt)
            paper_data['prac_obt']=list(prac_obt)
            paper_data['id']=list(self.env['results.paper.line'].search([('id','in',id_no)]))
            df=pd.DataFrame(paper_data)
            df['paper_id']="paper"
            df['subject_id']="subject"
            df['result_student_line']="student"
            df['student_id']="student"

            ### Here to Round obtained marks
            for index, row in df.iterrows():
                df.loc[index,'subj_obt']=self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up(df.loc[index,'subj_obt'])
                df.loc[index,'obj_obt']=self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up(df.loc[index,'obj_obt'])
                df.loc[index,'prac_obt']=self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up(df.loc[index,'prac_obt'])
                df.loc[index,'tut_obt']=self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up(df.loc[index,'tut_obt'])
                df.loc[index, 'paper_id'] = df.loc[index, 'id'].paper_id
                df.loc[index, 'subject_id'] = df.loc[index, 'id'].subject_line
                df.loc[index, 'student_id'] = student
                df.loc[index, 'result_line'] = df.loc[index, 'subject_id'].result_id


            df_average_paper_obt=df.groupby(['paper_id']).mean()

            for i,row in df_average_paper_obt.iterrows():
                studentPaperLine= self.env['results.paper.line'].search([('subject_line.result_id.exam_result_line','=',result_exam_line.id),
                                                                      ('subject_line.result_id.student_id','=',student.id),
                                                                      ('paper_id','=', i.id)])
                # Check if students result paper line exist , edit line
                if len(studentPaperLine)>0:
                    studentPaperLine.tut_obt=row['tut_obt']
                    studentPaperLine.subj_obt=row['subj_obt']
                    studentPaperLine.obj_obt=row['obj_obt']
                    studentPaperLine.prac_obt=row['prac_obt']
                # Check if students result paper line exist , edit line
                else:
                    paper_line_data={
                       'pass_rule_id':self.env['exam.paper.pass.rules'].search([('paper_id','=',i.id),
                                                            ('subject_rule_id.result_exam_line','=',result_exam_line.id)]).id,

                        'subject_line': self.env['results.subject.line.new'].search([('result_id.exam_result_line','=',result_exam_line.id),
                                                                                     ('result_id.student_id', '=',student.id),
                                                                                     ('subject_id','=',i.subject_id.id)]).id,
                        'paper_id': i.id,
                        'tut_obt':row['tut_obt'],
                        'subj_obt': row['subj_obt'],
                        'obj_obt': row['obj_obt'],
                        'prac_obt':row['prac_obt'],
                        }
                    studentPaperLine.create(paper_line_data)
        self.calculate_subject_rules(subject_ids,result_exam_line)
        self.calculate_subjects_results(result_exam_line)
        #
        # self.calculate_exam_average_results(result_exam_line)



    @api.multi
    def calculate_exam_results(self,result_exam_line):
        for exam in result_exam_line.exam_ids:
            results_new_list=[]
            result_subject_line_list=[]
            result_paper_line_list=[]
            new_results=self.env['education.exam.results.new'].search([('exam_result_line', '=', result_exam_line.id)])
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
                        "exam_result_line":result_exam_line.id,
                        "exam_id": exam.id,
                        "student_id": result.student_id.id,
                        "result_id": result.id,
                        "academic_year": exam.academic_year.id,
                        # "student_name": result.student_name,
                        # "class_id": result.division_id.id,
                        # "section_id": result.division_id.section_id.id,
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
                        [('result_exam_line', '=', result_exam_line.id), ('subject_id', '=', paper.subject_id.subject_id.id)])
                    if len(present_subject_rules) == 0:
                        values = {
                            'subject_id': paper.subject_id.subject_id.id,
                            'exam_id': exam.id,
                            'result_exam_line':result_exam_line.id,
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
            self.calculate_subject_rules(subject_list,result_exam_line)
        # self.calculate_result_paper_lines(result_paper_line_list)
        #self.calculate_result_subject_lines(result_subject_line_list)
        self.get_result_type_count()
        self.calculate_subjects_results(result_exam_line)

    @api.multi
    def calculate_exam_average_results(self, result_exam_line):
        result_student_lines=self.env['education.exam.results.new'].search([('exam_result_line','=',result_exam_line.id)])
        for line in result_student_lines:
            line.calculate_result()


    @api.multi
    def calculate_subjects_results(self,exam_result_line):
        student_lines = self.env['education.exam.results.new'].search([('exam_result_line', '=', exam_result_line.id)])
        for student in student_lines:
            obtained_general = 0
            obtained_general_converted = 0
            count_general_subjects = 0
            count_general_paper = 0
            count_general_fail = 0
            student.general_fail_count = 0
            full_general_mark = 0
            full_general_mark_converted = 0
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
            res_type_count = 0
            hide_tut = True
            hide_subj = True
            hide_obj = True
            hide_prac = True
            hide_paper = True
            for subject in student.subject_line:
                paper_count = 0
                PassFail = True
                optional = False
                extra = False
                obt_tut = 0
                obt_prac = 0
                obt_subj = 0
                obt_obj = 0
                mark_tut = 0
                mark_prac = 0
                mark_subj = 0
                mark_obj = 0
                subject_obtained = 0
                subject_obtained_converted = 0
                subject_full = 0
                subject_full_converted = 0
                count_fail = 0
                for paper in subject.paper_ids:
                    paper_obtained = 0
                    paper_obtained_converted = 0
                    paper_full = 0
                    paper_full_converted = 0
                    paper_count = paper_count + 1
                    if paper.paper_id in student.student_history.optional_subjects:
                        optional = True
                    elif paper.paper_id.evaluation_type == 'extra':
                        extra = True
                    if paper.pass_rule_id.tut_mark > 0:
                        hide_tut = False
                        if paper.tut_pr == True:
                            paper_obtained = paper_obtained + paper.tut_obt
                            obt_tut = obt_tut + paper.tut_obt
                            paper_full = paper_full + paper.pass_rule_id.tut_mark
                            mark_tut = mark_tut + paper.pass_rule_id.tut_mark
                        else:
                            PassFail = False
                    if paper.pass_rule_id.subj_mark > 0:
                        hide_subj = False
                        if paper.subj_pr == True:
                            paper_obtained = paper_obtained + paper.subj_obt
                            paper_full = paper_full + paper.pass_rule_id.subj_mark
                            obt_subj = obt_subj + paper.subj_obt
                            mark_subj = mark_subj + paper.pass_rule_id.subj_mark
                        else:
                            PassFail = False
                    if paper.pass_rule_id.obj_mark > 0:
                        hide_obj = False
                        if paper.obj_pr == True:
                            paper_obtained = paper_obtained + paper.obj_obt
                            paper_full = paper_full + paper.pass_rule_id.obj_mark
                            obt_obj = obt_obj + paper.obj_obt
                            mark_obj = mark_obj + paper.pass_rule_id.obj_mark
                        else:
                            PassFail = False
                    if paper.pass_rule_id.prac_mark > 0:
                        hide_prac = False
                        if paper.prac_pr == True:
                            paper_obtained = paper_obtained + paper.prac_obt
                            paper_full = paper_full + paper.pass_rule_id.prac_mark
                            obt_prac = obt_prac + paper.prac_obt
                            mark_prac = mark_prac + paper.pass_rule_id.prac_mark
                        else:
                            PassFail = False

                    if paper.pass_rule_id.tut_pass > paper.tut_obt:
                        PassFail = False
                    elif paper.pass_rule_id.subj_pass > paper.subj_obt:
                        PassFail = False
                    elif paper.pass_rule_id.obj_pass > paper.obj_obt:
                        PassFail = False
                    elif paper.pass_rule_id.prac_pass > paper.prac_obt:
                        PassFail = False

                    paper.paper_obt = paper_obtained
                    paper.passed = PassFail
                    paper.paper_marks = paper_full
                    if paper_full >= 100:
                        paper.paper_marks_converted = 100
                    else:
                        paper.paper_marks_converted = 50
                    if paper_full>0:
                        paper.paper_obt_converted = self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up(
                            (paper_obtained / paper_full) * paper.paper_marks_converted)
                    subject_obtained = subject_obtained + paper.paper_obt
                    subject_obtained_converted = subject_obtained_converted + paper.paper_obt_converted
                    subject_full = subject_full + paper_full
                    subject_full_converted = subject_full_converted + paper.paper_marks_converted
                subject.obj_obt = obt_obj
                subject.tut_obt = obt_tut
                subject.subj_obt = obt_subj
                subject.prac_obt = obt_prac
                subject.subject_obt = subject_obtained
                subject.subject_marks = subject_full
                if subject_full>0:
                    subject.subject_obt_converted = self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up(
                            (subject_obtained / subject_full) * subject_full_converted)  # subject_obtained_converted

                subject.subject_marks_converted = subject_full_converted
                if subject.pass_rule_id.tut_pass > subject.tut_obt:
                    PassFail = False
                elif subject.pass_rule_id.subj_pass > subject.subj_obt:
                    PassFail = False
                elif subject.pass_rule_id.obj_pass > subject.obj_obt:
                    PassFail = False
                elif subject.pass_rule_id.prac_pass > subject.prac_obt:
                    PassFail = False
                subject.pass_or_fail = PassFail
                if PassFail == False:
                    count_fail = 1
                    subject_grade_point = 0
                    subject_letter_grade = 'F'
                else:
                    count_fail = 0
                    subject_grade_point = self.env['education.result.grading'].get_grade_point(
                        subject_full, subject_obtained)
                    subject_letter_grade = self.env['education.result.grading'].get_letter_grade(
                        subject_full, subject_obtained)
                if subject_letter_grade == 'F':
                    count_fail = 1
                subject.grade_point = subject_grade_point
                subject.letter_grade = subject_letter_grade
                if extra == True:
                    subject.extra_for = student.id
                    obtained_extra = obtained_extra + subject.subject_obt
                    obtained_extra_converted = obtained_extra_converted + subject.subject_obt_converted
                    count_extra_subjects = count_extra_subjects + 1
                    count_extra_paper = count_extra_paper + paper_count
                    extra_full_mark = extra_full_mark + subject_full
                    extra_full_mark_converted = extra_full_mark_converted + subject_full_converted
                    gp_extra = gp_extra + subject_grade_point
                    count_extra_fail = count_extra_fail + count_fail
                elif optional == True:
                    subject.optional_for = student.id
                    obtained_optional = obtained_optional + subject.subject_obt
                    obtained_optional_converted = obtained_optional_converted + subject.subject_obt_converted
                    count_optional_subjects = count_optional_subjects + 1
                    count_optional_paper = count_optional_paper + paper_count
                    optional_full_mark = optional_full_mark + subject.pass_rule_id.subject_marks
                    optional_full_mark_converted = optional_full_mark_converted + subject_full_converted
                    gp_optional = gp_optional + subject_grade_point
                    count_optional_fail = count_optional_fail + count_fail
                else:
                    full_general_mark = full_general_mark + subject_full
                    full_general_mark_converted = full_general_mark_converted + subject_full_converted
                    subject.general_for = student.id
                    count_general_subjects = count_general_subjects + 1
                    obtained_general = obtained_general + subject.subject_obt
                    obtained_general_converted = obtained_general_converted + subject.subject_obt_converted
                    count_general_paper = count_general_paper + paper_count
                    gp_general = gp_general + subject_grade_point
                    count_general_fail = count_general_fail + count_fail
                subject.paper_count = paper_count
                if paper_count > 1:
                    hide_paper = False
            if hide_tut == True:
                student.show_tut = False
            else:
                student.show_tut = True
            if hide_subj == True:
                student.show_subj = False
            else:
                student.show_subj = True
            if hide_obj == True:
                student.show_obj = False
            else:
                student.show_obj = True
            if hide_prac == True:
                student.show_prac = False
            else:
                student.show_prac = True
            if hide_paper == True:
                student.show_paper = False
            else:
                student.show_paper = True

            if student.show_tut == True:
                res_type_count = res_type_count + 1
            if student.show_subj == True:
                res_type_count = res_type_count + 1
            if student.show_obj == True:
                res_type_count = res_type_count + 1
            if student.show_prac == True:
                res_type_count = res_type_count + 1
            student.result_type_count = res_type_count
            student.extra_row_count = count_extra_paper
            student.extra_count = count_extra_subjects
            student.extra_obtained = obtained_extra
            student.extra_obtained_converted = obtained_extra_converted
            student.extra_fail_count = count_extra_fail
            student.extra_full_mark = extra_full_mark
            student.extra_full_mark_converted = extra_full_mark_converted

            student.general_row_count = count_general_paper
            student.general_count = count_general_subjects
            student.general_obtained = obtained_general
            student.general_obtained_converted = obtained_general_converted
            student.general_fail_count = count_general_fail
            student.general_gp = gp_general
            student.general_full_mark = full_general_mark
            student.general_full_mark_converted = full_general_mark_converted

            student.optional_row_count = count_optional_paper
            student.optional_count = count_optional_subjects
            student.optional_obtained = obtained_optional
            student.optional_obtained_converted = obtained_optional_converted
            student.optional_fail_count = count_optional_fail
            student.optional_gp = gp_optional
            student.optional_full_mark = optional_full_mark
            student.optional_full_converted = optional_full_mark_converted
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
                optional_40_perc_converted = student.optional_full_converted * 40 / 100
                student.optional_obtained_above_40_perc = student.optional_obtained - optional_40_perc
                student.optional_obtained_above_40_perc_converted = student.optional_obtained_converted - optional_40_perc_converted
            student.net_obtained = student.general_obtained + student.optional_obtained_above_40_perc
            student.net_obtained_converted = student.general_obtained_converted + student.optional_obtained_above_40_perc_converted
            if student.general_count > 0:
                if student.optional_gpa_above_2 < 0:
                    student.optional_gpa_above_2 = 0
                netGPA = student.general_gpa + (student.optional_gpa_above_2 / student.general_count)
                if netGPA < 5:
                    student.net_gpa = round(netGPA, 2)
                else:
                    student.net_gpa = 5
                student.net_lg = self.env['education.result.grading'].get_lg(student.net_gpa)
            if student.extra_count > 0:
                if student.extra_fail_count < 1:
                    student.extra_gpa = student.extra_gp / student.extra_count

        #   TODO   Here to genrate Merit List
        # result_lines=self.env['education.exam.results.new'].sorted(key=lambda r: (r.name, r.country_id.name))
        #

        # ############# TODO get subject Highest

        subject_rule_lines = self.env['exam.subject.pass.rules'].search([('result_exam_line', '=', exam_result_line.id)])
        for subject_rule_line in subject_rule_lines:
            subject_result_lines = self.env['results.subject.line.new'].search(
                [('pass_rule_id', '=', subject_rule_line.id)], limit=1, order='subject_obt DESC')
            subject_rule_line.subject_highest = subject_result_lines.subject_obt
            for paper_rule_line in subject_rule_line.paper_ids:
                paper_result_line = self.env['results.paper.line'].search([('pass_rule_id', '=', paper_rule_line.id)],
                                                                          limit=1, order='paper_obt DESC')
                paper_rule_line.paper_highest = paper_result_line.paper_obt
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
    def calculate_subject_rules(self,subject_list,result_exam_line):
        for subjects in subject_list:
            subjectRules= self.env['exam.subject.pass.rules'].search(
                    [('result_exam_line', '=', result_exam_line.id), ('subject_id', '=', subjects.id)])
            for line in subjectRules:
                for paper_rule in line.paper_ids:
                    paper_rule.name = paper_rule.paper_id.paper
                    paper_rule.paper_marks = paper_rule.tut_mark + paper_rule.subj_mark + paper_rule.obj_mark + paper_rule.prac_mark
                if line.exam_id:
                    line.academic_year = line.exam_id.academic_year.id
                line.name = line.subject_id.name
                if line.class_id.name :
                    line.name = line.name + line.class_id.name
                if line.academic_year.name:
                    line.name = line.name + " for " + "-" + line.academic_year.name
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
    def get_result_type_count(self):
        result_lines=self.env['education.exam.results.new'].search([('exam_id','=',self.exam_ids.id)])
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


class EducationExamResultsNew(models.Model):
    _name = 'education.exam.results.new'
    _description = "this table contains student Wise exam results"

    name = fields.Char(string='Name' ,related="result_id.name" )
    exam_result_line=fields.Many2one('education.exam.result.exam.line',string='Result Line',ondelete="cascade")
    apeared_exams=fields.Integer('apeared sessions',default='1')
    result_id=fields.Many2one("education.exam.results","result_id")             #relation to the result table
    exam_id = fields.Many2one('education.exam', string='Exam')
    class_id = fields.Many2one('education.class.division',related='student_history.class_id', string='Class')
    level_id=fields.Many2one('education.class',string='Level',related="class_id.class_id",store='True')
    # todo here to change class_id to level
    # todo group for merit list of group
    group=fields.Many2one('education.division',string='Group', related="class_id.division_id")
    # todo make division as related field
    division_id = fields.Many2one('education.class.division', string='Division')
    section_id = fields.Many2one('education.class.section',related='student_history.section', string='Section')
    roll_no = fields.Integer('Roll', related='student_history.roll_no')
    student_id = fields.Many2one('education.student', string='Student')
    student_history=fields.Many2one('education.class.history',"Student History",compute='get_student_history',store="True")
    student_name = fields.Char(string='Student',related='student_id.name')
    subject_line = fields.One2many('results.subject.line.new', 'result_id', string='Subjects')
    general_subject_line = fields.One2many('results.subject.line.new', 'general_for', string='General Subjects')
    optional_subject_line = fields.One2many('results.subject.line.new', 'optional_for', string='optional Subjects')
    extra_subject_line = fields.One2many('results.subject.line.new', 'extra_for', string='extra Subjects')
    academic_year = fields.Many2one('education.academic.year', string='Academic Year')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    total_pass_mark = fields.Float(string='Total Pass Mark')
    total_max_mark = fields.Float(string='Total Max Mark')
    total_max_mark_converted = fields.Float(string='Total Converte Mark')

    general_full_mark=fields.Float("Full Mark")
    general_full_mark_converted=fields.Float("Converted Full Mark")
    general_obtained=fields.Integer("General_total")
    general_obtained_converted=fields.Integer("Converted General total")
    general_count=fields.Integer("General Subject Count")
    general_row_count=fields.Integer("General Paper Count")
    general_fail_count = fields.Integer("Genera Fail")
    general_gp=fields.Float('general GP')
    general_gpa = fields.Float("general GPA")

    extra_Full=fields.Integer("extra Full mark")
    extra_Full_converted=fields.Integer("converted extra Full mark")
    extra_obtained=fields.Integer("extra Obtained")
    extra_obtained_converted=fields.Integer("Converted Extra Obtained")
    extra_count=fields.Integer("extra Count")
    extra_row_count=fields.Integer("extra Row Count")
    extra_fail_count=fields.Integer("Extra Fail")
    extra_gp=fields.Float('Extra GP')
    extra_gpa = fields.Float("Extra GPA")

    optional_full=fields.Integer("Optional full")
    optional_full_converted=fields.Integer("Converted Optional full")
    optional_obtained=fields.Integer("Optional obtained")
    optional_obtained_converted=fields.Integer("Converted Optional obtained")
    optional_count=fields.Integer("optional Count")
    optional_row_count=fields.Integer("optional Row Count")
    optional_fail_count=fields.Integer("optional Fail Count")
    optional_gp=fields.Float('Optional LG')
    optional_gpa = fields.Float("Optional GPA")
    optional_gpa_above_2 = fields.Float("Optional GPA Above 2")
    optional_obtained_above_40_perc=fields.Integer("Aditional marks from optionals")
    optional_obtained_above_40_perc_converted=fields.Integer("Converted Aditional marks from optionals")

    net_obtained = fields.Integer(string='Total Marks Scored')
    net_obtained_converted = fields.Integer(string='Total Marks Scored')
    net_pass = fields.Boolean(string='Overall Pass/Fail')
    net_lg=fields.Char("Letter Grade")
    net_gp = fields.Float("Net GP")
    net_gpa=fields.Float("GPA")

    merit_class=fields.Integer("Position In Class")
    merit_section=fields.Integer("Position In Section")
    merit_group=fields.Integer("Position In Group")

    # working_days=fields.Integer('Working Days')
    attendance=fields.Integer('Attendance')
    percentage_of_attendance=fields.Float("Percentage of Attendance")
    behavior=fields.Many2one("student.behavior","Behavior",default='3')
    sports=fields.Many2one("student.sports","Sports" ,default='3')
    uniform=fields.Many2one("student.uniform","Uniform",default='3')
    cultural=fields.Many2one("student.cultural","Cultural",default='3')
    state=fields.Selection([('draft',"Draft"),('done',"Done")],"State",default='draft')

    show_tut=fields.Boolean('Show Tutorial')
    show_subj=fields.Boolean('Show Subj')
    show_obj=fields.Boolean('Show Obj')
    show_prac=fields.Boolean('Show Prac')
    show_paper=fields.Boolean('Show Papers')
    result_type_count=fields.Integer("result type Count")
    generate_date=fields.Date("Generated Date")



    @api.multi
    def calculate_merit_list(self,result_exam_lines,level):
        for line in result_exam_lines:
            results=[]
            roll_no=[]
            general_total=[]
            net_total=[]
            net_gpa=[]
            optional_fail=[]
            general_fail=[]
            extra_fail=[]
            section=[]
            exam_no=[]
            group=[]
            records=self.env['education.exam.results.new'].search([('exam_result_line','=',line.id),('class_id.class_id','=',level.id)])
            for rec in records:
                results.append(rec)
                roll_no.append(rec.student_history.roll_no)
                general_total.append(rec.general_obtained)
                net_total.append(rec.net_obtained)
                net_gpa.append(rec.net_gpa)
                optional_fail.append(rec.optional_fail_count)
                general_fail.append(rec.general_fail_count)
                extra_fail.append(rec.extra_fail_count)
                section.append(rec.student_history.section)
                group.append(rec.group)
                # exam_no.append(exam)
            data={
                'result':results,
                'gen_total':general_total,
                'net_total': net_total,
                'net_gpa': net_gpa,
                'gen_fail': general_fail,
                'op_fail': optional_fail,
                'ext_fail': extra_fail,
                'section': section,
                'group':group,
                'roll': roll_no,
                # 'exam': exam_no,
                'merit_class':0,
                'merit_section':0,
                'merit_group':0,

            }
            df = pd.DataFrame(data)
            df1=df.sort_values(['gen_fail','net_gpa','net_total', 'op_fail','ext_fail','roll'], ascending=[True, False,False,True,True,True])
            df= df1.reset_index(drop=True)
            for index, row in df.iterrows():
                row['result'].merit_class=index+1
            grouped = df.groupby('section')
            for name, group in grouped:
                df_section = df[(df['section'] == name)]
                df_section_sorted=df_section.sort_index()
                df_section_indexed=df_section_sorted.reset_index(drop=True)
                for index,row in df_section_indexed.iterrows():
                    row['result'].merit_section=index+1
                # df_section_sorted.to_csv(r'C:\Users\Khan Store\Downloads\pandas\df_section_'+str(name.id) +'.csv')
            grouped = df.groupby('group')
            for name, group in grouped:
                df_section = df[(df['group'] == name)]
                df_section_sorted = df_section.sort_index()
                df_section_indexed = df_section_sorted.reset_index(drop=True)
                for index, row in df_section_indexed.iterrows():
                    row['result'].merit_group = index + 1

            for index, row in df.iterrows():
                print(df.loc[index,'merit_class'])

    @api.onchange('general_gp','general_count','optional_gp','optional_count')
    def get_general_gpa(self):
        for rec in self:
            if rec.general_count>0:
                rec.general_gpa=rec.general_gp/rec.general_count
            else:
                rec.general_gpa=0
            if rec.optional_count>0:
                if rec.optional_fail_count<1:
                    rec.optional_gpa=rec.optional_gp/rec.optional_count
                    if rec.optional_gpa>2:
                        rec.optional_gpa_above_2=rec.optional_gpa-2
                    else:
                        rec.optional_gpa = 0

                    if rec.optional_gpa>0:
                        optional_40_perc=rec.optional_full*100/40
                        rec.optional_obtained_above_40_perc=rec.optional_obtained-optional_40_perc
            rec.net_obtained=rec.general_obtained+rec.optional_obtained_above_40_perc
            if rec.general_count>0:
                if rec.optional_gpa_above_2>0:
                    rec.optional_gpa_above_2=0
                rec.net_gpa=rec.general_gpa+(rec.optional_gpa_above_2/rec.general_count)
            if rec.extra_count>0:
                if rec.extra_fail_count<1:
                    rec.extra_gpa=rec.extra_gp/rec.extra_count

    @api.depends('student_id','class_id')
    def get_student_history(self):
        for rec in self:
            history = self.env['education.class.history'].search(
                [('student_id', '=', rec.student_id.id), ('academic_year_id', '=', rec.academic_year.id)])
            rec.student_history=history.id

    @api.multi
    def calculate_result(self):
        showTut=False
        showSubj=False
        showObj=False
        showPrac=False
        resultType=0
        generalObt=0
        optionalObt=0
        extraObt=0
        genFailCount=0
        opFailCount=0
        exFailCount=0
        genRowCount = 0
        opRowCount = 0
        exRowCount = 0
        genCount = 0
        opCount = 0
        exCount = 0
        showPaper=False

        for subject in self.subject_line:
            failed=0
            resultType = 0
            subject.paper_count=len(subject.paper_ids)
            subject.calculate_subject_results()
            if subject.tut_mark>0:
                showTut=True
                resultType=resultType+1
            if subject.subj_mark>0:
                showSubj=True
                resultType = resultType + 1
            if subject.obj_mark>0:
                showObj=True
                resultType = resultType + 1
            if subject.prac_mark>0:
                showPrac=True
                resultType = resultType + 1
            if subject.pass_or_fail==False:
                failed=1
            if subject.paper_count>1:
                showPaper=True

            if len(subject.optional_for)>0:
                optionalObt=optionalObt+subject.subject_obt
                opFailCount=opFailCount+failed
                opRowCount=opRowCount+subject.paper_count
                opCount=opCount+1
            elif len(subject.optional_for)>0:
                extraObt=extraObt+subject.subject_obt
                exFailCount=exFailCount+failed
                exRowCount=exRowCount+subject.paper_count
                exCount=exCount+1
            else:
                generalObt=generalObt+subject.subject_obt
                genFailCount=genFailCount+failed
                genRowCount=genRowCount+subject.paper_count
                genCount=genCount+1

        self.general_obtained=generalObt
        self.optional_obtained=optionalObt
        self.extra_obtained=extraObt
        self.show_tut=showTut
        self.show_subj=showSubj
        self.show_obj=showObj
        self.show_prac=showPrac
        self.result_type_count=resultType
        self.show_paper=showPaper
        self.general_fail_count=genFailCount
        self.extra_fail_count=exFailCount
        self.optional_fail_count=opFailCount
        self.general_row_count=genRowCount
        self.extra_row_count=exRowCount
        self.optional_row_count=opRowCount
        self.general_count=genCount
        self.extra_count=exCount
        self.optional_count=opCount


    def calculate_resultBK(self):
        for exam in exams:
            self.env['education.exam.results.new'].search([('exam_id','=',exam.id)]).unlink()
            results = self.env['education.exam.results'].search([('exam_id','=',exam.id)])
            for result in results:
                result_data={
                    "name": exam.name,
                    "exam_id": exam.id,
                    "student_id": result.student_id.id,
                    "result_id": result.id,
                    "academic_year": exam.academic_year.id,
                    "student_name": result.student_name,
                    "class_id": result.class_id.id
                }
                student_exam_obtained=0
                student_exam_passed=True

                newResult=self.create(result_data)
                subject_list = {}

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
                            'tut_mark':paper.subject_id.tut_mark,
                            'subj_mark':paper.subject_id.subj_mark,
                            'obj_mark':paper.subject_id.obj_mark,
                            'prac_mark':paper.subject_id.prac_mark
                        }
                        present_paper_rules = present_paper_rules.create(paper_values)
                        present_paper_rules.calculate_paper_pass_rule_fields

                    subjectId=paper.subject_id.subject_id
                    if subjectId not in subject_list:
                        subject_data={
                            "subject_id":subjectId.id,
                            "result_id":newResult.id,
                            "pass_rule_id":present_subject_rules.id
                        }
                        newSubject=self.env["results.subject.line.new"].create(subject_data)
                        subject_list[subjectId] = newSubject
                    else:
                        newSubject=subject_list[subjectId]
                    paper_data={
                        "subject_line": newSubject.id,
                        "paper_id": paper.subject_id.id,
                        "pass_rule_id": present_paper_rules.id,
                        "tut_obt": paper.tut_obt,
                        "subj_obt": paper.subj_obt,
                        "obj_obt": paper.obj_obt,
                        "prac_obt": paper.prac_obt,
                        "tut_pr": paper.tut_pr,  #pr for present/Absent data
                        "subj_pr": paper.subj_pr,
                        "obj_pr": paper.obj_pr,
                        "prac_pr": paper.prac_pr,
                        }
                    new_paper=self.env["results.paper.line"].create(paper_data)
                    new_paper.get_name
                newResult.get_result_type_count
class ResultsSubjectLineNew(models.Model):
    _name = 'results.subject.line.new'
    _order="serial asc"
    name = fields.Char(string='Name',related='subject_id.name')
    result_id = fields.Many2one('education.exam.results.new', string='Result Id',ondelete='cascade')
    general_for = fields.Many2one('education.exam.results.new', string='General', ondelete="cascade")
    optional_for = fields.Many2one('education.exam.results.new', string='optional', ondelete="cascade")
    extra_for = fields.Many2one('education.exam.results.new', string='Extra', ondelete="cascade")
    pass_rule_id=fields.Many2one('exam.subject.pass.rules',"Pass Rule",ondelete="cascade")
    serial=fields.Integer("marksheet serial",related="pass_rule_id.sl")
    subject_id = fields.Many2one('education.subject', string='Subject')
    paper_ids=fields.One2many('results.paper.line','subject_line','Papers')

    tut_mark=fields.Float("Tutorial",related="pass_rule_id.tut_mark")
    subj_mark=fields.Float("Subjective",related="pass_rule_id.subj_mark")
    obj_mark=fields.Float("Objective",related="pass_rule_id.obj_mark")
    prac_mark=fields.Float("Practical",related="pass_rule_id.prac_mark")
    subject_marks=fields.Float("Full Mark")

    tut_obt = fields.Integer(string='Tutorial')
    subj_obt = fields.Integer(string='Subjective')
    obj_obt = fields.Integer(string='Objective')
    prac_obt = fields.Integer(string='Practical')
    subject_obt = fields.Float(string='Mark Scored')
    subject_obt_converted = fields.Float(string='Mark Scored')
    paper_count=fields.Integer('Paper Count')
    letter_grade=fields.Char('Grade')
    grade_point=fields.Float('GP')
    subject_highest = fields.Float(string='Max Mark')
    subject_highest_converted = fields.Float(string='Max Mark')
    pass_mark = fields.Float(string='Pass Mark')
    pass_or_fail = fields.Boolean(string='Pass/Fail')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    @api.multi
    def calculate_subject_results(self):
        pass_rules = self.pass_rule_id
        subject_passed = True
        subject_obtained = 0
        subject_tut_obtained=0
        subject_subj_obtained=0
        subject_obj_obtained=0
        subject_prac_obtained=0
        extra=False
        optional=False

        for paper in self.paper_ids:
            paper.calculte_paper_results()

            subject_passed = paper.passed
            subject_obtained = subject_obtained+paper.paper_obt
            subject_tut_obtained = subject_tut_obtained+paper.tut_obt
            subject_subj_obtained = subject_subj_obtained+paper.subj_obt
            subject_obj_obtained = subject_obj_obtained+paper.obj_obt
            subject_prac_obtained = subject_prac_obtained+paper.prac_obt
            if paper.paper_id in self.result_id.student_history.optional_subjects:
                optional = True
            elif paper.paper_id.evaluation_type == 'extra':
                extra = True
        self.tut_obt=subject_tut_obtained
        self.subj_obt=subject_subj_obtained
        self.obj_obt=subject_obj_obtained
        self.prac_obt=subject_prac_obtained

        if self.tut_obt < pass_rules.tut_pass:
            subject_passed = False
        subject_obtained = subject_obtained + self.tut_obt

        if self.subj_obt < pass_rules.subj_pass:
            subject_passed = False
        subject_obtained = subject_obtained + self.subj_obt

        if self.obj_obt < pass_rules.obj_pass:
            subject_passed = False
        subject_obtained = subject_obtained + self.obj_obt

        if self.prac_obt < pass_rules.prac_pass:
            subject_passed = False
        subject_obtained = subject_obtained + self.prac_obt

        self.subject_obt = subject_obtained
        self.passed = subject_passed
        if subject_passed==True:
            self.grade_point = self.env['education.result.grading'].get_grade_point(
                self.subject_marks, self.subj_obt)
            self.letter_grade = self.env['education.result.grading'].get_letter_grade(
                self.subject_marks, self.subj_obt)
        else:
            self.grade_point = 0
            self.letter_grade = 'F'
        if extra == True:
            self.extra_for = self.result_id.id
        elif optional == True:
            self.optional_for = self.result_id.id


class result_paper_line(models.Model):
    _name = 'results.paper.line'
    name=fields.Char("Name")
    pass_rule_id=fields.Many2one('exam.paper.pass.rules',ondelete="cascade")
    subject_line=fields.Many2one('results.subject.line.new',ondelete="cascade")
    paper_id=fields.Many2one("education.syllabus","Paper")
    tut_obt = fields.Float(string='Tutorial')
    subj_obt = fields.Float(string='Subjective')
    obj_obt = fields.Float(string='Objective')
    prac_obt = fields.Float(string='Practical')
    prac_pr = fields.Boolean(string='P',default=True)
    subj_pr = fields.Boolean(string='P',default=True)
    obj_pr = fields.Boolean(string='P',default=True)
    tut_pr = fields.Boolean(string='P',default=True)
    paper_obt=fields.Float("Paper obtained Mark")
    paper_obt_converted=fields.Float("Paper obtained Mark")
    passed=fields.Boolean("Passed?" )
    paper_marks=fields.Float("Paper Full Mark")
    lg=fields.Char("letter Grade")
    gp=fields.Float("grade Point")

    @api.multi
    def calculte_paper_results(self):
        pass_rules=self.pass_rule_id
        paper_passed=True
        paper_obtained=0

        if self.tut_pr==True:
            if self.tut_obt<pass_rules.tut_pass:
                paper_passed=False
            paper_obtained=paper_obtained+self.tut_obt
        else:
            paper_passed = False

        if self.subj_pr==True:
            if self.subj_obt<pass_rules.subj_pass:
                paper_passed=False
            paper_obtained=paper_obtained+self.subj_obt
        else:
            paper_passed = False

        if self.obj_pr==True:
            if self.obj_obt<pass_rules.obj_pass:
                paper_passed=False
            paper_obtained=paper_obtained+self.obj_obt
        else:
            paper_passed = False

        if self.prac_pr==True:
            if self.prac_obt<pass_rules.prac_pass:
                paper_passed=False
            paper_obtained=paper_obtained+self.prac_obt
        else:
            paper_passed = False

        self.paper_obt=paper_obtained
        self.passed=paper_passed



    @api.onchange('paper_obt','passed')
    def calculate_lg_gp(self):
        for rec in self:
            if rec.passed==True:
                rec.gp=self.env['education.result.grading'].get_grade_point(rec.pass_rule_id.paper_marks,rec.paper_obt)
                rec.lg=self.env['education.result.grading'].get_letter_grade(rec.pass_rule_id.paper_marks,rec.paper_obt)
class StudentBehavior(models.Model):
    _name="student.behavior"
    _discription="This data to be printed on academic Transcript as student Behavior"
    name=fields.Char('Behaviour')
    note=fields.Char("Note")
class StudentSports(models.Model):
    _name="student.sports"
    _discription="This data to be printed on academic Transcript as student Sports"
    name=fields.Char('Sports')
    note=fields.Char("Note")
class StudentCultural(models.Model):
    _name="student.cultural"
    _discription="This data to be printed on academic Transcript as student Cultural"
    name=fields.Char('Cultural')
    note=fields.Char("Note")
class StudentUniform(models.Model):
    _name="student.uniform"
    _discription="This data to be printed on academic Transcript as student Uniform"
    name=fields.Char('Uniform')
    note=fields.Char("Note")
