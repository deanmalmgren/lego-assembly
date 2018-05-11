import random
import copy

import vapory


def hex2rgb(hex):
    return tuple(float(int(hex[i:i+2], 16))/255.0 for i in (0, 2 ,4))


# brick sizes
# http://lego.wikia.com/wiki/Brick#Sizes
# http://lego.wikia.com/wiki/Colour_Palette
HEIGHT_TO_WIDTH_RATIO = 1.2
DOT_RADIUS = (1 - HEIGHT_TO_WIDTH_RATIO/3) / 2
DOT_HEIGHT = 0.2
COLORS = [
    "ff0000",
    "1c58a7",
    "Ffff00",
    "9C9291",
    "0000ff",
    "00ff00",
    "ff6600",
    "95B90B",
    "002541",
    "80081B",
    "7b5d41",
    "990066",
]
COLORS = [hex2rgb(hex) for hex in COLORS]


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
                return w, h


class Contraption(object):
    def __init__(self, X=80, Y=40, Z=20):
        self.n_bricks = 0
        self.X = X
        self.Y = Y
        self.Z = Z

        # space stores a 3D representation of whether a particular lego 1x1x1
        # is occupied
        self.space = []
        for x in range(self.X):
            ys = []
            for y in range(self.Y):
                zs = [False] * self.Z
                ys.append(zs)
            self.space.append(ys)

        # footprint stores a list of all x,y coordinates that are occupied
        self.footprint = set()

        # render the pieces
        self.render_objects = []

    def __repr__(self):
        s = ''
        for y in reversed(range(self.Y)):
            for x in range(self.X):
                max_z = self.max_z(x, y)
                if max_z > 0:
                    s += str(max_z)
                else:
                    s += ' '
            s += '\n'
        return s

    def place_brick(self, x0, y0, x1, y1, z):
        # fill the space
        for x in range(x0, x1):
            for y in range(y0, y1):
                if self.space[x][y][z]:
                    raise 'that shouldnt happen'
                self.space[x][y][z] = True
                self.footprint.add((x, y))

        # render the bricks
        color = COLORS[self.n_bricks % len(COLORS)]
        self.render_objects.append(vapory.Box(
            [x0-0.5, (z - 1) * HEIGHT_TO_WIDTH_RATIO, y0-0.5],
            [x1-0.5, z * HEIGHT_TO_WIDTH_RATIO, y1-0.5],
            vapory.Texture(
                vapory.Pigment('color', color),
            ),
        ))
        for x in range(x0, x1):
            for y in range(y0, y1):
                self.render_objects.append(vapory.Cylinder(
                    [x, z * HEIGHT_TO_WIDTH_RATIO, y],
                    [x, z * HEIGHT_TO_WIDTH_RATIO + DOT_HEIGHT, y],
                    DOT_RADIUS,
                    vapory.Texture(
                        vapory.Pigment('color', color),
                    ),
                ))

        self.n_bricks += 1


    def max_z(self, x, y):
        # TODO: bisection OR smarter data structures
        for z in reversed(range(self.Z)):
            if self.space[x][y][z]:
                return z
        return 0

    def max_z_in_area(self, x0, y0, x1, y1):
        z = 0
        for x in range(x0, x1):
            for y in range(y0, y1):
                z = max(z, self.max_z(x, y))
        return z

    def randomly_flip_brick(self, w, h):
        if random.random() < 0.5:
            return w, h
        else:
            return h, w

    def random_x0y0(self, w, h):
        x0 = random.randint(0, self.X-w-1)
        y0 = random.randint(0, self.Y-h-1)
        return x0, y0

    def random_x0_y0_on_top(self, w, h):
        xys_with_adjascent = set()
        for x, y in self.footprint:
            if x + w < self.X and y + h < self.Y:
                xys_with_adjascent.add((x, y))
                if self.space[x][y][0]:
                    if x - 1 > 0:
                        xys_with_adjascent.add((x - 1, y))
                    if x + 1 < self.X:
                        xys_with_adjascent.add((x + 1, y))
                    if y - 1 > 0:
                        xys_with_adjascent.add((x, y - 1))
                    if y + 1 < self.Y:
                        xys_with_adjascent.add((x, y + 1))
        return random.choice(list(xys_with_adjascent))

    def randomly_place_brick_down(self, w, h):
        w, h = self.randomly_flip_brick(w, h)
        x0, y0 = self.random_x0y0(w, h)
        z = self.max_z_in_area(x0, y0, x0+w, y0+h)
        self.place_brick(x0, y0, x0+w, y0+h, z+1)

    def randomly_place_brick_on_top(self, w, h):

        # place first brick
        if self.n_bricks == 0:
            self.randomly_place_brick_down(w, h)

        else:
            w, h = self.randomly_flip_brick(w, h)
            x0, y0 = self.random_x0_y0_on_top(w, h)
            try:
                z = self.max_z_in_area(x0, y0, x0+w, y0+h)
            except:
                print('FUCK', x0, y0, w, h)
                raise
            self.place_brick(x0, y0, x0+w, y0+h, z+1)

    def randomly_assemble(self, bucket, n_pieces=10, verbose=False):
        for i in range(n_pieces):
            w, h = bucket.random_brick()
            self.randomly_place_brick_on_top(w, h)
            if verbose:
                print("=" * 70, w, h)
                print(contraption)

    def center_of_mass(self):
        xc, yc, zc = 0.0, 0.0, 0.0
        n = 0
        for x in range(self.X):
            for y in range(self.Y):
                for z in range(self.Z):
                    if self.space[x][y][z]:
                        xc += x
                        yc += y
                        zc += z
                        n += 1
        xc /= n
        yc /= n
        zc /= n
        return xc, yc, zc

    def render(self, filename='contraption.png', width=300, height=300,
               antialiasing=0.001):

        # add the background color and light sources
        self.render_objects.extend([
            vapory.Background("color", [77./255, 149./255, 232./255]),
            vapory.LightSource(
                [0, 0, 0],
                'color',[1, 1, 1],
                'translate', [-100, 100, 100],
            ),
            vapory.LightSource(
                [0, 0, 0],
                'color', [0.5, 0.5, 0.5],
                'translate', [100, -50, 50]
            ),
        ])

        # place the camera
        # TODO tailor location, look_at based on location of things
        xc, yc, zc = self.center_of_mass()
        camera = vapory.Camera(
            'location',  [xc+10, zc+8, yc+10], #0.0, 0.5, -4.0],
            # 'direction', [0, 0, 1.5],
            'look_at',  [xc, zc, yc],
        )

        # render the scene
        scene = vapory.Scene(camera, objects=self.render_objects)
        scene.render(
            filename, width=width, height=height, antialiasing=antialiasing,
        )


if __name__ == '__main__':
    bucket = Bucket()
    contraption = Contraption()
    # contraption.randomly_assemble(bucket, n_pieces=20, verbose=True)
    contraption.randomly_assemble(bucket, n_pieces=20)
    contraption.render()
