from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from dependencies import get_db
import models
import librosa
from phoneme import wordOffsetGet, textToPhoneme, audioToPhoneme, groupPhonemes, processor, processor2, model, model2, sr
from pydantic import BaseModel
from typing import List, Optional, Annotated 
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
from jiwer import wer
from datetime import datetime, timezone
from starlette.responses import JSONResponse
import numpy as np
from scipy.signal import medfilt
import soundfile as sf
import scipy.fftpack as fft
import pytz
import re
import noisereduce as nr
router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"]
)

db_dependency = Annotated[Session, Depends(get_db)]

philippine_timezone = pytz.timezone("Asia/Manila")

class ComprehensionChoices(BaseModel):
  choice_id: Optional[int] = 0
  choice_text: str
  is_correct: bool

class ComprehensionQuestion(BaseModel):
  question_id: Optional[int] = 0
  question_text: str
  choices: List[ComprehensionChoices]

class ComprehensionSubmission(BaseModel):
  student_id: Optional[int] = None
  assessment_id: int
  score: float
  answers_id: List[int]
  stage_id: int
  
class PhonemeSubmission(BaseModel):
  student_id: int
  history_id: int
  score: float
  assessment_id: int
  assessment_title: str
  text_content: str
  # text_html: str
  audio_url: str
  phoneme_content: List[str]
  phoneme_output: List[str]
  date_taken:datetime

class ComprehensionSubmissionHistory(BaseModel):
  student_id: int
  history_id: int
  score: float
  assessment_id: int
  assessment_title: str
  date_taken:datetime
  questions: List[ComprehensionQuestion]
  answers: List[int]

class StudentHistory(BaseModel):
  student_id: int
  history_id: int
  assessment_id: int
  score: float
  assessment_title: str
  date_taken: datetime

@router.post("/submit/phoneme/")
async def submit_phoneme_assessment(db: db_dependency, student_id: int,
  assessment_id: int,
  stage_id: int,
  file: UploadFile = File(...),
  file2: UploadFile = File(...)):
  #might be best to separate this into another function
  db_assessment = db.query(models.PronunciationAssessment).filter(models.PronunciationAssessment.assessment_id == assessment_id).first()
  if not db_assessment:
    raise HTTPException(status_code=404, detail='Assessment is not found')
  db_user = db.query(models.User).filter(models.User.user_id == student_id).first()
  if not db_user:
    raise HTTPException(status_code=404, detail='User is not found')
  # db_stage = db.query(models.Stages).filter(models.Stages.stage_sequence == db_user.current_stage, models.Stages.level_requirement ==db_user.level).first()
  db_stage = db.query(models.Stages).filter(models.Stages.stage_id == stage_id).first()
  if not db_stage or stage_id != db_stage.stage_id or db_stage.pronunciation_assessment_id != assessment_id:
    print(db_stage.stage_id)
    print(f"Assessment id: {db_stage.pronunciation_assessment_id}")
    print(f"User Current Stage: {db_user.current_stage}")
    print(f"User Level: {db_user.level}")

    raise HTTPException(status_code=400, detail='Stage requirements not met')
  try:
    text_phonemes = db_assessment.raw_phoneme_content
    input_values, _ = librosa.load(file.file, sr=sr)
    S_full, phase = librosa.magphase(librosa.stft(input_values))
    noise_power = np.mean(S_full[:, :int(sr*0.1)], axis=1)
    mask = S_full > noise_power[:, None]
    mask = mask.astype(float)
    mask = medfilt(mask, kernel_size=(1,5))
    S_clean = S_full * mask
    y_clean = librosa.istft(S_clean * phase)
    y_clean2 = nr.reduce_noise(y=input_values, sr=sr, stationary=True)
    inputsMedfilt = processor(y_clean, return_tensors="pt", padding=True)
    inputsNoFilter = processor(input_values, return_tensors="pt", padding=True)
    inputsNoiseReduce = processor(y_clean2, return_tensors="pt", padding=True)
    # inputs = processor(y_clean, return_tensors="pt", padding=True)
    phonem1, offset, predicted_phonemes = audioToPhoneme(inputsMedfilt)
    phonem2, offset2, predicted_phonemes2 = audioToPhoneme(inputsNoFilter)
    phonem3, offset3, predicted_phonemes3 = audioToPhoneme(inputsNoiseReduce)
    score_test1 = 1-wer(' '.join(text_phonemes), ' '.join(predicted_phonemes))
    score_test2 = 1-wer(' '.join(text_phonemes), ' '.join(predicted_phonemes2))
    score_test3 = 1-wer(' '.join(text_phonemes), ' '.join(predicted_phonemes3))
    best_score = max(score_test1, score_test2, score_test3)
    if best_score == score_test1:
        # best_method = "Median Filtering"
        word_offsets = wordOffsetGet(inputsMedfilt)
        audioPhonemes = phonem1
        char_offsets = offset
        transcription = predicted_phonemes
    elif best_score == score_test2:
        # best_method = "No Filter (Raw Audio)"
        word_offsets = wordOffsetGet(inputsNoFilter)
        audioPhonemes = phonem2
        char_offsets = offset2
        transcription = predicted_phonemes2
    elif best_score == score_test3:
        # best_method = "NoiseReduce"
        word_offsets = wordOffsetGet(inputsNoiseReduce)
        audioPhonemes = phonem3
        char_offsets = offset3
        transcription = predicted_phonemes3
    
    grouped_phonemes = groupPhonemes(audioPhonemes, word_offsets, char_offsets)
    duration = librosa.get_duration(y=input_values, sr=sr)
