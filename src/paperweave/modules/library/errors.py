class SourceNotFoundError(LookupError): pass
class DuplicateSourceError(ValueError):
    def __init__(self, source_id: str):
        self.source_id = source_id
        super().__init__("An equivalent source record already exists in the project")
class DuplicateFileError(ValueError): pass
class InvalidPdfError(ValueError): pass
class FileTooLargeError(ValueError): pass
class ReferencedFileError(ValueError): pass
