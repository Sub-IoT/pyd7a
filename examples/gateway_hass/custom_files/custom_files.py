from .custom_file_ids import CustomFileIds
from .pir_file import PirFile

from .button_file import ButtonFile

class CustomFiles:
    enum_class = CustomFileIds

    files = {
        CustomFileIds.BUTTON: ButtonFile(),
        CustomFileIds.PIR: PirFile()
    }

    def get_all_files(self):
        return sorted(self.files, key=lambda t: t.value)