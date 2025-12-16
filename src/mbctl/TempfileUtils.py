from tempfile import NamedTemporaryFile
from contextlib import contextmanager
import os
from typing import Iterator, Union
from os import PathLike


# Utility function to create a temporary file with given content, returns the file path
def create_tempfile_with_content(content: str, suffix: str = ".yaml") -> str:

    with NamedTemporaryFile("w+", suffix=suffix, delete=False) as temp_file:
        temp_file.write(content)
        temp_file.flush()
        return temp_file.name


@contextmanager
def change_cwd(path: Union[str, PathLike]) -> Iterator[None]:
    prev_dir = os.getcwd()
    os.chdir(os.fspath(path))
    try:
        yield
    finally:
        os.chdir(prev_dir)

