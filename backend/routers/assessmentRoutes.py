from fastapi import APIRouter, Depends, HTTPException, UploadFile,Form, File
from phoneme import wordOffsetGet, textToPhoneme, audioToPhoneme, groupPhonemes, processor, processor2, model, model2, sr
from dependencies import get_db
import models
from pydantic import BaseModel
from typing import List, Optional, Annotated 
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader

class Assessment(BaseModel):
  title: str
  input_text: str
  html_text: str
  phoneme_text: List
  teacher_id: int
  assessment_type: int

class ComprehensionChoices(BaseModel):
  choice_id: Optional[int] = 0
  choice_text: str
  is_correct: bool

class ComprehensionQuestion(BaseModel):
  question_id: Optional[int] = 0
  question_text: str
  choices: List[ComprehensionChoices]
  
class ComprehensionAssessment(BaseModel):
  assessment_id: Optional[int] = 0
  title: str
  assessment_type: int
  story: str
  questions: List[ComprehensionQuestion]
  
class ComprehensionAssessmentList(BaseModel):
  comp_assessment_id: Optional[int] = None
  assessment_title: Optional[str] = None
  assessment_type: Optional[int] = None
  assessment_type_name: Optional[str] = None

class PronunciationAssessmentList(BaseModel):
  assessment_id: Optional[int] = None
  assessment_title: Optional[str] = None
  assessment_type: Optional[int] = None
  assessment_type_name: Optional[str] = None

router = APIRouter(
    prefix="/assessments",
    tags=["Assessments"]
)

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/phoneme")
async def create_phoneme_assessment(
  db: db_dependency, 
  title: str = Form(...),
  input_text: str = Form(...),
  html_text: str = Form(...),
  teacher_id: int = Form(...),
  assessment_type: int = Form(...), 
  audio_file: Optional[UploadFile] = File(None)):
  
  phoneme_text, raw_phones = textToPhoneme(input_text)
  audio_url = None
  audio_public_id = None
  
  if(audio_file):
    upload_result = cloudinary.uploader.upload(audio_file.file, resource_type="auto")
    audio_url = upload_result["secure_url"]
    audio_public_id = upload_result["public_id"]
    
  db_question = models.PronunciationAssessment(assessment_title = title, 
                                               text_content = input_text, 
                                               text_html = html_text, 
                                               phoneme_content = phoneme_text, 
                                               assessment_type = assessment_type, 
                                               raw_phoneme_content = raw_phones, 
                                               teacher_id = teacher_id, 
                                               audio_url = audio_url,
                                               audio_public_id = audio_public_id)

  db.add(db_question)
  db.commit()
  # db.refresh(db_question)
  # tasks.append(task)
  
@router.post("/comprehension/")
async def create_comprehension_assessment(assessment: ComprehensionAssessment, db:db_dependency):
  db_assessment = models.ComprehensionAssessment(assessment_title = assessment.title, assessment_type = assessment.assessment_type, text_html = assessment.story)
  db.add(db_assessment)
  db.commit()
  for questions in assessment.questions:
    db_question = models.ComprehensionAssessmentQuestion(comp_assessment_id = db_assessment.comp_assessment_id, question_text = questions.question_text)
    db.add(db_question)
    db.commit()
    for choices in questions.choices:
      db_choice = models.ComprehensionAssessmentQuestionChoices(comp_assessment_question_id = db_question.comp_assessment_question_id, choice_text = choices.choice_text, is_correct = choices.is_correct)
      db.add(db_choice)
      db.commit()

@router.get("/words/all/{student_id}")
async def get_student_practice_words(student_id: int, db: db_dependency):
  db_practice = db.query(models.PracticeWords).filter(models.PracticeWords.student_id == student_id, 
                                                      models.PracticeWords.is_completed == False).all()
  if not db_practice:
    raise HTTPException(status_code=404, detail='No Practice Words')
  return db_practice

@router.get("/words/{word_id}")
async def get_specific_practice_word(word_id: int, db:db_dependency):
  db_practice = db.query(models.PracticeWords).filter(models.PracticeWords.practice_id == word_id).first()
  if not db_practice:
    raise HTTPException(status_code=404, detail='No Practice Words')
  return db_practice

@router.get("/phoneme/type/")
async def get_phoneme_assessment_types(db:db_dependency):
  result = db.query(models.PronunciationAssessmentType).all()
  if not result:
    raise HTTPException(status_code=404, detail='No Submissions')
  return result

@router.get("/comprehension/type/")
async def get_phoneme_assessment_types(db:db_dependency):
  result = db.query(models.ComprehensionAssessmentType).all()
  if not result:
    raise HTTPException(status_code=404, detail='No Submissions')
  return result

@router.get("/{assessment_id}")
async def get_specific_phoneme_assessments(assessment_id: int, db: db_dependency):
  result = db.query(models.PronunciationAssessment).filter(models.PronunciationAssessment.assessment_id == assessment_id).first()
  if not result:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  return result

