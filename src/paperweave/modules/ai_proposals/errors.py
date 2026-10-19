class ProposalNotFoundError(Exception):
    pass


class ProposalConflictError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class InvalidSelectionError(Exception):
    pass


class ProposalAdapterError(Exception):
    pass
