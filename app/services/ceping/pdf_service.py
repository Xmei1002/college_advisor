# app/services/pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import json
import os
import time
from flask import current_app

class PdfService:
    """PDF报告生成服务"""
    
    def __init__(self):
        # 注册字体
        self._register_fonts()
        
        # 设置样式
        self.styles = self._create_styles()
        
        # 创建输出目录
        base_dir = current_app.root_path
        self.output_dir = os.path.join(base_dir, 'static', 'reports')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _register_fonts(self):
        """注册字体"""
        try:
            # 使用项目根目录的绝对路径
            base_dir = current_app.root_path
            font_path = os.path.join(base_dir, 'static', 'fonts', 'msyh.ttf')
            bold_font_path = os.path.join(base_dir, 'static', 'fonts', 'msyhbd.ttf')
            
            # 检查文件是否存在
            if os.path.exists(font_path) and os.path.exists(bold_font_path):
                pdfmetrics.registerFont(TTFont('msyh', font_path))
                pdfmetrics.registerFont(TTFont('msyhbd', bold_font_path))
                self.default_font = 'msyh'
                self.default_bold_font = 'msyhbd'
                print(f"字体加载成功: {font_path}")
            else:
                print(f"字体文件不存在: {font_path}")
                # 使用fallback字体
                self.default_font = 'Helvetica'
                self.default_bold_font = 'Helvetica-Bold'
        except Exception as e:
            print(f"字体加载失败: {str(e)}")
            self.default_font = 'Helvetica'
            self.default_bold_font = 'Helvetica-Bold'
            
    def _create_styles(self):
        """创建样式"""
        # 获取基础样式
        base_styles = getSampleStyleSheet()
        
        # 创建自己的样式字典，避免冲突
        styles = {}
        
        # 添加自定义样式(使用不同名称)
        styles['CN_Title'] = ParagraphStyle(
            name='CN_Title',
            fontName='msyhbd',
            fontSize=24,
            leading=32,
            alignment=1,
            spaceAfter=20
        )
        
        styles['CN_Heading1'] = ParagraphStyle(
            name='CN_Heading1',
            fontName='msyhbd',
            fontSize=18,
            leading=25,
            spaceAfter=10
        )
        
        styles['CN_Heading2'] = ParagraphStyle(
            name='CN_Heading2',
            fontName='msyhbd',
            fontSize=16,
            leading=22,
            spaceAfter=8
        )
        
        styles['CN_Heading3'] = ParagraphStyle(
            name='CN_Heading3',
            fontName='msyhbd',
            fontSize=14,
            leading=20,
            spaceAfter=6
        )
        
        styles['CN_Normal'] = ParagraphStyle(
            name='CN_Normal',
            fontName='msyh',
            fontSize=12,
            leading=20,
            spaceAfter=6
        )
        
        styles['CN_Cover'] = ParagraphStyle(
            name='CN_Cover',
            fontName='msyhbd',
            fontSize=36,
            leading=45,
            alignment=1,
            spaceAfter=30
        )
        
        return styles
    
    def generate_mbti_report(self, answer, student):
        """生成MBTI测评报告"""
        from app.models.ceping_mbti_leixing import CepingMbtiLeixing
        
        # 解析结果
        jieguo = json.loads(answer.jieguo)
        
        # 计算人格类型
        leixing = ""
        if jieguo['I']['count'] >= jieguo['E']['count']:
            leixing += 'I'
        else:
            leixing += 'E'
            
        if jieguo['N']['count'] >= jieguo['S']['count']:
            leixing += 'N'
        else:
            leixing += 'S'
            
        if jieguo['F']['count'] >= jieguo['T']['count']:
            leixing += 'F'
        else:
            leixing += 'T'
            
        if jieguo['P']['count'] >= jieguo['J']['count']:
            leixing += 'P'
        else:
            leixing += 'J'
        
        # 获取类型详情
        type_info = CepingMbtiLeixing.query.filter_by(name=leixing).first()
        
        # 创建PDF文件
        filename = f"MBTI_{student.name}_{answer.id}_{int(time.time())}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # 构建PDF内容
        story = []
        
        # 添加封面、前言、目录等内容
        self._add_mbti_cover(story, student, answer)
        story.append(PageBreak())
        
        self._add_mbti_preface(story)
        story.append(PageBreak())
        
        self._add_mbti_toc(story)
        story.append(PageBreak())
        
        self._add_mbti_introduction(story)
        story.append(PageBreak())
        
        self._add_mbti_results(story, jieguo, leixing, type_info)
        story.append(PageBreak())
        
        self._add_mbti_tips(story)
        
        # 构建并保存PDF
        doc.build(story)
        
        return filepath

    def _add_mbti_cover(self, story, student, answer):
        """添加MBTI报告封面"""
        title = '性格能力测评'
        subtitle = 'Personality and ability evaluation report'
        
        story.append(Paragraph(title, self.styles['CN_Cover']))
        story.append(Paragraph(subtitle, self.styles['CN_Title']))
        story.append(Spacer(1, 50*mm))
        
        # 学生信息表格
        student_data = [
            ['姓名:', student.name],
            ['学校:', student.school or ''],
            ['报告时间:', time.strftime('%Y-%m-%d', time.localtime(answer.addtime))]
        ]
        student_table = Table(student_data, colWidths=[80, 200])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'msyh'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(student_table)
    
    def _add_mbti_preface(self, story):
        """添加MBTI报告前言"""
        story.append(Paragraph('前言', self.styles['CN_Title']))
        story.append(Paragraph('''
            性格能力测评采用当今世界上应用最广泛的性格测试工具之一MBTI作为基础研发。MBTI被翻译成近20种世界主要语言，每年的使用者多达千万。据有关统计，世界500强公司中有92%引入了MBTI测试，应用于员工的MBTI测试，可以帮助员工自我发展及提升组织绩效。
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            探索自我，性格能力测评可以帮助了解：我是什么性格？我适合什么职业？我的性格优势和劣势是什么？性格能力测评可以更好的帮你了解自我、从而做出最适合你的职业选择，更容易获取事业上的成功。
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            性格能力测评系统是启明星高考为解决考生的迷茫，家长老师的困惑，让考生都能选择适合自己的科目，正确做出职业生涯规划，经过多年研究及开发，针对我省高考现状，结合大学生职业规划调查报告，参考大学生就业情况，为高考学生量身打造的。
        ''', self.styles['CN_Normal']))
    
    def _add_mbti_toc(self, story):
        """添加MBTI报告目录"""
        story.append(Paragraph('目录 Catalog', self.styles['CN_Title']))
        
        toc_data = [
            ['Part.1 性格能力测评体系介绍', '1'],
            ['Part.2 性格能力测评结果分析', '2'],
            ['Part.3 温馨提示', '4']
        ]
        toc_table = Table(toc_data, colWidths=[400, 40])
        toc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'msyh'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(toc_table)
    
    def _add_mbti_introduction(self, story):
        """添加MBTI测评体系介绍"""
        story.append(Paragraph('Part.1 性格能力测评体系介绍', self.styles['CN_Heading1']))
        story.append(Paragraph('''
            MBTI从能量的来源方向、信息收集的方式、做决定时候的偏好、以及生活态度四个方面对人格进行考量，其中每个一部分又分两个倾向，分别是：能量来源-内向(I)、外向(E)；信息收集-感觉(S)、直觉(N)；决定偏好-思考(T)、情感(F)；生活态度-感知(P)、判断(J)。MBTI性格评估主要应用于职业规划、团队建设、人际交往、教育等方面。
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            心理学认为，"性格"是一种个体内部的行为倾向，它具有整体性、结构性、持久稳定性等特点，是每个人特有的，可以对个人外显的行为、态度提供统一的、内在的解释。MBTI的人格类型分为四个维度，每个维度上有两个方向，一共八个方面，对应八种人格特点，具体如下：
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('我们与世界相互作用方式：外向Extraversion (E)---内向Introversion (I)', self.styles['CN_Normal']))
        story.append(Paragraph('我们获得信息的主要方式：感觉Sensing (S)---直觉iNtuition (N)', self.styles['CN_Normal']))
        story.append(Paragraph('我们的决策方式：思考Thinking (T)---情感Feeling (F)', self.styles['CN_Normal']))
        story.append(Paragraph('我们的做事方式：判断Judging (J)---感知Perceiving (P)', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            性格能力评估系统可以帮助我们认清自己，但是并不剥夺我们认知的自由，把结论强加于人；MBTI可以有效地评估我们的性格类型；引导我们建立自信，信任并理解他人；进而在职业定位和发展、人际关系等领域为我们提供帮助。
        ''', self.styles['CN_Normal']))
    
    def _add_mbti_results(self, story, jieguo, leixing, type_info):
        """添加MBTI测评结果分析"""
        story.append(Paragraph('Part.2 性格能力测评结果分析', self.styles['CN_Heading1']))
        story.append(Paragraph('职业性格分析', self.styles['CN_Heading2']))
        story.append(Paragraph('根据您测评结果进行分析，您的职业性格结果如下所示：', self.styles['CN_Normal']))
        
        # 分数条
        dimensions = [
            {'key': 'E', 'label': '外向(E)', 'opposing_key': 'I', 'opposing_label': '内向(I)'},
            {'key': 'S', 'label': '感觉(S)', 'opposing_key': 'N', 'opposing_label': '直觉(N)'},
            {'key': 'T', 'label': '思考(T)', 'opposing_key': 'F', 'opposing_label': '情感(F)'},
            {'key': 'J', 'label': '判断(J)', 'opposing_key': 'P', 'opposing_label': '知觉(P)'}
        ]
        
        for dim in dimensions:
            # 获取维度分数
            key = dim['key']
            opposing_key = dim['opposing_key']
            
            score1 = jieguo[key]['count']
            score2 = jieguo[opposing_key]['count']
            total = score1 + score2
            
            if total == 0:
                continue
            
            # 计算比例
            percent1 = int((score1 / total) * 100) if total > 0 else 0
            percent2 = 100 - percent1
            
            # 创建分数条
            table_data = [[dim['label'], str(score1), dim['opposing_label'], str(score2)]]
            dim_table = Table(table_data, colWidths=[100, 50, 100, 50])
            dim_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'msyh'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('ALIGN', (3, 0), (3, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(dim_table)
            
            # 添加进度条
            progress_data = [[' ' * 20, ' ' * 20]]
            progress_table = Table(progress_data, colWidths=[percent1 * 3, percent2 * 3])
            progress_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.blue),
                ('BACKGROUND', (1, 0), (1, 0), colors.orange),
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('LINEBEFORE', (0, 0), (0, 0), 1, colors.black),
                ('LINEAFTER', (1, 0), (1, 0), 1, colors.black),
            ]))
            story.append(progress_table)
            story.append(Spacer(1, 10*mm))
        
        # 得分汇总表格
        story.append(Paragraph('维度得分汇总:', self.styles['CN_Heading3']))
        score_data = [
            ['性格维度', '得分', '倾向'],
            ['我们如何与世界相互作用', max(jieguo['E']['count'], jieguo['I']['count']), 
                '外向' if jieguo['E']['count'] > jieguo['I']['count'] else '内向'],
            ['我们关注哪些事物', max(jieguo['S']['count'], jieguo['N']['count']), 
                '感觉' if jieguo['S']['count'] > jieguo['N']['count'] else '直觉'],
            ['我们如何思考问题', max(jieguo['T']['count'], jieguo['F']['count']), 
                '思考' if jieguo['T']['count'] > jieguo['F']['count'] else '情感'],
            ['我们如何做事', max(jieguo['J']['count'], jieguo['P']['count']), 
                '判断' if jieguo['J']['count'] > jieguo['P']['count'] else '知觉']
        ]
        
        score_table = Table(score_data, colWidths=[200, 100, 100])
        score_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'msyh'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        story.append(score_table)
        
        # 性格类型分析
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph(f'您的职业性格是 {leixing}，具体特征如下：', self.styles['CN_Normal']))
        
        # 性格特质
        if type_info:
            story.append(Paragraph('性格特质', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.xingge.replace('\n', '<br/>'), self.styles['CN_Normal']))
            
            story.append(Paragraph('优势分析', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.youshi.replace('\n', '<br/>'), self.styles['CN_Normal']))
            
            story.append(Paragraph('劣势分析', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.lueshi.replace('\n', '<br/>'), self.styles['CN_Normal']))
            
            story.append(Paragraph('职业领域', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.zhiye.replace('\n', '<br/>'), self.styles['CN_Normal']))
            
            story.append(Paragraph('典型职业', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.dianxing.replace('\n', '<br/>'), self.styles['CN_Normal']))

    def _add_mbti_tips(self, story):
        """添加MBTI测评温馨提示"""
        story.append(Paragraph('Part.3 温馨提示', self.styles['CN_Heading1']))
        story.append(Paragraph('亲爱的同学：', self.styles['CN_Normal']))
        story.append(Paragraph('''
            性格能力测评报告展示的是你的性格倾向，而不是你的知识、技能、经验。只要你是认真、真实地填写了测试问卷，那么通常情况下你都能得到一个确实和你的性格相匹配的类型。希望你能从中或多或少地获得一些有益的信息。
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            MBTI提供的性格类型描述仅供测试者确定自己的性格类型之用，性格类型没有好坏，只有不同。每一种性格特征都有其价值和优点，也有缺点和需要注意的地方。清楚地了解自己的性格优劣势，有利于更好地发挥自己的特长，而尽可能的在为人处事中避免自己性格中的劣势，更好地和他人相处，更好地作重要的决策。
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            您在答题时，难免受到当时的答题环境、心情等各种因素的影响。如果您觉得最终的测试结果与您的实际情况不是很符合，可能有如下几种原因：
        ''', self.styles['CN_Normal']))
        
        tips = [
            '1. 请回忆您作答时候的情形, 您是根据自己的第一反应做出的回答吗？',
            '2. 您是否受到自己应该选择什么或者别人希望您选择什么的影响？',
            '3. 您答题的时候心情是不是比较放松？',
            '4. 您是否对绝大多数题都进行了认真做答？',
            '5. 您答题的时候有没有受到干扰？'
        ]
        
        for tip in tips:
            story.append(Paragraph(tip, self.styles['CN_Normal']))
        
        story.append(Paragraph('您可以在适当的时候选择重新进行测试。', self.styles['CN_Normal']))
        story.append(Paragraph('希望性格能力测评报告能为您的选择提供有价值的参考。', self.styles['CN_Normal']))
    
    def generate_job_report(self, answer, student):
        """生成职业兴趣测评报告"""
        from app.models.ceping_job_leixing import CepingJobLeixing
        from app.models.ceping_job_zhuanye import CepingJobZhuanye
        from app.models.ceping_job_timu import CepingJobTimu
        
        # 获取题目信息
        timu = CepingJobTimu.query.order_by(CepingJobTimu.tid).all()
        timu_dict = {str(q.id): {"tid": q.tid, "wid": q.wid} for q in timu}
        
        # 解析答案
        answer_data = json.loads(answer.answer)
        
        # 计算结果
        count = {
            "S": {'count': 0, 'color': 'green'},
            "R": {'count': 0, 'color': 'green'},
            "C": {'count': 0, 'color': 'green'},
            "E": {'count': 0, 'color': 'green'},
            "I": {'count': 0, 'color': 'green'},
            "A": {'count': 0, 'color': 'green'}
        }
        
        # 统计各维度得分
        for question_id, answer_value in answer_data.items():
            if question_id in timu_dict and answer_value == "A":
                wid = timu_dict[question_id]["wid"]
                count[wid]['count'] += 1
        
        # 设置颜色
        for key in count:
            if key in answer.jieguo:
                count[key]['color'] = 'orange'
        
        # 获取类型详情
        type_info = CepingJobLeixing.query.filter_by(title=answer.jieguo).first()
        
        # 获取推荐专业
        recommended_majors = CepingJobZhuanye.query.filter_by(title=answer.jieguo).all()
        
        # 创建PDF文件
        filename = f"职业兴趣_{student.name}_{answer.id}_{int(time.time())}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # 构建PDF内容
        story = []
        
        # 添加封面、前言、目录等内容
        self._add_job_cover(story, student, answer)
        story.append(PageBreak())
        
        self._add_job_preface(story)
        story.append(PageBreak())
        
        self._add_job_toc(story)
        story.append(PageBreak())
        
        self._add_job_introduction(story)
        story.append(PageBreak())
        
        self._add_job_results(story, count, answer.jieguo, type_info, recommended_majors)
        story.append(PageBreak())
        
        self._add_job_tips(story)
        
        # 构建并保存PDF
        doc.build(story)
        
        return filepath
    
    def _add_job_cover(self, story, student, answer):
        """添加职业兴趣报告封面"""
        title = '职业兴趣测评报告'
        subtitle = 'Professional Interest Assessment Report'
        
        story.append(Paragraph(title, self.styles['CN_Cover']))
        story.append(Paragraph(subtitle, self.styles['CN_Title']))
        story.append(Spacer(1, 50*mm))
        
        # 学生信息表格
        student_data = [
            ['姓名:', student.name],
            ['学校:', student.school or ''],
            ['报告时间:', time.strftime('%Y-%m-%d', time.localtime(answer.addtime))]
        ]
        student_table = Table(student_data, colWidths=[80, 200])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'msyh'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(student_table)
    
    def _add_job_preface(self, story):
        """添加职业兴趣报告前言"""
        story.append(Paragraph('前言', self.styles['CN_Title']))
        story.append(Paragraph('''
            高考是影响考生人生发展的一次重要事件，历来都是学生本人和家长乃至全社会最为重视的事情。高考作为基础教育的"指挥棒"，自从1977年恢复高考以来，关于高考的变革都影响着教育的基本方向和教学策略。《中国职业技术教育》中曾对大学生入校后的关于对专业了解程度的调查显示：对自己所学专业与社会职业要求不清楚的学生占92.2%，选择专业时家长做主的占71.2%，选择专业时听取同学、亲戚意见的占55.3%，对自己不了解的占51.5%，对社会不了解的占62.1%，对职业不了解的占89.2%。从这些数据看来大学生入学时对所学专业与社会职业的了解是有限的，或者说是盲目的。人的一生里总要面临各种抉择，而高考选择专业可能是整个人生的抉择中最有影响、最具挑战性的一个。每逢高考志愿填报时，考生迷茫、家长困惑、老师谨慎。
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            职业兴趣测评系统是启明星高考为解决考生的迷茫，家长老师的困惑，让考生都能选择适合自己的专业，正确做出职业生涯规划，经过多年研究及开发，针对我省高考现状，结合大学生职业规划调查报告，参考大学生就业情况，为高考学生量身打造的。
        ''', self.styles['CN_Normal']))
    
    def _add_job_toc(self, story):
        """添加职业兴趣报告目录"""
        story.append(Paragraph('目录 Catalog', self.styles['CN_Title']))
        
        toc_data = [
            ['Part.1 职业兴趣测评体系介绍', '1'],
            ['Part.2 职业兴趣测评结果分析', '3'],
            ['Part.3 温馨提示', '6']
        ]
        toc_table = Table(toc_data, colWidths=[400, 40])
        toc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'msyh'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(toc_table)
    
    def _add_job_introduction(self, story):
        """添加职业兴趣测评体系介绍"""
        story.append(Paragraph('Part.1 职业兴趣测评体系介绍', self.styles['CN_Heading1']))
        story.append(Paragraph('''
            职业兴趣测评是以美国心理学家Holland的职业兴趣理论为基础，同时在题目内容设计、常模选取方面结合了考生的实际情况而开发的专业测评工具。通过该系统，可以帮助测试者相对精确地了解自身的个体特点和职业特点之间的匹配关系，同时为测评者在进行职业规划时，提供客观的参考依据分析你的兴趣爱好，推荐你感兴趣和适合的职业作为参考。
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('''
            职业兴趣与职业环境的匹配是决定成功的最重要的因素之一。人们通常倾向于选择与自我职业兴趣类型匹配的职业环境，如具有艺术倾向的个体通常希望在艺术型的职业环境中工作，以便最大限度地发挥个人的潜能。Holland从兴趣的角度出发来探索职业指导问题，根据人格与环境交互作用的观点，把人分为六大类：现实型(R)、研究型(I)、艺术型(A)、社会型(S)、企业型(E)、传统型(C)。
        ''', self.styles['CN_Normal']))
        
        # 添加Holland六种类型介绍
        holland_types = [
            ('现实型(R)', '喜欢具体、实际的工作，喜欢户外活动，有操作机械设备的能力，适合工程技术、农业、制造等领域。'),
            ('研究型(I)', '喜欢思考问题，进行研究和分析，解决复杂问题，适合科学研究、医疗、技术分析等领域。'),
            ('艺术型(A)', '喜欢从事艺术、音乐、文学等富有创造性和表现力的活动，适合设计、表演、写作等领域。'),
            ('社会型(S)', '喜欢与人交往，帮助他人，具有教导、培训和咨询的能力，适合教育、社会服务、医疗护理等领域。'),
            ('企业型(E)', '善于组织、领导和说服他人，喜欢从事管理和销售，适合管理、销售、法律等领域。'),
            ('传统型(C)', '喜欢按部就班、有序和规则的工作，善于处理数据，适合会计、行政、档案管理等领域。')
        ]
        
        for h_type, desc in holland_types:
            story.append(Paragraph(f'{h_type}', self.styles['CN_Heading3']))
            story.append(Paragraph(desc, self.styles['CN_Normal']))
    
    def _add_job_results(self, story, count, job_type, type_info, recommended_majors):
        """添加职业兴趣测评结果分析"""
        story.append(Paragraph('Part.2 职业兴趣测评结果分析', self.styles['CN_Heading1']))
        story.append(Paragraph('根据您测评结果进行分析，您的职业兴趣结果如下所示：', self.styles['CN_Normal']))
        
        # 创建分数条
        holland_types = [
            {'key': 'A', 'label': 'A艺术型'},
            {'key': 'S', 'label': 'S社会型'},
            {'key': 'E', 'label': 'E企业型'},
            {'key': 'C', 'label': 'C传统型'},
            {'key': 'R', 'label': 'R实际型'},
            {'key': 'I', 'label': 'I研究型'}
        ]
        
        # 分数展示
        for holland in holland_types:
            key = holland['key']
            score = count[key]['count']
            color_name = count[key]['color']
            color_value = colors.green if color_name == 'green' else colors.orange
            
            # 创建表格来展示分数条
            table_data = [[holland['label'], str(score)]]
            bar_width = min(score * 10, 300) # 根据分数设置条形宽度
            bar_table = Table(table_data, colWidths=[100, bar_width])
            bar_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, 0), 'msyh'),
                ('FONTNAME', (1, 0), (1, 0), 'msyh'),
                ('FONTSIZE', (0, 0), (1, 0), 12),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (1, 0), 'MIDDLE'),
                ('BACKGROUND', (1, 0), (1, 0), color_value),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ]))
            story.append(bar_table)
            story.append(Spacer(1, 5*mm))
        
        # 职业兴趣代码
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f'您的职业兴趣（霍兰德）代码是：{job_type}', self.styles['CN_Heading2']))
        
        # 得分表格
        score_data = [
            ['职业类型', '艺术型(A)', '社会型(S)', '企业型(E)', '传统型(C)', '实际型(R)', '研究型(I)'],
            ['分值', str(count['A']['count']), str(count['S']['count']), str(count['E']['count']), 
             str(count['C']['count']), str(count['R']['count']), str(count['I']['count'])]
        ]
        
        score_table = Table(score_data)
        score_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'msyh'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        story.append(score_table)
        
        # 类型说明
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph('职业兴趣满分为20分', self.styles['CN_Normal']))
        
        # 添加分页符
        story.append(PageBreak())
        
        # 类型详情
        if type_info:
            story.append(Paragraph('职业兴趣测评详细分析', self.styles['CN_Heading2']))
            
            story.append(Paragraph('职业兴趣倾向', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.zyxqqx.replace('\n', '<br/>'), self.styles['CN_Normal']))
            
            story.append(Paragraph('性格倾向', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.xgqx.replace('\n', '<br/>'), self.styles['CN_Normal']))
            
            story.append(Paragraph('职业领域', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.zyly.replace('\n', '<br/>'), self.styles['CN_Normal']))
            
            story.append(Paragraph('典型职业', self.styles['CN_Heading3']))
            story.append(Paragraph(type_info.dxzy.replace('\n', '<br/>'), self.styles['CN_Normal']))
        
        # 添加分页符
        story.append(PageBreak())
        
        # 推荐专业
        story.append(Paragraph('适合专业分析', self.styles['CN_Heading2']))
        story.append(Paragraph('''
            根据您在职业兴趣倾向、职业性格测评的得分，通过数据统计和分析，将其与常模的数据进行比较，结合国家教育部最新公布的普通高等院校专业目录，我们为您提供匹配度最高的专业大类，专业大类招生是高校招生未来的趋势，根据教育部专业目录要求，专业大类是学科门类下设的一级学科，未来学生选择的专业是专业大类下设的二级学科。不同高校的专业建设情况及人才培养需求不同，因而同一专业大类下设的专业数量和专业方向也不尽相同。在此提醒家长和学生在专业选择上，务必明确目标院校中是否开设意愿就读的专业及您的孩子是否可以报考该专业！
        ''', self.styles['CN_Normal']))
        
        story.append(Paragraph('推荐专业大类', self.styles['CN_Heading3']))
        majors_text = '、'.join([major.zymc for major in recommended_majors])
        story.append(Paragraph(majors_text, self.styles['CN_Normal']))
    
    def _add_job_tips(self, story):
        """添加职业兴趣测评温馨提示"""
        story.append(Paragraph('Part.3 温馨提示', self.styles['CN_Heading1']))
        story.append(Paragraph('''
            希望我们的测评报告会对您的专业选择提供有效的帮助。本测试仅作为考生在高考专业选择时的一种参考，并不代表我们推荐的适合测试者的专业可作为唯一的专业报考依据，本测评系统的研发单位不为个人的最终选择承担责任，除本报告外，建议您在报考时参考多方面的因素：
        ''', self.styles['CN_Normal']))
        
        tips = [
            '1. 适当考虑自身性格、气质、价值观等因素，选择专业。',
            '2. 审视自己的家庭经济状况（个别院校、专业学费较高）。',
            '3. 考虑自己的身体状况（部分专业对考生的身体素质有特殊要求，如公安类院校需要体能测试）。',
            '4. 考虑自己对地域环境的适应性（不同的地域，其社会风俗人情、生活饮食习惯、消费水平和气候等都有很大差异）。',
            '5. 选专业先了解专业真正含义（就业前景、就业率、就业方向、供职部门、行业发展等因素）。',
            '6. 权衡学校和专业，二者兼顾。（全方位了解学校和专业，权衡自己对专业和学校的要求）。',
            '7. 考虑社会的发展对所选专业的对应行业领域的影响。',
            '8. 考虑报考政策和录取政策。'
        ]
        
        for tip in tips:
            story.append(Paragraph(tip, self.styles['CN_Normal']))