# -*- coding: utf-8 -*-

import os
import random
import math
from app.models import Answer


# Основные переменные для работы шаблона задания
class QuestionTemplate:  # Все переменные хранятся здесь обращение к ним чрез question.a
    type = None  # тип задания 1 - практическое, 2 - теоретическое (для разделения на типы может быть)
    # список для сохранения сгенерированных для задания чисел. Нужно чтобы числа не повторялись
    chisla = []

    # Основные переменные задания для инициализации присвоено значение None далее работает Random можно добавить больше или убрать лишние
    a = None
    b = None
    c = None
    d = None
    e = None
    f = None

    # результат задания всегда присаивается переменной rez_z
    rez_z = None

    @classmethod
    def create_question(cls, obj, taskType):
        """Метод генерирующий вопросы и ответы по типам задачи

        Arg:
            obj (TopicQuestion): Объекто вопроса
            taskType (str): Тип генерируемой задачи
        """
        dict_of_types = {
            1: QuestionTemplate.generate_question,
            2: QuestionTemplate.generate_question_two,
            4: QuestionTemplate.generate_question_four,
            5: QuestionTemplate.generate_ost_one
        }
        generated_data = dict_of_types[taskType]()
        obj.text = generated_data['text']
        answers = []
        for i in generated_data['variable_answers']:
            right = True if generated_data['truly_answer'] == generated_data['variable_answers'].index(i) else False
            answers.append(Answer(text=i, right=right, question=obj))
        Answer.objects.bulk_create(answers)
        obj.save()

    @classmethod
    def generate_question(cls):
        # генерируем значения
        random_var(cls)
        # вычисляем решение
        reshenie(cls)
        # тут вызывается функция создания вариантов ответа и результат присваивается переменным
        var_a, var_b,  var_c, var_d, prav_otv = variants(cls)
        # Тут вызывается функция для формирования текста задания
        text_zad = zadaine(cls)
        
        # очищаем список chisla
        if len(question.chisla):
            question.chisla.clear()

        response_data = {
            'text': text_zad,
            'variable_answers': [var_a, var_b, var_c, var_d],
            'truly_answer': prav_otv
        }

        return response_data

    @classmethod
    def generate_question_two(cls):
        # Генерируем сторону квадарата
        row_of_square = random.randint(3, 10)
        # Генерируем квадарат
        N = row_of_square * row_of_square
        answer = int(math.log2(N))
        cls.a = answer
        ansers = generate_random_variables(answer)
        # Генерируем текст задачи
        text = zadaine_type_2(cls)
        
        
        response_data = {
            'text': text,
            'variable_answers': ansers[0:4],
            'truly_answer': ansers.index(answer)
        }
        return response_data

    @classmethod
    def generate_question_four(cls):
        # Создаем массив чисел с основнием 2, для удобного счета
        arr = [2**i for i in range(7)]
        # Выьраем рандомное число из созданного массива
        count = random.choice(arr)
        # Делаем срез для выбора меньшего подмассива. Т.к выбранное число не может быть больше общего числа объектов
        less = arr[:arr.index(count)]
        # Выбор меньшего числа из созданного подмассива
        selected = random.choice(less)
        # Вычисление вероятности
        p = selected / count
        cls.a = count
        cls.b = selected
        # Получаем ответ
        answer = int(math.log2(1/p))
        # Генерируем набор ответов
        anwsers = generate_random_variables(answer)
        # Генерируем текст задачи
        text = zadaine_type_3(cls)
        

        # Словарь с сгенерированными данными
        response_data = {
            'text': text,
            'variable_answers': anwsers[0:4],
            'truly_answer': anwsers.index(answer)
        }
        return response_data

    @classmethod
    def generate_ost_one(cls):
        # генерируем значения
        random_ost1(cls)
        p = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'           
        answer=''
        y = cls.a
        while y:
            y, c = divmod(y, cls.b) 
            answer=p[c]+answer
        answerr = generate_random_variables(answer)
        # Генерируем текст задачи
        text = ost_1(cls)

        # Словарь с сгенерированными данными
        response_data = {
            'text': text,
            'variable_answers': answerr[0:4],
            'truly_answer': answerr.index(answer)
        }
        return response_data


question = QuestionTemplate()

