import random

from app.helpers import QuestionTester
from app.models import StudentTestQuestion


def generate_questions_for_student_test(student_test):
    def get_topic_questions(question_from_test):
        return question_from_test.topic.questions.all()

    questions_in_teacher_test = student_test.test.questions.all()
    # словарь, где ключ — тема вопроса из теста преподавателя, значение - множество использованных id вопросов из темы задания
    used_topic_questions_ids = {}
    for q in questions_in_teacher_test:
        possible_questions = get_topic_questions(q)
        if q.topic not in used_topic_questions_ids:
            used_topic_questions_ids[q.topic] = set()

        # если кол-во вопросов по теме больше, чем кол-во вопросов, которые мы использовали
        # то отфильтровываем те, что встречались
        # иначе просто берем любой по теме — все равно все доступные уже перебрали
        if possible_questions.count() > len(used_topic_questions_ids[q.topic]):
            possible_questions = possible_questions.exclude(id__in=used_topic_questions_ids[q.topic])

        topic_question = random.choice(possible_questions)
        used_topic_questions_ids[q.topic].add(topic_question.id)

        StudentTestQuestion.objects.create(
            test=student_test,
            test_question=q,
            question=topic_question
        )


def evaluate_student_test(student_test):
    for student_question in student_test.questions.order_by('test_question__number'):
        if hasattr(student_question, 'answer'):
            # Возможно можно придумать что-то лучше
            if not QuestionTester.is_free(student_question):
                if set(student_question.question.get_right_answers()) == set(student_question.answer.answers.all()):
                    student_question.points = student_question.test_question.points
                    student_question.save()
    student_test.summarize_points()
