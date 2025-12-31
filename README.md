# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/dbus2mqtt/\_\_init\_\_.py                                 |        8 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/\_\_main\_\_.py                                 |        3 |        1 |        2 |        1 |     60% |         4 |
| src/dbus2mqtt/config/\_\_init\_\_.py                          |      134 |       12 |       26 |        2 |     86% |19-21, 46-48, 119, 209, 225-228 |
| src/dbus2mqtt/config/jsonarparse.py                           |       16 |        0 |        2 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_client.py                            |      556 |      370 |      238 |       20 |     30% |47-49, 73-76, 80-103, 113-135, 139-154, 159, 165-166, 169-177, 180-188, 192-196, 200-207, 211-217, 220, 224-228, 232, 236-240, 244-255, 259-278, 304, 306, 309-311, 315-346, 350-387, 391-403, 407-427, 435-460, 464-499, 508-526, 531-571, 583-592, 596-633, 643-708, 714->713, 758-759, 763-765, 767->770, 776-783, 787-790, 794-801, 805-808, 812-815, 823->822, 829, 831->822, 847-848, 852-866, 870->869, 872->870, 874, 911, 927-929, 944-946, 950->952, 953, 966-968, 979-990, 1007-1065 |
| src/dbus2mqtt/dbus/dbus\_types.py                             |       13 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_util.py                              |      110 |       15 |       64 |       10 |     83% |21, 42, 66, 82-83, 95, 111, 114-119, 126, 133, 177 |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_playerctl.py |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_vlc.py       |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/event\_broker.py                                |       28 |        2 |        0 |        0 |     93% |    40, 49 |
| src/dbus2mqtt/flow/\_\_init\_\_.py                            |       30 |        2 |        6 |        3 |     86% |49, 50->52, 52->54, 61 |
| src/dbus2mqtt/flow/actions/context\_set.py                    |       19 |        0 |        4 |        0 |    100% |           |
| src/dbus2mqtt/flow/actions/log\_action.py                     |       20 |        3 |        0 |        0 |     85% |     32-34 |
| src/dbus2mqtt/flow/actions/mqtt\_publish.py                   |       36 |       11 |        8 |        2 |     66% | 32, 40-53 |
| src/dbus2mqtt/flow/flow\_processor.py                         |      160 |       40 |       76 |        5 |     72% |38-39, 43-49, 52-76, 88-95, 107, 108->111, 122->125, 125->116, 172-190, 203 |
| src/dbus2mqtt/main.py                                         |       85 |       32 |        4 |        2 |     62% |28-36, 46-60, 64-66, 72-87, 104, 118-119, 138-139, 143-144 |
| src/dbus2mqtt/mqtt/mqtt\_client.py                            |      140 |       66 |       54 |        5 |     50% |58, 76->75, 84, 90-137, 141-149, 154-188, 206->205, 210->213, 219->222 |
| src/dbus2mqtt/template/\_\_init\_\_.py                        |        0 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/template/dbus\_template\_functions.py           |       39 |       26 |       12 |        0 |     25% |16, 40-45, 92-102, 106-116, 120-129 |
| src/dbus2mqtt/template/templating.py                          |       91 |       11 |       24 |        5 |     86% |47, 89, 102-103, 110-111, 120->exit, 132, 143-144, 153->exit, 159, 165 |
| **TOTAL**                                                     | **1492** |  **591** |  **520** |   **55** | **56%** |           |


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