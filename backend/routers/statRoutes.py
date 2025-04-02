from fastapi import APIRouter, Depends, HTTPException, Response
from dependencies import get_db
import models
from sqlalchemy.orm import Session
from typing import Annotated, List, Dict
from sqlalchemy import func
from pydantic import BaseModel
import openpyxl
import matplotlib.pyplot as plt
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.legend import Legend
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor
from datetime import datetime, timezone
from openpyxl.styles import Font, Alignment
from io import BytesIO
import pytz

router = APIRouter(
    prefix="/stats",
    tags=["Student Statistics"]
)

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/average_pronunciation_score/{student_id}")
async def get_average_pronunciation_score(student_id: int, db: db_dependency):
    average_score = db.query(func.avg(models.AssessmentHistory.score)).filter(models.AssessmentHistory.student_id == student_id).scalar()
    if average_score is None:
        raise HTTPException(status_code=404, detail="Student not found or no pronunciation assessments taken.")
    return {"average_pronunciation_score": average_score}

@router.get("/average_comprehension_score/{student_id}")
async def get_average_comprehension_score(student_id: int, db: db_dependency):
    average_score = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).filter(models.ComprehensionAssessmentHistory.student_id == student_id).scalar()
    if average_score is None:
        raise HTTPException(status_code=404, detail="Student not found or no comprehension assessments taken.")
    return {"average_comprehension_score": average_score}

@router.get("/pronunciation_scores/{student_id}")
async def get_pronunciation_scores(student_id: int, db: db_dependency):
    scores = db.query(models.AssessmentHistory.score).filter(models.AssessmentHistory.student_id == student_id).all()
    if not scores:
        raise HTTPException(status_code=404, detail="Student not found or no pronunciation assessments taken.")
    return {"pronunciation_scores": [score[0] for score in scores]}

@router.get("/comprehension_scores/{student_id}")
async def get_comprehension_scores(student_id: int, db: db_dependency):
    scores = db.query(models.ComprehensionAssessmentHistory.score).filter(models.ComprehensionAssessmentHistory.student_id == student_id).all()
    if not scores:
        raise HTTPException(status_code=404, detail="Student not found or no comprehension assessments taken.")
    return {"comprehension_scores": [score[0] for score in scores]}

@router.get("/average_score_by_level/{level_id}")
async def get_average_score_by_level(level_id: int, db: db_dependency):
    pronunciation_average = db.query(func.avg(models.AssessmentHistory.score)).join(models.User, models.User.user_id == models.AssessmentHistory.student_id).filter(models.User.level == level_id).scalar()
    comprehension_average = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id).filter(models.User.level == level_id).scalar()

    return {"pronunciation_average": pronunciation_average, "comprehension_average": comprehension_average}

@router.get("/assessment_counts_by_level/{level_id}")
async def get_assessment_counts_by_level(level_id: int, db: db_dependency):
    pronunciation_count = db.query(models.AssessmentHistory).join(models.User, models.User.user_id == models.AssessmentHistory.student_id).filter(models.User.level == level_id).count()
    comprehension_count = db.query(models.ComprehensionAssessmentHistory).join(models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id).filter(models.User.level == level_id).count()

    return {"pronunciation_count": pronunciation_count, "comprehension_count": comprehension_count}

@router.get("/score_trends/{student_id}")
async def get_score_trends(student_id: int, db: db_dependency):
    pronunciation_query = db.query(
        models.AssessmentHistory.date_taken,
        models.AssessmentHistory.score
    ).filter(models.AssessmentHistory.student_id == student_id)

    comprehension_query = db.query(
        models.ComprehensionAssessmentHistory.date_taken,
        models.ComprehensionAssessmentHistory.score
    ).filter(models.ComprehensionAssessmentHistory.student_id == student_id)

    pronunciation_scores = pronunciation_query.order_by(models.AssessmentHistory.date_taken).all()
    comprehension_scores = comprehension_query.order_by(models.ComprehensionAssessmentHistory.date_taken).all()

    pronunciation_data = [{"date": date.isoformat(), "score": score} for date, score in pronunciation_scores]
    comprehension_data = [{"date": date.isoformat(), "score": score} for date, score in comprehension_scores]

    return {
        "pronunciation_scores": pronunciation_data,
        "comprehension_scores": comprehension_data
    }
    
