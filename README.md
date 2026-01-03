# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/dbus2mqtt/\_\_init\_\_.py                                 |        8 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/\_\_main\_\_.py                                 |        3 |        1 |        2 |        1 |     60% |         4 |
| src/dbus2mqtt/config/\_\_init\_\_.py                          |      140 |       10 |       30 |        3 |     89% |21, 64-66, 187, 299, 317-320 |
| src/dbus2mqtt/config/jsonarparse.py                           |       16 |        0 |        2 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_client.py                            |      543 |      297 |      226 |       29 |     43% |47-49, 72-75, 79-104, 114-142, 146-165, 174, 182-183, 186-196, 199-209, 213-217, 221-230, 234-242, 245, 264->exit, 266->exit, 273-286, 292-310, 338, 340, 343-345, 355-391, 397-439, 443-459, 463-485, 493-520, 526-562, 581->579, 588->586, 596->exit, 607-617, 654-663, 677->696, 680-690, 697->701, 728->731, 770->788, 776->786, 788->766, 809-810, 814-819, 821->824, 834-843, 849-852, 858-865, 869-876, 880-883, 920-934, 938->937, 940->938, 942, 983, 999-1003, 1022-1024, 1028->1032, 1033, 1051-1053, 1070-1085, 1116-1173 |
| src/dbus2mqtt/dbus/dbus\_types.py                             |       13 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_util.py                              |      110 |       15 |       64 |       10 |     83% |22, 46, 70, 86-89, 102, 118, 121-126, 133, 140, 186 |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_playerctl.py |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_vlc.py       |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/event\_broker.py                                |       28 |        2 |        0 |        0 |     93% |    43, 52 |
| src/dbus2mqtt/flow/\_\_init\_\_.py                            |       30 |        2 |        6 |        3 |     86% |50, 51->53, 53->55, 62 |
| src/dbus2mqtt/flow/actions/context\_set.py                    |       19 |        0 |        4 |        0 |    100% |           |
| src/dbus2mqtt/flow/actions/log\_action.py                     |       20 |        3 |        0 |        0 |     85% |     29-34 |
| src/dbus2mqtt/flow/actions/mqtt\_publish.py                   |       36 |       11 |        8 |        2 |     66% | 33, 43-60 |
| src/dbus2mqtt/flow/flow\_processor.py                         |      156 |       33 |       70 |        7 |     78% |41, 47-53, 59-82, 97-101, 121, 122->125, 136->139, 139->130, 184-207, 222 |
| src/dbus2mqtt/flow/flow\_trigger\_handlers.py                 |       40 |        0 |        6 |        3 |     93% |43->46, 72->75, 82->85 |
| src/dbus2mqtt/flow/flow\_trigger\_processor.py                |       54 |        2 |       26 |        1 |     96% |53->52, 79, 87 |
| src/dbus2mqtt/main.py                                         |       85 |       32 |        4 |        2 |     62% |28-36, 47-61, 66-68, 73-88, 108, 123-124, 145-146, 151-152 |
| src/dbus2mqtt/mqtt/mqtt\_client.py                            |      126 |       66 |       40 |        2 |     43% |64, 84->83, 92, 98-153, 157-167, 172-212 |
| src/dbus2mqtt/template/\_\_init\_\_.py                        |        0 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/template/dbus\_template\_functions.py           |       39 |       26 |       12 |        0 |     25% |16, 40-45, 94-106, 117-129, 134-143 |
| src/dbus2mqtt/template/templating.py                          |       91 |       11 |       24 |        5 |     86% |49, 90, 103-104, 115-116, 127->exit, 144, 159-160, 171->exit, 177, 188 |
| **TOTAL**                                                     | **1561** |  **511** |  **524** |   **68** | **64%** |           |


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