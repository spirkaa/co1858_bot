import logging
import re
from .wday import get_wday


logger = logging.getLogger(__name__)

async def send_bell(chat):
    wday = get_wday()
    lesson_index = wday['lesson']
    robj = re.compile(r'({}\. [\d\s:-]*)(\n)'.format(lesson_index))
    text = """
🔔 Расписание звонков в ЦО № 1858:
1. 08:30 - 09:15\n2. 09:30 - 10:15\n3. 10:30 - 11:20
4. 11:35 - 12:20\n5. 12:40 - 13:25\n6. 13:45 - 14:30
7. 14:50 - 15:35\n8. 15:50 - 16:35\n9. 16:50 - 17:35
    """
    text = re.sub(robj, r'*\1* 👈\2', text)
    await chat.send_text(text, parse_mode='Markdown')
