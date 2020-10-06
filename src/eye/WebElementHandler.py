from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import InvalidSelectorException
import typing
import numpy as np
from io import BytesIO
from PIL import Image


class WebElementHandler:
    def __init__(self, web_element: WebElement) -> None:
        self.web_element = web_element
        self.driver = self.web_element.parent  # type: WebDriver

        self._restore_operations = []

    @staticmethod
    def _get_parents(element: WebElement) -> typing.List[WebElement]:
        try:
            parents = element.find_elements_by_xpath('..')
            parents_of_parents = []

            for parent in parents:
                parents_of_parents += WebElementHandler._get_parents(parent)

            parents += parents_of_parents
        except InvalidSelectorException:
            parents = []

        return parents

    def restore(self):
        for operation in self._restore_operations:
            operation()

    def _set_element_opacity(self, element: WebElement, opacity: float) -> None:
        self.driver.execute_script('arguments[0].opacity = {0};'.format(opacity))

    def remove_transparency(self) -> None:
        current_opacity = self.driver.execute_script('return arguments[0].opacity;', self.web_element)
        self._restore_operations.append(
            lambda: self._set_element_opacity(self.web_element, current_opacity)
        )
        self._set_element_opacity(self.web_element, 1.0)

    def _get_elements_by_coords(
            self, x_start: int, y_start: int, width: int, height: int
    ) -> typing.List[typing.List[WebElement]]:
        self.driver.set_script_timeout(60 * 30)
        elements = self.driver.execute_script(
            """
            function trace_element() {
                var width = %d;
                var height = %d;
                var x_start = %d;
                var y_start = %d;

                console.log(width);
                console.log(height);
                console.log(x_start);
                console.log(y_start);

                var mas = new Array(height);

                // init massive
                for (let i = 0; i < height; i++) {
                    mas[i] = new Array(width);
                }
                // console.log(mas);

                // trace element
                for (let x = 0; x < width; x++) {
                    for (let y = 0; y < height; y++) {
                        mas[y][x] = document.elementFromPoint(x_start + x, y_start + y);
                    }
                } 
                // console.log(mas);
                return mas;
            }

            return trace_element();
            """ % (int(width), int(height), int(x_start), int(y_start))
        )
        return elements

    @staticmethod
    def _get_children(element: WebElement) -> typing.List[WebElement]:
        try:
            children = element.find_elements_by_xpath('./*')
            children_of_children = []

            for child in children:
                children_of_children += WebElementHandler._get_children(child)

            children += children_of_children
        except InvalidSelectorException:
            children = []

        return children

    def _trace_pixel(
            self, elements_map: list, valid_elements: list, x: int, y: int, smoothing_radius: int = 1
    ) -> bool:

        for x_s in (-smoothing_radius, smoothing_radius + 1):
            for y_s in (-smoothing_radius, smoothing_radius + 1):
                cur_y = y + y_s
                cur_x = x + x_s
                if cur_y < 0 or cur_x < 0 or cur_y >= len(elements_map) or cur_x >= len(elements_map[0]):
                    return False

                if elements_map[cur_y][cur_x] not in valid_elements:
                    return False

        return True

    def get_tracing_mask(self, include_children: bool = True) -> Image.Image:
        if include_children:
            valid_elements = WebElementHandler._get_children(self.web_element)
        else:
            valid_elements = []
        valid_elements.append(self.web_element)

        rect = self.web_element.rect
        start_x = rect['x']
        start_y = rect['y']
        width = rect['width']
        height = rect['height']

        arr = np.empty([height, width, 3])
        elements = self._get_elements_by_coords(start_x, start_y, width, height)

        for y in range(0, height):
            for x in range(0, width):
                arr[y][x] = (255, 255, 255,) if self._trace_pixel(elements, valid_elements, x, y) else (0, 0, 0,)

        im_mask = Image.fromarray(np.uint8(arr), mode='RGB').convert('L')
        im_mask.show()
        return im_mask

    def get_screenshot(
            self,
            remove_transparency: bool = False,
            enable_tracing: bool = False
    ) -> Image.Image:

        # pre processing
        if remove_transparency:
            self.remove_transparency()

        # screenshot
        screenshot_bytes = self.web_element.screenshot_as_png
        screenshot_im = Image.open(BytesIO(screenshot_bytes))

        # post processing
        self.restore()

        if enable_tracing:
            mask_im = self.get_tracing_mask()
            black_im = Image.new('RGBA', mask_im.size, (0, 0, 0, 255))
            screenshot_im = Image.composite(screenshot_im, black_im, mask_im)

        return screenshot_im
