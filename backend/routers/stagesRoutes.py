from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_db
import models
from pydantic import BaseModel
from typing import List, Optional, Annotated 
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(
    prefix="/stages",
    tags=["Stages"]
)

db_dependency = Annotated[Session, Depends(get_db)]

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

class StageCreate(BaseModel):
  stage_id: Optional[int] = None
  stage_name: str
  level_requirement: int
  stage_sequence: int
  pronunciation_assessment_id: Optional[int] = None
  comp_assessment_id: Optional[int] = None

class Attempt(BaseModel):
    history_id: int
    student_id: int
    assessment_id: int
    score: float
    date_taken: datetime
    attempt_type: str

class StageAttempts(BaseModel):
    stage_id: int
    stage_name: str
    attempts: List[Attempt]

@router.post("/")
async def create_stage(stage: StageCreate, db: db_dependency):
  db_stage = models.Stages(
    stage_name = stage.stage_name,
    level_requirement = stage.level_requirement,
    stage_sequence = stage.stage_sequence,
    pronunciation_assessment_id = stage.pronunciation_assessment_id,
    comp_assessment_id = stage.comp_assessment_id
  )
  db.add(db_stage)
  db.commit()
  return("Stage Created")
  
@router.get("/{level}")
async def get_stages_by_level(level: int, db: db_dependency):
  result = db.query(models.Stages).filter(models.Stages.level_requirement == level).order_by(models.Stages.stage_sequence).all()
  return result

@router.put("/{levelReq}") 
async def edit_stage(levelReq:int,stage_update: List[StageCreate], db:db_dependency):
  edited_stages = []
  for stages in stage_update:
      db_stage = db.query(models.Stages).filter(models.Stages.stage_id == stages.stage_id).first()
      if not db_stage:
        db_newStage = models.Stages(
          stage_name = stages.stage_name,
    level_requirement = stages.level_requirement,
    stage_sequence = stages.stage_sequence,
    pronunciation_assessment_id = stages.pronunciation_assessment_id,
    comp_assessment_id = stages.comp_assessment_id
        )
        db.add(db_newStage)
        db.commit()
        edited_stages.append(db_newStage.stage_id)
      else:
        db_stage.stage_name = stages.stage_name
        db_stage.level_requirement = stages.level_requirement
        db_stage.stage_sequence = stages.stage_sequence
        db_stage.pronunciation_assessment_id = stages.pronunciation_assessment_id
        db_stage.comp_assessment_id = stages.comp_assessment_id
        edited_stages.append(db_stage.stage_id)
  delete_stages = [val for val, in db.query(models.Stages.stage_id).filter(models.Stages.level_requirement == levelReq) if val not in edited_stages]
  for stages in delete_stages:
    db_stage = db.query(models.Stages).filter(models.Stages.stage_id == stages).first()
    db.delete(db_stage)
    db.commit()
  student_progress = db.query(models.User).filter(models.User.level == levelReq).all()
  current_stage_count = db.query(models.Stages).filter(models.Stages.level_requirement == levelReq).count()
  for progress in student_progress:
      if progress.current_stage > current_stage_count:
          progress.current_stage = current_stage_count
      elif progress.current_stage != 1:  # Optionally reset if stages are reordered/deleted
          progress.current_stage = 1
      db.add(progress)
  db.commit()
  return("Stage Edited and Student Progress Updated")

@router.get("/assessment/pronunciation/{stageId}")
async def get_stage_assessment_pronunciation(stageId: int, db:db_dependency):
  db_assessment = db.query(models.PronunciationAssessment).join(models.Stages).filter(models.Stages.stage_id == stageId).first()
  if not db_assessment:
    raise HTTPException(status_code=404, detail='Assessment not found')
  return {'assessment':db_assessment, 'stage_id':stageId}

