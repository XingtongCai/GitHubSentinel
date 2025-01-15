# src/github_client.py

import requests  # 导入requests库用于HTTP请求
from datetime import datetime, date, timedelta  # 导入日期处理模块
import os  # 导入os模块用于文件和目录操作
from logger import LOG  # 导入日志模块

class GitHubClient:
    def __init__(self, token):
        self.token = token  # GitHub API令牌
        self.headers = {'Authorization': f'token {self.token}'}  # 设置HTTP头部认证信息

    def fetch_updates(self, repo, since=None, until=None):
        # 获取指定仓库的更新，可以指定开始和结束日期
        updates = {
            'commits': self.fetch_commits(repo, since, until),  # 获取提交记录
            'issues': self.fetch_issues(repo, since, until),  # 获取问题
            'pull_requests': self.fetch_pull_requests(repo, since, until)  # 获取拉取请求
        }
        return updates
    def fetch_data(self, url, since=None, until=None, state='closed', sort='updated', direction='asc'):
        # 通用的数据获取方法，支持分页和时间范围过滤。
        # :param url: API 地址
        # :param since: 起始时间
        # :param until: 结束时间
        # :param state: 数据状态（open、closed、all）
        # :param sort: 排序字段
        # :param direction: 排序方向（asc 或 desc）
        # :return: 过滤后的数据列表
        data_list = []
        page = 1

        while True:
            params = {
                'state': state,
                'since': since,
                'sort': sort,
                'direction': direction,
                'page': page,
                'per_page': 100  # 每页最多获取100条记录
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                break  # 如果没有数据，说明已经获取完所有页
            # 如果 until 参数存在，过滤掉超过 until 时间的数据
            if until:
                data = [item for item in data if item['updated_at'] <= until]
            data_list.extend(data)
            # 如果最后一页的最后一条记录的更新时间超过 until，停止分页
            if until and data and data[-1]['updated_at'] > until:
                break
            
            # 如果当前页的数据量小于 per_page，说明没有更多数据了，停止分页
            if len(data) < 100:
                break

            page += 1

        return data_list

    def fetch_commits(self, repo, since=None, until=None):
        # https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28#list-commits
        # commits 里面有unitl属性
        url = f'https://api.github.com/repos/{repo}/commits'  # 构建获取提交的API URL
        params = {}
        if since:
            params['since'] = since  # 如果指定了开始日期，添加到参数中
        if until:
            params['until'] = until  # 如果指定了结束日期，添加到参数中

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()  # 检查请求是否成功
        return response.json()  # 返回JSON格式的数据

    def fetch_issues(self, repo, since=None, until=None):
        url = f'https://api.github.com/repos/{repo}/issues'
        return self.fetch_data(url, since, until, state='closed')

    def fetch_pull_requests(self, repo, since=None, until=None):
        url = f'https://api.github.com/repos/{repo}/pulls'
        return self.fetch_data(url, since, until, state='closed')

    def export_daily_progress(self, repo):
        today = datetime.now().date().isoformat()  # 获取今天的日期
        updates = self.fetch_updates(repo, since=today)  # 获取今天的更新数据
        
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))  # 构建存储路径
        os.makedirs(repo_dir, exist_ok=True)  # 确保目录存在
        
        file_path = os.path.join(repo_dir, f'{today}.md')  # 构建文件路径
        with open(file_path, 'w') as file:
            file.write(f"# Daily Progress for {repo} ({today})\n\n")
            file.write("\n## Issues Closed Today\n")
            for issue in updates['issues']:  # 写入今天关闭的问题
                file.write(f"- {issue['title']} #{issue['number']}\n")
            file.write("\n## Pull Requests Merged Today\n")
            for pr in updates['pull_requests']:  # 写入今天合并的拉取请求
                file.write(f"- {pr['title']} #{pr['number']}\n")
        
        LOG.info(f"Exported daily progress to {file_path}")  # 记录日志
        return file_path

    def export_progress_by_date_range(self, repo, days):
        today = date.today()  # 获取当前日期
        since = today - timedelta(days=days)  # 计算开始日期
        
        updates = self.fetch_updates(repo, since=since.isoformat(), until=today.isoformat())  # 获取指定日期范围内的更新
        
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))  # 构建目录路径
        os.makedirs(repo_dir, exist_ok=True)  # 确保目录存在
        
        # 更新文件名以包含日期范围
        date_str = f"{since}_to_{today}"
        file_path = os.path.join(repo_dir, f'{date_str}.md')  # 构建文件路径
        
        with open(file_path, 'w') as file:
            file.write(f"# Progress for {repo} ({since} to {today})\n\n")
            file.write(f"\n## Issues Closed in the Last {days} Days\n")
            for issue in updates['issues']:  # 写入在指定日期内关闭的问题
                file.write(f"- {issue['title']} #{issue['number']}\n")
            file.write(f"\n## Pull Requests Merged in the Last {days} Days\n")
            for pr in updates['pull_requests']:  # 写入在指定日期内合并的拉取请求
                file.write(f"- {pr['title']} #{pr['number']}\n")
        
        LOG.info(f"Exported time-range progress to {file_path}")  # 记录日志
        return file_path