#     print(' '.join(transcription))
#     print(' '.join(text_phonemes))
    if best_score < 0:
      best_score = 0
    # print(score_test)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error processing audio file: {str(e)}")
  upload_result = cloudinary.uploader.upload(file2.file, resource_type="auto")
  db_submission = models.AssessmentHistory(
    student_id = student_id,
    assessment_id = assessment_id,
    phoneme_output =  grouped_phonemes,
    score = round(best_score*100, 2),
    date_taken = datetime.now(pytz.timezone("Asia/Manila")),
    audio_url = upload_result["secure_url"],
    raw_phoneme_output = transcription,
    audio_public_id = upload_result["public_id"],
    stage_id = stage_id,
    duration = duration
    )
  
  db.add(db_submission)
  db.commit()
  
  #stage_is_completed = check_stage_completion(student_id, db_stage, db)
  if round(best_score*100, 2)>=40 and db_user.current_stage == db_stage.stage_sequence:
    advance_stage(db_user, db)
  elif db_user.current_stage < db_stage.stage_sequence:
    raise HTTPException(status_code=400, detail='Stage requirements not met 1')
   
  practice_words = []
  practice_db = []
  expected_words = db_assessment.text_content.split(' ')
  expected_phonemes = db_assessment.phoneme_content
  student_words = grouped_phonemes 
  word_index = 0
  for expected_word in expected_words:
      if word_index < len(student_words) and word_index < len(expected_phonemes):
          expected_phoneme = expected_phonemes[word_index]
          student_phoneme = student_words[word_index]
          word_wer = wer(expected_phoneme, student_phoneme)
          if word_wer > 0.5 and len(expected_word) > 1:  #testing here
              practice_words.append(expected_word)
      word_index += 1

    # Add practice words if any
  existing_practice_words = [set(word.words)
                             for word in db.query(models.PracticeWords).filter(models.PracticeWords.student_id == student_id).all()]
  if practice_words:
      try:
        for word in practice_words:
          cleaned_word = clean_word(word)
          word_list = list(cleaned_word)
          word_set = set(word_list)
          # print(word_list)
          # print(word_set)
          if word_set in existing_practice_words:
            continue
          
          # existing_practice_word = db.query(models.PracticeWords).filter(
          #   models.PracticeWords.student_id == student_id,
          #   models.PracticeWords.assessment_id == assessment_id,
          #   models.PracticeWords.words == list(word_phonemes)
          # ).first()
          # if existing_practice_word:
          #   continue
          text, raw_phoneme = textToPhoneme(word) 
          create_practice_words_model = models.PracticeWords(
            student_id=student_id,
            assessment_id=assessment_id,
            words=word_list,
            date_added=datetime.now(pytz.timezone("Asia/Manila")),
            raw_phoneme_content = raw_phoneme
          )

          db.add(create_practice_words_model)
          
          db.commit()
          practice_db.append(create_practice_words_model.practice_id)
      except Exception as e:
          db.rollback()
          raise HTTPException(status_code=500, detail=f"An error occurred while adding practice words: {str(e)}")

    # Log and return response
  response_data = {
      "score": round(best_score * 100, 2),
      "audio_url": upload_result["secure_url"],
      "audio_id": upload_result["public_id"],
      "phoneme_output": grouped_phonemes,
      "transcription": transcription,
      "practice_words_added": practice_words,
      "practice_words_id": practice_db,
      "history_id": db_submission.history_id
  }

  # Return the response
  return JSONResponse(response_data)

