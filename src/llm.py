import os
from openai import OpenAI
from logger import LOG

class LLM:
    def __init__(self,model,apiKey,apiUrl):
        # 创建一个OpenAI客户端实例
        self.client = OpenAI(
            api_key=apiKey,  # 传入 API Key
            base_url=apiUrl  # 传入 API URL
        )
        # 确定使用的模型版本
        self.model = model
        # 配置日志文件，当文件大小达到1MB时自动轮转，日志级别为DEBUG
        LOG.add("daily_progress/llm_logs.log", rotation="1 MB", level="DEBUG")

    def generate_daily_report(self, markdown_content, dry_run=False):
        # 构建一个用于生成报告的提示文本，要求生成的报告包含新增功能、主要改进和问题修复
        prompt = f"以下是项目的最新进展，根据功能合并同类项，形成一份简报，至少包含：1）新增功能；2）主要改进；3）修复问题；:\n\n{markdown_content}"
        
        if dry_run:
            # 如果启用了dry_run模式，将不会调用模型，而是将提示信息保存到文件中
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/prompt.txt", "w+") as f:
                f.write(prompt)
            LOG.debug("Prompt saved to daily_progress/prompt.txt")
            return "DRY RUN"

        # 日志记录开始生成报告
        LOG.info("Starting report generation using GPT model.")
        
        try:
            # 调用deepseek模型生成报告
            response = self.client.chat.completions.create(
                model= self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的项目进展分析助手。请根据用户提供的内容，根据功能合并同类项，整理出一份简报，要求：1）新增功能；2）主要改进；3）修复问题。所有输出必须使用中文，且语言风格简洁明了。"
                    },
                    {
                        "role": "user",
                        "content": f"请整理以下项目进展内容：\n\n{markdown_content}"
                    }
                ]
            )
            LOG.debug("GPT response: {}", response)
            # 返回模型生成的内容
            return response.choices[0].message.content
        except Exception as e:
            # 如果在请求过程中出现异常，记录错误并抛出
            LOG.error("An error occurred while generating the report: {}", e)
            raise
