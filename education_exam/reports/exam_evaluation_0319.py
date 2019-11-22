# -*- coding: utf-8 -*-

from datetime import datetime
import time
from eagle import fields, models,api
import pandas as pd
import numpy


class acdemicTranscripts(models.AbstractModel):
    _name = 'report.education_exam.report_dsblsc_tabulation'

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

    def get_subjects(self, students):
        subject_list = []
        for student in students:
            for subj in student.compulsory_subjects:
                if subj.subject_id not in subject_list:
                    subject_list.append(subj.subject_id)
            for subj in student.optional_subjects:
                if subj.subject_id not in subject_list:
                    subject_list.append(subj.subject_id)
            for subj in student.selective_subjects:
                if subj.subject_id not in subject_list:
                    subject_list.append(subj.subject_id)
        return subject_list

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

    def get_date(self, date):
        date1 = datetime.strptime(date, "%Y-%m-%d")
        return str(date1.month) + ' / ' + str(date1.year)

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['academic.transcript'].browse(docids)
        return {
            'doc_model': 'education.exam.results',
            'docs': docs,
            'time': time,
            'get_students': self.get_students,
            'get_exams': self.get_exams,
            'get_subjects': self.get_subjects,
            'get_gradings':self.get_gradings,
            'num2serial': self.num2serial,
            'get_results': self.get_results,
            'get_sections': self.get_sections,
        }
