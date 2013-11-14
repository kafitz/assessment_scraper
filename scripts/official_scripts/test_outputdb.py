#!/usr/bin/env python
# Kyle Fitzsimmons 2013

from DatabaseConns import Database

OUTPUT_DB = 'test_output.db'
TEST_DATA = [{
    'start_address': 4295, 
    'db_suite': None, 
    'orientation': None, 
    'article_code': None, 
    'total_value': 411000.0, 
    'end_address': 4299, 
    'street_name': 'DROLET', 
    'suite_num': u'', 
    'land_value': 133800.0, 
    'building_value': 277200.0, 
    'street_number_upper': u'4299', 
    'street_type': 'rue', 
    'street_code': '80', 
    'sale_price': 375000.0, 
    'street_nominal': 'Rue Drolet', 
    'joining_article': None, 
    'street_number_lower': u'4295'
    }]


def main():
    db = Database(OUTPUT_DB)
    db.write_rows(TEST_DATA)


if __name__ == '__main__':
    main()