def clean_word(word):
  return re.sub(r"[^\w\s'-]", '', word)

@router.post("/submit/comprehension/")
async def submit_comprehension_assessment(db: db_dependency, submission: ComprehensionSubmission):
  db_user = db.query(models.User).filter(models.User.user_id == submission.student_id).first()
  db_stage = db.query(models.Stages).filter(models.Stages.stage_id == submission.stage_id).first()
  if not db_user:
    raise HTTPException(status_code=404, detail='User is not found')
  db_submission = models.ComprehensionAssessmentHistory(
    student_id = submission.student_id,
    assessment_id = submission.assessment_id,
    answers = submission.answers_id,
    score = submission.score,
    date_taken = datetime.now(pytz.timezone("Asia/Manila")),
    stage_id = submission.stage_id
  )
  db.add(db_submission)
  db.commit()
  
  if(submission.score > 60) and db_user.current_stage == db_stage.stage_sequence:
    advance_stage(db_user, db)
  elif db_user.current_stage < db_stage.stage_sequence:
    raise HTTPException(status_code=400, detail='Stage requirements not met')
  
def check_stage_completion(student_id: int, stage: models.Stages, db:db_dependency) -> bool:
  if stage.pronunciation_assessment_id:
    db_complete = db.query(models.AssessmentHistory).filter(
      models.AssessmentHistory.student_id == student_id,
      models.AssessmentHistory.assessment_id == stage.pronunciation_assessment_id
    ).first()
    if not db_complete:
      return False
  
  if stage.comp_assessment_id:
    db_complete = db.query(models.ComprehensionAssessmentHistory).filter(
      models.ComprehensionAssessmentHistory.student_id == student_id,
      models.ComprehensionAssessmentHistory.assessment_id == stage.comp_assessment_id
    ).first()
    if not db_complete:
      return False
  return True

#add logic for no more next stage/100% completion
def advance_stage(user: models.User, db:db_dependency):
  # print(user.current_stage)
  db_next = db.query(models.Stages).filter(models.Stages.stage_sequence > user.current_stage).order_by(
    models.Stages.stage_sequence
  ).first()
  if db_next:
    user.current_stage = db_next.stage_sequence
  db.commit()

