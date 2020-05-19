from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from app import models
from app.helpers import QuestionTester
from app.services import evaluate_student_test


class QuestionAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        test = getattr(obj, 'test', None)
        return getattr(test, 'created_by', None) == request.user


class TestForm(forms.ModelForm):
    created_by = forms.ModelChoiceField(queryset=models.User.objects.all())

    class Meta:
        model = models.Test
        exclude = ()


class QuestionForTestInline(admin.StackedInline):
    model = models.Question
    extra = 0


class TestAdmin(admin.ModelAdmin):
    inlines = [QuestionForTestInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(created_by=request.user)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "created_by":
                kwargs["queryset"] = models.Teacher.objects.filter(id=request.user.id)
                kwargs["initial"] = request.user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TopicQuestionInline(admin.StackedInline):
    model = models.TopicQuestion
    extra = 0
    readonly_fields = ('get_answers', 'add_answers_link')

    def get_answers(self, obj):
        if obj.answers.count() > 0:
            return mark_safe(
                '<br>'.join(
                    f'{i}. {ans.text} | {"верный" if ans.right else "неверный"}' for i, ans in enumerate(
                        obj.answers.all(),
                        start=1
                    )
                )
            )
        return '-'

    def add_answers_link(self, obj):
        if obj.id:
            link_to_object_change_view = reverse("admin:app_topicquestion_change", kwargs=dict(object_id=obj.id))
            return mark_safe(
                f'<a href="{link_to_object_change_view}" target="_blank">Добавить ответы на вопрос</a>'
            )
        return 'Доступно только после создания вопроса'

    add_answers_link.short_description = 'Добавить варианты ответов'
    get_answers.short_description = 'Ответы'


class TopicAdmin(admin.ModelAdmin):
    inlines = [TopicQuestionInline]
    list_display = ('name', 'number_of_questions')

    add_form_template = 'question_change_form.html'
    change_form_template = 'question_change_form.html'

    def number_of_questions(self, obj):
        return obj.questions.count()

    number_of_questions.short_description = 'Количество вопросов'


class AnswerInline(admin.StackedInline):
    model = models.Answer
    extra = 0

    def generate_random_question(self, obj):
        if obj.id:
            link_to_object_change_view = reverse("admin:app_topicquestion_change", kwargs=dict(object_id=obj.id))
            return mark_safe(
                f'<a href="{link_to_object_change_view}" target="_blank">Добавить ответы на вопрос</a>'
            )
        return '<button> Сгенерировать</button>'

    generate_random_question.short_description = 'Сгенерировать вопрос'
    readonly_fields = ('generate_random_question',)


class TopicQuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    add_form_template = 'question_change_form.html'
    change_form_template = 'question_change_form.html'


class StudentTestQuestionInline(admin.TabularInline):
    model = models.StudentTestQuestion
    extra = 0
    fields = ('get_question', 'get_answer', 'points', 'get_max_points')
    readonly_fields = ('get_question', 'get_answer', 'get_max_points')
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('test_question__number')

    def get_question(self, obj):
        return obj.question.text

    def get_free_answer(self, obj):
        answer = getattr(obj.answers.first(), 'text', '-')
        return answer if answer else '-'

    def get_answer(self, obj):
        if not hasattr(obj, 'answer'):
            return '-'
        else:
            if QuestionTester.is_free(obj):
                return obj.answer.text
            else:
                return ' | '.join(['+' if i.right else '-' for i in obj.answer.answers.all()])

    def get_max_points(self, obj):
        return obj.test_question.points

    get_question.short_description = 'Вопрос'
    get_free_answer.short_description = 'Свободный ответ'
    get_answer.short_description = 'Ответы'
    get_max_points.short_description = 'Максимальное количество баллов'


class StudentTestAdmin(admin.ModelAdmin):
    inlines = [StudentTestQuestionInline, ]
    exclude = ('ending_time',)
    list_display = ('student', 'group', 'test', 'points', 'checked')
    list_filter = ('checked', 'group')
    change_form_template = 'studenttest_change_form.html'

    def response_change(self, request, obj):
        # к этому моменту объект и related объекты сохранились и можно с чистой душой пересчитать баллы
        evaluate_student_test(obj)
        obj.checked = True
        obj.save()
        self.message_user(request, 'Баллы будут пересчитаны и сохранены')
        return super().response_change(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Б - Безопасность
        return request.user.is_superuser or getattr(getattr(obj, 'test', None), 'created_by', None) == request.user


admin.site.register(models.User)
admin.site.register(models.Group)
admin.site.register(models.Test, TestAdmin)
admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Topic, TopicAdmin)
admin.site.register(models.TopicQuestion, TopicQuestionAdmin)
admin.site.register(models.Answer)
admin.site.register(models.StudentTest, StudentTestAdmin)
