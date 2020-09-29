Решение проблем отсутсвием привелегий использования блютуз

````bash
# получаем путь
find / -name bluepy-helper
# указываем права 
sudo setcap cap_net_raw+e  <PATH>/bluepy-helper
sudo setcap cap_net_admin+eip  <PATH>/bluepy-helper
````