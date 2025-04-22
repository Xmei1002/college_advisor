from app.models.base import Base
from app.models.user import User
from app.models.studentProfile import Student,AcademicRecord
from app.models.planner_info import PlannerInfo
from app.models.collegePreference import CollegePreference
# from app.models.careerPreference import CareerPreference
from app.models.prompt_template import PromptTemplate

# ZWH相关表模型导入
from app.models.zwh_areas import ZwhAreas
from app.models.zwh_divisions import ZwhDivisions
from app.models.zwh_scorerank import ZwhScorerank
from app.models.zwh_specialties_type import ZwhSpecialtiesType

# 分数线表
from app.models.zwh_xgk_fenshuxian_2021 import ZwhXgkFenshuxian2021
from app.models.zwh_xgk_fenshuxian_2022 import ZwhXgkFenshuxian2022
from app.models.zwh_xgk_fenshuxian_2023 import ZwhXgkFenshuxian2023
from app.models.zwh_xgk_fenshuxian_2024 import ZwhXgkFenshuxian2024
from app.models.zwh_xgk_fenshuxian_2025 import ZwhXgkFenshuxian2025

# 其他ZWH表
from app.models.zwh_xgk_fenzu_2025 import ZwhXgkFenzu2025
from app.models.zwh_xgk_picixian import ZwhXgkPicixian
from app.models.zwh_xgk_yuanxiao_2025 import ZwhXgkYuanxiao2025
from app.models.zwh_xgk_zhuanye_2025 import ZwhXgkZhuanye2025

from app.models.student_volunteer_plan import StudentVolunteerPlan, VolunteerCollege, VolunteerSpecialty

# AI聊天
from app.models.messages import Message
from app.models.conversations import Conversation
from app.models.llm_configuration import LLMConfiguration