@router.get("/level/{level_id}/completion_rate")
async def get_level_completion_rate(level_id: int, db: db_dependency):
    pronunciation_query = db.query(
        func.date_trunc("day", models.AssessmentHistory.date_taken).label("date"),
        func.count(models.AssessmentHistory.history_id).label("count")
    ).join(models.User, models.User.user_id == models.AssessmentHistory.student_id).filter(models.User.level == level_id)

    comprehension_query = db.query(
        func.date_trunc("day", models.ComprehensionAssessmentHistory.date_taken).label("date"),
        func.count(models.ComprehensionAssessmentHistory.history_id).label("count")
    ).join(models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id).filter(models.User.level == level_id)

    pronunciation_counts = pronunciation_query.group_by("date").order_by("date").all()
    comprehension_counts = comprehension_query.group_by("date").order_by("date").all()

    pronunciation_data = [{"date": date.isoformat(), "count": count} for date, count in pronunciation_counts]
    comprehension_data = [{"date": date.isoformat(), "count": count} for date, count in comprehension_counts]

    return {
        "pronunciation_completion": pronunciation_data,
        "comprehension_completion": comprehension_data
    }
    
@router.get("/section/{section_id}/completion_rate")
async def get_section_completion_rate(section_id: int, db: db_dependency):
    pronunciation_query = db.query(
        func.date_trunc("day", models.AssessmentHistory.date_taken).label("date"),
        func.count(models.AssessmentHistory.history_id).label("count")
    ).join(models.User, models.User.user_id == models.AssessmentHistory.student_id).filter(models.User.section_id == section_id)

    comprehension_query = db.query(
        func.date_trunc("day", models.ComprehensionAssessmentHistory.date_taken).label("date"),
        func.count(models.ComprehensionAssessmentHistory.history_id).label("count")
    ).join(models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id).filter(models.User.section_id == section_id)

    pronunciation_counts = pronunciation_query.group_by("date").order_by("date").all()
    comprehension_counts = comprehension_query.group_by("date").order_by("date").all()

    pronunciation_data = [{"date": date.isoformat(), "count": count} for date, count in pronunciation_counts]
    comprehension_data = [{"date": date.isoformat(), "count": count} for date, count in comprehension_counts]

    return {
        "pronunciation_completion": pronunciation_data,
        "comprehension_completion": comprehension_data
    }

@router.get("/level/{level_id}/score_trends")
async def get_level_score_trends(level_id: int, db: db_dependency):
    pronunciation_query = db.query(
        models.AssessmentHistory.date_taken,
        models.AssessmentHistory.score
    ).join(models.User, models.User.user_id == models.AssessmentHistory.student_id).filter(models.User.level == level_id)

    comprehension_query = db.query(
        models.ComprehensionAssessmentHistory.date_taken,
        models.ComprehensionAssessmentHistory.score
    ).join(models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id).filter(models.User.level == level_id)

    pronunciation_scores = pronunciation_query.order_by(models.AssessmentHistory.date_taken).all()
    comprehension_scores = comprehension_query.order_by(models.ComprehensionAssessmentHistory.date_taken).all()

    pronunciation_data = [{"date": date.isoformat(), "score": score} for date, score in pronunciation_scores]
    comprehension_data = [{"date": date.isoformat(), "score": score} for date, score in comprehension_scores]

    return {
        "pronunciation_scores": pronunciation_data,
        "comprehension_scores": comprehension_data
    }
    
