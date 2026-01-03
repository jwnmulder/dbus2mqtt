# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/dbus2mqtt/\_\_init\_\_.py                                 |        8 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/\_\_main\_\_.py                                 |        3 |        1 |        2 |        1 |     60% |         4 |
| src/dbus2mqtt/config/\_\_init\_\_.py                          |      140 |       10 |       30 |        3 |     89% |21, 57-59, 144, 247, 263-266 |
| src/dbus2mqtt/config/jsonarparse.py                           |       16 |        0 |        2 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_client.py                            |      546 |      297 |      226 |       29 |     43% |57-59, 84-87, 91-114, 124-146, 150-165, 170, 176-177, 180-188, 191-199, 203-207, 211-218, 222-228, 231, 248->exit, 250->exit, 255-266, 270-289, 315, 317, 320-322, 326-357, 361-398, 402-414, 418-438, 446-471, 475-510, 529->527, 536->534, 545->exit, 558-568, 605-614, 628->648, 632-642, 649->653, 675->678, 719->736, 726->734, 736->712, 751-752, 756-758, 760->763, 769-776, 780-783, 787-794, 798-805, 809-812, 847-861, 865->864, 867->865, 869, 906, 922-924, 939-941, 945->947, 948, 961-963, 974-985, 1002-1060 |
| src/dbus2mqtt/dbus/dbus\_types.py                             |       13 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_util.py                              |      110 |       15 |       64 |       10 |     83% |21, 42, 66, 82-83, 95, 111, 114-119, 126, 133, 177 |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_playerctl.py |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_vlc.py       |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/event\_broker.py                                |       28 |        2 |        0 |        0 |     93% |    40, 49 |
| src/dbus2mqtt/flow/\_\_init\_\_.py                            |       30 |        2 |        6 |        3 |     86% |49, 50->52, 52->54, 61 |
| src/dbus2mqtt/flow/actions/context\_set.py                    |       19 |        0 |        4 |        0 |    100% |           |
| src/dbus2mqtt/flow/actions/log\_action.py                     |       20 |        3 |        0 |        0 |     85% |     32-34 |
| src/dbus2mqtt/flow/actions/mqtt\_publish.py                   |       36 |       11 |        8 |        2 |     66% | 32, 40-53 |
| src/dbus2mqtt/flow/flow\_processor.py                         |      153 |       33 |       68 |        7 |     77% |42, 50-56, 62-83, 98-102, 114, 115->118, 129->132, 132->123, 180-198, 211 |
| src/dbus2mqtt/flow/flow\_trigger\_handlers.py                 |       40 |        0 |        6 |        3 |     93% |47->50, 76->79, 88->91 |
| src/dbus2mqtt/flow/flow\_trigger\_processor.py                |       54 |        2 |       26 |        1 |     96% |57->56, 83, 91 |
| src/dbus2mqtt/main.py                                         |       85 |       32 |        4 |        2 |     62% |28-36, 46-60, 64-66, 72-87, 104, 118-119, 138-139, 143-144 |
| src/dbus2mqtt/mqtt/mqtt\_client.py                            |      126 |       66 |       40 |        2 |     43% |63, 81->80, 89, 95-142, 146-154, 159-193 |
| src/dbus2mqtt/template/\_\_init\_\_.py                        |        0 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/template/dbus\_template\_functions.py           |       39 |       26 |       12 |        0 |     25% |16, 40-45, 92-102, 106-116, 120-129 |
| src/dbus2mqtt/template/templating.py                          |       91 |       11 |       24 |        5 |     86% |47, 89, 102-103, 110-111, 120->exit, 132, 143-144, 153->exit, 159, 165 |
| **TOTAL**                                                     | **1561** |  **511** |  **522** |   **68** | **64%** |           |


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