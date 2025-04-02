class Vocab(dict):

    def put_text(self, text):
        if text is None:
            return None
        if not isinstance(text, str):
            raise Exception("annotation is not string")

        if text in self:
            return self[text]
        
        i = len(self) // 2
        self[text] = i
        self[i] = text
        return i
    
    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