@router.get("/average_score/section_gender")
async def get_average_score_section_gender(db: db_dependency):
    sections = db.query(models.Sections).all()
    results = []

    for section in sections:
        section_data = {
            "section_id": section.section_id,
            "section_name": section.section_name,
            "gender_data": []
        }

        genders = ["Male", "Female"]  # Assuming these are the gender values
        for gender in genders:
            pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).join(
                models.User, models.User.user_id == models.AssessmentHistory.student_id
            ).filter(models.User.section_id == section.section_id, models.User.gender == gender).scalar()

            comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(
                models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id
            ).filter(models.User.section_id == section.section_id, models.User.gender == gender).scalar()

            section_data["gender_data"].append({
                "gender": gender,
                "pronunciation_average": pronunciation_avg,
                "comprehension_average": comprehension_avg
            })

        results.append(section_data)

    return results

@router.get("/average_score/gender")
async def get_average_score_gender(db: db_dependency):
    genders = ["Male", "Female"]
    results = []

    for gender in genders:
        pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).join(
            models.User, models.User.user_id == models.AssessmentHistory.student_id
        ).filter(models.User.gender == gender).scalar()

        comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(
            models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id
        ).filter(models.User.gender == gender).scalar()

        results.append({
            "gender": gender,
            "pronunciation_average": pronunciation_avg,
            "comprehension_average": comprehension_avg
        })

    # Total average (no gender separation)
    total_pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).scalar()
    total_comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).scalar()

    results.append({
        "gender": "Total",
        "pronunciation_average": total_pronunciation_avg,
        "comprehension_average": total_comprehension_avg
    })

    return results

@router.get("/student_count/level_section_gender")
async def get_student_count_level_section_gender(db: db_dependency):
    sections = db.query(models.Sections).all()
    levels = db.query(models.PronunciationAssessmentType).all() #Assuming type_id in PronunciationAssessmentType is the same as level in User
    genders = ["Male", "Female"]
    results = []

    for section in sections:
        section_data = {
            "section_id": section.section_id,
            "section_name": section.section_name,
            "level_data": []
        }

        for level in levels:
            level_data = {
                "level_id": level.type_id,
                "level_name": level.type_name,
                "gender_counts": []
            }

            for gender in genders:
                count = db.query(func.count(models.User.user_id)).filter(
                    models.User.section_id == section.section_id,
                    models.User.level == level.type_id,
                    models.User.gender == gender
                ).scalar()

                level_data["gender_counts"].append({
                    "gender": gender,
                    "count": count
                })

            section_data["level_data"].append(level_data)

        results.append(section_data)

    return results

@router.get("/students/gender-distribution")
async def get_students_grouped_by_gender(db: db_dependency):
    student_counts = (
        db.query(models.User.gender, func.count(models.User.user_id).label("total_students"))
        .filter(models.User.role == "student")
        .group_by(models.User.gender)
        .all()
    )

    return [{"gender": gender, "total_students": total_students} for gender, total_students in student_counts]


