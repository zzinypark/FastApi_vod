import random
from datetime import datetime

import sqids

sqid = sqids.Sqids()


class Squids:

    @classmethod
    def encode(cls, nums: list[int]) -> str:
        return sqid.encode(nums)


if __name__ == "__main__":
    now = datetime.now()
    print(
        Squids.encode(
            [now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond, random.randint(1, 9)]
        )
    )