# Генерация целых чисел в качестве параметра передается min - минимальное число, max-максимальное число
def rand_int(min, max):
    if (
        min == max
    ):  # Если минимальное значение и максимальное при вызове функции будут равны произойдет ошибка
        max += 1  # Если да то увеличиваем аксимальное значение на 1
    a = random.randint(min, max)  # Генерируем значение в диапазоне мин. макс.
    while (
        a in question.chisla or a == question.rez_z
    ):  # Проверяем список chisla было ли сгенерировано такое же число ранее
        a += 1  # Если да увеличиваем значение
    question.chisla.append(
        a
    )  # Добавляем в список полученное неповотрябщееся число
    return a  # на выходе А-случайное число в диапазоне


# Генерация дробных чисел в качестве параметров передается Х-максимальное число, P-количество знаков после запятой
def rand_float(x, p):
    a = random.uniform(1, x)
    a = round(a, p)
    return a  # на выходе А-случайное дробное число в диапазоне с указанной точностью x.p


# Генерация boolean значений для вариантов ответов
def rand_boolean():
    a = random.randint(0, 1)
    if a:  # Если А=1 то будет значение True
        if str(a) in question.chisla:  # Если True же было сгенерировано ранее
            a = "False"  # Присваиваем значение False
            question.chisla.append(a)  # Заносим в список chisla
    else:  # Тоже самое проделываем если изначально А=0 и значение False
        if str(a) in question.chisla:
            question.chisla.append(a)
    return a


# Функция для генерации значения основных переменных
def random_var(question):
    question.a = rand_int(1, 10) * rand_int(1, 10)
    question.b = rand_int(1, 6) * rand_int(1, 6)

def random_ost1(question):
    question.a = rand_int(10, 999) 
    question.b = rand_int(2, 16) 

def random_ost2(question):
    question.a = rand_intА

# Функция для вывода задания теста %s места где вставляются переменные а в скобках сами переменные в порядке следования
def zadaine(question):
    # Текст задания ##########################################################################################
    text_z = """Пусть в тексте, содержащем {a} знаков, буква «р» встретилась {b} раз. Какое количество информации несет появление буквы «р» в тексте?
                """.format(a=question.a, b=question.b)
    return text_z

def zadaine_type_2(question):
    # Текст задания Тип 2
    text_z = """Какое количество информации несет сообщение о ходе первого игрока при игре в «крестики-нолики» на поле {a}X{a}? Ответ дать в битах.
                """.format(
        a=question.a
    )
    return text_z


def zadaine_type_3(question):
    # Текст задания Тип 3
    text_z = """В ящике находится {a} теннисных мяча, среди которых есть мячи желтого цвета. Наудачу вынимается один мяч. 
                Сообщение «извлечен мяч НЕ желтого цвета» несет {b} бита информации. Сколько мячей желтого цвета в ящике?
                """.format(
        a=question.a, b=question.b
    )
    return text_z

def ost_1(question):
    # 1 задача по теоретическим основам информатики
    text_z = """Преобразуйте каждое из приведенных ниже десятичных значений в эквивалентное d-ичное представление: {a}, d = {b};""".format(
        a=question.a, b=question.b
    )
    return text_z

# Функция для вычисления решения задания
def reshenie(question):
    f = 1
    k = question.a / question.b
    while k > 2:
        k = k / 2
        f += 1
    question.rez_z = f

# Функция для подготовки вариантов ответа
def variants(question):
    # Правильный вариант ответа
    var_pr = question.rez_z
    # Остальные варианты ответов
    otvety = generate_random_variables(var_pr)
    # находим какой букве теперь соответсвует правильный ответ
    prav_otv = otvety.index(var_pr)
    var_a, var_b, var_c, var_d = otvety[0:4]
    # на выходе получаем все ответы (ABCD)и номер правильного ответа (1234)
    return var_a, var_b, var_c, var_d, prav_otv


# Сценарий выполнения программы, последовательность выполнения функций
# Главная программа будет вызывать эту функцию чтобы получить задание
def main():  
    print(question.generate_question())
    return question.generate_question()


def generate_random_variables(answer):
    data = []
    while len(data) < 3:
        val = random.randint(1, 20)
        if val not in data and val != answer:
            data.append(val)

    data.append(answer)
    random.shuffle(data)

    return data

