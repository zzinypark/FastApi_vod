import string
from typing import Final


class Base62:
    BASE: Final[str] = string.ascii_letters + string.digits
    BASE_LEN: Final[int] = len(BASE)

    @classmethod
    def encode(cls, num: int) -> str:
        if num < 0:
            raise ValueError("양의 정수를 입력하세요")

        if num == 0:
            return cls.BASE[0]

        result = []
        while num:
            num, remainder = divmod(num, cls.BASE_LEN)
            result.append(cls.BASE[remainder])
        return "".join(result)


print(Base62.encode(100))
