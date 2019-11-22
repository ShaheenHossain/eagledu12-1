# -*- coding: utf-8 -*-

from datetime import datetime
import time
import pandas as pd
from eagle import fields, models,api


class examEvaluation(models.AbstractModel):
    _name = 'report.education_exam.report_exam_evaluation'

    def get_all_subjects(self,section,result_exam_lines):
        result_lines=self.env['education.exam.results.new'].search([
            ('exam_result_line','in',[line.id for line in result_exam_lines]),
            ('class_id','=',section.id)])
        all_subjects=result_lines.mapped('subject_line.subject_id')
        return all_subjects
    def get_mark_type_for_subjects(self,subject_id,exam_lines):
        ## if any merk =0 , should not show in evaluation
        show_fields=[]
        subject_rules=self.env['exam.subject.pass.rules'].search([('subject_id','=',subject_id.id),('result_exam_line','in',[exam.id for exam in exam_lines])])
        tut_field=subject_rules.mapped('tut_mark')
        for val in tut_field:
            if val >0:
                if 'tut' not in show_fields:
                    show_fields.append('tut')
        subj_field=subject_rules.mapped('subj_mark')
        for val in subj_field:
            if val > 0:
                if 'subj' not in show_fields:
                    show_fields.append('subj')
        obj_field=subject_rules.mapped('obj_mark')
        for val in obj_field:
            if val > 0:
                if 'obj' not in show_fields:
                    show_fields.append('obj')
        prac_field=subject_rules.mapped('prac_mark')
        for val in prac_field:
            if val > 0:
                if 'prac' not in show_fields:
                    show_fields.append('prac')
        return show_fields

    def get_subject_mark_types(self,all_subjects, result_exam_lines):
        mark_types={}
        mark_types['colum']=0
        for subject in all_subjects:
            mark_types[subject]={}
            line = self.get_mark_type_for_subjects(subject,result_exam_lines)
            mark_types[subject]['colum'] = 0
            mark_types[subject]['tut'] = 0
            mark_types[subject]['subj'] = 0
            mark_types[subject]['obj'] = 0
            mark_types[subject]['prac'] = 0
            for val in line:
                mark_types[subject][val]=1
                mark_types['colum']=mark_types['colum']+1
                mark_types[subject]['colum'] =mark_types[subject]['colum']+ 1
        return mark_types

    def get_max_paper_count(self,result_exam_lines):
        subject_rules=self.env['exam.subject.pass.rules'].search([('result_exam_line','in',[line.id for line in result_exam_lines])])
        max_paper=0
        self.rules = subject_rules
        for line in self.rules:
            if len(line.paper_ids)>max_paper:
                max_paper=len(line.paper_ids)
        return max_paper

    def get_results(self,result_exam_lines,section):
        result_paper_line=self.env['results.paper.line'].search([('subject_line.result_id.exam_result_line','in',[line.id for line in result_exam_lines])])
        #                                    [results.paper.line].[result.subject.line.new]
        student=[]
        student_id=[]
        exam=[]
        exam_id=[]
        subject=[]
        subject_id=[]
        paper=[]
        result_line=[]
        subject_line=[]
        paper_line=[]

        for line in result_paper_line:
            student.append(line.subject_line.result_id.student_history)
            student_id.append(line.subject_line.result_id.student_history.id)
            exam.append(line.subject_line.result_id.exam_result_line)
            exam_id.append(line.subject_line.result_id.exam_result_line.id)
            subject_id.append(line.subject_line.subject_id.id)
            subject.append(line.subject_line.subject_id)
            subject_line.append(line.subject_line)
            paper.append(line.paper_id)
            paper_line.append(line)
            result_line.append(line.subject_line.result_id)
        data={'student':student,
              'studentId': student_id,
              'exam':exam,
              'examId':exam_id,
              'subject':subject,
              'subjectId':subject_id,
              'subjectline':subject_line,
              'paper':paper,
              'paperline':paper_line,
              'resultline':result_line}
        df=pd.DataFrame(data)
        return df
        # df1=df.groupby('student')
        # for index, row in df1:
        #     df_student=df[(df['student'] == index)]
        #     print(df_student)
    def get_student_result_line(self,student,result_exam_lines):
        results={}
        for line in result_exam_lines:
            result_line=self.env['education.exam.results.new'].search([
                ('exam_result_line','=',line.id),
                ('student_id','=',student.id)])
            results[line]={}
            results[line]['res']=result_line
            for subject in result_line.subject_line:
                results[line][subject.subject_id]={}
                results[line][subject.subject_id]['res']=subject
                for paper in subject.paper_ids:
                    results[line][subject.subject_id][paper]=paper
        return results

    def get_sections(self,object):
        sections=[]

        if object.section:
            return object.section
        elif object.level:
            section=self.env['education.class.division'].search([('class_id','=',object.level.id),('academic_year_id','=',object.academic_year.id)])
            return section
    def get_exams(self, objects):
        exams = []
        for exam in objects.exams:
           exams.extend(exam)

        return exams

    def get_students(self,object,section):
        if len(object.student)>0:
            students=self.env['education.class.history'].search([('id', '=', object.student.id)])
            return students
        else:
            students=self.env['education.class.history'].search([('class_id.id', '=', section.id)])
            return students
    def get_subjects(self, section,obj):
        subjs=self.env['education.syllabus'].search([('class_id','=',section.class_id.id),('academic_year','=',obj.academic_year.id)])
        subject_list=[]
        for subj in subjs:
            if len(subj.compulsory_for)>0:
                subject_list.append(subj)
            elif len(subj.optional_for)>0:
                subject_list.append(subj)
            elif len(subj.optional_for)>0:
                subject_list.append(subj)

        return subject_list

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
    def get_record_per_page(self,obj):
        return obj.record_per_page

    def get_converted_report(self,obj):
        if obj.report_type=='2' :
            converted_report=True
        else:
            converted_report=False
        return converted_report
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

    def get_date(self, date):
        date1 = datetime.strptime(date, "%Y-%m-%d")
        return str(date1.month) + ' / ' + str(date1.year)

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['education.exam.result.wizard'].browse(docids)

        return {
            'doc_model': 'education.exam.results',
            'docs': docs,
            'time': time,
            'get_students': self.get_students,
            'get_exams': self.get_exams,
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
            'half_round_up': self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up,
            'get_results': self.get_results,
            'get_exam_result_lines': self.get_exam_result_lines,
            'get_all_subjects': self.get_all_subjects,
            'get_student_result_line': self.get_student_result_line,
            'get_max_paper_count': self.get_max_paper_count,
            'num2serial': self.env['report.education_exam.report_exam_marksheet'].num2serial,
            'get_mark_type_for_subjects': self.get_mark_type_for_subjects,
            'get_subject_mark_types': self.get_subject_mark_types,
            'get_record_per_page': self.get_record_per_page,


        }
