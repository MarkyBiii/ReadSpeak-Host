from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, ARRAY
from sqlalchemy.orm import relationship, backref
try:
    from database import Base
except ImportError:
    from backend.database import Base

metadata = Base.metadata
class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key = True, index = True)
    name = Column(String, index = True)
    email = Column(String, index = True)
    role = Column(String, index = True)
    hashed_password = Column(String)
    date_created = Column(DateTime, index = True)
    is_verified = Column(Boolean, index = True)
    date_verified = Column(DateTime, index = True)
    gender = Column(String, index = True)
    level = Column(Integer, ForeignKey("pronunciation_assessment_types.type_id"), nullable=True)
    section_id = Column(Integer, ForeignKey("sections.section_id", ondelete="CASCADE"), nullable=True)
    current_stage = Column(Integer, nullable=True)
    first_login = Column(Boolean, index = True)
    
class Stages(Base):
    __tablename__ = 'stages'
    stage_id = Column(Integer, primary_key=True, index=True)
    stage_name = Column(String,index=True)
    level_requirement = Column(Integer, ForeignKey("pronunciation_assessment_types.type_id"), nullable=True)
    stage_sequence = Column(Integer, index=True)
    pronunciation_assessment_id = Column(Integer, ForeignKey("pronunciation_assessments.assessment_id"), nullable=True)
    comp_assessment_id = Column(Integer, ForeignKey("comprehension_assessments.comp_assessment_id"), nullable=True)
    pronunciation_assessment = relationship("PronunciationAssessment", backref="stage_pronunciation", uselist=False)
    comprehension_assessment = relationship("ComprehensionAssessment", backref="stage_comprehension", uselist=False)
    
class Sections(Base):
    __tablename__ = 'sections'
    section_id = Column(Integer, primary_key = True, index = True)
    section_name = Column(String, index = True)
    
class PronunciationAssessment(Base):
    __tablename__ = 'pronunciation_assessments'
    
    assessment_id = Column(Integer, primary_key = True, index = True)
    assessment_title = Column(String, index = True)
    text_content = Column(String, index = True)
    text_html = Column(String, index = True) #added column
    raw_phoneme_content = Column(ARRAY(String, dimensions=1), index = True)
    phoneme_content = Column(ARRAY(String, dimensions=1), index = True)
    teacher_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    assessment_type = Column(Integer, ForeignKey("pronunciation_assessment_types.type_id"), nullable=True)
    

class PronunciationAssessmentType(Base):
    __tablename__ = 'pronunciation_assessment_types'
    
    type_id = Column(Integer, primary_key = True, index = True)
    type_name = Column(String, index = True)
    
class ComprehensionAssessmentType(Base):
    __tablename__ = 'comprehension_assessment_types'
    
    type_id = Column(Integer, primary_key = True, index = True)
    type_name = Column(String, index = True)

class ComprehensionAssessment(Base):
    __tablename__ = 'comprehension_assessments'
    
    comp_assessment_id = Column(Integer, primary_key = True, index = True)
    assessment_title = Column(String, index = True)
    assessment_type = Column(Integer, ForeignKey("comprehension_assessment_types.type_id"), nullable=True)
    text_content = Column(String, index = True)
    text_html = Column(String, index = True)

class ComprehensionAssessmentQuestion(Base):
    __tablename__ = 'comprehension_assessment_questions'
    
    comp_assessment_question_id = Column(Integer, primary_key = True, index = True)
    comp_assessment_id = Column(Integer, ForeignKey("comprehension_assessments.comp_assessment_id", ondelete='CASCADE'), nullable=True)
    assessment = relationship("ComprehensionAssessment", backref=backref('children', passive_deletes=True))
    question_text = Column(String, index = True)    

class ComprehensionAssessmentQuestionChoices(Base):
    __tablename__ = 'comprehension_assessment_choices'
    
    comp_assessment_choice_id = Column(Integer, primary_key = True, index = True)
    comp_assessment_question_id = Column(Integer, ForeignKey("comprehension_assessment_questions.comp_assessment_question_id", ondelete='CASCADE'), nullable=True)
    question = relationship("ComprehensionAssessmentQuestion", backref=backref('children', passive_deletes=True))
    choice_text = Column(String, index = True)
    is_correct = Column(Boolean, index = True)  

class PracticeWords(Base):
    __tablename__ = 'practice_words'
    
    practice_id = Column(Integer, primary_key = True, index = True)
    student_id = Column(Integer, ForeignKey("users.user_id"))
    assessment_id = Column(Integer, ForeignKey("pronunciation_assessments.assessment_id"))
    words = Column(ARRAY(String), index = True)
    date_added = Column(DateTime, index=True)
    is_completed = Column(Boolean, default=False, index = True)
    raw_phoneme_content = Column(ARRAY(String, dimensions=1), index = True)
    
class PracticeWordSubmissionHistory(Base):
    __tablename__ = 'practice_submission_history'
    history_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.user_id"))
    practice_id = Column(Integer, ForeignKey("practice_words.practice_id"))
    phoneme_output = Column(ARRAY(String), index=True)
    score = Column(Float, index=True)
    date_taken = Column(DateTime, index=True)
    audio_url = Column(String, index=True)
    audio_public_id = Column(String, index=True)
    raw_phoneme_output = Column(ARRAY(String), index=True)
    duration = Column(Float, index=True)
    
class AssessmentHistory(Base):
    __tablename__ = 'phoneme_assessment_history'
    
    history_id = Column(Integer, primary_key = True, index = True)
    student_id = Column(Integer, ForeignKey("users.user_id"), nullable = True)
    assessment_id = Column(Integer, ForeignKey("pronunciation_assessments.assessment_id"))
    raw_phoneme_output = Column(ARRAY(String), index = True)
    phoneme_output = Column(ARRAY(String), index = True)
    score = Column(Float, index = True)
    date_taken = Column(DateTime, index = True)
    audio_url = Column(String, index=True)
    audio_public_id = Column(String, index=True)
    stage_id = Column(Integer, ForeignKey("stages.stage_id"), nullable=True)
    duration = Column(Float, index=True)

class ComprehensionAssessmentHistory(Base):
    __tablename__ = 'comprehension_assessment_history'
    
    history_id = Column(Integer, primary_key = True, index = True)
    student_id = Column(Integer, ForeignKey("users.user_id"), nullable = True)
    assessment_id = Column(Integer, ForeignKey("comprehension_assessments.comp_assessment_id"))
    answers = Column(ARRAY(Integer), index = True)
    score = Column(Float, index = True)
    date_taken = Column(DateTime, index = True) 
    stage_id = Column(Integer, ForeignKey("stages.stage_id"), nullable=True)

class ExpiredTokens(Base):
    __tablename__ = 'expired_tokens'
    
    token_id = Column(Integer, primary_key = True, index = True)
    token_string = Column(String, index=True)