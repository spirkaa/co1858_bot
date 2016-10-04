import logging
import re
from content.wday import get_wday

logger = logging.getLogger(__name__)

async def send_bell(chat):
    wday = get_wday()
    lesson_index = wday['lesson']
    robj = re.compile(r'({}\. [\d\s:-]*)(\n)'.format(lesson_index))
    text = """
🔔 Расписание звонков в ЦО № 1858:
1. 08:30 - 09:15\n2. 09:30 - 10:15\n3. 10:30 - 11:20
4. 11:30 - 12:15\n5. 12:35 - 13:20\n6. 13:40 - 14:25
7. 14:40 - 15:25\n8. 15:35 - 16:20\n9. 16:30 - 17:15
    """
    text = re.sub(robj, r'*\1* 👈\2', text)
    await chat.send_text(text, parse_mode='Markdown')