@router.get("/download")
async def get_average_score_gender_excel(db: db_dependency):
    sections = db.query(models.Sections).all()
    genders = ["Male", "Female", "Total"]
    results = []

    for section in sections:
        for gender in genders:
            if gender != "Total":
                student_count = db.query(func.count(models.User.user_id)).filter(
                    models.User.section_id == section.section_id,
                    models.User.gender == gender
                ).scalar()

                pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.AssessmentHistory.student_id
                ).filter(models.User.section_id == section.section_id, models.User.gender == gender).scalar()

                comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id
                ).filter(models.User.section_id == section.section_id, models.User.gender == gender).scalar()
            else:
                student_count = db.query(func.count(models.User.user_id)).filter(
                    models.User.section_id == section.section_id,
                ).scalar()

                pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.AssessmentHistory.student_id
                ).filter(models.User.section_id == section.section_id, ).scalar()

                comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id
                ).filter(models.User.section_id == section.section_id, ).scalar()

            results.append({
                "section_name": section.section_name,
                "gender": gender,
                "student_count": student_count or 0,
                "pronunciation_average": round(pronunciation_avg, 2) if pronunciation_avg is not None else 0,
                "comprehension_average": round(comprehension_avg, 2) if comprehension_avg is not None else 0
            })

    workbook = openpyxl.Workbook()
    sheet = workbook.active

    # Add table headers
    sheet["A1"] = "Section"
    sheet["B1"] = "Gender"
    sheet["C1"] = "Student Count"
    sheet["D1"] = "Pronunciation Average"
    sheet["E1"] = "Comprehension Average"

    for i, row in enumerate(results):
        sheet[f"A{i+2}"] = row["section_name"]
        sheet[f"B{i+2}"] = row["gender"]
        sheet[f"C{i+2}"] = row["student_count"]
        sheet[f"D{i+2}"] = row["pronunciation_average"]
        sheet[f"E{i+2}"] = row["comprehension_average"]

    # Create bar chart
    chart = BarChart()
    chart.title = "Overall (%) of Reading Fluency and Comprehension in English"
    chart.y_axis.delete = False
    chart.x_axis.delete = False
    chart.y_axis.scaling.max = 100 
    chart.y_axis.majorUnit = 10
    chart.y_axis.scaling.min = 0
    chart.y_axis.majorGridlines = None
    chart.x_axis.majorGridlines = None
    chart.dataLabels = DataLabelList()
    chart.dataLabels.showVal = True
    chart.dataLabels.showSerName = False
    chart.dataLabels.showCatName = False
    chart.dataLabels.showLegendKey = False
    chart.legend = Legend()
    chart.legend.position = 'b'
    chart.legend.overlay = False

    genders_chart = ["Male", "Female", "Total"]
    results_chart = []
    
    for gender in genders_chart:
        if gender != "Total":
          pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).join(
              models.User, models.User.user_id == models.AssessmentHistory.student_id
          ).filter(models.User.gender == gender).scalar()

          comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(
              models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id
          ).filter(models.User.gender == gender).scalar()
        else:
          pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).scalar()
          comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).scalar()
        results_chart.append({
            "gender": gender,
            "pronunciation_average": round(pronunciation_avg, 2) if pronunciation_avg is not None else 0,
            "comprehension_average": round(comprehension_avg, 2) if comprehension_avg is not None else 0
        })
    chart_data_start_row = len(results) + 5 #start below the table
    sheet[f"A{chart_data_start_row-1}"] = "Gender"
    sheet[f"B{chart_data_start_row-1}"] = "Pronunciation Average"
    sheet[f"C{chart_data_start_row-1}"] = "Comprehension Average"
    for i, row in enumerate(results_chart):
        sheet[f"A{chart_data_start_row + i}"] = row["gender"]
        sheet[f"B{chart_data_start_row + i}"] = row["pronunciation_average"]
        sheet[f"C{chart_data_start_row + i}"] = row["comprehension_average"]
    
    data = Reference(sheet, min_col=2, min_row=chart_data_start_row-1, max_col=3, max_row=chart_data_start_row + len(results_chart) -1)
    categories = Reference(sheet, min_col=1, min_row=chart_data_start_row, max_row=chart_data_start_row + len(results_chart) -1)

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)

    sheet.add_chart(chart, f"A{chart_data_start_row-1}")

    generation_date = datetime.now(pytz.timezone("Asia/Manila")).strftime("%Y-%m-%d %H:%M:%S PHT")
    notice_text = f"Generation Notice: This report was automatically generated by the ReadSpeak system on {generation_date}."

    # Find the row below the chart
    notice_row = chart_data_start_row + len(results_chart) + 2 # Add some space
    sheet[f"A33"] = notice_text

    # Apply styling to the notice cell
    notice_cell = sheet[f"A33"]
    notice_cell.font = Font(size=10, italic=True)
    notice_cell.alignment = Alignment(horizontal='left')

    # Save the Excel file to a BytesIO object
    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)

    # Return the Excel file as a response
    headers = {
        'Content-Disposition': 'attachment; filename="ReadSpeak Analytics.xlsx"'
    }
    return Response(content=excel_file.read(), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")