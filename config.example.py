# -*- coding: utf-8 -*-
"""配置模板。复制本文件为 config.py 并填入你自己的服务器地址、Cookie 和课程信息。

config.py 会被 .gitignore 忽略、不会提交到公开仓库，避免泄露账号 / Cookie。
"""

# 服务器地址与接口路径（真实地址请勿提交到公开仓库）
HOST = "你的服务器地址"
PATH = "/你的接口路径"

DEFAULT_COOKIES = {
    "COOKIES_KEY_USERNAME": "你的学号",
    "fzsy": "在这里粘贴浏览器里 fzsy 的值",
    "ASP.NET_SessionId": "在这里粘贴 ASP.NET_SessionId",
}

# 无 request.txt 时兜底使用的默认课程（换成你的目标课程，示例值均为占位符）
DEFAULT_OBJECT_IDS = [{
    "WeekId": "示例",
    "Weeks": "示例",
    "LabID": "示例",
    "TimePartID": "示例",
    "Capacity": "示例",
    "IsQuried": "0",
    "ClassDate": "示例日期",
    "StartTime": "示例",
    "EndTime": "示例",
    "OpenTime": "示例",
    "ModuleID": "1",
    "CourseID": "示例",
    "StudentID": "你的学号",
    "TeacherID": "示例",
    "SemesterID": 19,
    "LabGroupID": "示例",
    "LabStatusID": "0",
    "LabClassNo": "示例",
    "LabName": "课程名称",
}]