@router.get("/", response_model=list[PronunciationAssessmentList])
async def get_all_phoneme_assessments(db: db_dependency):
  assessments = db.query(models.PronunciationAssessment).all()
  if not assessments:
    raise HTTPException(status_code=404, detail='Assessment is not found') 
  result = []
  for assessment in assessments:
    type = db.query(models.PronunciationAssessmentType).join(models.PronunciationAssessment).filter(models.PronunciationAssessment.assessment_type == assessment.assessment_type).first()
    result.append(PronunciationAssessmentList(assessment_id=assessment.assessment_id, assessment_type=assessment.assessment_type, assessment_title=assessment.assessment_title, assessment_type_name=type.type_name))
  return result

@router.get("/comprehension/", response_model=list[ComprehensionAssessmentList])
async def get_all_comprehension_assessments(db: db_dependency):
  assessments = db.query(models.ComprehensionAssessment).all()
  if not assessments:
    raise HTTPException(status_code=404, detail='Assessment is not found') 
  result = []
  for assessment in assessments:
    type = db.query(models.ComprehensionAssessmentType).join(models.ComprehensionAssessment).filter(models.ComprehensionAssessment.assessment_type == assessment.assessment_type).first()
    result.append(ComprehensionAssessmentList(comp_assessment_id=assessment.comp_assessment_id, assessment_type=assessment.assessment_type, assessment_title=assessment.assessment_title, assessment_type_name=type.type_name))
  return result

@router.get("/comprehension/{assessment_id}", response_model=ComprehensionAssessment)
async def get_specific_comprehension_assessments(assessment_id: int, db: db_dependency):
  assessment = db.query(models.ComprehensionAssessment).filter(models.ComprehensionAssessment.comp_assessment_id == assessment_id).first()
  if not assessment:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  questions = db.query(models.ComprehensionAssessmentQuestion).filter(models.ComprehensionAssessmentQuestion.comp_assessment_id == assessment.comp_assessment_id).all()
  questionArr = []
  for question in questions:
    choiceArr = []
    choices = (db.query(models.ComprehensionAssessmentQuestionChoices).filter(models.ComprehensionAssessmentQuestionChoices.comp_assessment_question_id == question.comp_assessment_question_id).all())
    for choice in choices:
      currChoice = ComprehensionChoices(choice_id= choice.comp_assessment_choice_id, choice_text= choice.choice_text, is_correct=choice.is_correct)
      choiceArr.append(currChoice)
    currQuestion = ComprehensionQuestion(question_id=question.comp_assessment_question_id, question_text=question.question_text, choices=choiceArr) 
    questionArr.append(currQuestion)
  result = ComprehensionAssessment(title=assessment.assessment_title,assessment_type=assessment.assessment_type, assessment_id=assessment.comp_assessment_id, questions=questionArr, story=assessment.text_html)
  # result.title = assessment.assessment_title
  # result.assessment_id = assessment.comp_assessment_id
  # result.questions = questionArr
  # print(result.model_dump_json())
  return result

@router.get("/types/pronunciation/{type_id}")
async def get_pronunciation_assessment_type(type_id: int, db: db_dependency):
  result = db.query(models.PronunciationAssessmentType).filter(models.PronunciationAssessmentType.type_id == type_id).first()
  if not result:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  return result

@router.get("/types/comprehension/{type_id}")
async def get_comprehension_assessment_type(type_id: int, db: db_dependency):
  result = db.query(models.ComprehensionAssessmentType).filter(models.ComprehensionAssessmentType.type_id == type_id).first()
  if not result:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  return result

@router.get("/pronunciation/type/{type_id}")
async def get_pronunciation_assessments_of_type(type_id: int, db: db_dependency):
  result = db.query(models.PronunciationAssessment).filter(models.PronunciationAssessment.assessment_type == type_id).all()
  if not result:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  return result

@router.get("/comprehension/type/{type_id}")
async def get_comprehension_assessments_of_type(type_id: int, db: db_dependency):
  result = db.query(models.ComprehensionAssessment).filter(models.ComprehensionAssessment.assessment_type == type_id).all()
  if not result:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  return result
  

@router.put("/edit/{assessment_id}")
async def edit_assessment(
  db: db_dependency, 
  assessment_id: int, 
  title: str = Form(...),
  input_text: str = Form(...),
  html_text: str = Form(...),
  assessment_type: int = Form(...), 
  audio_file: Optional[UploadFile] = File(None)):
  phoneme_text, raw_phones = textToPhoneme(input_text)
  audio_url = None
  audio_public_id = None
  
  db_assessment = db.query(models.PronunciationAssessment).filter(models.PronunciationAssessment.assessment_id == assessment_id).first()
  if not db_assessment:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  if(audio_file):
    upload_result = cloudinary.uploader.upload(audio_file.file, resource_type="auto")
    if(upload_result):
        cloudinary.uploader.destroy(db_assessment.audio_public_id, resource_type="video")
    audio_url = upload_result["secure_url"]
    audio_public_id = upload_result["public_id"]
    db_assessment.audio_public_id = audio_public_id
    db_assessment.audio_url = audio_url
  db_assessment.assessment_title = title
  db_assessment.raw_phoneme_content = raw_phones
  db_assessment.text_content = input_text
  db_assessment.phoneme_content = phoneme_text
  db_assessment.assessment_type = assessment_type
  db_assessment.text_html = html_text
  db_assessment.assessment_type = assessment_type
  db.commit()
  
