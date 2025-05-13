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
import math

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
        models.AssessmentHistory.score,
        models.User.section_id
    ).join(models.User, models.User.user_id == models.AssessmentHistory.student_id).filter(models.User.level == level_id)

    comprehension_query = db.query(
        models.ComprehensionAssessmentHistory.date_taken,
        models.ComprehensionAssessmentHistory.score,
        models.User.section_id
    ).join(models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id).filter(models.User.level == level_id)

    pronunciation_scores = pronunciation_query.order_by(models.AssessmentHistory.date_taken).all()
    comprehension_scores = comprehension_query.order_by(models.ComprehensionAssessmentHistory.date_taken).all()

    pronunciation_data = [
        {"date": date.isoformat(), "score": score, "section_id": section_id}
        for date, score, section_id in pronunciation_scores
    ]

    comprehension_data = [
        {"date": date.isoformat(), "score": score, "section_id": section_id}
        for date, score, section_id in comprehension_scores
    ]
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
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

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
    sheet.title = "ReadSpeak Report"

    # === Style helpers ===
    title_font = Font(size=14, bold=True)
    header_font = Font(size=12, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # === Title ===
    sheet.merge_cells("A1:E1")
    sheet["A1"] = "ReadSpeak System - Student Performance Report"
    sheet["A1"].font = title_font
    sheet["A1"].alignment = center_align

    # === Subtitle ===
    sheet.merge_cells("A2:E2")
    generated_on = datetime.now(pytz.timezone("Asia/Manila")).strftime("%B %d, %Y – %I:%M %p")
    sheet["A2"] = f"Generated on {generated_on}"
    sheet["A2"].alignment = Alignment(horizontal="right")

    # === Table Headers ===
    headers = ["Section", "Gender", "Student Count", "Pronunciation Average", "Comprehension Average"]
    sheet.append(headers)
    for col_num, header in enumerate(headers, 1):
        cell = sheet.cell(row=3, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
        column_letter = get_column_letter(col_num)
        sheet.column_dimensions[column_letter].width = 24

    # === Table Data ===
    for i, row in enumerate(results):
        data_row = [
            row["section_name"],
            row["gender"],
            row["student_count"],
            row["pronunciation_average"],
            row["comprehension_average"]
        ]
        sheet.append(data_row)
        for col_num in range(1, 6):
            cell = sheet.cell(row=4 + i, column=col_num)
            cell.alignment = center_align
            cell.border = border

    # === Chart Data Below Table ===
    chart_data_start = len(results) + 9
    # print(chart_data_start)
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

    # Chart headers
    sheet[f"A{chart_data_start - 1}"] = "Gender"
    sheet[f"B{chart_data_start - 1}"] = "Pronunciation Average"
    sheet[f"C{chart_data_start - 1}"] = "Comprehension Average"

    sheet.merge_cells(f"A{chart_data_start-3}:B{chart_data_start-3}")
    sheet[f"A{chart_data_start-3}"] = "Grade 3 Average(%) Performance by Gender"
    sheet[f"A{chart_data_start-3}"].font = title_font
    # sheet[f"A{chart_data_start-3}"].alignment = center_align
    
    # Chart data
    for i, row in enumerate(results_chart):
        sheet[f"A{chart_data_start + i}"] = row["gender"]
        sheet[f"B{chart_data_start + i}"] = row["pronunciation_average"]
        sheet[f"C{chart_data_start + i}"] = row["comprehension_average"]

    # Create the bar chart
    chart = BarChart()
    chart.title = "Average(%) Performance by Gender\n"
    # chart.y_axis.scaling.max = 100
    # chart.y_axis.scaling.min = 0
    # chart.dataLabels = DataLabelList(showVal=True)
    # chart.legend.position = 'b'
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
    chart.title.overlay = False
    chart.overlap = -20 

    data = Reference(sheet, min_col=2, min_row=chart_data_start - 1, max_col=3, max_row=chart_data_start + 2)
    categories = Reference(sheet, min_col=1, min_row=chart_data_start, max_row=chart_data_start + 2)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.series[0].graphicalProperties.solidFill = "FF0000"
    chart.series[1].graphicalProperties.solidFill = "FFFF00"
    sheet.add_chart(chart, f"A{chart_data_start-1}")
    
    # === Charts per section ===
    section_chart_start_row = chart_data_start + 18  # start below the first chart
    chart_width = 4  # columns between each chart
    chart_height_rows = 16
    charts_per_row = 2
    
    # Adding chart header
    chart_header_row = section_chart_start_row - 2  # Row above the first chart
    sheet.merge_cells(f"A{chart_header_row}:B{chart_header_row}")
    chart_header_cell = sheet[f"A{chart_header_row}"]
    chart_header_cell.value = "Per Section Performance"
    chart_header_cell.font = title_font
    # chart_header_cell.alignment = Alignment(horizontal="center", vertical="center")

    for idx, section in enumerate(sections):
        chart_row = section_chart_start_row + (idx // charts_per_row) * chart_height_rows
        chart_col = (idx % charts_per_row) * chart_width + 1
        chart_anchor = f"{get_column_letter(chart_col)}{chart_row}"

        # Fetch per-gender averages
        section_gender_averages = []
        for gender in ["Male", "Female", "Total"]:
            if gender != "Total":
                pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.AssessmentHistory.student_id
                ).filter(models.User.gender == gender, models.User.section_id == section.section_id).scalar()

                comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id
                ).filter(models.User.gender == gender, models.User.section_id == section.section_id).scalar()
            else:
                pronunciation_avg = db.query(func.avg(models.AssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.AssessmentHistory.student_id
                ).filter(models.User.section_id == section.section_id).scalar()

                comprehension_avg = db.query(func.avg(models.ComprehensionAssessmentHistory.score)).join(
                    models.User, models.User.user_id == models.ComprehensionAssessmentHistory.student_id
                ).filter(models.User.section_id == section.section_id).scalar()

            section_gender_averages.append({
                "gender": gender,
                "pronunciation_average": round(pronunciation_avg, 2) if pronunciation_avg is not None else 0,
                "comprehension_average": round(comprehension_avg, 2) if comprehension_avg is not None else 0
            })

        # Write data to cells
        data_start_row = chart_row + 2
        sheet[f"{get_column_letter(chart_col)}{data_start_row - 1}"] = "Gender"
        sheet[f"{get_column_letter(chart_col + 1)}{data_start_row - 1}"] = "Pronunciation Average"
        sheet[f"{get_column_letter(chart_col + 2)}{data_start_row - 1}"] = "Comprehension Average"

        for i, row in enumerate(section_gender_averages):
            sheet.cell(row=data_start_row + i, column=chart_col, value=row["gender"])
            sheet.cell(row=data_start_row + i, column=chart_col + 1, value=row["pronunciation_average"])
            sheet.cell(row=data_start_row + i, column=chart_col + 2, value=row["comprehension_average"])

        # === Chart styling (matches first chart) ===
        chart = BarChart()
        chart.title = f"{section.section_name} Performance by Gender\n"
        chart.y_axis.scaling.max = 100
        chart.y_axis.scaling.min = 0
        chart.y_axis.majorUnit = 10
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
        chart.title.overlay = False
        chart.overlap = -20
        chart.y_axis.delete = False
        chart.x_axis.delete = False

        # Add data
        data = Reference(sheet, min_col=chart_col + 1, min_row=data_start_row - 1, max_col=chart_col + 2, max_row=data_start_row + 2)
        categories = Reference(sheet, min_col=chart_col, min_row=data_start_row, max_row=data_start_row + 2)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(categories)

        # Bar colors
        chart.series[0].graphicalProperties.solidFill = "FF0000"  # red for pronunciation
        chart.series[1].graphicalProperties.solidFill = "FFFF00"  # yellow for comprehension

        # Place chart
        sheet.add_chart(chart, chart_anchor)

    # Dimensions
    charts_per_row = 2
    chart_height = 16  # estimated vertical space used per chart
    start_row = chart_data_start + 5  # space after first gender chart

    # Calculate max vertical position from rows of charts
    num_charts = len(sections)
    rows_of_charts = math.ceil(num_charts / charts_per_row)
    last_chart_row = start_row + (rows_of_charts * chart_height)

    # Footer
    footer_row = last_chart_row + 15
    sheet.merge_cells(f"A{footer_row}:E{footer_row}")
    footer_cell = sheet[f"A{footer_row}"]
    footer_cell.value = f"Notice: This report was automatically generated by the ReadSpeak system."
    footer_cell.font = Font(size=10, italic=True)
    footer_cell.alignment = Alignment(horizontal="left")

    # Save and respond
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="ReadSpeak_Report.xlsx"'
    }
    return Response(content=output.read(), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    