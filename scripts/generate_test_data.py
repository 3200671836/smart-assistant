"""
生成测试简历数据
生成 50 份不同行业、技能的模拟简历
"""

import os
import random
from datetime import datetime

# 测试数据目录
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "test_data", "resumes")
os.makedirs(TEST_DATA_DIR, exist_ok=True)

# 姓名库
FIRST_NAMES = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋",
               "勇", "艳", "杰", "娟", "涛", "明", "超", "秀", "霞", "平",
               "刚", "桂", "英", "华", "建", "文", "辉", "宇", "博", "浩"]
LAST_NAMES = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "吴", "周",
              "徐", "孙", "马", "朱", "胡", "郭", "何", "林", "罗", "高"]

# 专业方向
MAJORS = [
    "计算机科学与技术", "软件工程", "信息安全", "网络工程", "数据科学",
    "人工智能", "电子信息工程", "通信工程", "自动化", "物联网工程",
    "金融学", "会计学", "工商管理", "市场营销", "人力资源管理",
    "法学", "英语", "日语", "汉语言文学", "新闻学",
    "临床医学", "护理学", "药学", "医学检验", "口腔医学",
    "土木工程", "建筑学", "机械工程", "电气工程", "材料科学"
]

# 技能库
SKILLS_POOL = [
    "Java", "Python", "C++", "Go", "Rust", "JavaScript", "TypeScript",
    "Spring Boot", "Spring Cloud", "Django", "Flask", "FastAPI",
    "Vue.js", "React", "Angular", "Node.js", "Express",
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions",
    "AWS", "阿里云", "腾讯云", "华为云",
    "Linux", "Nginx", "Tomcat", "Apache",
    "Git", "SVN", "Maven", "Gradle", "npm",
    "RESTful API", "GraphQL", "gRPC", "WebSocket",
    "RabbitMQ", "Kafka", "RocketMQ",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
    "Hadoop", "Spark", "Flink", "Hive",
    "HTML", "CSS", "Sass", "Less", "Bootstrap", "Tailwind CSS",
    "JVM调优", "SQL优化", "性能测试", "单元测试", "集成测试",
    "微服务架构", "分布式系统", "高并发", "高可用",
    "设计模式", "数据结构与算法", "操作系统", "计算机网络"
]

# 项目经验模板
PROJECT_TEMPLATES = [
    """项目名称：{project_name}
技术栈：{tech_stack}
项目描述：{description}
主要职责：
- {responsibility1}
- {responsibility2}
- {responsibility3}
项目成果：{achievement}""",
]

# 项目名
PROJECT_NAMES = [
    "电商平台", "社交应用", "在线教育", "金融系统", "物流管理",
    "医疗健康", "智能家居", "游戏后端", "视频直播", "即时通讯",
    "企业OA", "CRM系统", "ERP系统", "数据分析平台", "推荐系统",
    "搜索引擎", "广告投放", "支付系统", "风控系统", "内容管理"
]

# 公司名
COMPANIES = [
    "阿里巴巴", "腾讯", "字节跳动", "美团", "京东",
    "百度", "华为", "小米", "滴滴", "快手",
    "网易", "携程", "拼多多", "哔哩哔哩", "知乎",
    "商汤科技", "旷视科技", "依图科技", "云从科技", "第四范式",
    "平安科技", "招商银行", "中信证券", "华泰证券", "陆金所"
]

# 学校
SCHOOLS = [
    "清华大学", "北京大学", "浙江大学", "上海交通大学", "复旦大学",
    "南京大学", "中国科学技术大学", "华中科技大学", "武汉大学", "西安交通大学",
    "中山大学", "哈尔滨工业大学", "北京航空航天大学", "同济大学", "东南大学",
    "中国人民大学", "北京师范大学", "南开大学", "天津大学", "山东大学"
]


def generate_name():
    """生成姓名"""
    return random.choice(LAST_NAMES) + random.choice(FIRST_NAMES)


def generate_skills(count=8):
    """生成技能列表"""
    return random.sample(SKILLS_POOL, min(count, len(SKILLS_POOL)))


