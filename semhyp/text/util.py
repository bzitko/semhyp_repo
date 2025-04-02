class IOBTag(str):

    @property
    def iob(self):
        i = self.find("-")
        if i >= 0:
            return self[:i]
        return self

    @property
    def tag(self):
        i = self.find("-")
        if i >= 0:
            return self[i + 1:]
        return ""

    @staticmethod
    def create(iob, tag=""):
        if tag != "":
            return IOBTag(f"{iob}-{tag}")
        return IOBTag(iob)

    @staticmethod
    def single(lbl):
        return IOBTag(f"S-{lbl}")

    @staticmethod
    def begin(lbl):
        return IOBTag(f"B-{lbl}")

    @staticmethod
    def inside(lbl):
        return IOBTag(f"I-{lbl}")

    @staticmethod
    def end(lbl):
        return IOBTag(f"E-{lbl}")

    @staticmethod
    def other():
        return IOBTag("O")
    
    def is_other(self):
        return self == "O"