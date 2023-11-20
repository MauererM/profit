#Todo add header of file

class IndexData:
    def __init__(self, fname, interpol_days, data):
        self.name = fname
        self.interpol_days = interpol_days
        self.dates = data[0]
        self.values = data[1]