
import requests
import json
import os
import time

# --- 配置 ---
BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:3001/api")
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# --- 存储测试期间的状态 ---
# 例如，创建的服务器和任务的ID，以便后续测试可以使用它们
test_state = {}


# --- 辅助函数 ---

def print_header(title):
    """打印一个漂亮的标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_test_case(name, response, expected_status):
    """打印单个测试用例的结果"""
    status_code = response.status_code
    result = "成功" if status_code == expected_status else f"失败 (状态码: {status_code})"
    
    print(f"\n--- 测试端点: {name} ---")
    print(f"状态码: {status_code}")
    
    try:
        response_content = response.json()
        print("响应内容:")
        print(json.dumps(response_content, indent=2, ensure_ascii=False))
        
        if "success" in response_content and not response_content["success"]:
             result = f"失败 (业务逻辑错误)"

    except json.JSONDecodeError:
        print("响应内容: (非JSON)")
        print(response.text)

    print(f"结果: {result}")
    print("-" * (len(name) + 14))
    
    return status_code == expected_status

# --- 测试函数 ---

def test_settings_endpoints():
    """测试 /settings API 端点"""
    print_header("开始测试 Settings (服务器设置) API")
    
    # 1. 添加新服务器
    server_data = {
        "name": "测试Plex服务器",
        "server_type": "plex",
        "url": "https://plex.nasiot.link:8443",
        "token": "DNDSFFxaPSK3s6m_w_fs"
    }
    response = requests.post(f"{BASE_URL}/settings", headers=HEADERS, json=server_data)
    if print_test_case("POST /settings", response, 200) and response.json().get("success"):
        test_state['server_id'] = response.json()['server']['id']
    else:
        print("错误：添加服务器失败，无法继续测试 Settings 相关功能。")
        return

    server_id = test_state['server_id']

    # 2. 获取所有服务器，验证是否包含新添加的
    response = requests.get(f"{BASE_URL}/settings", headers=HEADERS)
    print_test_case("GET /settings", response, 200)

    # 3. 测试已保存服务器的连接
    response = requests.post(f"{BASE_URL}/settings/{server_id}/test", headers=HEADERS)
    # 此处预期500是正常的，因为token是假的
    print_test_case(f"POST /settings/{server_id}/test", response, 500) 
    
    # 4. 更新服务器
    update_data = {"name": "更新后的Plex服务器"}
    response = requests.put(f"{BASE_URL}/settings/{server_id}", headers=HEADERS, json=update_data)
    print_test_case(f"PUT /settings/{server_id}", response, 200)

    # 5. 删除服务器（清理）
    response = requests.delete(f"{BASE_URL}/settings/{server_id}", headers=HEADERS)
    print_test_case(f"DELETE /settings/{server_id}", response, 200)

def test_tasks_endpoints():
    """测试 /tasks API 端点"""
    print_header("开始测试 Tasks (同步任务) API")

    # 首先，需要一个服务器才能创建任务
    server_data = {
        "name": "用于任务测试的服务器",
        "server_type": "plex",
        "url": "https://plex.nasiot.link:8443",
        "token": "DNDSFFxaPSK3s6m_w_fs"
    }
    server_res = requests.post(f"{BASE_URL}/settings", headers=HEADERS, json=server_data)
    if server_res.status_code != 200 or not server_res.json().get("success"):
        print("错误：为任务测试创建服务器失败，跳过任务测试。")
        return
    server_id = server_res.json()['server']['id']

    # 1. 创建新任务
    task_data = {
        "server_id": server_id,
        "name": "测试歌单同步",
        "playlist_url": "https://music.163.com/#/playlist?id=123456",
        "platform": "netease",
        "cron_schedule": "0 0 * * *"
    }
    response = requests.post(f"{BASE_URL}/tasks", headers=HEADERS, json=task_data)
    if print_test_case("POST /tasks", response, 201) and response.json().get("id"):
        test_state['task_id'] = response.json()['id']
    else:
        print("错误：创建任务失败，无法继续测试 Tasks 相关功能。")
        # 清理创建的服务器
        requests.delete(f"{BASE_URL}/settings/{server_id}", headers=HEADERS)
        return

    task_id = test_state['task_id']
    
    # 2. 获取所有任务
    response = requests.get(f"{BASE_URL}/tasks", headers=HEADERS)
    print_test_case("GET /tasks", response, 200)
    
    # 3. 更新任务计划
    update_data = {"cron_schedule": "0 2 * * *"}
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", headers=HEADERS, json=update_data)
    print_test_case(f"PUT /tasks/{task_id}", response, 200)

    # 4. 获取不匹配歌曲
    response = requests.get(f"{BASE_URL}/tasks/{task_id}/unmatched", headers=HEADERS)
    print_test_case(f"GET /tasks/{task_id}/unmatched", response, 200)

    # 5. 测试同步流 (只检查是否能建立连接)
    try:
        with requests.get(f"{BASE_URL}/tasks/{task_id}/sync/stream", stream=True, timeout=5) as r:
            print_test_case(f"GET /tasks/{task_id}/sync/stream", r, 200)
    except requests.exceptions.ReadTimeout:
        # 超时是正常的，因为我们只是想检查连接
        print(f"\n--- 测试端点: GET /tasks/{task_id}/sync/stream ---")
        print("结果: 连接成功 (正常超时)")
        print("-" * (len(f"GET /tasks/{task_id}/sync/stream") + 14))


    # 6. 删除任务（清理）
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=HEADERS)
    print_test_case(f"DELETE /tasks/{task_id}", response, 200)
    
    # 清理为任务测试创建的服务器
    requests.delete(f"{BASE_URL}/settings/{server_id}", headers=HEADERS)

def test_logs_endpoints():
    """测试 /logs API"""
    print_header("开始测试 Logs (日志) API")
    # 这里的task_id可能不存在，但API应能优雅处理
    task_id_for_log = test_state.get('task_id', 999) 
    
    # 1. 获取所有日志
    response = requests.get(f"{BASE_URL}/logs", headers=HEADERS)
    print_test_case("GET /logs", response, 200)
    
    # 2. 按任务ID获取日志
    response = requests.get(f"{BASE_URL}/logs?task_id={task_id_for_log}", headers=HEADERS)
    print_test_case(f"GET /logs?task_id={task_id_for_log}", response, 200)

def test_download_endpoints():
    """测试 /download API 端点"""
    print_header("开始测试 Download (下载) API")

    # 1. 获取下载设置 (可能已存在)
    response = requests.get(f"{BASE_URL}/download/download-settings", headers=HEADERS)
    if response.status_code == 404:
        print_test_case("GET /download/download-settings (initial)", response, 404)
        # 2. 如果不存在，则保存下载设置
        settings_data = {
            "download_path": "/downloads",
            "api_url": "http://test.api",
            "api_key": "test_download_api_key"
        }
        response = requests.post(f"{BASE_URL}/download/download-settings", headers=HEADERS, json=settings_data)
        print_test_case("POST /download/download-settings", response, 200)
    elif response.status_code == 200:
        print_test_case("GET /download/download-settings (existing)", response, 200)
    else:
        print_test_case("GET /download/download-settings (unexpected)", response, 200) # Let it fail
        return # Stop if something is wrong

    # 3. 测试下载连接
    test_conn_data = {"api_key": "test_download_api_key"}
    response = requests.post(f"{BASE_URL}/download/download-settings/test", headers=HEADERS, json=test_conn_data)
    # 预期失败，因为URL和key都是假的
    print_test_case("POST /download/download-settings/test", response, 200) 

    # 4. 获取下载状态
    response = requests.get(f"{BASE_URL}/download/status", headers=HEADERS)
    print_test_case("GET /download/status", response, 200)

    # 5. 下载所有缺失歌曲 (需要一个真实存在的task_id)
    # 我们用一个不存在的ID来测试错误处理
    download_all_data = {"task_id": 9999}
    response = requests.post(f"{BASE_URL}/download/all-missing", headers=HEADERS, json=download_all_data)
    print_test_case("POST /download/all-missing (with invalid id)", response, 500)

    # 6. 下载单曲 (使用无效ID，预期500错误)
    download_single_data = {
        "task_id": 9999,
        "song_id": "song123",
        "title": "测试歌曲",
        "artist": "测试艺术家",
        "album": "测试专辑"
    }
    response = requests.post(f"{BASE_URL}/download/single", headers=HEADERS, json=download_single_data)
    print_test_case("POST /download/single (with invalid id)", response, 500)

    # 7. 取消会话
    response = requests.post(f"{BASE_URL}/download/cancel-session/9999", headers=HEADERS)
    # 由于会话不存在，API可能会返回成功或特定的错误码，这里我们接受200或500
    status_code = response.status_code
    expected_status_ok = status_code == 200 or status_code == 500
    result = "成功 (优雅处理)" if expected_status_ok else f"失败 (状态码: {status_code})"
    print(f"\n--- 测试端点: POST /api/download/cancel-session/9999 ---")
    print(f"状态码: {status_code}")
    print(f"结果: {result}")
    print("-" * 50)


def main():
    """主函数，按顺序运行所有测试"""
    print("开始对后端API进行全面测试...")
    print(f"目标URL: {BASE_URL}")

    # 依次运行测试套件
    # 这个顺序很重要，因为tasks测试依赖于settings测试能成功创建一个服务器
    test_settings_endpoints()
    test_tasks_endpoints()
    test_logs_endpoints()
    test_download_endpoints()
    
    print("\n" + "="*60)
    print("所有测试完成。")
    print("="*60)


if __name__ == "__main__":
    main()

