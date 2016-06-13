class Model:
    def __init__(self, name):
        self.name = name
        self.pages = []

    def get_page_by_name(self, name):
        for p in self.pages:
            if p.name == name:
                return p
        return None

class Page:
    def __init__(self, name):
        self.name = name
        self.widgets = []

    def get_binary_fields(self):
        result = []
        for w in self.widgets:
            result += w.get_binary_fields()
        return result

    def get_text_areas(self):
        result = []
        for w in self.widgets:
            result += w.get_text_areas()
        return result


class Text:
    def __init__(self, text, position, fontname='Arial', fontsize=12):
        self.text = text
        self.position = position
        self.fontname = fontname
        self.fontsize = fontsize
        self.rotation = 0

    def get_binary_fields(self):
        return []

    def get_text_areas(self):
        return [self]


class BinaryField:
    def __init__(self, identifier, position, hint=''):
        self.name = identifier
        self.position = position
        self.hint = hint

    def get_binary_fields(self):
        return [self]

    def get_text_areas(self):
        return []