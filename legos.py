import random


def _init_null_matrix(width, height):
    matrix = []
    for w in range(width):
        matrix.append([None] * height)
    return matrix


class Brick(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # data structure to store which cells are occupied
        self.bottom = _init_null_matrix(self.width, self.height)
        self.top = _init_null_matrix(self.width, self.height)

    def connect(self, other_brick):
        raise NotImplementedError()


class Bucket(object):
    def __init__(self):
        # store width,height,ratio triplets for all legos in the bucket
        self.ratios = (
            (1, 1, 1),
            (2, 1, 1),
            (3, 1, 0.5),
            (4, 1, 0.25),
            (2, 2, 2),
            (3, 2, 4),
            (4, 2, 4),
        )
        self.cdf = []
        total = 0.0
        for w, h, r in self.ratios:
            total += r
            self.cdf.append(total)
        for i in range(len(self.cdf)):
            self.cdf[i] /= total

    def random_brick(self):
        # TODO bisection would be faster here
        r = random.random()
        for (w, h, _), c in zip(self.ratios, self.cdf):
            if r < c:
                return Brick(w, h)



class Contraption(object):
    def __init__(self):
        self.bricks = []

    def randomly_add_brick(self):
        