@router.get("/assessment/comprehension/{stageId}")
async def get_stage_assessment_pronunciation(stageId: int, db:db_dependency):
  db_stage = db.query(models.Stages).filter(models.Stages.stage_id == stageId).first()
  if not db_stage or not db_stage.comp_assessment_id:
    raise HTTPException(status_code=404, detail='Assessment not found for this stage')
  db_assessment = db.query(models.ComprehensionAssessment).filter(models.ComprehensionAssessment.comp_assessment_id == db_stage.comp_assessment_id).first()
  if not db_assessment:
      raise HTTPException(status_code=404, detail='Assessment is not found')
  questions = db.query(models.ComprehensionAssessmentQuestion).filter(models.ComprehensionAssessmentQuestion.comp_assessment_id == db_assessment.comp_assessment_id).all()
  questionArr = []
  for question in questions:
    choiceArr = []
    choices = (db.query(models.ComprehensionAssessmentQuestionChoices).filter(models.ComprehensionAssessmentQuestionChoices.comp_assessment_question_id == question.comp_assessment_question_id).all())
    for choice in choices:
      currChoice = ComprehensionChoices(choice_id= choice.comp_assessment_choice_id, choice_text= choice.choice_text, is_correct=choice.is_correct)
      choiceArr.append(currChoice)
    currQuestion = ComprehensionQuestion(question_id=question.comp_assessment_question_id, question_text=question.question_text, choices=choiceArr) 
    questionArr.append(currQuestion)
  result = ComprehensionAssessment(title=db_assessment.assessment_title,assessment_type=db_assessment.assessment_type, assessment_id=db_assessment.comp_assessment_id, questions=questionArr, story=db_assessment.text_html)  
  
  return {'assessment':result, 'stage_id':stageId}

@router.get("/student/progress/{student_id}")
async def get_student_stage_progress(student_id: int, db: db_dependency):
  student = db.query(models.User).filter(models.User.user_id == student_id).first()
  if not student:
      raise HTTPException(status_code=404, detail="Student not found")
  level_id = student.level
  # Get all stages for the student's level
  all_stages = db.query(models.Stages).filter(models.Stages.level_requirement == level_id).order_by(models.Stages.stage_sequence).all()
  # Get all pronunciation attempts
  pronunciation_attempts = db.query(models.AssessmentHistory).filter(models.AssessmentHistory.student_id == student_id).order_by(models.AssessmentHistory.date_taken.desc()).all()
  # Get all comprehension attempts
  comprehension_attempts = db.query(models.ComprehensionAssessmentHistory).filter(models.ComprehensionAssessmentHistory.student_id == student_id).order_by(models.ComprehensionAssessmentHistory.date_taken.desc()).all()
  # Combine attempts and group by stage
  all_attempts = []
  for attempt in pronunciation_attempts:
      all_attempts.append({
          "stage_id": attempt.stage_id,
          "attempt": Attempt(
              history_id=attempt.history_id,
              student_id=attempt.student_id,
              assessment_id=attempt.assessment_id,
              score=attempt.score,
              date_taken=attempt.date_taken,
              attempt_type="Pronunciation"
          )
      })
  for attempt in comprehension_attempts:
      all_attempts.append({
          "stage_id": attempt.stage_id,
          "attempt": Attempt(
              history_id=attempt.history_id,
              student_id=attempt.student_id,
              assessment_id=attempt.assessment_id,
              score=attempt.score,
              date_taken=attempt.date_taken,
              attempt_type="Comprehension"
          )
      })
  # Group attempts by stage
  stage_grouped_attempts = {}
  for item in all_attempts:
      stage_id = item["stage_id"]
      attempt = item["attempt"]
      if stage_id not in stage_grouped_attempts:
          stage_grouped_attempts[stage_id] = {"attempts": []}
      stage_grouped_attempts[stage_id]["attempts"].append(attempt)
  # Build the result list with all stages
  result = []
  for stage in all_stages:
      stage_id = stage.stage_id
      stage_name = stage.stage_name
      attempts = stage_grouped_attempts.get(stage_id, {}).get("attempts", [])
      result.append(StageAttempts(stage_id=stage_id, stage_name=stage_name, attempts=attempts))
  return result

