import datetime
import random

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum

from app.enums import AnswerTypeChoices
from app.helpers import random_chars


class BaseModel(models.Model):
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Group(BaseModel):
    name = models.CharField(max_length=30, verbose_name='Номер группы')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['name']


class User(AbstractUser, BaseModel):
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, related_name='users', verbose_name='Группа')

    def __str__(self):
        return f'{self.last_name} {self.first_name} {self.middle_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Test(BaseModel):
    # Тест, который составляется преподавателем
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='Название теста')
    duration = models.PositiveSmallIntegerField(verbose_name='Продолжительность теста в минутах')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tests',
                                   verbose_name='Составил')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'


class Question(BaseModel):
    # Вопрос в тесте, который составляется преподавателем. Содержит информацию о вопросе в тесте, но не само задание
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест')
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name='test_questions', verbose_name='Тема')
    points = models.PositiveSmallIntegerField(default=0, verbose_name='Количество баллов за вопрос')
    number = models.PositiveSmallIntegerField(default=1, verbose_name='Номер вопроса в тесте',
                                              help_text='Номер вопроса в рамках теста должен быть уникален')

    def __str__(self):
        test_name = self.test.name
        if len(test_name) > 10:
            test_name = test_name[:10]
        return f'Вопрос №{self.number} в тесте "{test_name}" из {self.topic}'

    class Meta:
        verbose_name = 'Вопрос в тесте'
        verbose_name_plural = 'Вопросы в тесте'
        unique_together = ('test', 'number')


class Topic(BaseModel):
    # Тема вопроса, из которой будет выбран случайный вопрос для студента
    name = models.CharField(max_length=100, verbose_name='Название темы')

    def __str__(self):
        return f'{self.name}, вопросов: {self.questions.count()}'

    def get_random_question(self):
        return random.choice(self.questions.all())

    class Meta:
        verbose_name = 'Тема для вопроса'
        verbose_name_plural = 'Темы для вопросов'


class TopicQuestion(BaseModel):
    #  Вопрос с заданием, который может попасться студенту
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, null=True,
        related_name='questions', verbose_name='Тема'
    )
    text = models.TextField(verbose_name='Текст вопроса', max_length=1000)
    image = models.ImageField(verbose_name='Изображение для вопроса', upload_to="images", blank=True, null=True)
    answer_type = models.CharField(
        max_length=10,
        verbose_name='Тип ответа на вопрос',
        help_text='Используйте соответствующее количество правильных вариантов ответов, '
                  'для вопроса в свободной форме ответ не требуется',
        choices=[(ans_type.name, ans_type.value) for ans_type in AnswerTypeChoices]
    )

    def __str__(self):
        answer_type = [ans for ans in AnswerTypeChoices if self.answer_type == ans.name][0]
        return f'{self.topic.name}, {answer_type}, {self.text}'

    def get_right_answers(self):
        return self.answers.filter(right=True)

    def generate_random(self):
        return self

    class Meta:
        verbose_name = 'Вопрос из темы'
        verbose_name_plural = 'Вопросы из темы'


class Answer(BaseModel):
    # Варианты ответов к вопросу
    question = models.ForeignKey(TopicQuestion, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    text = models.CharField(max_length=1000, verbose_name='Текст ответа')
    image = models.ImageField(verbose_name='Изображение для ответа', upload_to="images", blank=True, null=True)
    right = models.BooleanField(default=False, verbose_name='Верный ли вариант ответа')

    def __str__(self):
        return f'{self.question}, {self.text}'

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответа'


class StudentTest(BaseModel):
    # Конкретный случай прохождения теста студентом
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='students', verbose_name='Студент')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, related_name='tests', verbose_name='Группа')
    test = models.ForeignKey(
        Test,
        on_delete=models.SET_NULL,
        null=True,
        related_name='student_tests',
        verbose_name='Тест'
    )
    points = models.PositiveSmallIntegerField(default=0, verbose_name='Количество набранных баллов за тест')
    token = models.CharField(max_length=20, default=random_chars, editable=False, unique=True)
    checked = models.BooleanField(default=False, verbose_name='Проверен ли тест')

    @property
    def calculated_ending_time(self):
        return self.created_time + datetime.timedelta(minutes=self.test.duration)

    @property
    def number_of_questions(self):
        return self.questions.count()

    def summarize_points(self):
        self.points = self.questions.aggregate(total=Sum('points')).get('total')
        self.save()

    def __str__(self):
        return f'{self.student} {self.group} {self.test}'

    class Meta:
        verbose_name = 'Тест студента'
        verbose_name_plural = 'Тесты студентов'


class StudentTestQuestion(BaseModel):
    # Конкретный вопрос в тесте для студента из числа TopicQuestion
    question = models.ForeignKey(
        TopicQuestion,
        on_delete=models.SET_NULL,
        null=True,
        related_name='test_questions',
        verbose_name='Конкретный вопрос для студента'
    )
    test_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        related_name='student_test_questions',
        verbose_name='Вопрос из теста преподавателя'
    )
    test = models.ForeignKey(StudentTest, on_delete=models.SET_NULL, null=True, related_name='questions',
                             verbose_name='Тест')
    points = models.SmallIntegerField(default=0, verbose_name='Количество баллов за ответы на вопрос')

    def __str__(self):
        return f'{self.test_question}'

    class Meta:
        verbose_name = 'Вопрос в тесте для студента'
        verbose_name_plural = 'Вопросы в тесте для студента'
        unique_together = ('test', 'test_question')


class StudentAnswer(BaseModel):
    # Ответ студента в определенном тесте на определенный вопрос
    question = models.OneToOneField(StudentTestQuestion, on_delete=models.SET_NULL, null=True, related_name='answer',
                                    verbose_name='Вопрос')
    answers = models.ManyToManyField(
        Answer,
        related_name='student_answers',
        verbose_name='Ответ'
    )
    text = models.TextField(verbose_name='Текст для случая со свободной формой ответа', null=True, blank=True)

    def __str__(self):
        return f'{self.id} {self.question} {self.text}'

    class Meta:
        verbose_name = 'Ответ студента'
        verbose_name_plural = 'Ответы студента'
