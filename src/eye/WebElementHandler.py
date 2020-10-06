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
        self.driver = self.web_element.parent   # type: WebDriver

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

    @staticmethod
    def _set_element_opacity(element: WebElement, opacity: float) -> None:

        pass

    def remove_transparency(self) -> None:
        current_opacity = self.driver.execute_script('return arguments[0].opacity;', self.web_element)
        self._restore_operations.append(
            lambda: WebElementHandler._set_element_opacity(self.web_element, current_opacity)
        )
        WebElementHandler._set_element_opacity(self.web_element, 1.0)

    def _get_element_by_coords(self, x: int, y: int) -> WebElement:
        return self.driver.execute_script('return document.elementFromPoint({0}, {1});'.format(x, y))

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

        for y in range(start_y, start_y + height):
            for x in range(start_x, start_x + width):
                arr = (255, 255, 255,) if (self._get_element_by_coords(x, y) in valid_elements) else (0, 0, 0,)

        return Image.fromarray(np.uint8(arr), mode='RGB').convert('L')

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
            screenshot_im.paste(im=mask_im, box=(0, 0), mask=mask_im)

        return screenshot_im
