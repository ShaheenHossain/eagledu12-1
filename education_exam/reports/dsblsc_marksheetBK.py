# -*- coding: utf-8 -*-

from datetime import datetime
import time
from eagle import fields, models,api
import pandas as pd
import numpy


class acdemicTranscripts(models.AbstractModel):
    _name = 'report.education_exam.report_dsblsc_marksheet'
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

    def get_exams(self, objects):
        obj = []
        for object in objects.exams:
           obj.extend(object)

        return obj

    def get_results(self,student, exam):
        results=self.env['education.exam.results.new'].search([('student_history','=',student),('exam_id','=',exam)])
        return results
    def get_paper_field(self,result_line):
        for subject in result_line.subject_line:
            count_paper=0
            for paper in subject.paper_ids:
                count_paper=count_paper+1
            if count_paper>1:
                return True
        return False


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
            'num2serial': self.num2serial,
            'get_students': self.get_students,
            'get_exams': self.get_exams,
            'get_results': self.get_results,
        }
