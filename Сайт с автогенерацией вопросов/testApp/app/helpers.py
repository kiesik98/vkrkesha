import random
import string

from django.utils import timezone

from app import models
from app.enums import AnswerTypeChoices


# перемешивание с возвратом iterable
def shuffle(iterable):
    a = iterable
    random.shuffle(a)
    return a


def random_chars(n=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def get_student_test(pk):
    return models.StudentTest.objects.get(pk=pk)


def get_test_question(test_id, question_number):
    student_test = get_student_test(test_id)

    student_question = student_test.questions.filter(
        test_question__number=question_number
    ).first()
    return student_question


# возможные ответы и ответы пользователя + контекст для страницы с тестированием
def get_context_for_test(student_test, test_question):
    context = dict(
        student_test=student_test,
        test_question=test_question,
        type=test_question.question.answer_type
    )

    if test_question.question.answer_type == AnswerTypeChoices.FREE.name:
        context.update(
            dict(
                student_answer=getattr(test_question, 'answer', None)
            )
        )

    elif test_question.question.answer_type == AnswerTypeChoices.SINGLE.name:
        student_answer = getattr(test_question, 'answer', None)
        if student_answer:
            student_answer = student_answer.answers.first()
        context.update(
            dict(
                answers=shuffle(list(test_question.question.answers.all())),
                student_answer=student_answer
            )
        )

    elif test_question.question.answer_type == AnswerTypeChoices.MULTIPLE.name:
        context.update(
            dict(
                answers=shuffle(list(test_question.question.answers.all())),
                student_answers=shuffle(
                    [a for a in test_question.answer.answers.all()] if hasattr(test_question, 'answer') else [None]
                )
            )
        )
    context.update(get_context_for_questions_table(student_test))
    context.update(get_timer_context(student_test))
    return context


def get_timer_context(student_test):
    return dict(
        time_left_in_seconds=round((student_test.calculated_ending_time - timezone.now()).total_seconds()),
        seconds_passed=round((timezone.now() - student_test.created_time).total_seconds()),
        duration_in_minutes=student_test.test.duration,
        duration_in_seconds=student_test.test.duration * 60
    )


# таблица пройденных/пустых вопросов
def get_context_for_questions_table(student_test):
    is_empty_table = {
        i: not hasattr(question, 'answer')
        for i, question in enumerate(student_test.questions.order_by('test_question__number'), start=1)
    }
    return {'is_empty_table': is_empty_table}


# обработка отправленного вопроса
def process_form(test_question, request):
    if len(request.POST.getlist('answers', [])) > 0 or request.POST.get('text', None) not in ['', None]:
        # есть предыдущий ответ - сбрасываем
        if hasattr(test_question, 'answer'):
            test_question.answer.delete()

        answer, created = models.StudentAnswer.objects.get_or_create(
            question=test_question, text=request.POST.get('text')
        )
        # есть ли какие-то ответы или нет - просто обновляем связь m2m
        answer.answers.set(models.Answer.objects.filter(id__in=request.POST.getlist('answers')))
    # пришла пустая форма - пользователь обнуляет ответ, либо ничего не выбрал
    elif hasattr(test_question, 'answer'):
        test_question.answer.delete()


class QuestionTester:
    @staticmethod
    def is_free(q):
        return q.question.answer_type == AnswerTypeChoices.FREE.name

    @staticmethod
    def is_single(q):
        return q.question.answer_type == AnswerTypeChoices.SINGLE.name

    @staticmethod
    def is_multiple(q):
        return q.question.answer_type == AnswerTypeChoices.MULTIPLE.name
