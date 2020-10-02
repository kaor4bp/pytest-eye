import os
import re
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from selenium.webdriver.remote.webelement import WebElement

from eye.comparator import Comparator


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
    def received_path(self) -> str:
        return '{0}/{1}_received.png'.format(self.screenshots_directory_path, self.test_name)

    def is_screenshot_exists(self) -> bool:
        return os.path.exists(self.screenshot_path)

    def clear_staff_images(self):
        if os.path.exists(self.received_path):
            os.remove(self.received_path)
        if os.path.exists(self.highlight_path):
            os.remove(self.highlight_path)

    def assert_equal(self, element: WebElement) -> None:
        self.clear_staff_images()

        if not self.is_screenshot_exists():
            element.screenshot(self.screenshot_path)
            return

        fact_img = Image.open(BytesIO(element.screenshot_as_png))
        comparator = Comparator(
            expected_img=Image.open(self.screenshot_path),
            fact_img=fact_img
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