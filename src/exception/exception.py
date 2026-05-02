import sys
from src.logging.logger import logger

class CustomException(Exception):
    def __init__(self, message: str, sys_info: sys):
        super().__init__(message)

        self.message = message
        _, _, exc_tb = sys_info.exc_info()
        self.file_name = exc_tb.tb_frame.f_code.co_filename
        self.line_number = exc_tb.tb_lineno

    def __str__(self) -> str:
        error_message = f"Error message: {self.message}\nError line no: {self.line_number}\nError file name: {self.file_name}"
        logger.error(error_message)
        return error_message

if __name__ == "__main__":
    try:
        a = 1 / 0
    except Exception as e:
        print(CustomException(str(e), sys))

        