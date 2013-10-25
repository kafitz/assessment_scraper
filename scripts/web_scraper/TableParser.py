#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

from BeautifulSoup import BeautifulSoup


class ParseTable(object):
    ''' This class is heavily specific to evalweb.ville.montreal.qc.ca and is
        never intended to be adaptable other than as a simple model.'''

    def __init__(self, html_source=object):
        self.bad_soup = BeautifulSoup(html_source)

    def extract_tables(self):
        ''' Add tables each to their own list. Can't use BeautifulSoup
        table' html tag because of sloppy programming on assessment page.'''

        tag_list = self.bad_soup.findAll(['h2', 'tr'])
        tables_list = []
        for item in tag_list:
            if item.name == 'h2':
                table = [item.text]
                tables_list.append(table)
            if item.name == 'tr':
                # Get the most recently added table
                th_objects = item.findAll('th')
                for th in th_objects:
                    # Remove html junk
                    nohtml_th = th.text.split('&nbsp')[0]
                    clean_th = nohtml_th.rstrip()
                    tables_list[-1].append(clean_th)

                td_objects = item.findAll('td')
                for td in td_objects:
                    nohtml_td = td.text.split('&nbsp')[0]
                    clean_td = nohtml_td.rstrip()
                    tables_list[-1].append(clean_td)

        self.return_table = []

        # Table1
        table1 = tables_list[0]
        self.parse_table1(table1)

        # Table 2
        table2 = tables_list[1]
        self.parse_table2(table2)

        # Table 3
        table3 = tables_list[2]
        self.parse_table3(table3)

        # Table 4
        table4 = tables_list[3]
        self.parse_table4(table4)

        try:
            # Table 5
            table5 = tables_list[4]
            self.parse_table5(table5)
        except:
            pass  # No Cadastres listed

    def parse_table1(self, table):
        # Unicode objects stored to tuple (if tuple printed, text will be
        # different that tuple[index]
        header = table[0]
        # Split string on whitespace and rejoin it, removing excess between
        # words
        split_address = table[2].split()
        formatted_address = ' '.join(split_address)
        address_tuple = ("address", formatted_address)
        municipality_tuple = ("municipality", table[5])
        owner_raw = table[6]
        owner_raw = ' '.join(owner_raw.split())
        owner = owner_raw.split('th&gt')[0]  # Remove trailing junk from string
        owner_tuple = ("principal_owner", owner)
        neighborhood_tuple = ("neighborhood", table[9])
        no_arr_tuple = ("no_arr", table[10])
        matricule_tuple = ("civic_number", table[14])
        account_tuple = ("account_number", table[15])
        iduef_tuple = ("id_uef", table[16])

        # print header
        # print address_tuple
        # print municipality_tuple
        # print owner_tuple
        # print neighborhood_tuple
        # print no_arr_tuple
        # print matricule_tuple
        # print account_tuple
        # print iduef_tuple

        self.return_table.append(header)
        self.return_table.append(address_tuple)
        self.return_table.append(municipality_tuple)
        self.return_table.append(owner_tuple)
        self.return_table.append(neighborhood_tuple)
        self.return_table.append(no_arr_tuple)
        self.return_table.append(matricule_tuple)
        self.return_table.append(account_tuple)
        self.return_table.append(account_tuple)
        self.return_table.append(iduef_tuple)

    def parse_table2(self, table):
        header = table[0]
        cubf_tuple = ("cubf", table[8])
        no_of_units_tuple = ("no_of_units", table[9])
        unite_de_voisinage_tuple = ("unite_de_voisinage_score", table[10])
        lot_width_tuple = ("lot_width", table[11])
        lot_depth_tuple = ("lot_depth", table[12])
        lot_area_tuple = ("lot_area", table[13])
        non_residential_tuple = (
            "non-residential_class", table[21])  # None if false
        industrial_tuple = ("industrial_class", table[22])  # None if false
        terrain_vague_tuple = ("terrain_vague_desservi", table[23])
        year_built_tuple = ("year_built", table[24])
        number_of_floors_tuple = ("number_of_floors", table[25])
        other_locations_tuple = ("number_of_other_locations", table[26])

        # print header
        # print cubf_tuple
        # print no_of_units_tuple
        # print unite_de_voisinage_tuple
        # print lot_width_tuple
        # print lot_depth_tuple
        # print lot_area_tuple
        # print non_residential_tuple
        # print industrial_tuple
        # print terrain_vague_tuple
        # print year_built_tuple
        # print number_of_floors_tuple
        # print other_locations_tuple

        self.return_table.append(header)
        self.return_table.append(cubf_tuple)
        self.return_table.append(no_of_units_tuple)
        self.return_table.append(unite_de_voisinage_tuple)
        self.return_table.append(lot_width_tuple)
        self.return_table.append(lot_depth_tuple)
        self.return_table.append(lot_area_tuple)
        self.return_table.append(non_residential_tuple)
        self.return_table.append(industrial_tuple)
        self.return_table.append(terrain_vague_tuple)
        self.return_table.append(year_built_tuple)
        self.return_table.append(number_of_floors_tuple)
        self.return_table.append(other_locations_tuple)

    def parse_table3(self, table):
        header = table[0]
        role_year_tuple = ("role_year", table[6])
        land_value_tuple = ("land_value", table[7])
        building_value_tuple = ("building_value", table[8])
        property_value_tuple = ("total_property_value", table[9])

        # print header
        # print role_year_tuple
        # print land_value_tuple
        # print building_value_tuple
        # print property_value_tuple

        self.return_table.append(header)
        self.return_table.append(role_year_tuple)
        self.return_table.append(land_value_tuple)
        self.return_table.append(building_value_tuple)
        self.return_table.append(property_value_tuple)

    def parse_table4(self, table):
        header = table[0]
        land_value_tuple = ("land_value", table[16])
        building_value_tuple = ("building_value", table[17])
        property_value_tuple = ("total_property_value", table[18])
        imposition_tuple = ("imposition_code", table[19])
        exemption_tuple = ("exemption_code", table[20])

        # print header
        # print land_value_tuple
        # print building_value_tuple
        # print property_value_tuple
        # print imposition_tuple
        # print exemption_tuple

        self.return_table.append(header)
        self.return_table.append(land_value_tuple)
        self.return_table.append(building_value_tuple)
        self.return_table.append(property_value_tuple)
        self.return_table.append(imposition_tuple)
        self.return_table.append(exemption_tuple)

    def parse_table5(self, table):
        header = 'CADASTRES'
        del table[0]
        index = 1
        # Iterate through table for as many cadastres are listed
        while True:
            if len(table) > 8:
                del table[:8]
                # Needs to somehow check if there's multiple cadastres in table
                renovated_lot_num_tuple = ("renovated_lot_number", table[0])
                paroisse_tuple = ("paroisse", table[1])
                lot_tuple = ("lot", table[2])
                subdivision_tuple = ("subdivision", table[3])
                type_of_lot_tuple = ("type_of_lot", table[4])
                cadastre_area_tuple = ("cadastre_area", table[5])
                cadastre_width_tuple = ("cadastre_depth", table[6])

                iteration_header = header + " " + str(index)

                # print iteration_header
                # print renovated_lot_num_tuple
                # print paroisse_tuple
                # print lot_tuple
                # print subdivision_tuple
                # print type_of_lot_tuple
                # print cadastre_area_tuple
                # print cadastre_width_tuple

                self.return_table.append(iteration_header)
                self.return_table.append(renovated_lot_num_tuple)
                self.return_table.append(paroisse_tuple)
                self.return_table.append(lot_tuple)
                self.return_table.append(subdivision_tuple)
                self.return_table.append(type_of_lot_tuple)
                self.return_table.append(cadastre_area_tuple)
                self.return_table.append(cadastre_width_tuple)

                index += 1
            else:
                break
