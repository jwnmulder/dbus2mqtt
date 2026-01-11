# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/dbus2mqtt/\_\_init\_\_.py                                 |        8 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/\_\_main\_\_.py                                 |        3 |        1 |        2 |        1 |     60% |         4 |
| src/dbus2mqtt/config/\_\_init\_\_.py                          |      138 |        7 |       26 |        3 |     91% |21, 66, 187, 315-318 |
| src/dbus2mqtt/config/jsonarparse.py                           |       16 |        0 |        2 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_client.py                            |      543 |      269 |      226 |       29 |     48% |46-48, 71-74, 78-103, 113-141, 145-164, 173, 181-182, 185-195, 198-208, 212-216, 220-229, 233-241, 244, 263->exit, 265->exit, 272-285, 291-309, 337, 339, 342-344, 354-390, 396-438, 442-458, 462-484, 492-519, 525-561, 580->578, 587->585, 595->exit, 606-616, 653-662, 676->695, 679-689, 696->700, 727->730, 769->787, 775->785, 787->765, 808-809, 813-818, 820->823, 833-842, 857-864, 868-875, 879-882, 919-933, 937->936, 939->937, 941, 982, 998-1002, 1027->1031, 1032, 1050-1052, 1077-1079, 1140, 1146, 1160->exit, 1173-1174 |
| src/dbus2mqtt/dbus/dbus\_types.py                             |       13 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_util.py                              |      105 |       15 |       62 |       10 |     83% |22, 26, 45, 73-76, 89, 105, 108-113, 120, 127, 173 |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_playerctl.py |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/introspection\_patches/mpris\_vlc.py       |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/event\_broker.py                                |       28 |        2 |        0 |        0 |     93% |    43, 52 |
| src/dbus2mqtt/flow/\_\_init\_\_.py                            |       30 |        2 |        6 |        3 |     86% |50, 51->53, 53->55, 62 |
| src/dbus2mqtt/flow/actions/context\_set.py                    |       19 |        0 |        4 |        0 |    100% |           |
| src/dbus2mqtt/flow/actions/log\_action.py                     |       20 |        3 |        0 |        0 |     85% |     29-34 |
| src/dbus2mqtt/flow/actions/mqtt\_publish.py                   |       34 |       10 |        6 |        1 |     68% |     41-58 |
| src/dbus2mqtt/flow/flow\_processor.py                         |      156 |       33 |       70 |        7 |     78% |41, 47-53, 59-82, 97-101, 121, 122->125, 136->139, 139->130, 184-207, 222 |
| src/dbus2mqtt/flow/flow\_trigger\_handlers.py                 |       40 |        0 |        6 |        3 |     93% |43->46, 72->75, 82->85 |
| src/dbus2mqtt/flow/flow\_trigger\_processor.py                |       54 |        2 |       26 |        1 |     96% |53->52, 79, 87 |
| src/dbus2mqtt/main.py                                         |       84 |       30 |        4 |        2 |     64% |29-37, 48-62, 67-69, 74-82, 107, 122-123, 144-145, 150-151 |
| src/dbus2mqtt/mqtt/mqtt\_client.py                            |      136 |       73 |       40 |        2 |     43% |64, 84->83, 92, 98-153, 157-167, 170-175, 180-220, 237-241 |
| src/dbus2mqtt/template/\_\_init\_\_.py                        |        0 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/template/dbus\_template\_functions.py           |       39 |       26 |       12 |        0 |     25% |16, 40-45, 94-106, 117-129, 134-143 |
| src/dbus2mqtt/template/templating.py                          |       91 |       11 |       24 |        5 |     86% |49, 90, 103-104, 115-116, 127->exit, 144, 159-160, 171->exit, 177, 188 |
| **TOTAL**                                                     | **1561** |  **484** |  **516** |   **67** | **66%** |           |


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