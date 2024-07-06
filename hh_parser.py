import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import os
import psycopg2

import config

# Функция для получения html-кода страницы
def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return response.text

# Функция для парсинга данных о вакансиях
def parse_vacancies(html):
    soup = BeautifulSoup(html, 'lxml')

    # Получаем блок с фильтрами
    filters = soup.find('div', {'class': 'bloko-column bloko-column_xs-0 bloko-column_s-0 bloko-column_m-3 bloko-column_l-3'})
    
    # Получаем данные из фильтров
    data = {}
    for filter in filters.find_all('fieldset', {'class': 'novafilters-group-wrapper'}):
        try:
            title = filter.find('legend').text.strip()
        except:
            continue
        items = []
        for item in filter.find_all('li', {'class': 'novafilters-list__item'}):
            name_text = item.find('span', {'data-qa': 'serp__novafilter-title'})
            try:
                name_text = name_text.text.replace('\xa0', ' ').replace("\u202f", "")
            except:
                continue

            try:
                count = int(item.find('span', {'class': 'bloko-text bloko-text_tertiary'}).text.replace('\xa0', ' ').replace("\u202f", ""))
            except:
                count = 0

            items.append((name_text, count))
        data[title] = items

    # Удаление малозначимых полей и полей ввода (в полях ввода всегда нули)
    list_for_excluding = ["Исключить слова", "Ключевые слова", "Регион", "Специализации", "Отрасль компании"]
    for item in list_for_excluding:
        data.pop(item)

    # Убрать поле "Своя зарплата", где на сайте ввод данных 
    # и поэтому при парсинге в этом поле всегда 0
    data["Уровень дохода"].pop(-2)

    return data


def print_data(data):
    for key in data:
        print(key)
        for item in data[key]:
            if item[0]:
                print(f"{item[0]}: {item[1]}")
        print()

def get_data(data):
    string = ""
    for key in data:
        string += f'{key}\n'
        for item in data[key]:
            if item[0]:
                string += f"{item[0]}: {item[1]}\n"
        string += "\n"
    return string

def build_histogram(data, save_dir = "pics"):
    # Итерация по ключам в data
    for key, items in data.items():
        # Создание новой фигуры для каждой диаграммы
        plt.figure(figsize=(12, 8))

        # Создание списков для подписей и данных
        labels = [item[0] for item in items]
        values = [item[1] for item in items]

        # Разбиение меток на отдельные строки через каждые 15 символов
        for element_index, label in enumerate(labels):
            counter = 0
            for string_index, char in enumerate(label[:-1]):
                if char != " ":
                    counter += 1
                elif char == " " and counter > 5 and not label[string_index + 1].isdigit():
                    labels[element_index] = label[:string_index] + "\n" + label[string_index + 1:]
                    counter = 0

        # Создание столбчатой диаграммы
        plt.bar(labels, values)

        # Добавление заголовка диаграммы (название)
        plt.title(key)

        plt.tight_layout()

        # Отображение диаграммы
        #plt.show()

        # Создание папки, если она не существует
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        plt.savefig(os.path.join(save_dir, f'{key}.png'))



