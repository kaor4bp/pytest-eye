import numpy as np
from PIL import Image, ImageDraw
from PIL import ImageChops


class Comparator:
    admissible_pixel_color_error = 2
    highlight_intensity = .4
    highlight_radius = 10

    def __init__(self, expected_img: Image.Image, fact_img: Image.Image) -> None:
        self.expected_img = expected_img
        self.fact_img = fact_img

    def is_equal(self, approximation: float = None) -> bool:
        if not self.is_equal_dimensions():
            return False

        diff = ImageChops.difference(self.expected_img.convert('RGB'), self.fact_img.convert('RGB'))
        result = diff.getbbox() is None

        if not result and approximation is not None:
            result = self._is_approximate_equal(approximation)

        return result

    def _is_approximate_equal(self, approximation: float) -> bool:
        new_size = (self.expected_img.width * approximation, self.expected_img.height * approximation,)
        expected_resized_im = self.expected_img.copy().resize(new_size)
        fact_resized_im = self.fact_img.copy().resize(new_size)

        diff = ImageChops.difference(expected_resized_im.convert('RGB'), fact_resized_im.convert('RGB'))
        return diff.getbbox() is None

    def is_equal_dimensions(self) -> bool:
        return self.expected_img.height == self.fact_img.height and self.expected_img.width == self.fact_img.width

    def _highlight_area_around_of_point(self, arr, x, y):
        for iter_y in range(y - self.highlight_radius, y + self.highlight_radius):
            for iter_x in range(x - self.highlight_radius, x + self.highlight_radius):
                if iter_y < 0 or iter_x < 0 or iter_y >= len(arr) or iter_x >= len(arr[0]):
                    continue

                x = arr[iter_y][iter_x][0] + self.highlight_intensity
                x = 255 if x > 255 else x
                arr[iter_y][iter_x][0] = x

        return arr

    def highlight_differences(self) -> Image.Image:
        expected_arr = np.asarray(self.expected_img, dtype='int16')
        fact_arr = np.asarray(self.fact_img, dtype='int16')

        arr_diff = np.subtract(expected_arr, fact_arr)
        arr_diff = np.absolute(arr_diff)

        highlight_img = self.expected_img.copy()
        draw = ImageDraw.ImageDraw(highlight_img)

        for iter_y in range(len(expected_arr)):
            for iter_x in range(len(expected_arr[0])):
                if np.any(arr_diff[iter_y][iter_x] > self.admissible_pixel_color_error):
                    draw.ellipse((
                        (iter_x - self.highlight_radius, iter_y - self.highlight_radius),
                        (iter_x + self.highlight_radius, iter_y + self.highlight_radius)
                    ),
                        fill=(255, 0, 0, 255)
                    )

        return Image.blend(self.expected_img, highlight_img, alpha=self.highlight_intensity)