@router.put("/delete/{assessment_id}")
async def delete_assessment(assessment_id: int, db: db_dependency):
  stage_exists = db.query(models.Stages).filter(models.Stages.pronunciation_assessment_id == assessment_id).first()
  if stage_exists:
    raise HTTPException(status_code=400, detail="Cannot delete assessment, it is assigned to a stage.")
  
  db_assessment = db.query(models.PronunciationAssessment).filter(models.PronunciationAssessment.assessment_id == assessment_id).first()

  if not db_assessment:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  cloudinary.uploader.destroy(db_assessment.audio_public_id, resource_type="video")
  db.delete(db_assessment)
  db.commit()

@router.put("/comprehension/edit/{assessment_id}")
async def edit_comprehension_assessment(assessment_id: int, assessment_update: ComprehensionAssessment, db: db_dependency):
  db_assessment = db.query(models.ComprehensionAssessment).filter(models.ComprehensionAssessment.comp_assessment_id == assessment_id).first()
  if not db_assessment:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  db_assessment.assessment_title = assessment_update.title
  db_assessment.assessment_type = assessment_update.assessment_type
  db_assessment.text_html = assessment_update.story
  #get ids of all questions and choices from db and input, then compare, then all ids are stored in separate arrays, loop to delete
  edited_questions = []
  edited_choices = []
  for questions in assessment_update.questions:
    db_question = db.query(models.ComprehensionAssessmentQuestion).filter(models.ComprehensionAssessmentQuestion.comp_assessment_question_id == questions.question_id).first()
    if not db_question:
      db_question = models.ComprehensionAssessmentQuestion(comp_assessment_id = db_assessment.comp_assessment_id, question_text = questions.question_text)
      db.add(db_question)
      db.commit()
      edited_questions.append(db_question.comp_assessment_question_id)
    else:
      db_question.question_text = questions.question_text
      edited_questions.append(db_question.comp_assessment_question_id)
      db.commit()
    for choices in questions.choices:
      db_choice = db.query(models.ComprehensionAssessmentQuestionChoices).filter(models.ComprehensionAssessmentQuestionChoices.comp_assessment_choice_id == choices.choice_id).first()
      if not db_choice:
        db_choice = models.ComprehensionAssessmentQuestionChoices(comp_assessment_question_id = db_question.comp_assessment_question_id, choice_text = choices.choice_text, is_correct = choices.is_correct)
        db.add(db_choice)
        db.commit()
        edited_choices.append(db_choice.comp_assessment_choice_id)
      else:
        db_choice.choice_text = choices.choice_text
        db_choice.is_correct = choices.is_correct
        edited_choices.append(db_choice.comp_assessment_choice_id)
        db.commit()
  delete_questions = [val for val, in db.query(models.ComprehensionAssessmentQuestion.comp_assessment_question_id).filter(models.ComprehensionAssessmentQuestion.comp_assessment_id == assessment_id) if val not in edited_questions]
  delete_choices = [val for val, in db.query(models.ComprehensionAssessmentQuestionChoices.comp_assessment_choice_id).join(models.ComprehensionAssessmentQuestion).filter(models.ComprehensionAssessmentQuestion.comp_assessment_id == assessment_id) if val not in edited_choices]
  for choices in delete_choices:
    db_choice = db.query(models.ComprehensionAssessmentQuestionChoices).filter(models.ComprehensionAssessmentQuestionChoices.comp_assessment_choice_id == choices).first()
    db.delete(db_choice)
    db.commit()
  for questions in delete_questions:
    db_question = db.query(models.ComprehensionAssessmentQuestion).filter(models.ComprehensionAssessmentQuestion.comp_assessment_question_id == questions).first()
    db.delete(db_question)
    db.commit()
    
  db.commit()

@router.put("/comprehension/delete/{assessment_id}")
async def delete_comprehension_assessment(assessment_id: int, db: db_dependency):
  stage_exists = db.query(models.Stages).filter(models.Stages.comp_assessment_id == assessment_id).first()
  if stage_exists:
    raise HTTPException(status_code=400, detail="Cannot delete comprehension assessment, it is assigned to a stage.")

  db_assessment = db.query(models.ComprehensionAssessment).filter(models.ComprehensionAssessment.comp_assessment_id == assessment_id).first()
  if not db_assessment:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  db.delete(db_assessment)
  db.commit()