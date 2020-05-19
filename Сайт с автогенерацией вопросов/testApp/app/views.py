from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import CreateView


from app import forms as app_forms, helpers, models, services, permissions


from app.models import Group


class HomeView(permissions.AnonymousRequiredMixin, CreateView):
    template_name = 'home.html'
    form_class = app_forms.StudentTestForm

    def get(self, request, *args, **kwargs):
        test_token = request.COOKIES.get('test_token', None)
        # если остался токен от незавершенного теста, который еще не закончился, то кидаем юзера на тест
        if test_token:
            test = models.StudentTest.objects.get(token=test_token)
            if test.calculated_ending_time > timezone.now():
                return redirect('app:test', pk=test.id, q=1)
        else:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        services.generate_questions_for_student_test(self.object)
        response.set_cookie(
            key='test_token',
            value=self.object.token,
            max_age=60 * self.object.test.duration  # длительность теста
        )
        return response

    def get_success_url(self):
        return reverse('app:test', kwargs={'pk': self.object.id, 'q': 1})


# @user_passes_test(lambda u: u.is_anonymous, reverse_lazy('app:home'))
def test_view(request, pk, q=1):
    student_test = helpers.get_student_test(pk)
    student_test.student = request.user
    student_test.group = Group.objects.get(name=request.user.group)
    student_test.save()
    # если path параметр для вопроса больше количества вопросов в тесте, то кидаем на 1
    if q > student_test.number_of_questions:
        return redirect('app:test', pk=pk, q=1)

    test_question = helpers.get_test_question(pk, q)

    if request.method == 'GET':
        # рассматриваем все варианты присутствия/отсутствия идущего/закончившегося теста
        token = request.COOKIES.get('test_token', None)
        calculated_ending_time = student_test.calculated_ending_time

        if token:
            if student_test.token == token:
                if calculated_ending_time > timezone.now():
                    # нормальная отдача страницы
                    context = helpers.get_context_for_test(student_test, test_question)
                    return render(request, 'test_page.html', context)
                else:
                    messages.info(request, 'Время теста истекло')
                    return redirect('app:finish', pk=student_test.id)
            else:
                messages.add_message(request, messages.ERROR, 'Неудачная попытка продолжить тест')
                return redirect('app:home')
        else:
            if calculated_ending_time < timezone.now():
                student_test.ending_time = calculated_ending_time
                student_test.save()
                messages.info(request, 'Время теста истекло')
            else:
                messages.info(request, 'Тест еще не создан')
            return redirect('app:home')
    else:
        with transaction.atomic():
            kwargs = {}
            if hasattr(test_question, 'answer'):
                kwargs['instance'] = test_question.answer
            form = app_forms.StudentAnswerForm(request.POST, **kwargs)
            if form.is_valid():
                helpers.process_form(test_question, request)
            else:
                errors = form.errors
                return render(request, 'test_page.html', {'errors': errors})

        # если был последний вопрос
        if q == student_test.number_of_questions:
            for question in student_test.questions.order_by('test_question__number'):
                # смотрим, есть ли вопрос без ответа
                # и кидаем на первый по порядку вопрос без ответов
                if not getattr(question, 'answer', None):
                    return redirect('app:test', pk=pk, q=question.test_question.number)
            # иначе предлагаем завершить тест
            return redirect('app:finish', pk=student_test.id)
        # иначе просто перекидываем на следующий
        return redirect('app:test', pk=pk, q=q + 1)


# @user_passes_test(lambda u: u.is_anonymous, reverse_lazy('app:home'))
def finish(request, pk):
    if request.method == 'POST':
        student_test = helpers.get_student_test(pk)
        student_test.ending_time = timezone.now()
        services.evaluate_student_test(student_test)

        messages.info(request, f'Набрано баллов за тестовую часть: {student_test.points}')
        response = redirect('app:home')
        response.delete_cookie('test_token')
        return response
    else:
        student_test = helpers.get_student_test(pk)
        context = dict(
            student_test=student_test,
            **helpers.get_context_for_questions_table(student_test),
            **helpers.get_timer_context(student_test)
        )
        return render(request, 'test_finish.html', context)
