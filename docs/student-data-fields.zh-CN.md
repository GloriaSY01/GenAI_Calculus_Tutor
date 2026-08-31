# 学生端数据字段

本文列出学生使用 Concept、Practice、Tutor 和收藏功能时需要保留的数据字段。
这些数据由学生端提交或由后端根据学生操作生成，后续可供教师端按班级查看学习情况。

## 1. 学生与班级

| 字段 | 来源 | 含义 |
| --- | --- | --- |
| `student_id` | 学生端 | 学生标识；当前来自姓名输入，正式使用时应替换为稳定的匿名 ID |
| `class_id` | 学生端 | 学生在侧栏选择的班级标识 |

## 2. 学习位置

| 字段 | 来源 | 含义 |
| --- | --- | --- |
| `section_id` | 学生端 | 当前学习的教材小节标识 |
| `learning_stage` | 学生端 | 当前阶段：`concept`、`practice` 或 `tutor` |

## 3. 练习记录

| 字段 | 来源 | 含义 |
| --- | --- | --- |
| `question_id` | 后端 | 题目唯一标识 |
| `question_type` | 后端 | 题型：单选、多选、填空或步骤排序 |
| `difficulty` | 学生端 | 学生选择的题目难度 |
| `correct` | 后端 | 本次提交是否正确，以服务端判分为准 |
| `attempts` | 后端 | 当前题目的累计尝试次数 |
| `submitted_at` | 后端 | 学生提交答案的时间 |

学生端只提交答案和题目标识，不能自行提交或修改 `correct`。是否正确、尝试次数和
提交时间都应由后端生成。

## 4. Tutor 学习记录

| 字段 | 来源 | 含义 |
| --- | --- | --- |
| `session_id` | 后端 | 一次 Tutor 会话的唯一标识 |
| `hint_level` | 后端 | 当前会话已经推进到的提示等级 |
| `mastery` | 后端 | Tutor 根据当前对话维护的启发式掌握度 |
| `is_solved` | 后端 | 学生是否已经完成当前题目 |

`mastery` 是系统内部的启发式状态，不等同于考试成绩或经过验证的真实学习能力。

## 5. 收藏记录

收藏不建议保存为学生表中的 `favorite_question_ids` 数组，而应为每次收藏建立独立记录：

| 字段 | 来源 | 含义 |
| --- | --- | --- |
| `student_id` | 学生端 | 收藏所属学生 |
| `class_id` | 学生端 | 学生收藏时所属班级 |
| `question_id` | 后端 | 被收藏的题目标识 |
| `saved_at` | 后端 | 收藏时间 |

## 6. 字段汇总

学生端相关的最小字段集合为：

```text
student_id
class_id
section_id
learning_stage
question_id
question_type
difficulty
correct
attempts
submitted_at
session_id
hint_level
mastery
is_solved
favorite.student_id
favorite.class_id
favorite.question_id
favorite.saved_at
```

这份清单只说明学生学习流程需要产生和保留哪些数据，不包含教师端页面指标、
完整埋点体系或数据库表设计。
