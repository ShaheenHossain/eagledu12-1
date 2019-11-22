# -*- coding: utf-8 -*-

from datetime import datetime
import time
from eagle import fields, models,api
import pandas as pd


class examEvaluation(models.AbstractModel):
    _name = 'report.education_exam.report_merit_list'

    def get_sections(self,object):
        sections=[]

        if object.section:
            return object.section
        elif object.level:
            section=self.env['education.class.division'].search([('class_id','=',object.level.id),('academic_year_id','=',object.academic_year.id)])
            return section

    def get_students(self,section):

        students=self.env['education.class.history'].search([('class_id.id', '=', section.id)])

        return students
    def get_converted_report(self,object):
        if object.report_type==1:
            return 0
        else:
            return 1
    def get_merit_class_display(self,object):
        if object.show_merit_class:
            return 1
        else: return 0
    def get_merit_group_display(self,object):
        if object.show_merit_group:
            return 1
        else: return 0


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

    def get_results(self,objects):
        section=self.get_sections(objects)
        exam_result_lines=self.get_exam_result_lines(objects)
        results={}
        students = self.get_students(section)
        for student in students:
            results[student]={}
            for line in exam_result_lines:
                result_line=self.env['education.exam.results.new'].search([('student_history','=',student.id),
                                                                           ('exam_result_line','=',line.id)])
                results[student][line]=result_line

        return results

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['education.exam.result.wizard'].browse(docids)

        return {
            'doc_model': 'education.exam.results',
            'docs': docs,
            'time': time,
            'get_exam_result_lines': self.get_exam_result_lines,
            'get_results': self.get_results,
            'get_students': self.get_students,
            'get_sections': self.get_sections,
            'get_converted_report': self.get_converted_report,
            'get_merit_group_display': self.get_merit_group_display,
            'get_merit_class_display': self.get_merit_class_display,
            'half_round_up': self.env['report.education_exam.report_dsblsc_marksheet'].half_round_up,
        }
