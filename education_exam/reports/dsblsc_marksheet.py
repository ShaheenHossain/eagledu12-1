# -*- coding: utf-8 -*-

from datetime import datetime
import time, math
from eagle import fields, models,api
import pandas as pd
import numpy


class report_dsblsc_marksheet(models.AbstractModel):
    _name = 'report.education_exam.report_dsblsc_marksheet'

    def get_student_no(self,object):
        student_list = self.env['education.class.history'].search([('level.id', '=', object.level.id),
                                                                   ('academic_year_id.id', '=',
                                                                    object.academic_year.id)])
        return len(student_list)
    def get_student_in_section(self,student_history):
        student_list = self.env['education.class.history'].search([('class_id.id', '=', student_history.class_id.id)])
        return len(student_list)


    def get_students(self,objects):

        student=[]
        if objects.specific_student==True :
            student_list = self.env['education.class.history'].search([('student_id.id', '=', objects.student.id),('academic_year_id.id', '=', objects.academic_year.id)])
            for stu in student_list:
                student.extend(stu)
        elif objects.section:
            student_list=self.env['education.class.history'].search([('class_id.id', '=', objects.section.id)])
            for stu in student_list:
                student.extend(stu)
        elif objects.level:
            student_list = self.env['education.class.history'].search([('level.id', '=', objects.level.id),
                                                                       ('academic_year_id.id', '=', objects.academic_year.id)])
            for stu in student_list:
                student.extend(stu)

        return student

    def get_sections(self,object):
        sections=[]
        if object.section:
            return object.section
        elif object.level:
            section=self.env['education.class.division'].search([('class_id','=',object.level.id),('academic_year_id','=',object.academic_year.id)])
            return section
    def get_merit_class_display(self,object):
        if object.show_merit_class==True:
            return 1
    def get_merit_group_display(self,object):
        if object.show_merit_group==True:
            return 1

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

    def get_student_result(self,student,exam):
        student_result = self.env['education.exam.results.new'].search(
                    [('student_history.id', '=', student.id), ('exam_id', '=', exam.id)])
        return student_result

    def get_exams(self, objects):
        return objects.exams

    def get_exam_result(self,objects,student):
        exam_list={}
        for exam in objects.exams:
            result_type_count=0
            exam_list[exam.id]={}
            exam_list[exam.id]['result']=self.get_student_result(student,exam)
            if exam_list[exam.id]['result'].show_obj:
                result_type_count=result_type_count+1
            if exam_list[exam.id]['result'].show_tut:
                result_type_count=result_type_count+1
            if exam_list[exam.id]['result'].show_subj:
                result_type_count=result_type_count+1
            if exam_list[exam.id]['result'].show_prac:
                result_type_count=result_type_count+1
            exam_list[exam.id]['row_count'] = result_type_count
        return exam_list
    def get_total_working_days(self,exams):
        working_days=0
        for exam in exams:
            working_days=working_days+exam.total_working_days
        return working_days



    def get_results(self,objects):
        results={}
        students = self.get_students(objects)
        for exam in objects.exams:
            results[exam.id]={}
            for student in students:
                results[exam.id][student.id]={}
                student_results = self.env['education.exam.results.new'].search([('exam_id', '=', exam.id),('student_history','=',student.id)])
                results[exam.id][student.id]['result']=student_results
                for subject in student_results.subject_line:
                    results[exam.id][student.id][subject.subject_id.id]=subject
        return results

    def get_gradings(self,obj):
        grading=self.env['education.result.grading'].search([('id','>','0')],order='min_per desc',)
        grades=[]
        for grade in grading:
            grades.extend(grade)
        return grades


    def half_round_up(self,n, decimals=0):
        multiplier = 10 ** decimals
        number= math.floor(n * multiplier + 0.5) / multiplier
        if decimals==0:
            return round(number)
        else: return number
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

    def get_date(self,objects):
        date1 = datetime.now()
        return self.num2serial(int(date1.day)) + " " + date1.strftime('%B') + ' ' + str(date1.year)

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['education.exam.result.wizard'].browse(docids)
        return {
            'doc_model': 'education.exam.results',
            'docs': docs,
            'time': time,
            'get_date': self.get_date,
            'get_students': self.get_students,
            'get_exams': self.get_exams,
            'get_subjects': self.get_subjects,
            'get_gradings':self.get_gradings,
            'get_total_working_days':self.get_total_working_days,
            'num2serial': self.num2serial,
            'get_results': self.get_results,
            'get_sections': self.get_sections,
            'get_student_no': self.get_student_no,
            'get_student_in_section': self.get_student_in_section,
            'half_round_up': self.half_round_up,
            'get_merit_group_display': self.get_merit_group_display,
            'get_merit_class_display': self.get_merit_class_display,
        }

class report_dsblsc_marksheet_converted(models.AbstractModel):
    _name = 'report.education_exam.report_dsblsc_marksheet_converted'


    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['education.exam.result.wizard'].browse(docids)
        return {
            'doc_model': 'education.exam.results',
            'docs': docs,
            'time': time,
            'get_students': self.env['report.education_exam.report_dsblsc_marksheet'].get_students,
            'get_exams': self.env['report.education_exam.report_dsblsc_marksheet'].get_exams,
            'get_subjects': self.env['report.education_exam.report_dsblsc_marksheet'].get_subjects,
            'get_gradings':self.env['report.education_exam.report_dsblsc_marksheet'].get_gradings,
            'num2serial': self.env['report.education_exam.report_dsblsc_marksheet'].num2serial,
            'get_results': self.env['report.education_exam.report_dsblsc_marksheet'].get_results,
            'get_total_working_days': self.env['report.education_exam.report_dsblsc_marksheet'].get_total_working_days,
            'get_sections': self.env['report.education_exam.report_dsblsc_marksheet'].get_sections,
            'get_student_no': self.env['report.education_exam.report_dsblsc_marksheet'].get_student_no,
            'get_student_in_section': self.env['report.education_exam.report_dsblsc_marksheet'].get_student_in_section,
            'half_round_up': self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up,
            'get_converted_report': self.env['report.education_exam.report_exam_evaluation'].get_converted_report,
            'get_merit_group_display': self.env['report.education_exam.report_dsblsc_marksheet'].get_merit_group_display,
            'get_merit_class_display': self.env['report.education_exam.report_dsblsc_marksheet'].get_merit_class_display,
        }
class acdemicTranscripts(models.AbstractModel):
    _name = 'report.education_exam.report_dsblsc_evaluation'

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['education.exam.result.wizard'].browse(docids)
        return {
            'doc_model': 'education.exam.results',
            'docs': docs,
            'time': time,
            'get_students': self.env['report.education_exam.report_dsblsc_marksheet'].get_students,
            'get_exams': self.env['report.education_exam.report_dsblsc_marksheet'].get_exams,
            'get_subjects': self.env['report.education_exam.report_dsblsc_marksheet'].get_subjects,
            'get_gradings':self.env['report.education_exam.report_dsblsc_marksheet'].get_gradings,
            'num2serial': self.env['report.education_exam.report_dsblsc_marksheet'].num2serial,
            'get_results': self.env['report.education_exam.report_dsblsc_marksheet'].get_results,
            'get_sections': self.env['report.education_exam.report_dsblsc_marksheet'].get_sections,
        }