@router.post("/submit/practice/")
async def submit_practice_word(db: db_dependency,
  student_id: int,
  practice_id: int,
  file: UploadFile = File(...),
  file2: UploadFile = File(...),):
  
  db_practice = db.query(models.PracticeWords).filter(models.PracticeWords.practice_id == practice_id).first()
  if not db_practice:
    raise HTTPException(status_code=404, detail="Practice word not found.")
  
  text_phonemes = db_practice.raw_phoneme_content
  input_values, _ = librosa.load(file.file, sr=sr)
  
  S_full, phase = librosa.magphase(librosa.stft(input_values))
  noise_power = np.mean(S_full[:, :int(sr*0.1)], axis=1)
  mask = S_full > noise_power[:, None]
  mask = mask.astype(float)
  mask = medfilt(mask, kernel_size=(1,5))
  S_clean = S_full * mask
  y_clean = librosa.istft(S_clean * phase)
  
  inputs = processor(y_clean, return_tensors="pt", padding=True)
  audioPhonemes, char_offsets, transcription = audioToPhoneme(inputs)
  duration = librosa.get_duration(y=input_values, sr=sr)
  # print(text_phonemes)
  # print(transcription)
  score_test = 1 - wer(' '.join(text_phonemes), ' '.join(transcription))
  if score_test < 0:
    score_test = 0
  upload_result = cloudinary.uploader.upload(file2.file, resource_type="auto")
  
  db_submission = models.PracticeWordSubmissionHistory(
    student_id = student_id,
    practice_id = practice_id,
    phoneme_output = audioPhonemes,
    score = round(score_test*100, 2),
    date_taken = datetime.now(pytz.timezone("Asia/Manila")),
    audio_url = upload_result["secure_url"],
    audio_public_id = upload_result["public_id"],
    raw_phoneme_output = transcription,
    duration = duration
  )
  db.add(db_submission)
  if round(score_test * 100, 2) >= 50:
    db_practice.is_completed = True
    
  db.commit()
  
  return {'score': round(score_test*100, 2)}

@router.get("/practice/student/{student_id}")
async def get_student_practice_submissions(student_id:int, db: db_dependency):
  db_practice = db.query(models.PracticeWordSubmissionHistory).filter(models.PracticeWordSubmissionHistory.student_id == student_id).all()
  if not db_practice:
    raise HTTPException(status_code=404, detail='Submission is not found')
  return db_practice

@router.get("/practice/{sub_id}")
async def get_specific_practice_submission(sub_id: int, db: db_dependency) :
  db_submission = db.query(models.PracticeWordSubmissionHistory).filter(models.PracticeWordSubmissionHistory.history_id == sub_id).first()
  if not db_submission:
    raise HTTPException(status_code=404, detail='Submission is not found')
  db_practice = db.query(models.PracticeWords).filter(models.PracticeWords.practice_id == db_submission.practice_id).first()
  return {"submission":db_submission, "practice":db_practice}

@router.get("/{sub_id}/", response_model=PhonemeSubmission)
async def get_specific_submission(sub_id: int, db: db_dependency):
  history = db.query(models.AssessmentHistory).filter(models.AssessmentHistory.history_id == sub_id).first()
  assessment = db.query(models.PronunciationAssessment).join(models.AssessmentHistory).filter(models.AssessmentHistory.history_id == sub_id).first()
  if not history:
    raise HTTPException(status_code=404, detail='Submission is not found')
  date_taken_ph = history.date_taken.astimezone(philippine_timezone)
  result = PhonemeSubmission(student_id=history.student_id,  history_id=history.history_id, score=history.score, assessment_id=history.assessment_id,
                             assessment_title=assessment.assessment_title, text_content=assessment.text_content, 
                             audio_url=history.audio_url, phoneme_content=assessment.phoneme_content,
                            phoneme_output=history.phoneme_output, date_taken=date_taken_ph)
  return result

