from serials import *


s1 = get_serial('com3', 115200, 0.2)
s2 = get_serial('com4', 115200, 0.2)


issue_command(s1, 'ls', False)
issue_command(s2, 'ls', False)