def write_to_db(data, query_text):

    # подключение к базе данных
    conn = psycopg2.connect(
        dbname= config.dbname,
        user=config.user,
        password=config.password,
        host=config.host
    )

    # создание курсора
    cur = conn.cursor()

    # проверка, существует ли запрос в таблице requests
    cur.execute("SELECT id FROM requests WHERE query_text = %s", (query_text,))
    request_id = cur.fetchone()

    # если запрос не существует, добавляем его в таблицу requests и вставляем данные в таблицы
    if request_id is None:
        cur.execute("INSERT INTO requests (query_text) VALUES (%s) RETURNING id", (query_text,))
        request_id = cur.fetchone()[0]

        cur.execute("INSERT INTO part_time_jobs (request_id, num_from_4_hours_per_day, in_the_evenings, on_weekends, one_time_task) VALUES (%s, %s, %s, %s, %s)",
                    (request_id, data['Подработка'][0][1], data['Подработка'][1][1], data['Подработка'][2][1], data['Подработка'][3][1]))

        # cur.execute("INSERT INTO income_levels (request_id, starts_from_10_000, starts_from_50_000, starts_from_90_000, starts_from_130_000, starts_from_170_000, starts_from_210_000, is_indicated_by_income) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        #             (request_id, data['Уровень дохода'][0][1], data['Уровень дохода'][1][1], data['Уровень дохода'][2][1], data['Уровень дохода'][3][1], data['Уровень дохода'][4][1], data['Уровень дохода'][5][1], data['Уровень дохода'][6][1]))

        cur.execute("INSERT INTO education_levels (request_id, not_required_or_not_specified, secondary_vocational, higher_education) VALUES (%s, %s, %s, %s)",
                    (request_id, data['Образование'][0][1], data['Образование'][1][1], data['Образование'][2][1]))

        cur.execute("INSERT INTO work_experience (request_id, it_doesnt_matter, no_experience, from_1_year_to_3_years, from_3_to_6_years, more_than_6_years) VALUES (%s, %s, %s, %s, %s, %s)",
                    (request_id, data['Опыт работы'][0][1], data['Опыт работы'][1][1], data['Опыт работы'][2][1], data['Опыт работы'][3][1], data['Опыт работы'][4][1]))

        # cur.execute("INSERT INTO employment_types (request_id, full_time, part_time, internship, project_work, volunteering, registration_by_GPH_or_part_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        #             (request_id, data['Тип занятости'][0][1], data['Тип занятости'][1][1], data['Тип занятости'][2][1], data['Тип занятости'][3][1], data['Тип занятости'][4][1], data['Тип занятости'][5][1]))

        cur.execute("INSERT INTO work_schedules (request_id, full_day, shift_schedule, shift_method, flexible_schedule, remote_work) VALUES (%s, %s, %s, %s, %s, %s)",
                    (request_id, data['График работы'][0][1], data['График работы'][1][1], data['График работы'][2][1], data['График работы'][3][1], data['График работы'][4][1]))

        cur.execute("INSERT INTO other_parameters (request_id, no_vacancies_from_recruitment_agencies, with_the_address, less_than_10_responses, accessible_to_people_with_disabilities, from_accredited_IT_companies, available_from_the_age_of_14) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (request_id, data['Другие параметры'][0][1], data['Другие параметры'][1][1], data['Другие параметры'][2][1], data['Другие параметры'][3][1], data['Другие параметры'][4][1], data['Другие параметры'][5][1]))
    # если запрос существует, обновляем данные в таблицах
    else:
        request_id = request_id[0]

        cur.execute("UPDATE part_time_jobs SET num_from_4_hours_per_day = %s, in_the_evenings = %s, on_weekends = %s, one_time_task = %s WHERE request_id = %s",
                    (data['Подработка'][0][1], data['Подработка'][1][1], data['Подработка'][2][1], data['Подработка'][3][1], request_id))

        # cur.execute("UPDATE income_levels SET starts_from_10_000 = %s, starts_from_50_000 = %s, starts_from_90_000 = %s, starts_from_130_000 = %s, starts_from_170_000 = %s, starts_from_210_000 = %s, is_indicated_by_income = %s WHERE request_id = %s",
        #             (data['Уровень дохода'][0][1], data['Уровень дохода'][1][1], data['Уровень дохода'][2][1], data['Уровень дохода'][3][1], data['Уровень дохода'][4][1], data['Уровень дохода'][5][1], data['Уровень дохода'][6][1], request_id))

        cur.execute("UPDATE education_levels SET not_required_or_not_specified = %s, secondary_vocational = %s, higher_education = %s WHERE request_id = %s",
                    (data['Образование'][0][1], data['Образование'][1][1], data['Образование'][2][1], request_id))

        cur.execute("UPDATE work_experience SET it_doesnt_matter = %s, no_experience = %s, from_1_year_to_3_years = %s, from_3_to_6_years = %s, more_than_6_years = %s WHERE request_id = %s",
                    (data['Опыт работы'][0][1], data['Опыт работы'][1][1], data['Опыт работы'][2][1], data['Опыт работы'][3][1], data['Опыт работы'][4][1], request_id))

        # cur.execute("UPDATE employment_types SET full_time = %s, part_time = %s, internship = %s, project_work = %s, volunteering = %s, registration_by_GPH_or_part_time = %s WHERE request_id = %s",
        #             (data['Тип занятости'][0][1], data['Тип занятости'][1][1], data['Тип занятости'][2][1], data['Тип занятости'][3][1], data['Тип занятости'][4][1], data['Тип занятости'][5][1], request_id))

        cur.execute("UPDATE work_schedules SET full_day = %s, shift_schedule = %s, shift_method = %s, flexible_schedule = %s, remote_work = %s WHERE request_id = %s",
                    (data['График работы'][0][1], data['График работы'][1][1], data['График работы'][2][1], data['График работы'][3][1], data['График работы'][4][1], request_id))

        cur.execute("UPDATE other_parameters SET no_vacancies_from_recruitment_agencies = %s, with_the_address = %s, less_than_10_responses = %s, accessible_to_people_with_disabilities = %s, from_accredited_IT_companies = %s, available_from_the_age_of_14 = %s WHERE request_id = %s",
                    (data['Другие параметры'][0][1], data['Другие параметры'][1][1], data['Другие параметры'][2][1], data['Другие параметры'][3][1], data['Другие параметры'][4][1], data['Другие параметры'][5][1], request_id))

    # подтверждение записи данных в базу данных
    conn.commit()

    # закрытие курсора и соединения
    cur.close()
    conn.close()

def select_db():
    # подключение к базе данных
    conn = psycopg2.connect(
        dbname= config.dbname,
        user=config.user,
        password=config.password,
        host=config.host
    )

    # создание курсора
    cur = conn.cursor()

    # выполнение запроса SELECT для извлечения данных из таблиц
    cur.execute("""
    SELECT
        pt.num_from_4_hours_per_day,
        pt.in_the_evenings,
        pt.on_weekends,
        pt.one_time_task,
        ed.not_required_or_not_specified,
        ed.secondary_vocational,
        ed.higher_education,
        we.it_doesnt_matter,
        we.no_experience,
        we.from_1_year_to_3_years,
        we.from_3_to_6_years,
        we.more_than_6_years,
        ws.full_day,
        ws.shift_schedule,
        ws.shift_method,
        ws.flexible_schedule,
        ws.remote_work,
        op.no_vacancies_from_recruitment_agencies,
        op.with_the_address,
        op.less_than_10_responses,
        op.accessible_to_people_with_disabilities,
        op.from_accredited_IT_companies,
        op.available_from_the_age_of_14
    FROM
        part_time_jobs pt
    JOIN
        education_levels ed ON pt.request_id = ed.request_id
    JOIN
        work_experience we ON pt.request_id = we.request_id
    JOIN
        work_schedules ws ON pt.request_id = ws.request_id
    JOIN
        other_parameters op ON pt.request_id = op.request_id
    """)

    # извлечение данных из результата запроса
    data = cur.fetchall()

    # преобразование данных в словарь для удобства работы
    data_dict = {
        "Подработка": [
            ("От 4 часов в день", data[0][0]),
            ("По вечерам", data[0][1]),
            ("По выходным", data[0][2]),
            ("Разовое задание", data[0][3])
        ],
        "Образование": [
            ("Не требуется или не указано", data[0][4]),
            ("Среднее профессиональное", data[0][5]),
            ("Высшее", data[0][6])
        ],
        "Опыт работы": [
            ("Не имеет значения", data[0][7]),
            ("Нет опыта", data[0][8]),
            ("От 1 года до 3 лет", data[0][9]),
            ("От 3 до 6 лет", data[0][10]),
            ("Более 6 лет", data[0][11])
        ],
        "График работы": [
            ("Полный день", data[0][12]),
            ("Сменный график", data[0][13]),
            ("Вахтовый метод", data[0][14]),
            ("Гибкий график", data[0][15]),
            ("Удаленная работа", data[0][16])
        ],
        "Другие параметры": [
            ("Без вакансий от кадровых агентств", data[0][17]),
            ("Меньше 10 откликов", data[0][19]),
            ("С адресом", data[0][18]),
            ("Доступные людям с инвалидностью", data[0][20]),
            ("Доступные с 14 лет", data[0][22]),
            ("От аккредитованных ИТ-компаний", data[0][21])
        ]
    }

    
    # построение гистограмм
    build_histogram(data_dict)

    # закрытие курсора и соединения
    cur.close()
    conn.close()

    return get_data(data_dict)


def parseing(search):

    search = "+".join(search.split())

    # Ссылка на сайт
    url = f'https://hh.ru/search/vacancy?text={search}&area=113&hhtmFrom=main&hhtmFromLabel=vacancy_search_line'

    # Получаем html-код страницы
    html = get_html(url)

    # Парсим данные о вакансиях
    data = parse_vacancies(html)

    write_to_db(data, search)
    return select_db()


def main():
    search = input("Введите название вакансии: ")

    search = "+".join(search.split())

    # Ссылка на сайт
    url = f'https://hh.ru/search/vacancy?text={search}&area=113&hhtmFrom=main&hhtmFromLabel=vacancy_search_line'

    # Получаем html-код страницы
    html = get_html(url)

    # Парсим данные о вакансиях
    data = parse_vacancies(html)

    # print(data) 

    # print_data(data)

    # build_histogram(data)

    write_to_db(data, search)

    select_db()
