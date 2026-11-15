@property
def is_terminal(self) -> bool:
    return self in (self.__class__.SHIPPED, self.__class__.CANCELLED)