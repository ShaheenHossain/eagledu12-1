# -*- coding: utf-8 -*-

from datetime import datetime
import time
from eagle import fields, models,api


class exam_marksheet(models.AbstractModel):
    _name = 'report.education_exam.report_exam_marksheet'

    def get_exams(self, objects):
        exams = []
        for exam in objects.exams:
           exams.extend(exam)
        return exams


    def get_exam_result_lines(self, objects):
        result_lines = []
        for exam in objects.exams:
            results=self.env['education.exam.result.exam.line'].search([('exam_count','=',1),('exam_ids','=',exam.id)])
            result_lines.append(results)
        if len(objects.exams)>1 and objects.show_average==True:
            results = self.env['education.exam.result.exam.line'].search(
                [('exam_count', '=', len(objects.exams)), ('exam_ids', 'in',[exm.id for exm in objects.exams])])
            result_lines.append(results)

        return result_lines
    def get_student_result_line(self,exam_result_line,student):
        student_result_line=self.env['education.exam.results.new'].search([('exam_result_line','=',exam_result_line.id)
                                                                              ,('student_id','=',student.id)])
        return student_result_line

    # def get_results(self,object,students,exams):
    #     examLine=[]
    #     studentLine=[]
    #     resultLine
    #     for examResultLine in get_exam_result_lines(object):
    #         for student in get_students(object):
    #             for studentResultLine in get_student_result_line(examResultLine,student):
    #                 pass






    def get_results(self,object,students):

        results={}
        for student in students:
            results[student]={}
            results[student]['compulsory']={}
            results[student]['optional']={}
            results[student]['selective']={}
            results[student]['subjects']={}
            results[student]['papers']={}
            comp_results = {}
            op_results = {}
            sel_results = {}
            for exam in self.get_exam_result_lines( object):
                result_line=self.env['education.exam.results.new'].search([('student_history','=',student.id),('exam_result_line','=',exam.id)])
                results[student][exam]={}
                results[student][exam]['subjects']={}
                results[student][exam]['result']=result_line


                for subject in student.compulsory_subjects:
                    if subject.subject_id not in results[student][exam]['subjects']:
                        subject_line=self.env['results.subject.line.new'].search([('result_id','=',result_line.id),('subject_id','=',subject.subject_id.id)])
                        if subject.subject_id not in results[student]['compulsory']:
                            results[student]['compulsory'][subject.subject_id]={}
                        if subject.subject_id not in results[student]['subjects']:
                            results[student]['subjects'][subject.subject_id]={}
                        if exam not in  results[student]['subjects'][subject.subject_id]:
                            results[student]['subjects'][subject.subject_id][exam]={}
                        results[student]['compulsory'][subject.subject_id][exam]=subject_line
                        results[student][exam]['subjects'][subject.subject_id]=subject_line
                        results[student]['subjects'][subject.subject_id][exam]['res']=subject_line

                        for paper in subject_line.paper_ids:
                            if paper.paper_id not in results[student]['papers']:
                                results[student]['papers'][paper.paper_id]={}
                            results[student]['papers'][paper.paper_id][exam]=paper

                for subject in student.optional_subjects:
                    if subject.subject_id not in results[student][exam]['subjects']:
                        subject_line=self.env['results.subject.line.new'].search([('result_id','=',result_line.id),('subject_id','=',subject.subject_id.id)])
                        if subject.subject_id not in results[student]['optional']:
                            results[student]['optional'][subject.subject_id]={}
                        if subject.subject_id not in results[student]['subjects']:
                            results[student]['subjects'][subject.subject_id]={}
                        if exam not in results[student]['subjects'][subject.subject_id]:
                            results[student]['subjects'][subject.subject_id][exam] = {}
                        results[student]['optional'][subject.subject_id][exam]=subject_line
                        results[student][exam]['subjects'][subject.subject_id]=subject_line
                        results[student]['subjects'][subject.subject_id][exam]['res']=subject_line
                        for paper  in subject_line.paper_ids:
                            if paper.paper_id not in results[student]['papers']:
                                results[student]['papers'][paper.paper_id]={}
                            results[student]['papers'][paper.paper_id][exam]=paper

                for subject in student.selective_subjects:
                    if subject.subject_id not in results[student][exam]['subjects']:
                        subject_line=self.env['results.subject.line.new'].search([('result_id','=',result_line.id),('subject_id','=',subject.subject_id.id)])
                        if subject.subject_id not in results[student]['selective']:
                            results[student]['selective'][subject.subject_id]={}
                        if subject.subject_id not in results[student]['subjects']:
                            results[student]['subjects'][subject.subject_id]={}
                        if exam not in results[student]['subjects'][subject.subject_id]:
                            results[student]['subjects'][subject.subject_id][exam]={}
                        results[student]['selective'][subject.subject_id][exam]=subject_line
                        results[student][exam]['subjects'][subject.subject_id]=subject_line
                        results[student]['subjects'][subject.subject_id][exam]['res']=subject_line
                        for paper in subject_line.paper_ids:
                            if paper.paper_id not in results[student]['papers']:
                                results[student]['papers'][paper.paper_id]={}
                            results[student]['papers'][paper.paper_id][exam]=paper
        return results

    def get_sections(self,object):
        if len(object.section)>0:
            return object.section
        elif object.level:
            section=self.env['education.class.division'].search([('class_id','=',object.level.id),('academic_year_id','=',object.academic_year.id)])
            return section
    def get_students(self,objects):
        sections=self.get_sections(objects)
        student=[]
        if len(objects.student)>0 :
            student_list = self.env['education.class.history'].search([('student_id.id', '=', objects.student.id),('academic_year_id.id', '=', objects.academic_year.id)])
            for stu in student_list:
                student.extend(stu)
        elif len(objects.section)>0:
            student_list=self.env['education.class.history'].search([('class_id.id', '=', objects.section.id)])
            for stu in student_list:
                student.extend(stu)
        elif objects.level:
            student_list = self.env['education.class.history'].search([('level.id', '=', objects.level.id),
                                                                       ('academic_year_id.id', '=', objects.academic_year.id)])
            for stu in student_list:
                student.extend(stu)
        return student

    def get_students_in_section(self,section):
        student_list = self.env['education.class.history'].search([('class_id.id', '=', section.id)])
        return student_list



    def get_students_in_student_section(self,student):
        student_list = self.env['education.class.history'].search([('class_id.id', '=', student.section.id)])
        return student_list

    def get_subjects(self,student):
        subjs = {}
        subjs['general']=[]
        subjs['optional']=[]
        subjs['extra']=[]
        gen_row_count=0
        op_row_count=0
        ex_row_count=0
        for subj in student.compulsory_subjects:
            if subj.evaluation_type=='general' :
                gen_row_count=gen_row_count+1
                if subj.subject_id not in subjs['general']:
                    subjs['general'].append(subj.subject_id)
            elif subj.evaluation_type=='extra' :
                ex_row_count=ex_row_count+1
                if subj.subject_id not in subjs['extra']:
                    subjs['extra'].append(subj.subject_id)
        for subj in student.optional_subjects:
            op_row_count=op_row_count+1
            if subj.subject_id not in subjs['optional']:
                subjs['optional'].append(subj.subject_id)
        for subj in student.selective_subjects:
            if subj.subject_id not in subjs['optional']:
                if subj.evaluation_type=='general':
                    gen_row_count = gen_row_count + 1
                    if subj.subject_id not in subjs['general']:
                        subjs['general'].append(subj.subject_id)
                if subj.evaluation_type=='extra':
                    ex_row_count = ex_row_count + 1
                    if subj.subject_id not in subjs['extra']:
                        subjs['extra'].append(subj.subject_id)
        subjs['gen_row_count']=gen_row_count
        subjs['op_row_count']=op_row_count
        subjs['ex_row_count']=ex_row_count
        return subjs

    def check_optional(self,subject,student,exam):
        is_optional=0
        student_history = self.env['education.class.history'].search(
            [('student_id', '=', student.id), ('academic_year_id', '=', exam.academic_year.id)])
        optional_subject=student_history.optional_subjects
        for sub in optional_subject:
            if sub.id==subject.id:
                is_optional=1


        return is_optional
    def get_marks(self,exam,subject,student):
        result_line=self.env['education.exam.results.new'].search([('exam_id','=',exam.id),('student_id','=',student.id)])
        marks=self.env['results.subject.line.new'].search([('subject_id','=',subject.subject_id.id),('result_id','=',result_line.id)])
        return marks
    def get_paper(self,result_subject_line_new):
        papers=result_subject_line_new.paper_ids
        return papers
    def get_exam_obtained_total(self, exam, student_history, optional, evaluation):
        grand_total = self.env['report.education_exam.report_exam_academic_transcript_s'].get_exam_obtained_total( exam,
                                                                                                                   student_history,
                                                                                                                   optional,
                                                                                                                    evaluation)
        return grand_total

    def get_exam_total(self,exam,student_history,optional,evaluation):
        grand_total=self.env['report.education_exam.report_exam_academic_transcript_s'].get_exam_total(exam,student_history,optional,evaluation)
        return grand_total

    def get_gpa(self, student_history, exam, optional, evaluation_type):
        gpa = self.env['report.education_exam.report_exam_academic_transcript_s'].get_gpa(student_history,exam,optional,evaluation_type)
        return gpa
    def get_lg(self, student_history, exam, optional, evaluation_type):
        gpa = self.env['report.education_exam.report_exam_academic_transcript_s'].get_gpa(student_history,exam,optional,evaluation_type)
        grades = self.env['education.result.grading'].search([('score', '<=', gpa)] ,limit=1, order='score DESC')

        gpa = grades.result
        return gpa


    def get_gradings(self,obj):
        grading=self.env['education.result.grading'].search([('id','>','0')],order='min_per desc',)
        grades=[]
        for grade in grading:
            grades.extend(grade)
        return grades
    def show_paper(self,obj):
        paper_show=obj.show_paper
        return paper_show
    def show_tut(self,obj):
        paper_show=obj.show_tut
        return paper_show
    def show_obj(self,obj):
        paper_show=obj.show_objective
        return paper_show
    def show_prac(self,obj):
        paper_show=obj.show_prac
        return paper_show
    def get_convert_resue(self,subject):
        ratio=subject.subject_id
        return ratio

    def get_total_working_days(self,object):
        working_days=0
        for exam in object.exams:
            working_days=working_days+exam.total_working_days
        return working_days

    def get_converted_report(self,obj):
        if obj.report_type=='2' :
            converted_report=True
        else:
            converted_report=False
        return converted_report
    def show_merit_class(self,obj):
        return obj.show_merit_class
    def show_merit_group(self,obj):
        return obj.show_merit_group
    def show_merit_section(self,obj):
        return obj.show_merit_section

    def get_date(self, date):
        date1 = datetime.strptime(date, "%Y-%m-%d")
        return str(date1.month) + ' / ' + str(date1.year)
    def num2serial(self,numb):
        if numb < 20:  # determining suffix for < 20
            if numb == 1:
                suffix = 'st'
            elif numb == 2:
                suffix = 'nd'
            elif numb == 3:
                suffix = 'rd'
            else:
                suffix = 'th'
        else:  # determining suffix for > 20
            tens = str(numb)
            tens = tens[-2]
            unit = str(numb)
            unit = unit[-1]
            if tens == "1":
                suffix = "th"
            else:
                if unit == "1":
                    suffix = 'st'
                elif unit == "2":
                    suffix = 'nd'
                elif unit == "3":
                    suffix = 'rd'
                else:
                    suffix = 'th'
        return str(numb) + suffix


    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['education.exam.result.wizard'].browse(docids)

        return {
            'doc_model': 'education.exam.results',
            'docs': docs,
            'time': time,
            'get_students': self.get_students,
            'get_exams': self.get_exams,
            'get_total_working_days': self.get_total_working_days,
            'get_subjects': self.get_subjects,
            'get_gradings':self.get_gradings,
            'get_date': self.get_date,
            'get_sections': self.get_sections,
            'get_marks': self.get_marks,
            'get_gpa': self.get_gpa,
            'show_paper': self.show_paper,
            'show_tut': self.show_tut,
            'show_obj': self.show_obj,
            'show_prac': self.show_prac,
            'get_converted_report': self.get_converted_report,
            'get_lg': self.get_lg,
            'get_exam_obtained_total': self.get_exam_obtained_total,
            'check_optional': self.check_optional,
            'num2serial': self.num2serial,
            'get_exam_result_lines': self.get_exam_result_lines,
            'get_student_result_line': self.get_student_result_line,
            'get_results': self.get_results,
            'half_round_up': self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up,
            'get_students_in_section': self.get_students_in_section,
            'show_merit_class': self.show_merit_class,
            'show_merit_group': self.show_merit_group,
            'show_merit_section': self.show_merit_section,
        }
