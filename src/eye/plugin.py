import os
import re
from pathlib import Path

import pytest
from PIL import Image
from selenium.webdriver.remote.webelement import WebElement

from eye.comparator import Comparator
from eye.WebElementHandler import WebElementHandler


def pytest_addoption(parser):
    group = parser.getgroup('eye')
    group.addoption(
        '--screenshots-update',
        action='store_true',
        default=False,
        dest='screenshot_update',
        help='Update the screenshots'
    )


class EyeManager:
    def __init__(self, request):
        self.request = request
        self.current_screenshot = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def update_mode(self):
        return self.request.config.option.screenshot_update

    @property
    def test_name(self) -> str:
        cls_name = getattr(self.request.node.cls, '__name__', '')
        flattened_node_name = re.sub(r"\s+", " ", self.request.node.name.replace(r"\n", " "))

        return '{}{}{}'.format(
            '{}.'.format(cls_name) if cls_name else '',
            flattened_node_name,
            '_{}'.format(self.current_screenshot) if self.current_screenshot else ''
        )

    @property
    def screenshots_directory_path(self) -> str:
        p = Path(self.request.node.location[0])
        path = '{0}/{1}/screenshots'.format(os.getcwd(), p.parent)
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    @property
    def screenshot_path(self) -> str:
        return '{0}/{1}.png'.format(self.screenshots_directory_path, self.test_name)

    @property
    def highlight_path(self) -> str:
        return '{0}/{1}_highlight.png'.format(self.screenshots_directory_path, self.test_name)

    @property
    def mask_path(self) -> str:
        return '{0}/{1}_mask.png'.format(self.screenshots_directory_path, self.test_name)

    @property
    def received_path(self) -> str:
        return '{0}/{1}_received.png'.format(self.screenshots_directory_path, self.test_name)

    def is_screenshot_exists(self) -> bool:
        return os.path.exists(self.screenshot_path)

    @property
    def mask_im(self) -> Image.Image:
        if os.path.exists(self.mask_path):
            return Image.open(self.mask_path)
        else:
            return None

    def clear_staff_images(self):
        if os.path.exists(self.received_path):
            os.remove(self.received_path)
        if os.path.exists(self.highlight_path):
            os.remove(self.highlight_path)

    def assert_similar(
            self,
            element: WebElement,
            admissible_pixel_color_error: int = 2,
            auto_mask: bool = False,
            remove_transparency: bool = False,
            approximation: float = .1
    ) -> None:
        self.assert_equal(
            element, admissible_pixel_color_error,
            auto_mask, remove_transparency, approximation
        )

    def assert_equal(
            self,
            element: WebElement,
            admissible_pixel_color_error: int = 2,
            auto_mask: bool = False,
            remove_transparency: bool = False,
            approximation: float = 1.0
    ) -> None:

        self.clear_staff_images()

        handler = WebElementHandler(element)

        fact_img, mask_im = handler.get_screenshot(
            remove_transparency=remove_transparency,
            enable_tracing=auto_mask,
            mask_im=self.mask_im
        )
        if mask_im is not None:
            mask_im.save(self.mask_path)

        if not self.is_screenshot_exists():
            fact_img.save(self.screenshot_path)
            return

        comparator = Comparator(
            expected_img=Image.open(self.screenshot_path),
            fact_img=fact_img,
            admissible_pixel_color_error=admissible_pixel_color_error,
            approximation=approximation
        )
        if comparator.is_equal():
            return

        # not equal part

        # update mode
        if self.update_mode:
            fact_img.save(self.screenshot_path)
            return

        # handle error mode
        fact_img.save(self.received_path)
        if not comparator.is_equal_dimensions():
            raise AssertionError('Images have got different dimensions!')
        highlighted_img = comparator.highlight_differences()
        highlighted_img.save(self.highlight_path)

        raise AssertionError('Images are not equal!')


@pytest.fixture
def eye(request):
    with EyeManager(request) as mgr:
        yield mgr
