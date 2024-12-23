import math
import random


class Perlin:
    def __init__(self, seed: int):
        self.seed = seed
        self.gradients = {}

    def _random_gradient(self, x: float, y: float) -> tuple[float, float]:
        random.seed(self.seed)

        key = (x, y)
        if self.gradients.get(key) is not None:
            return self.gradients[key]

        angle = random.uniform(0, 2 * 3.14159)
        self.gradients[key] = (math.cos(angle), math.sin(angle))

        return self.gradients[key]

    def _dot_gradient(self, ix: int, iy: int, x: float, y: float) -> float:
        gradient = self._random_gradient(ix, iy)
        dx, dy = x - ix, y - iy

        return dx * gradient[0] + dy * gradient[1]

    def _fade(self, t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def noise(self, x: float, y: float) -> float:
        x0 = math.floor(x)
        x1 = x0 + 1
        y0 = math.floor(y)
        y1 = y0 + 1

        sx = self._fade(x - x0)
        sy = self._fade(y - y0)

        n0 = self._dot_gradient(x0, y0, x, y)
        n1 = self._dot_gradient(x1, y0, x, y)
        ix0 = self._lerp(n0, n1, sx)

        n2 = self._dot_gradient(x0, y1, x, y)
        n3 = self._dot_gradient(x1, y1, x, y)
        ix1 = self._lerp(n2, n3, sx)

        return self._lerp(ix0, ix1, sy)

    def island(self, width: int = 600, height: int = 600) -> list[list[int]]:
        center_x, center_y = width / 2, height / 2
        max_distance = math.sqrt(center_x**2 + center_y**2)
        noise = [[0 for _ in range(width)] for _ in range(height)]
        size = 200

        for y in range(height):
            for x in range(width):
                nx = x / size
                ny = y / size
                distance = (
                    math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) / max_distance
                )

                noise_value = (self.noise(nx / 2, ny / 2) - (2 * distance)) + (
                    (0.5 * self.noise(nx * 3, ny * 3)) - distance
                )

                noise[y][x] = ((noise_value + 1) / 2) > 0.1

        return noise