def generate_project():
    """生成项目经验"""
    project_name = random.choice(PROJECT_NAMES)
    tech_stack = ", ".join(random.sample(SKILLS_POOL, 5))
    
    descriptions = [
        f"基于微服务架构的{project_name}系统，支持百万级用户并发访问",
        f"使用云原生技术构建的{project_name}平台，日均处理千万级请求",
        f"面向企业级客户的{project_name}解决方案，支持多租户隔离",
        f"采用分布式架构设计的{project_name}系统，实现高可用部署"
    ]
    
    responsibilities = [
        "负责系统架构设计与核心模块开发",
        "主导数据库设计与性能优化，SQL查询效率提升50%",
        "实现分布式缓存方案，系统响应时间降低60%",
        "设计并实现消息队列中间件，解耦系统模块",
        "负责CI/CD流程搭建，部署效率提升3倍",
        "编写单元测试与集成测试，代码覆盖率达85%",
        "参与需求分析与技术方案评审",
        "指导初级开发人员，组织技术分享"
    ]
    
    achievements = [
        "系统上线后稳定运行，用户满意度达95%",
        "性能优化后QPS提升200%，获得团队优秀项目奖",
        "成功支撑双11大促，峰值QPS达10万",
        "项目获得公司技术创新奖，申请专利2项",
        "降低系统运维成本30%，获得客户好评"
    ]
    
    return {
        "project_name": project_name,
        "tech_stack": tech_stack,
        "description": random.choice(descriptions),
        "responsibility1": random.choice(responsibilities),
        "responsibility2": random.choice(responsibilities),
        "responsibility3": random.choice(responsibilities),
        "achievement": random.choice(achievements)
    }


def generate_resume(index):
    """生成一份简历"""
    name = generate_name()
    major = random.choice(MAJORS)
    school = random.choice(SCHOOLS)
    company = random.choice(COMPANIES)
    skills = generate_skills(random.randint(6, 12))
    
    # 工作年限
    work_years = random.randint(1, 8)
    
    # 项目经验
    projects = [generate_project() for _ in range(random.randint(2, 4))]
    
    resume = f"""# 个人简历

## 基本信息

姓名：{name}
学历：本科
专业：{major}
毕业院校：{school}
工作年限：{work_years}年

## 联系方式

手机：138{random.randint(1000, 9999)}{random.randint(1000, 9999)}
邮箱：{name.lower()}{random.randint(100, 999)}@email.com

## 求职意向

期望职位：{major}相关岗位
期望城市：北京/上海/深圳/杭州
期望薪资：{random.randint(15, 50)}K-{random.randint(20, 60)}K

## 专业技能

"""
    
    for i, skill in enumerate(skills, 1):
        level = random.choice(["精通", "熟练", "熟悉", "了解"])
        resume += f"{i}. {skill} - {level}\n"
    
    resume += "\n## 工作经历\n\n"
    resume += f"### {company}（{2024-work_years}.06 - 至今）\n\n"
    resume += f"职位：{major}工程师\n\n"
    resume += "工作内容：\n"
    resume += f"- 负责{major}相关系统的设计与开发\n"
    resume += "- 参与技术方案评审与代码审查\n"
    resume += "- 优化系统性能，提升用户体验\n"
    resume += "- 协助团队完成项目交付\n\n"
    
    resume += "## 项目经验\n\n"
    
    for i, project in enumerate(projects, 1):
        resume += f"### 项目{i}：{project['project_name']}\n\n"
        resume += f"技术栈：{project['tech_stack']}\n\n"
        resume += f"项目描述：{project['description']}\n\n"
        resume += "主要职责：\n"
        resume += f"- {project['responsibility1']}\n"
        resume += f"- {project['responsibility2']}\n"
        resume += f"- {project['responsibility3']}\n\n"
        resume += f"项目成果：{project['achievement']}\n\n"
    
    resume += "## 自我评价\n\n"
    evaluations = [
        "具有较强的学习能力和团队协作精神，善于沟通，能够快速适应新环境。",
        "热爱技术，关注行业动态，具备良好的问题分析和解决能力。",
        "工作认真负责，注重代码质量，有较强的时间管理能力。",
        "善于思考，勇于创新，能够在压力下保持高效工作。"
    ]
    resume += random.choice(evaluations) + "\n"
    
    return resume


def main():
    """生成 50 份测试简历"""
    print("开始生成测试简历数据...")
    
    total_chars = 0
    for i in range(1, 51):
        resume = generate_resume(i)
        filename = f"resume_{i:03d}.txt"
        filepath = os.path.join(TEST_DATA_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(resume)
        
        total_chars += len(resume)
        print(f"生成: {filename} ({len(resume)} 字符)")
    
    print(f"\n生成完成！")
    print(f"总文件数: 50")
    print(f"总字符数: {total_chars:,}")
    print(f"平均每份: {total_chars // 50:,} 字符")
    print(f"保存目录: {TEST_DATA_DIR}")


if __name__ == "__main__":
    main()
