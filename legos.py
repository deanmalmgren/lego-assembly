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

        # keep track of all of the pieces
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
            try:
                x0, y0 = self.random_x0_y0_on_top(w, h)
            except:
                print('FUCK', w, h)
                print('FUCK', self.footprint)
            z = self.max_z_in_area(x0, y0, x0+w, y0+h)
            self.place_brick(x0, y0, x0+w, y0+h, z+1)

    def randomly_assemble(self, bucket, n_pieces=10, verbose=False,
                          render=False, **kwargs):
        for i in range(n_pieces):
            w, h = bucket.random_brick()
            self.randomly_place_brick_on_top(w, h)
            if verbose:
                print("=" * 70, w, h)
                print(contraption)
            if render:
                self.render(filename="contraption-%03d.png" % i, **kwargs)

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

    def bounding_box(self):
        x0 = min(x for x, y in self.footprint)
        x1 = max(x for x, y in self.footprint)
        y0 = min(y for x, y in self.footprint)
        y1 = max(y for x, y in self.footprint)
        z0 = 0
        z1 = self.max_z_in_area(x0, y0, x1, y1)
        return x0, y0, z0, x1, y1, z1

    def density(self):
        x0, y0, z0, x1, y1, z1 = self.bounding_box()
        V = (x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1)
        v = 0.0
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if self.space[x][y][z]:
                        v += 1.0
        return v / V

    def render(self, filename='contraption.png', width=300, height=300,
               antialiasing=0.001):

        # place the camera
        xc, yc, zc = self.center_of_mass()
        # x0, y0, z0, x1, y1, z1 = self.bounding_box()
        camera = vapory.Camera(
            'location', [xc+10, zc+20, yc+10],
            'look_at',  [xc, zc, yc],
        )

        # create the background
        background = vapory.Background("color", hex2rgb("B6E0EA"))

        # create the light sources
        lights = [
            vapory.LightSource(
                [xc, zc+30, yc+5],
                'color',[0.8, 0.8, 0.8],
                # 'translate', [-10, 100, 100],
            ),
            vapory.LightSource(
                [xc, zc, yc],
                'color', [0.5, 0.5, 0.5],
                'translate', [100, 0, 100]
            ),
        ]

        # render the scene
        scene = vapory.Scene(
            camera,
            objects=self.render_objects + [background] + lights,
        )
        scene.render(
            filename, width=width, height=height, antialiasing=antialiasing,
        )


if __name__ == '__main__':
    bucket = Bucket()

    # # DEBUG command line printing of assembly
    # contraption = Contraption()
    # contraption.randomly_assemble(bucket, n_pieces=20, verbose=True)

    # DEBUG generate an aseembly and then render final image
    contraption = Contraption()
    contraption.randomly_assemble(bucket, n_pieces=20)
    contraption.render()

    # # DEBUG generate sequence of images during build
    # contraption = Contraption()
    # contraption.randomly_assemble(bucket, n_pieces=20, render=True)
    # contraption.randomly_assemble(bucket, n_pieces=20, render=True, width=1920, height=1080)

    # # DEBUG print out many contraptions
    # for i in range(10):
    #     contraption = Contraption()
    #     contraption.randomly_assemble(bucket, n_pieces=20)
    #     contraption.render(filename="contraption-sm-%03d.png" % i)
