# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                         |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/dbus2mqtt/\_\_init\_\_.py                                |        8 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/\_\_main\_\_.py                                |        3 |        1 |        2 |        1 |     60% |         4 |
| src/dbus2mqtt/config/\_\_init\_\_.py                         |      138 |        7 |       26 |        3 |     91% |21, 66, 187, 315-318 |
| src/dbus2mqtt/config/jsonarparse.py                          |       24 |        0 |        2 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_client.py                           |      551 |      260 |      232 |       33 |     50% |47-49, 73-76, 80-105, 115-143, 147-166, 175, 183-184, 187-197, 200-210, 214-218, 222-231, 235-243, 265->exit, 267->exit, 274-287, 293-311, 343, 345, 348-350, 360-396, 402-444, 448-451, 455-477, 485-512, 518-554, 573->571, 580->578, 588->exit, 599-609, 646-655, 669->688, 672-682, 689->693, 720->723, 762->780, 768->778, 780->758, 806, 819-824, 826->829, 841->844, 863-870, 874-881, 885-888, 926-940, 944->943, 946->944, 948, 989, 1006-1010, 1013-1016, 1041->1045, 1046, 1069-1071, 1097-1099, 1146->1148, 1148->1160, 1155, 1161, 1175->exit, 1188-1189 |
| src/dbus2mqtt/dbus/dbus\_types.py                            |       13 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_util.py                             |      121 |       17 |       72 |       13 |     82% |23, 27, 46, 74-77, 90, 106, 109-114, 121, 128, 174, 182->181, 195, 199 |
| src/dbus2mqtt/dbus/introspection/patcher.py                  |       48 |        7 |       32 |       11 |     78% |19, 22->31, 25, 31->35, 44, 55, 59, 61->57, 70, 74, 76->72 |
| src/dbus2mqtt/dbus/introspection/patches/mpris\_playerctl.py |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/event\_broker.py                               |       28 |        2 |        0 |        0 |     93% |    43, 52 |
| src/dbus2mqtt/flow/\_\_init\_\_.py                           |       30 |        2 |        6 |        3 |     86% |50, 51->53, 53->55, 62 |
| src/dbus2mqtt/flow/actions/context\_set.py                   |       19 |        0 |        4 |        0 |    100% |           |
| src/dbus2mqtt/flow/actions/log\_action.py                    |       20 |        3 |        0 |        0 |     85% |     29-34 |
| src/dbus2mqtt/flow/actions/mqtt\_publish.py                  |       34 |       10 |        6 |        1 |     68% |     41-58 |
| src/dbus2mqtt/flow/flow\_processor.py                        |      156 |       33 |       70 |        7 |     78% |41, 47-53, 59-82, 97-101, 121, 122->125, 136->139, 139->130, 184-207, 222 |
| src/dbus2mqtt/flow/flow\_trigger\_handlers.py                |       40 |        0 |        6 |        3 |     93% |43->46, 72->75, 82->85 |
| src/dbus2mqtt/flow/flow\_trigger\_processor.py               |       54 |        2 |       26 |        1 |     96% |53->52, 79, 87 |
| src/dbus2mqtt/main.py                                        |       77 |       30 |        4 |        2 |     60% |26-34, 45-59, 64-66, 71-79, 104, 119-120, 141-142, 147-148 |
| src/dbus2mqtt/mqtt/mqtt\_client.py                           |      136 |       73 |       40 |        2 |     43% |64, 84->83, 92, 98-153, 157-167, 170-175, 180-220, 237-241 |
| src/dbus2mqtt/template/\_\_init\_\_.py                       |        0 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/template/dbus\_template\_functions.py          |       39 |        6 |       12 |        3 |     78% |102, 106, 127, 135-137 |
| src/dbus2mqtt/template/templating.py                         |       91 |       11 |       24 |        5 |     86% |49, 90, 103-104, 115-116, 127->exit, 144, 159-160, 171->exit, 177, 188 |
| **TOTAL**                                                    | **1632** |  **464** |  **564** |   **88** | **68%** |           |


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