@router.get("/users/{userId}/", response_model=list[StudentHistory])
async def get_users_submission(userId: int, db: db_dependency):
  history = db.query(models.AssessmentHistory).filter(models.AssessmentHistory.student_id == userId).all()
  if not history:
    raise HTTPException(status_code=404, detail='No submissions found')
  result =[]
  for history in history:
    assessment = db.query(models.PronunciationAssessment).join(models.AssessmentHistory).filter(models.AssessmentHistory.student_id == userId, models.PronunciationAssessment.assessment_id == history.assessment_id).first()
    date_taken_ph = history.date_taken.astimezone(philippine_timezone)
    result.append(StudentHistory(student_id=userId, history_id=history.history_id, assessment_id=assessment.assessment_id, score=history.score, assessment_title=assessment.assessment_title, date_taken=date_taken_ph))
  return result

@router.get("/phonemes")
async def get_all_phoneme_submissions(db: db_dependency):
  result = db.query(models.AssessmentHistory).all()
  if not result:
    raise HTTPException(status_code=404, detail='Assessment is not found') 
  return result

@router.get("/comprehension")
async def get_all_comprehension_submissions(db: db_dependency):
  result = db.query(models.ComprehensionAssessmentHistory).all()
  if not result:
    raise HTTPException(status_code=404, detail='Assessment is not found') 
  return result

@router.get("/comprehension/{sub_id}/", response_model=ComprehensionSubmissionHistory)
async def get_specific_comprehension_submission(sub_id: int, db: db_dependency):
  history = db.query(models.ComprehensionAssessmentHistory).filter(models.ComprehensionAssessmentHistory.history_id == sub_id).first()
  assessment = db.query(models.ComprehensionAssessment).join(models.ComprehensionAssessmentHistory).filter(models.ComprehensionAssessmentHistory.history_id == sub_id).first()
  if not history:
    raise HTTPException(status_code=404, detail='Submission is not found')
  date_taken_ph = history.date_taken.astimezone(philippine_timezone)
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
  result = ComprehensionSubmissionHistory(student_id=history.student_id, 
                                          history_id=history.history_id, 
                                          score=history.score, 
                                          assessment_id=assessment.comp_assessment_id, 
                                          assessment_title=assessment.assessment_title, 
                                          date_taken=date_taken_ph, 
                                          questions=questionArr, 
                                          answers=history.answers)
  return result

@router.get("/comprehension/users/{userId}/",response_model=list[StudentHistory])
async def get_users_comprehension_submission(userId: int, db: db_dependency):
  history = db.query(models.ComprehensionAssessmentHistory).filter(models.ComprehensionAssessmentHistory.student_id == userId).all()
  if not history:
    raise HTTPException(status_code=404, detail='No submissions found')
  result =[]
  
  for history2 in history:
    assessment = db.query(models.ComprehensionAssessment).join(models.ComprehensionAssessmentHistory).filter(models.ComprehensionAssessmentHistory.student_id == userId, models.ComprehensionAssessment.comp_assessment_id == history2.assessment_id).first()
    date_taken_ph = history2.date_taken.astimezone(philippine_timezone)
    result.append(StudentHistory(student_id=userId, history_id=history2.history_id, assessment_id=assessment.comp_assessment_id, score=history2.score, assessment_title=assessment.assessment_title, date_taken=date_taken_ph))
  return result

#get submission history of specific assessment
@router.get("/{assessment_id}")
async def get_specific_assessment_submission_history(assessment_id: int, db: db_dependency):
  result = db.query(models.AssessmentHistory).filter(models.AssessmentHistory.assessment_id == assessment_id).all()
  if not result:
    raise HTTPException(status_code=404, detail='No Submissions')
  for entry in result:
    entry.date_taken = entry.date_taken.astimezone(philippine_timezone)
  return result

@router.get("/comprehension/{assessment_id}")
async def get_specific_comprehension_assessment_submission_history(assessment_id: int, db: db_dependency):
  
  result = db.query(models.ComprehensionAssessmentHistory).filter(models.ComprehensionAssessmentHistory.assessment_id == assessment_id).all()
  if not result:
    raise HTTPException(status_code=404, detail='No Submissions')
  for entry in result:
    entry.date_taken = entry.date_taken.astimezone(philippine_timezone)
  return result