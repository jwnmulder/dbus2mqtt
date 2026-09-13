# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/jwnmulder/dbus2mqtt/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                         |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/dbus2mqtt/\_\_init\_\_.py                                |       11 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/\_\_main\_\_.py                                |        3 |        1 |        2 |        1 |     60% |         4 |
| src/dbus2mqtt/config/\_\_init\_\_.py                         |      147 |        7 |       32 |        6 |     91% |21, 66, 77-\>exit, 191, 280-\>exit, 303-\>exit, 327-330 |
| src/dbus2mqtt/config/jsonargparse.py                         |       24 |        0 |        2 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_client.py                           |      544 |      258 |      232 |       33 |     50% |47-49, 74-77, 81-106, 116-144, 148-167, 176, 185-195, 198-208, 212-216, 220-229, 233-241, 263-\>exit, 265-\>exit, 272-285, 291-309, 341, 343, 346-348, 358-394, 400-442, 446-449, 453-475, 483-510, 516-552, 571-\>569, 578-\>576, 586-\>exit, 597-607, 644-653, 667-\>686, 670-680, 687-\>691, 718-\>717, 743-\>759, 749-\>757, 759-\>739, 783, 796-801, 803-\>806, 818-\>821, 840-847, 851-858, 862-865, 903-917, 921-\>920, 923-\>921, 925, 966, 983-987, 990-993, 1018-\>1022, 1023, 1046-1048, 1074-1076, 1123-\>1125, 1125-\>1137, 1132, 1138, 1152-\>exit, 1165-1166 |
| src/dbus2mqtt/dbus/dbus\_types.py                            |       13 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/dbus/dbus\_util.py                             |      121 |       17 |       72 |       13 |     82% |23, 27, 46, 74-77, 90, 106, 109-114, 121, 128, 174, 182-\>181, 195, 199 |
| src/dbus2mqtt/dbus/introspection/patcher.py                  |       48 |        7 |       32 |       11 |     78% |19, 22-\>31, 25, 31-\>35, 44, 55, 59, 61-\>57, 70, 74, 76-\>72 |
| src/dbus2mqtt/dbus/introspection/patches/mpris\_playerctl.py |        2 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/event\_broker.py                               |       28 |        2 |        0 |        0 |     93% |    43, 52 |
| src/dbus2mqtt/flow/\_\_init\_\_.py                           |       29 |        1 |        6 |        3 |     89% |50, 51-\>53, 53-\>55 |
| src/dbus2mqtt/flow/actions/context\_set.py                   |       19 |        0 |        4 |        0 |    100% |           |
| src/dbus2mqtt/flow/actions/log\_action.py                    |       20 |        3 |        0 |        0 |     85% |     29-34 |
| src/dbus2mqtt/flow/actions/mqtt\_publish.py                  |       34 |       10 |        6 |        1 |     68% |     41-58 |
| src/dbus2mqtt/flow/flow\_processor.py                        |      166 |       39 |       74 |        8 |     75% |43, 49-65, 71-94, 109-113, 133, 134-\>137, 148-\>151, 151-\>142, 192-193, 203-226, 241 |
| src/dbus2mqtt/flow/flow\_trigger\_handlers.py                |       41 |        0 |        6 |        2 |     96% |43-\>46, 72-\>76 |
| src/dbus2mqtt/flow/flow\_trigger\_processor.py               |       55 |        2 |       26 |        1 |     96% |53-\>52, 79, 87 |
| src/dbus2mqtt/main.py                                        |       78 |       31 |        4 |        2 |     60% |26-34, 45-59, 64-66, 71-81, 106, 121-122, 143-144, 149-150 |
| src/dbus2mqtt/mqtt/mqtt\_client.py                           |      136 |       73 |       40 |        2 |     43% |64, 84-\>83, 92, 98-153, 157-167, 170-175, 180-220, 237-241 |
| src/dbus2mqtt/template/\_\_init\_\_.py                       |        0 |        0 |        0 |        0 |    100% |           |
| src/dbus2mqtt/template/dbus\_template\_functions.py          |       41 |        7 |       14 |        4 |     76% |102, 106, 110, 131, 139-141 |
| src/dbus2mqtt/template/templating.py                         |      108 |        7 |       22 |        3 |     92% |91, 98-99, 143, 156-157, 176-\>exit, 200-\>exit, 206 |
| src/dbus2mqtt/util/dt.py                                     |       23 |        8 |       10 |        2 |     58% |46, 48, 64-71 |
| **TOTAL**                                                    | **1691** |  **473** |  **584** |   **92** | **69%** |           |


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