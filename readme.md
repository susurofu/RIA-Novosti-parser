# Парсер новостей РИА-НОВОСТИ

Этот скрипт загружает все новости, опубликованные на сайте новостного агенства [РИА-НОВОСТИ](https://ria.ru). Скрипт парсит новости, опубликованные в теченение каждого дня, за введенный интервал дат. В последующем будет реализован поиск по ключевым словам.

`python ria-novosti-parser.py --start_date 2020-01-01 --end_date 2020-03-03`

Результат сохраняется отдельно для каждого месяца в csv-файлы в рабочей директории.


# RIA-NOVOSTI news parser

This script downloads all news published on the website of the news agency [RIA-NOVOSTI](https://ria.ru). The script parses news published during each day, for the entered date range. Subsequently, a search by keywords will be implemented.

`python ria-novosti-parser.py --start_date 2020-01-01 --end_date 2020-03-03`

The result is saved separately for each month in csv files in the working directory.