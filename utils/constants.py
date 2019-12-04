

class GlobalVariables:

    const_pub_type = ["ARTICLE", "BOOK", "BOOKLET",  # 0-2
                "CONFERENCE", "INBOOK", "INCOLLECTION",  # 3-5
                "INPROCEEDINGS", "MANUAL", "MASTERSTHESIS",  # 6-8
                "MISC", "PHDTHESIS", "PROCEEDINGS",  # 9-11
                "TECHREPORT", "UNPUBLISHED"]  # 12-13
    const_edge_tpe = ['PUBLISHED_IN', 'CITE', 'AUTHORED_BY']

    const_node_type = ['PUBLICATION', 'VENUE', 'PERSON']

    const_field_name = ['node_type', 'id', 'author',  # 0-2
                        'editor', 'title', 'journal',  # 3-5
                        'publisher', 'year', 'volume',  # 6-8
                        'number', 'pages', 'month',  # 9-11
                        'note', 'series', 'address',  # 12-14
                        'edition', 'chapter', 'book_title',  # 15-17
                        'organization', 'how_published', 'school',  # 18-20
                        'keywords', 'type', 'institution',  # 21-23
                        'abstract', 'note_id', 'ei_index',  # 24-26
                        'sci_index', 'ssci_index', 'added_by',  # 27-29
                        'modified_date', 'uuid', 'added_date']  # 30-32
    pub_unique_fields = ["uuid", "id", ["title", "journal", "year", "author"]]  # 现只用前两项，第三项涉及到文献类型，后面再修改

    def get_var(self, var_name):
        if var_name == 'pub_type':
            return self.const_pub_type
        elif var_name == "edge_type":
            return self.const_edge_tpe
        elif var_name == 'node_type':
            return self.const_node_type
        elif var_name == 'field_name':
            return self.const_field_name
        else:
            return None
