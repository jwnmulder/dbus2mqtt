# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                         |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/dbus2mqtt/\_\_init\_\_.py                                |        8 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/\_\_main\_\_.py                                |        3 |        1 |        2 |        1 |     60% |         4 |
| src/dbus2mqtt/config/\_\_init\_\_.py                         |      138 |        7 |       26 |        3 |     91% |21, 66, 187, 315-318 |
| src/dbus2mqtt/config/jsonargparse.py                         |       24 |        0 |        2 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_client.py                           |      543 |      258 |      232 |       33 |     50% |47-49, 73-76, 80-105, 115-143, 147-166, 175, 184-194, 197-207, 211-215, 219-228, 232-240, 262-\>exit, 264-\>exit, 271-284, 290-308, 340, 342, 345-347, 357-393, 399-441, 445-448, 452-474, 482-509, 515-551, 570-\>568, 577-\>575, 585-\>exit, 596-606, 643-652, 666-\>685, 669-679, 686-\>690, 717-\>716, 742-\>758, 748-\>756, 758-\>738, 782, 795-800, 802-\>805, 817-\>820, 839-846, 850-857, 861-864, 902-916, 920-\>919, 922-\>920, 924, 965, 982-986, 989-992, 1017-\>1021, 1022, 1045-1047, 1073-1075, 1122-\>1124, 1124-\>1136, 1131, 1137, 1151-\>exit, 1164-1165 |
| src/dbus2mqtt/dbus/dbus\_types.py                            |       13 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_util.py                             |      121 |       17 |       72 |       13 |     82% |23, 27, 46, 74-77, 90, 106, 109-114, 121, 128, 174, 182-\>181, 195, 199 |
| src/dbus2mqtt/dbus/introspection/patcher.py                  |       48 |        7 |       32 |       11 |     78% |19, 22-\>31, 25, 31-\>35, 44, 55, 59, 61-\>57, 70, 74, 76-\>72 |
| src/dbus2mqtt/dbus/introspection/patches/mpris\_playerctl.py |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/event\_broker.py                               |       28 |        2 |        0 |        0 |     93% |    43, 52 |
| src/dbus2mqtt/flow/\_\_init\_\_.py                           |       29 |        1 |        6 |        3 |     89% |50, 51-\>53, 53-\>55 |
| src/dbus2mqtt/flow/actions/context\_set.py                   |       19 |        0 |        4 |        0 |    100% |           |
| src/dbus2mqtt/flow/actions/log\_action.py                    |       20 |        3 |        0 |        0 |     85% |     29-34 |
| src/dbus2mqtt/flow/actions/mqtt\_publish.py                  |       34 |       10 |        6 |        1 |     68% |     41-58 |
| src/dbus2mqtt/flow/flow\_processor.py                        |      156 |       33 |       70 |        7 |     78% |41, 47-53, 59-82, 97-101, 121, 122-\>125, 136-\>139, 139-\>130, 184-207, 222 |
| src/dbus2mqtt/flow/flow\_trigger\_handlers.py                |       41 |        0 |        6 |        2 |     96% |43-\>46, 72-\>76 |
| src/dbus2mqtt/flow/flow\_trigger\_processor.py               |       54 |        2 |       26 |        1 |     96% |53-\>52, 79, 87 |
| src/dbus2mqtt/main.py                                        |       77 |       30 |        4 |        2 |     60% |26-34, 45-59, 64-66, 71-79, 104, 119-120, 141-142, 147-148 |
| src/dbus2mqtt/mqtt/mqtt\_client.py                           |      136 |       73 |       40 |        2 |     43% |64, 84-\>83, 92, 98-153, 157-167, 170-175, 180-220, 237-241 |
| src/dbus2mqtt/template/\_\_init\_\_.py                       |        0 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/template/dbus\_template\_functions.py          |       41 |        7 |       14 |        4 |     76% |102, 106, 110, 131, 139-141 |
| src/dbus2mqtt/template/templating.py                         |      100 |        7 |       22 |        3 |     92% |49, 56-57, 98, 111-112, 131-\>exit, 155-\>exit, 161 |
| **TOTAL**                                                    | **1635** |  **458** |  **564** |   **86** | **69%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/jwnmulder/dbus2mqtt/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jwnmulder/dbus2mqtt/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fjwnmulder%2Fdbus2mqtt%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.