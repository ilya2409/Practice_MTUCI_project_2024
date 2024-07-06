import psycopg2
import config

def create_db():
    # подключение к базе данных
    conn = psycopg2.connect(
        dbname= config.dbname,
        user=config.user,
        password=config.password,
        host=config.host
    )

    # создание курсора
    cur = conn.cursor()

    # создание таблицы запросов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL
        )
    """)

    # создание таблицы вакансий с количеством по часам в день
    cur.execute("""
        CREATE TABLE IF NOT EXISTS part_time_jobs (
            request_id INTEGER REFERENCES requests(id),
            num_from_4_hours_per_day INTEGER,   
            in_the_evenings INTEGER,
            on_weekends INTEGER,
            one_time_task INTEGER,
            PRIMARY KEY (request_id)
        )
    """)

    # создание таблицы вакансий с уровнем дохода
    cur.execute("""
        CREATE TABLE IF NOT EXISTS income_levels (
            request_id INTEGER REFERENCES requests(id),
            starts_from_10_000 INTEGER,   
            starts_from_50_000 INTEGER,   
            starts_from_90_000 INTEGER,  
            starts_from_130_000 INTEGER,  
            starts_from_170_000 INTEGER,  
            starts_from_210_000 INTEGER,  
            is_indicated_by_income INTEGER, 
            PRIMARY KEY (request_id)
        )
    """)

    # создание таблицы вакансий по образованию
    cur.execute("""
        CREATE TABLE IF NOT EXISTS education_levels (
            request_id INTEGER REFERENCES requests(id),
            not_required_or_not_specified INTEGER,
            secondary_vocational INTEGER,
            higher_education INTEGER,
            PRIMARY KEY (request_id)
        )
    """)

    # создание таблицы вакансий по опыту работы
    cur.execute("""
        CREATE TABLE IF NOT EXISTS work_experience (
            request_id INTEGER REFERENCES requests(id),
            it_doesnt_matter INTEGER, 
            no_experience INTEGER, 
            from_1_year_to_3_years INTEGER, 
            from_3_to_6_years INTEGER, 
            more_than_6_years INTEGER,
            PRIMARY KEY (request_id)
        )
    """)

    # создание таблицы вакансий по типу занятости
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employment_types (
            request_id INTEGER REFERENCES requests(id),
            full_time INTEGER,
            part_time INTEGER,
            internship INTEGER,
            project_work INTEGER,
            volunteering INTEGER,
            registration_by_GPH_or_part_time INTEGER, 
            PRIMARY KEY (request_id)
        )
    """)

    # создание таблицы вакансий по графику работы
    cur.execute("""
        CREATE TABLE IF NOT EXISTS work_schedules (
            request_id INTEGER REFERENCES requests(id),
            full_day INTEGER,
            shift_schedule INTEGER,
            shift_method INTEGER,
            flexible_schedule INTEGER,
            remote_work INTEGER,
            PRIMARY KEY (request_id)
        )
    """)

    # создание таблицы вакансий с другими параметрами
    cur.execute("""
        CREATE TABLE IF NOT EXISTS other_parameters (
            request_id INTEGER REFERENCES requests(id),
            no_vacancies_from_recruitment_agencies INTEGER, 
            with_the_address INTEGER, 
            less_than_10_responses INTEGER, 
            accessible_to_people_with_disabilities INTEGER, 
            from_accredited_IT_companies INTEGER,
            available_from_the_age_of_14 INTEGER,
            PRIMARY KEY (request_id)
        )
    """)

    # подтверждение создания таблиц
    conn.commit()

    # закрытие курсора и соединения
    cur.close()
    conn.close()
