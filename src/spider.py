# -*- encoding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily
Date: 2023-07-15 23:15:00
Update: 2025-07-19 17:43:00
Copyright (c) 2023-2025 by Hmily, All Rights Reserved.
Function: Get live stream data.
"""

import hashlib
import random
import subprocess
import time
import uuid
from operator import itemgetter
import urllib.parse
import urllib.error
from typing import List
import httpx
import ssl
import re
import json
import execjs
import urllib.request
from . import JS_SCRIPT_PATH, utils
from .utils import trace_error_decorator, generate_random_string
from .logger import script_path
from .room import get_sec_user_id, get_unique_id, UnsupportedUrlError
from .http_clients.async_http import async_req


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
OptionalStr = str | None
OptionalDict = dict | None


def get_params(url: str, params: str) -> OptionalStr:
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    if params in query_params:
        return query_params[params][0]


async def get_play_url_list(m3u8: str, proxy: OptionalStr = None, header: OptionalDict = None,
                            abroad: bool = False) -> List[str]:
    resp = await async_req(url=m3u8, proxy_addr=proxy, headers=header, abroad=abroad)
    play_url_list = []
    for i in resp.split('\n'):
        if i.startswith('https://'):
            play_url_list.append(i.strip())
    if not play_url_list:
        for i in resp.split('\n'):
            if i.strip().endswith('m3u8'):
                play_url_list.append(i.strip())
    bandwidth_pattern = re.compile(r'BANDWIDTH=(\d+)')
    bandwidth_list = bandwidth_pattern.findall(resp)
    url_to_bandwidth = {url: int(bandwidth) for bandwidth, url in zip(bandwidth_list, play_url_list)}
    play_url_list = sorted(play_url_list, key=lambda url: url_to_bandwidth[url], reverse=True)
    return play_url_list


@trace_error_decorator
async def get_douyin_app_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://live.douyin.com/',
        'Cookie': 'ttwid=1%7CB1qls3GdnZhUov9o2NxOMxxYS2ff6OSvEWbv0ytbES4%7C1680522049%7C280d802d6d478e3e78d0c807f7c487e7ffec0ae4e5fdd6a0fe74c3c6af149511; my_rd=1; passport_csrf_token=3ab34460fa656183fccfb904b16ff742; passport_csrf_token_default=3ab34460fa656183fccfb904b16ff742; d_ticket=9f562383ac0547d0b561904513229d76c9c21; n_mh=hvnJEQ4Q5eiH74-84kTFUyv4VK8xtSrpRZG1AhCeFNI; store-region=cn-fj; store-region-src=uid; LOGIN_STATUS=1; __security_server_data_status=1; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; pwa2=%223%7C0%7C3%7C0%22; download_guide=%223%2F20230729%2F0%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.6%7D; strategyABtestKey=%221690824679.923%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1536%2C%5C%22screen_height%5C%22%3A864%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22; VIDEO_FILTER_MEMO_SELECT=%7B%22expireTime%22%3A1691443863751%2C%22type%22%3Anull%7D; home_can_add_dy_2_desktop=%221%22; __live_version__=%221.1.1.2169%22; device_web_cpu_core=8; device_web_memory_size=8; xgplayer_user_id=346045893336; csrf_session_id=2e00356b5cd8544d17a0e66484946f28; odin_tt=724eb4dd23bc6ffaed9a1571ac4c757ef597768a70c75fef695b95845b7ffcd8b1524278c2ac31c2587996d058e03414595f0a4e856c53bd0d5e5f56dc6d82e24004dc77773e6b83ced6f80f1bb70627; __ac_nonce=064caded4009deafd8b89; __ac_signature=_02B4Z6wo00f01HLUuwwAAIDBh6tRkVLvBQBy9L-AAHiHf7; ttcid=2e9619ebbb8449eaa3d5a42d8ce88ec835; webcast_leading_last_show_time=1691016922379; webcast_leading_total_show_times=1; webcast_local_quality=sd; live_can_add_dy_2_desktop=%221%22; msToken=1JDHnVPw_9yTvzIrwb7cQj8dCMNOoesXbA_IooV8cezcOdpe4pzusZE7NB7tZn9TBXPr0ylxmv-KMs5rqbNUBHP4P7VBFUu0ZAht_BEylqrLpzgt3y5ne_38hXDOX8o=; msToken=jV_yeN1IQKUd9PlNtpL7k5vthGKcHo0dEh_QPUQhr8G3cuYv-Jbb4NnIxGDmhVOkZOCSihNpA2kvYtHiTW25XNNX_yrsv5FN8O6zm3qmCIXcEe0LywLn7oBO2gITEeg=; tt_scid=mYfqpfbDjqXrIGJuQ7q-DlQJfUSG51qG.KUdzztuGP83OjuVLXnQHjsz-BRHRJu4e986'
    }
    if cookies:
        headers['Cookie'] = cookies

    async def get_app_data(room_id: str, sec_uid: str) -> dict:
        app_params = {
            "verifyFp": "verify_lxj5zv70_7szNlAB7_pxNY_48Vh_ALKF_GA1Uf3yteoOY",
            "type_id": "0",
            "live_id": "1",
            "room_id": room_id,
            "sec_user_id": sec_uid,
            "version_code": "99.99.99",
            "app_id": "1128"
        }
        api2 = f'https://webcast.amemv.com/webcast/room/reflow/info/?{urllib.parse.urlencode(app_params)}'
        json_str2 = await async_req(url=api2, proxy_addr=proxy_addr, headers=headers)
        json_data2 = json.loads(json_str2)['data']
        room_data2 = json_data2['room']
        room_data2['anchor_name'] = room_data2['owner']['nickname']
        return room_data2

    try:
        web_rid = url.split('?')[0].split('live.douyin.com/')
        if len(web_rid) > 1:
            web_rid = web_rid[1]
            params = {
                "aid": "6383",
                "app_name": "douyin_web",
                "live_id": "1",
                "device_platform": "web",
                "language": "zh-CN",
                "browser_language": "zh-CN",
                "browser_platform": "Win32",
                "browser_name": "Chrome",
                "browser_version": "116.0.0.0",
                "web_rid": web_rid

            }
            api = f'https://live.douyin.com/webcast/room/web/enter/?{urllib.parse.urlencode(params)}'
            json_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
            json_data = json.loads(json_str)['data']
            room_data = json_data['data'][0]
            room_data['anchor_name'] = json_data['user']['nickname']
        else:
            try:
                data = await get_sec_user_id(url, proxy_addr=proxy_addr)
                _room_id, _sec_uid = data
                room_data = await get_app_data(_room_id, _sec_uid)
            except UnsupportedUrlError:
                unique_id = await get_unique_id(url, proxy_addr=proxy_addr)
                return await get_douyin_stream_data(f'https://live.douyin.com/{unique_id}')

        if room_data['status'] == 2:
            if 'stream_url' not in room_data:
                raise RuntimeError(
                    "The live streaming type or gameplay is not supported on the computer side yet, please use the "
                    "app to share the link for recording."
                )
            live_core_sdk_data = room_data['stream_url']['live_core_sdk_data']
            pull_datas = room_data['stream_url']['pull_datas']
            if live_core_sdk_data:
                if pull_datas:
                    key = list(pull_datas.keys())[0]
                    json_str = pull_datas[key]['stream_data']
                else:
                    json_str = live_core_sdk_data['pull_data']['stream_data']
                json_data = json.loads(json_str)
                if 'origin' in json_data['data']:
                    stream_data = live_core_sdk_data['pull_data']['stream_data']
                    origin_data = json.loads(stream_data)['data']['origin']['main']
                    sdk_params = json.loads(origin_data['sdk_params'])
                    origin_hls_codec = sdk_params.get('VCodec') or ''

                    origin_url_list = json_data['data']['origin']['main']
                    origin_m3u8 = {'ORIGIN': origin_url_list["hls"] + '&codec=' + origin_hls_codec}
                    origin_flv = {'ORIGIN': origin_url_list["flv"] + '&codec=' + origin_hls_codec}
                    hls_pull_url_map = room_data['stream_url']['hls_pull_url_map']
                    flv_pull_url = room_data['stream_url']['flv_pull_url']
                    room_data['stream_url']['hls_pull_url_map'] = {**origin_m3u8, **hls_pull_url_map}
                    room_data['stream_url']['flv_pull_url'] = {**origin_flv, **flv_pull_url}
    except Exception as e:
        print(f"Error message: {e} Error line: {e.__traceback__.tb_lineno}")
        room_data = {'anchor_name': ""}
    return room_data


@trace_error_decorator
async def get_douyin_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://live.douyin.com/',
        'Cookie': 'ttwid=1%7CB1qls3GdnZhUov9o2NxOMxxYS2ff6OSvEWbv0ytbES4%7C1680522049%7C280d802d6d478e3e78d0c807f7c487e7ffec0ae4e5fdd6a0fe74c3c6af149511; my_rd=1; passport_csrf_token=3ab34460fa656183fccfb904b16ff742; passport_csrf_token_default=3ab34460fa656183fccfb904b16ff742; d_ticket=9f562383ac0547d0b561904513229d76c9c21; n_mh=hvnJEQ4Q5eiH74-84kTFUyv4VK8xtSrpRZG1AhCeFNI; store-region=cn-fj; store-region-src=uid; LOGIN_STATUS=1; __security_server_data_status=1; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; pwa2=%223%7C0%7C3%7C0%22; download_guide=%223%2F20230729%2F0%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.6%7D; strategyABtestKey=%221690824679.923%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1536%2C%5C%22screen_height%5C%22%3A864%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22; VIDEO_FILTER_MEMO_SELECT=%7B%22expireTime%22%3A1691443863751%2C%22type%22%3Anull%7D; home_can_add_dy_2_desktop=%221%22; __live_version__=%221.1.1.2169%22; device_web_cpu_core=8; device_web_memory_size=8; xgplayer_user_id=346045893336; csrf_session_id=2e00356b5cd8544d17a0e66484946f28; odin_tt=724eb4dd23bc6ffaed9a1571ac4c757ef597768a70c75fef695b95845b7ffcd8b1524278c2ac31c2587996d058e03414595f0a4e856c53bd0d5e5f56dc6d82e24004dc77773e6b83ced6f80f1bb70627; __ac_nonce=064caded4009deafd8b89; __ac_signature=_02B4Z6wo00f01HLUuwwAAIDBh6tRkVLvBQBy9L-AAHiHf7; ttcid=2e9619ebbb8449eaa3d5a42d8ce88ec835; webcast_leading_last_show_time=1691016922379; webcast_leading_total_show_times=1; webcast_local_quality=sd; live_can_add_dy_2_desktop=%221%22; msToken=1JDHnVPw_9yTvzIrwb7cQj8dCMNOoesXbA_IooV8cezcOdpe4pzusZE7NB7tZn9TBXPr0ylxmv-KMs5rqbNUBHP4P7VBFUu0ZAht_BEylqrLpzgt3y5ne_38hXDOX8o=; msToken=jV_yeN1IQKUd9PlNtpL7k5vthGKcHo0dEh_QPUQhr8G3cuYv-Jbb4NnIxGDmhVOkZOCSihNpA2kvYtHiTW25XNNX_yrsv5FN8O6zm3qmCIXcEe0LywLn7oBO2gITEeg=; tt_scid=mYfqpfbDjqXrIGJuQ7q-DlQJfUSG51qG.KUdzztuGP83OjuVLXnQHjsz-BRHRJu4e986'
    }
    if cookies:
        headers['Cookie'] = cookies

    try:
        origin_url_list = None
        html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
        match_json_str = re.search(r'(\{\\"state\\":.*?)]\\n"]\)', html_str)
        if not match_json_str:
            match_json_str = re.search(r'(\{\\"common\\":.*?)]\\n"]\)</script><div hidden', html_str)
        json_str = match_json_str.group(1)
        cleaned_string = json_str.replace('\\', '').replace(r'u0026', r'&')
        room_store = re.search('"roomStore":(.*?),"linkmicStore"', cleaned_string, re.DOTALL).group(1)
        anchor_name = re.search('"nickname":"(.*?)","avatar_thumb', room_store, re.DOTALL).group(1)
        room_store = room_store.split(',"has_commerce_goods"')[0] + '}}}'
        json_data = json.loads(room_store)['roomInfo']['room']
        json_data['anchor_name'] = anchor_name
        if 'status' in json_data and json_data['status'] == 4:
            return json_data
        stream_orientation = json_data['stream_url']['stream_orientation']
        match_json_str2 = re.findall(r'"(\{\\"common\\":.*?)"]\)</script><script nonce=', html_str)
        if match_json_str2:
            json_str = match_json_str2[0] if stream_orientation == 1 else match_json_str2[1]
            json_data2 = json.loads(
                json_str.replace('\\', '').replace('"{', '{').replace('}"', '}').replace('u0026', '&'))
            if 'origin' in json_data2['data']:
                origin_url_list = json_data2['data']['origin']['main']

        else:
            html_str = html_str.replace('\\', '').replace('u0026', '&')
            match_json_str3 = re.search('"origin":\\{"main":(.*?),"dash"', html_str, re.DOTALL)
            if match_json_str3:
                origin_url_list = json.loads(match_json_str3.group(1) + '}')

        if origin_url_list:
            origin_hls_codec = origin_url_list['sdk_params'].get('VCodec') or ''
            origin_m3u8 = {'ORIGIN': origin_url_list["hls"] + '&codec=' + origin_hls_codec}
            origin_flv = {'ORIGIN': origin_url_list["flv"] + '&codec=' + origin_hls_codec}
            hls_pull_url_map = json_data['stream_url']['hls_pull_url_map']
            flv_pull_url = json_data['stream_url']['flv_pull_url']
            json_data['stream_url']['hls_pull_url_map'] = {**origin_m3u8, **hls_pull_url_map}
            json_data['stream_url']['flv_pull_url'] = {**origin_flv, **flv_pull_url}
        return json_data

    except Exception as e:
        print(f"First data retrieval failed: {url} Preparing to switch parsing methods due to {e}")
        return await get_douyin_app_stream_data(url=url, proxy_addr=proxy_addr, cookies=cookies)


@trace_error_decorator
async def get_tiktok_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict | None:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Cookie': 'ttwid=1%7CM-rF193sJugKuNz2RGNt-rh6pAAR9IMceUSzlDnPCNI%7C1683274418%7Cf726d4947f2fc37fecc7aeb0cdaee52892244d04efde6f8a8edd2bb168263269; tiktok_webapp_theme=light; tt_chain_token=VWkygAWDlm1cFg/k8whmOg==; passport_csrf_token=6e422c5a7991f8cec7033a8082921510; passport_csrf_token_default=6e422c5a7991f8cec7033a8082921510; d_ticket=f8c267d4af4523c97be1ccb355e9991e2ae06; odin_tt=320b5f386cdc23f347be018e588873db7f7aea4ea5d1813681c3fbc018ea025dde957b94f74146dbc0e3612426b865ccb95ec8abe4ee36cca65f15dbffec0deff7b0e69e8ea536d46e0f82a4fc37d211; cmpl_token=AgQQAPNSF-RO0rT04baWtZ0T_jUjl4fVP4PZYM2QPw; uid_tt=319b558dbba684bb1557206c92089cd113a875526a89aee30595925d804b81c7; uid_tt_ss=319b558dbba684bb1557206c92089cd113a875526a89aee30595925d804b81c7; sid_tt=ad5e736f4bedb2f6d42ccd849e706b1d; sessionid=ad5e736f4bedb2f6d42ccd849e706b1d; sessionid_ss=ad5e736f4bedb2f6d42ccd849e706b1d; store-idc=useast5; store-country-code=us; store-country-code-src=uid; tt-target-idc=useast5; tt-target-idc-sign=qXNk0bb1pDQ0FbCNF120Pl9WWMLZg9Edv5PkfyCbS4lIk5ieW5tfLP7XWROnN0mEaSlc5hg6Oji1pF-yz_3ZXnUiNMrA9wNMPvI6D9IFKKVmq555aQzwPIGHv0aQC5dNRgKo5Z5LBkgxUMWEojTKclq2_L8lBciw0IGdhFm_XyVJtbqbBKKgybGDLzK8ZyxF4Jl_cYRXaDlshZjc38JdS6wruDueRSHe7YvNbjxCnApEFUv-OwJANSPU_4rvcqpVhq3JI2VCCfw-cs_4MFIPCDOKisk5EhAo2JlHh3VF7_CLuv80FXg_7ZqQ2pJeMOog294rqxwbbQhl3ATvjQV_JsWyUsMd9zwqecpylrPvtySI2u1qfoggx1owLrrUynee1R48QlanLQnTNW_z1WpmZBgVJqgEGLwFoVOmRzJuFFNj8vIqdjM2nDSdWqX8_wX3wplohkzkPSFPfZgjzGnQX28krhgTytLt7BXYty5dpfGtsdb11WOFHM6MZ9R9uLVB; sid_guard=ad5e736f4bedb2f6d42ccd849e706b1d%7C1690990657%7C15525213%7CMon%2C+29-Jan-2024+08%3A11%3A10+GMT; sid_ucp_v1=1.0.0-KGM3YzgwYjZhODgyYWI1NjIwNTA0NjBmOWUxMGRhMjIzYTI2YjMxNDUKGAiqiJ30keKD5WQQwfCppgYYsws4AkDsBxAEGgd1c2Vhc3Q1IiBhZDVlNzM2ZjRiZWRiMmY2ZDQyY2NkODQ5ZTcwNmIxZA; ssid_ucp_v1=1.0.0-KGM3YzgwYjZhODgyYWI1NjIwNTA0NjBmOWUxMGRhMjIzYTI2YjMxNDUKGAiqiJ30keKD5WQQwfCppgYYsws4AkDsBxAEGgd1c2Vhc3Q1IiBhZDVlNzM2ZjRiZWRiMmY2ZDQyY2NkODQ5ZTcwNmIxZA; tt_csrf_token=dD0EIH8q-pe3qDQsCyyD1jLN6KizJDRjOEyk; __tea_cache_tokens_1988={%22_type_%22:%22default%22%2C%22user_unique_id%22:%227229608516049831425%22%2C%22timestamp%22:1683274422659}; ttwid=1%7CM-rF193sJugKuNz2RGNt-rh6pAAR9IMceUSzlDnPCNI%7C1694002151%7Cd89b77afc809b1a610661a9d1c2784d80ebef9efdd166f06de0d28e27f7e4efe; msToken=KfJAVZ7r9D_QVeQlYAUZzDFbc1Yx-nZz6GF33eOxgd8KlqvTg1lF9bMXW7gFV-qW4MCgUwnBIhbiwU9kdaSpgHJCk-PABsHCtTO5J3qC4oCTsrXQ1_E0XtbqiE4OVLZ_jdF1EYWgKNPT2SnwGkQ=; msToken=KfJAVZ7r9D_QVeQlYAUZzDFbc1Yx-nZz6GF33eOxgd8KlqvTg1lF9bMXW7gFV-qW4MCgUwnBIhbiwU9kdaSpgHJCk-PABsHCtTO5J3qC4oCTsrXQ1_E0XtbqiE4OVLZ_jdF1EYWgKNPT2SnwGkQ='
    }
    if cookies:
        headers['Cookie'] = cookies
    for i in range(3):
        html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers, abroad=True, http2=False)
        time.sleep(1)
        if "We regret to inform you that we have discontinued operating TikTok" in html_str:
            msg = re.search('<p>\n\\s+(We regret to inform you that we have discontinu.*?)\\.\n\\s+</p>', html_str)
            raise ConnectionError(
                f"Your proxy node's regional network is blocked from accessing TikTok; please switch to a node in "
                f"another region to access. {msg.group(1) if msg else ''}"
            )
        if 'UNEXPECTED_EOF_WHILE_READING' not in html_str:
            try:
                json_str = re.findall(
                    '<script id="SIGI_STATE" type="application/json">(.*?)</script>',
                    html_str, re.DOTALL)[0]
            except Exception:
                raise ConnectionError("Please check if your network can access the TikTok website normally")
            json_data = json.loads(json_str)
            return json_data


@trace_error_decorator
async def get_kuaishou_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    }
    if cookies:
        headers['Cookie'] = cookies
    try:
        html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    except Exception as e:
        print(f"Failed to fetch data from {url}.{e}")
        return {"type": 1, "is_live": False}

    try:
        json_str = re.search('<script>window.__INITIAL_STATE__=(.*?);\\(function\\(\\)\\{var s;', html_str).group(1)
        play_list = re.findall('(\\{"liveStream".*?),"gameInfo', json_str)[0] + "}"
        play_list = json.loads(play_list)
    except (AttributeError, IndexError, json.JSONDecodeError) as e:
        print(f"Failed to parse JSON data from {url}. Error: {e}")
        return {"type": 1, "is_live": False}

    result = {"type": 2, "is_live": False}

    if 'errorType' in play_list or 'liveStream' not in play_list:
        error_msg = play_list['errorType']['title'] + play_list['errorType']['content']
        print(f"Failed URL: {url} Error message: {error_msg}")
        return result

    if not play_list.get('liveStream'):
        print("IP banned. Please change device or network.")
        return result

    anchor_name = play_list['author'].get('name', '')
    result.update({"anchor_name": anchor_name})

    if play_list['liveStream'].get("playUrls"):
        if 'h264' in play_list['liveStream']['playUrls']:
            if 'adaptationSet' not in play_list['liveStream']['playUrls']['h264']:
                return result
            play_url_list = play_list['liveStream']['playUrls']['h264']['adaptationSet']['representation']
        else:
            # TODO: Old version which not working at 20241128, could be removed if not working confirmed
            play_url_list = play_list['liveStream']['playUrls'][0]['adaptationSet']['representation']
        result.update({"flv_url_list": play_url_list, "is_live": True})

    return result


@trace_error_decorator
async def get_kuaishou_stream_data2(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict | None:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': "https://www.kuaishou.com/short-video/3x224rwabjmuc9y?fid=1712760877&cc=share_copylink&followRefer=151&shareMethod=TOKEN&docId=9&kpn=KUAISHOU&subBiz=BROWSE_SLIDE_PHOTO&photoId=3x224rwabjmuc9y&shareId=17144298796566&shareToken=X-6FTMeYTsY97qYL&shareResourceType=PHOTO_OTHER&userId=3xtnuitaz2982eg&shareType=1&et=1_i/2000048330179867715_h3052&shareMode=APP&originShareId=17144298796566&appType=21&shareObjectId=5230086626478274600&shareUrlOpened=0&timestamp=1663833792288&utm_source=app_share&utm_medium=app_share&utm_campaign=app_share&location=app_share",
        'content-type': 'application/json',
        'Cookie': 'did=web_e988652e11b545469633396abe85a89f; didv=1796004001000',
    }
    if cookies:
        headers['Cookie'] = cookies
    try:
        eid = url.split('/u/')[1].strip()
        data = {"source": 5, "eid": eid, "shareMethod": "card", "clientType": "WEB_OUTSIDE_SHARE_H5"}
        app_api = 'https://livev.m.chenzhongtech.com/rest/k/live/byUser?kpn=GAME_ZONE&captchaToken='
        json_str = await async_req(url=app_api, proxy_addr=proxy_addr, headers=headers, data=data)
        json_data = json.loads(json_str)
        live_stream = json_data['liveStream']
        anchor_name = live_stream['user']['user_name']
        result = {
            "type": 2,
            "anchor_name": anchor_name,
            "is_live": False,
        }
        live_status = live_stream['living']
        if live_status:
            result['is_live'] = True
            backup_m3u8_url = live_stream['hlsPlayUrl']
            backup_flv_url = live_stream['playUrls'][0]['url']
            if 'multiResolutionHlsPlayUrls' in live_stream:
                m3u8_url_list = live_stream['multiResolutionHlsPlayUrls'][0]['urls']
                result['m3u8_url_list'] = m3u8_url_list
            if 'multiResolutionPlayUrls' in live_stream:
                flv_url_list = live_stream['multiResolutionPlayUrls'][0]['urls']
                result['flv_url_list'] = flv_url_list
            result['backup'] = {'m3u8_url': backup_m3u8_url, 'flv_url': backup_flv_url}
        if result['anchor_name']:
            return result
    except Exception as e:
        print(f"{e}, Failed URL: {url}, preparing to switch to a backup plan for re-parsing.")
    return await get_kuaishou_stream_data(url, cookies=cookies, proxy_addr=proxy_addr)


@trace_error_decorator
async def get_huya_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Cookie': 'huya_ua=webh5&0.1.0&websocket; game_did=zXyXVqV1NF4ZeNWg7QaOFbpIEWqcsrxkoVy; alphaValue=0.80; isInLiveRoom=; guid=0a7df378828609654d01a205a305fb52; __yamid_tt1=0.8936157401010706; __yamid_new=CA715E8BC9400001E5A313E028F618DE; udb_guiddata=4657813d32ce43d381ea8ff8d416a3c2; udb_deviceid=w_756598227007868928; sdid=0UnHUgv0_qmfD4KAKlwzhqQB32nywGZJYLZl_9RLv0Lbi5CGYYNiBGLrvNZVszz4FEo_unffNsxk9BdvXKO_PkvC5cOwCJ13goOiNYGClLirWVkn9LtfFJw_Qo4kgKr8OZHDqNnuwg612sGyflFn1draukOt03gk2m3pwGbiKsB143MJhMxcI458jIjiX0MYq; Hm_lvt_51700b6c722f5bb4cf39906a596ea41f=1708583696; SoundValue=0.50; sdidtest=0UnHUgv0_qmfD4KAKlwzhqQB32nywGZJYLZl_9RLv0Lbi5CGYYNiBGLrvNZVszz4FEo_unffNsxk9BdvXKO_PkvC5cOwCJ13goOiNYGClLirWVkn9LtfFJw_Qo4kgKr8OZHDqNnuwg612sGyflFn1draukOt03gk2m3pwGbiKsB143MJhMxcI458jIjiX0MYq; sdidshorttest=test; __yasmid=0.8936157401010706; _yasids=__rootsid^%^3DCAA3838C53600001F4EE863017406250; huyawap_rep_cnt=4; udb_passdata=3; huya_web_rep_cnt=89; huya_flash_rep_cnt=20; Hm_lpvt_51700b6c722f5bb4cf39906a596ea41f=1709548534; _rep_cnt=3; PHPSESSID=r0klm0vccf08q1das65bnd8co1; guid=0a7df378828609654d01a205a305fb52; huya_hd_rep_cnt=8',
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    json_str = re.findall('stream: (\\{"data".*?),"iWebDefaultBitRate"', html_str)[0]
    json_data = json.loads(json_str + '}')
    return json_data


@trace_error_decorator
async def get_huya_app_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'xweb_xhr': '1',
        'referer': 'https://servicewechat.com/wx74767bf0b684f7d3/301/page-frame.html',
        'accept-language': 'zh-CN,zh;q=0.9',
    }

    if cookies:
        headers['Cookie'] = cookies
    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]

    if any(char.isalpha() for char in room_id):
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
        room_id = re.search('ProfileRoom":(.*?),"sPrivateHost', html_str)
        if room_id:
            room_id = room_id.group(1)
        else:
            raise Exception('Please use "https://www.huya.com/+room_number" for recording')

    params = {
        'm': 'Live',
        'do': 'profileRoom',
        'roomid': room_id,
        'showSecret': '1',
    }
    wx_app_api = f'https://mp.huya.com/cache.php?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=wx_app_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['profileInfo']['nick']
    live_status = json_data['data']['realLiveStatus']
    live_title = json_data['data']['liveData']['introduction']
    if live_status != 'ON':
        return {'anchor_name': anchor_name, 'is_live': False}
    else:
        base_steam_info_list = json_data['data']['stream']['baseSteamInfoList']
        play_url_list = []
        for i in base_steam_info_list:
            cdn_type = i['sCdnType']
            stream_name = i['sStreamName']
            s_flv_url = i['sFlvUrl']
            flv_anti_code = i['sFlvAntiCode']
            s_hls_url = i['sHlsUrl']
            hls_anti_code = i['sHlsAntiCode']
            m3u8_url = f'{s_hls_url}/{stream_name}.m3u8?{hls_anti_code}'
            flv_url = f'{s_flv_url}/{stream_name}.flv?{flv_anti_code}'
            play_url_list.append(
                {
                    'cdn_type': cdn_type,
                    'm3u8_url': m3u8_url,
                    'flv_url': flv_url,
                }
            )
        #print(json.dumps(play_url_list, indent=4, ensure_ascii=False))
        # flv_url = 'https://' + play_url_list[0]['flv_url'].split('://')[1]
        # record_url = flv_url

        # 设定优先级，优先选择 TX,2025/03/14时AL不可用
        priority_order = ["TX", "HW", "HS", "AL"]

        # 查找优先的 flv_url
        selected_flv_url = None
        selected_cdn_type = None

        for cdn in priority_order:
            for item in play_url_list:
                if item["cdn_type"] == cdn:
                    selected_flv_url = item["flv_url"]
                    selected_cdn_type = cdn
                    break
            if selected_flv_url:
                break

        # 处理 flv_url，确保使用 https
        if selected_flv_url:
            flv_url = 'https://' + selected_flv_url.split('://')[1]

            # 如果选择的是 TX，执行额外的字符串替换
            if selected_cdn_type == "TX":
                flv_url = flv_url.replace("&ctype=tars_mp", "&ctype=huya_webh5").replace("&fs=bhct", "&fs=bgct")

            record_url = flv_url
        else:
            record_url = None

        return {
            'anchor_name': anchor_name,
            'is_live': True,
            'm3u8_url': play_url_list[0]['m3u8_url'],
            'flv_url': play_url_list[0]['flv_url'],
            'record_url': record_url,
            'title': live_title
        }


def md5(data) -> str:
    return hashlib.md5(data.encode('utf-8')).hexdigest()


async def get_token_js(rid: str, did: str, proxy_addr: OptionalStr = None) -> List[str]:

    url = f'https://www.douyu.com/{rid}'
    html_str = await async_req(url=url, proxy_addr=proxy_addr)
    result = re.search(r'(vdwdae325w_64we[\s\S]*function ub98484234[\s\S]*?)function', html_str).group(1)
    func_ub9 = re.sub(r'eval.*?;}', 'strc;}', result)
    js = execjs.compile(func_ub9)
    res = js.call('ub98484234')

    t10 = str(int(time.time()))
    v = re.search(r'v=(\d+)', res).group(1)
    rb = md5(rid + did + t10 + v)

    func_sign = re.sub(r'return rt;}\);?', 'return rt;}', res)
    func_sign = func_sign.replace('(function (', 'function sign(')
    func_sign = func_sign.replace('CryptoJS.MD5(cb).toString()', '"' + rb + '"')

    js = execjs.compile(func_sign)
    params = js.call('sign', rid, did, t10)
    params_list = re.findall('=(.*?)(?=&|$)', params)
    return params_list


@trace_error_decorator
async def get_douyu_info_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Referer': 'https://m.douyu.com/3125893?rid=3125893&dyshid=0-96003918aa5365bc6dcb4933000316p1&dyshci=181',
        'Cookie': 'dy_did=413b835d2ae00270f0c69f6400031601; acf_did=413b835d2ae00270f0c69f6400031601; Hm_lvt_e99aee90ec1b2106afe7ec3b199020a7=1692068308,1694003758; m_did=96003918aa5365bc6dcb4933000316p1; dy_teen_mode=%7B%22uid%22%3A%22472647365%22%2C%22status%22%3A0%2C%22birthday%22%3A%22%22%2C%22password%22%3A%22%22%7D; PHPSESSID=td59qi2fu2gepngb8mlehbeme3; acf_auth=94fc9s%2FeNj%2BKlpU%2Br8tZC3Jo9sZ0wz9ClcHQ1akL2Nhb6ZyCmfjVWSlR3LFFPuePWHRAMo0dt9vPSCoezkFPOeNy4mYcdVOM1a8CbW0ZAee4ipyNB%2Bflr58; dy_auth=bec5yzM8bUFYe%2FnVAjmUAljyrsX%2FcwRW%2FyMHaoArYb5qi8FS9tWR%2B96iCzSnmAryLOjB3Qbeu%2BBD42clnI7CR9vNAo9mva5HyyL41HGsbksx1tEYFOEwxSI; wan_auth37wan=5fd69ed5b27fGM%2FGoswWwDo%2BL%2FRMtnEa4Ix9a%2FsH26qF0sR4iddKMqfnPIhgfHZUqkAk%2FA1d8TX%2B6F7SNp7l6buIxAVf3t9YxmSso8bvHY0%2Fa6RUiv8; acf_uid=472647365; acf_username=472647365; acf_nickname=%E7%94%A8%E6%88%B776576662; acf_own_room=0; acf_groupid=1; acf_phonestatus=1; acf_avatar=https%3A%2F%2Fapic.douyucdn.cn%2Fupload%2Favatar%2Fdefault%2F24_; acf_ct=0; acf_ltkid=25305099; acf_biz=1; acf_stk=90754f8ed18f0c24; Hm_lpvt_e99aee90ec1b2106afe7ec3b199020a7=1694003778'
    }
    if cookies:
        headers['Cookie'] = cookies

    match_rid = re.search('rid=(.*?)(?=&|$)', url)
    if match_rid:
        rid = match_rid.group(1)
    else:
        rid = re.search('douyu.com/(.*?)(?=\\?|$)', url).group(1)
        html_str = await async_req(url=f'https://m.douyu.com/{rid}', proxy_addr=proxy_addr, headers=headers)
        json_str = re.findall('<script id="vike_pageContext" type="application/json">(.*?)</script>', html_str)[0]
        json_data = json.loads(json_str)
        rid = json_data['pageProps']['room']['roomInfo']['roomInfo']['rid']

    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
    url2 = f'https://www.douyu.com/betard/{rid}'
    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    result = {
        "anchor_name": json_data['room']['nickname'],
        "is_live": False
    }
    if json_data['room']['videoLoop'] == 0 and json_data['room']['show_status'] == 1:
        result["title"] = json_data['room']['room_name'].replace('&nbsp;', '')
        result["is_live"] = True
        result["room_id"] = json_data['room']['room_id']
    return result


@trace_error_decorator
async def get_douyu_stream_data(rid: str, rate: str = '-1', proxy_addr: OptionalStr = None,
                          cookies: OptionalStr = None) -> dict:
    did = '10000000000000000000000000003306'
    params_list = await get_token_js(rid, did, proxy_addr=proxy_addr)
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Referer': 'https://m.douyu.com/3125893?rid=3125893&dyshid=0-96003918aa5365bc6dcb4933000316p1&dyshci=181',
        'Cookie': 'dy_did=413b835d2ae00270f0c69f6400031601; acf_did=413b835d2ae00270f0c69f6400031601; Hm_lvt_e99aee90ec1b2106afe7ec3b199020a7=1692068308,1694003758; m_did=96003918aa5365bc6dcb4933000316p1; dy_teen_mode=%7B%22uid%22%3A%22472647365%22%2C%22status%22%3A0%2C%22birthday%22%3A%22%22%2C%22password%22%3A%22%22%7D; PHPSESSID=td59qi2fu2gepngb8mlehbeme3; acf_auth=94fc9s%2FeNj%2BKlpU%2Br8tZC3Jo9sZ0wz9ClcHQ1akL2Nhb6ZyCmfjVWSlR3LFFPuePWHRAMo0dt9vPSCoezkFPOeNy4mYcdVOM1a8CbW0ZAee4ipyNB%2Bflr58; dy_auth=bec5yzM8bUFYe%2FnVAjmUAljyrsX%2FcwRW%2FyMHaoArYb5qi8FS9tWR%2B96iCzSnmAryLOjB3Qbeu%2BBD42clnI7CR9vNAo9mva5HyyL41HGsbksx1tEYFOEwxSI; wan_auth37wan=5fd69ed5b27fGM%2FGoswWwDo%2BL%2FRMtnEa4Ix9a%2FsH26qF0sR4iddKMqfnPIhgfHZUqkAk%2FA1d8TX%2B6F7SNp7l6buIxAVf3t9YxmSso8bvHY0%2Fa6RUiv8; acf_uid=472647365; acf_username=472647365; acf_nickname=%E7%94%A8%E6%88%B776576662; acf_own_room=0; acf_groupid=1; acf_phonestatus=1; acf_avatar=https%3A%2F%2Fapic.douyucdn.cn%2Fupload%2Favatar%2Fdefault%2F24_; acf_ct=0; acf_ltkid=25305099; acf_biz=1; acf_stk=90754f8ed18f0c24; Hm_lpvt_e99aee90ec1b2106afe7ec3b199020a7=1694003778'
    }
    if cookies:
        headers['Cookie'] = cookies

    data = {
        'v': params_list[0],
        'did': params_list[1],
        'tt': params_list[2],
        'sign': params_list[3],  # 10分钟有效期
        'ver': '22011191',
        'rid': rid,
        'rate': rate,  # 0蓝光、3超清、2高清、-1默认
    }

    # app_api = 'https://m.douyu.com/hgapi/livenc/room/getStreamUrl'
    app_api = f'https://www.douyu.com/lapi/live/getH5Play/{rid}'
    json_str = await async_req(url=app_api, proxy_addr=proxy_addr, headers=headers, data=data)
    json_data = json.loads(json_str)
    return json_data


@trace_error_decorator
async def get_yy_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://www.yy.com/',
        'Cookie': 'hd_newui=0.2103068903976506; hdjs_session_id=0.4929014850884579; hdjs_session_time=1694004002636; hiido_ui=0.923076230899782'
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    anchor_name = re.search('nick: "(.*?)",\n\\s+logo', html_str).group(1)
    cid = re.search('sid : "(.*?)",\n\\s+ssid', html_str, re.DOTALL).group(1)

    data = '{"head":{"seq":1701869217590,"appidstr":"0","bidstr":"121","cidstr":"' + cid + '","sidstr":"' + cid + '","uid64":0,"client_type":108,"client_ver":"5.17.0","stream_sys_ver":1,"app":"yylive_web","playersdk_ver":"5.17.0","thundersdk_ver":"0","streamsdk_ver":"5.17.0"},"client_attribute":{"client":"web","model":"web0","cpu":"","graphics_card":"","os":"chrome","osversion":"0","vsdk_version":"","app_identify":"","app_version":"","business":"","width":"1920","height":"1080","scale":"","client_type":8,"h265":0},"avp_parameter":{"version":1,"client_type":8,"service_type":0,"imsi":0,"send_time":1701869217,"line_seq":-1,"gear":4,"ssl":1,"stream_format":0}}'
    data_bytes = data.encode('utf-8')
    params = {
        "uid": "0",
        "cid": cid,
        "sid": cid,
        "appid": "0",
        "sequence": "1701869217590",
        "encode": "json"
    }
    url2 = f'https://stream-manager.yy.com/v3/channel/streams?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=url2, data=data_bytes, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    json_data['anchor_name'] = anchor_name

    params = {
        'uid': '',
        'sid': cid,
        'ssid': cid,
        '_': int(time.time() * 1000),
    }
    detail_api = f'https://www.yy.com/live/detail?{urllib.parse.urlencode(params)}'
    json_str2 = await async_req(detail_api, proxy_addr=proxy_addr, headers=headers)
    json_data2 = json.loads(json_str2)
    json_data['title'] = json_data2['data']['roomName']
    return json_data


@trace_error_decorator
async def get_bilibili_room_info_h5(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> str:
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36',
        'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'cookie': '',
        'origin': 'https://live.bilibili.com',
        'referer': 'https://live.bilibili.com/26066074',
    }
    if cookies:
        headers['cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    api = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getH5InfoByRoom?room_id={room_id}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    room_info = json.loads(json_str)
    title = room_info['data']['room_info']['title'] if room_info.get('data') else ''
    return title


@trace_error_decorator
async def get_bilibili_room_info(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    }
    if cookies:
        headers['Cookie'] = cookies

    try:
        room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
        json_str = await async_req(f'https://api.live.bilibili.com/room/v1/Room/room_init?id={room_id}',
                           proxy_addr=proxy_addr, headers=headers)
        room_info = json.loads(json_str)
        uid = room_info['data']['uid']
        live_status = True if room_info['data']['live_status'] == 1 else False

        api = f'https://api.live.bilibili.com/live_user/v1/Master/info?uid={uid}'
        json_str2 = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
        anchor_info = json.loads(json_str2)
        anchor_name = anchor_info['data']['info']['uname']

        title = await get_bilibili_room_info_h5(url, proxy_addr, cookies)
        return {"anchor_name": anchor_name, "live_status": live_status, "room_url": url, "title": title}
    except Exception as e:
        print(e)
        return {"anchor_name": '', "live_status": False, "room_url": url}


@trace_error_decorator
async def get_bilibili_stream_data(url: str, qn: str = '10000', platform: str = 'web', proxy_addr: OptionalStr = None,
                             cookies: OptionalStr = None) -> OptionalStr:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'origin': 'https://live.bilibili.com',
        'referer': 'https://live.bilibili.com/26066074',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    params = {
        'cid': room_id,
        'qn': qn,
        'platform': platform,
    }
    play_api = f'https://api.live.bilibili.com/room/v1/Room/playUrl?{urllib.parse.urlencode(params)}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    if json_data and json_data['code'] == 0:
        for i in json_data['data']['durl']:
            if 'd1--cn-gotcha' in i['url']:
                return i['url']
        return json_data['data']['durl'][-1]['url']
    else:
        params = {
            "room_id": room_id,
            "protocol": "0,1",
            "format": "0,1,2",
            "codec": "0,1,2",
            "qn": qn,
            "platform": "web",
            "ptype": "8",
            "dolby": "5",
            "panorama": "1",
            "hdr_type": "0,1"
        }

        # 此接口因网页上有限制, 需要配置登录后的cookie才能获取最高画质
        api = f'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?{urllib.parse.urlencode(params)}'
        json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        if json_data['data']['live_status'] == 0:
            print("The anchor did not start broadcasting.")
            return
        playurl_info = json_data['data']['playurl_info']
        format_list = playurl_info['playurl']['stream'][0]['format']
        stream_data_list = format_list[0]['codec']
        sorted_stream_list = sorted(stream_data_list, key=itemgetter("current_qn"), reverse=True)
        # qn: 30000=杜比 20000=4K 10000=原画 400=蓝光 250=超清 150=高清 80=流畅
        video_quality_options = {'10000': 0, '400': 1, '250': 2, '150': 3, '80': 4}
        qn_count = len(sorted_stream_list)
        select_stream_index = min(video_quality_options[qn], qn_count - 1)
        stream_data: dict = sorted_stream_list[select_stream_index]
        base_url = stream_data['base_url']
        host = stream_data['url_info'][0]['host']
        extra = stream_data['url_info'][0]['extra']
        m3u8_url = host + base_url + extra
        return m3u8_url

@trace_error_decorator
async def get_xhs_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'xy-common-params': 'platform=iOS&sid=session.1722166379345546829388',
        'referer': 'https://app.xhs.cn/',
    }
    if cookies:
        headers['Cookie'] = cookies

    if "xhslink.com" in url:
        url = await async_req(url, proxy_addr=proxy_addr, headers=headers, redirect_url=True)

    host_id = get_params(url, "host_id")
    user_id = re.search("/user/profile/(.*?)(?=/|\\?|$)", url)
    user_id = user_id.group(1) if user_id else host_id
    result = {"anchor_name": '', "is_live": False}
    html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
    match_data = re.search("<script>window.__INITIAL_STATE__=(.*?)</script>", html_str)

    if match_data:
        json_str = match_data.group(1).replace("undefined", "null")
        json_data = json.loads(json_str)

        if json_data.get("liveStream"):
            stream_data = json_data["liveStream"]
            if stream_data.get("liveStatus") == "success":
                room_info = stream_data["roomData"]["roomInfo"]
                title = room_info.get("roomTitle")
                if title and "回放" not in title:
                    live_link = room_info["deeplink"]
                    anchor_name = get_params(live_link, "host_nickname")
                    flv_url = get_params(live_link, "flvUrl")
                    room_id = flv_url.split('live/')[1].split('.')[0]
                    flv_url = f"http://live-source-play.xhscdn.com/live/{room_id}.flv"
                    m3u8_url = flv_url.replace('.flv', '.m3u8')
                    result |= {
                        "anchor_name": anchor_name,
                        "is_live": True,
                        "title": title,
                        "flv_url": flv_url,
                        "m3u8_url": m3u8_url,
                        'record_url': flv_url
                    }
                    return result

    profile_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
    html_str = await async_req(profile_url, proxy_addr=proxy_addr, headers=headers)
    anchor_name = re.search("<title>@(.*?) 的个人主页</title>", html_str)
    if anchor_name:
        result["anchor_name"] = anchor_name.group(1)

    return result


@trace_error_decorator
async def get_bigo_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://www.bigo.tv/',
    }
    if cookies:
        headers['Cookie'] = cookies

    if 'bigo.tv' not in url:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
        web_url = re.search(
            '<meta data-n-head="ssr" data-hid="al:web:url" property="al:web:url" content="(.*?)">',
            html_str).group(1)
        room_id = web_url.split('&amp;h=')[-1]
    else:
        if '&h=' in url:
            room_id = url.split('&h=')[-1]
        else:
            room_id = re.search('www.bigo.tv/cn/(\\w+)', url).group(1)

    data = {'siteId': room_id}  # roomId
    url2 = 'https://ta.bigo.tv/official_website/studio/getInternalStudioInfo'
    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, data=data)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['nick_name']
    live_status = json_data['data']['alive']
    result = {"anchor_name": anchor_name, "is_live": False}

    if live_status == 1:
        live_title = json_data['data']['roomTopic']
        m3u8_url = json_data['data']['hls_src']
        result['m3u8_url'] = m3u8_url
        result['record_url'] = m3u8_url
        result |= {"title": live_title, "is_live": True, "m3u8_url": m3u8_url, 'record_url': m3u8_url}
    elif result['anchor_name'] == '':
        html_str = await async_req(url=f'https://www.bigo.tv/cn/{room_id}', proxy_addr=proxy_addr, headers=headers)
        result['anchor_name'] = re.search('<title>欢迎来到(.*?)的直播间</title>', html_str, re.DOTALL).group(1)

    return result


@trace_error_decorator
async def get_blued_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    json_str = re.search('decodeURIComponent\\(\"(.*?)\"\\)\\),window\\.Promise', html_str, re.DOTALL).group(1)
    json_str = urllib.parse.unquote(json_str)
    json_data = json.loads(json_str)
    anchor_name = json_data['userInfo']['name']
    live_status = json_data['userInfo']['onLive']
    result = {"anchor_name": anchor_name, "is_live": False}

    if live_status:
        m3u8_url = json_data['liveInfo']['liveUrl']
        result |= {"is_live": True, "m3u8_url": m3u8_url, 'record_url': m3u8_url}
    return result


@trace_error_decorator
async def login_sooplive(username: str, password: str, proxy_addr: OptionalStr = None) -> OptionalStr:
    if len(username) < 6 or len(password) < 10:
        raise RuntimeError("sooplive login failed! Please enter the correct account and password for the sooplive "
                           "platform in the config.ini file.")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://play.sooplive.co.kr',
        'Referer': 'https://play.sooplive.co.kr/superbsw123/277837074',
    }

    data = {
        'szWork': 'login',
        'szType': 'json',
        'szUid': username,
        'szPassword': password,
        'isSaveId': 'true',
        'isSavePw': 'true',
        'isSaveJoin': 'true',
        'isLoginRetain': 'Y',
    }

    url = 'https://login.sooplive.co.kr/app/LoginAction.php'

    try:
        cookie_dict = await async_req(url, proxy_addr=proxy_addr, headers=headers,
                                      data=data, return_cookies=True, timeout=20)
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
        return cookie_str
    except Exception as e:
        print(f"An error occurred during login: {e}")
        raise Exception(
            "sooplive login failed, please check if the account password in the configuration file is correct."
        )


@trace_error_decorator
async def get_sooplive_cdn_url(broad_no: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Origin': 'https://play.sooplive.co.kr',
        'Referer': 'https://play.sooplive.co.kr/oul282/249469582',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    if cookies:
        headers['Cookie'] = cookies

    params = {
        'return_type': 'gcp_cdn',
        'use_cors': 'false',
        'cors_origin_url': 'play.sooplive.co.kr',
        'broad_key': f'{broad_no}-common-master-hls',
        'time': '8361.086329376785',
    }

    url2 = 'http://livestream-manager.sooplive.co.kr/broad_stream_assign.html?' + urllib.parse.urlencode(params)
    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)

    return json_data


@trace_error_decorator
async def get_sooplive_tk(url: str, rtype: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> str | tuple:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Origin': 'https://play.sooplive.co.kr',
        'Referer': 'https://play.sooplive.co.kr/secretx/250989857',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    if cookies:
        headers['Cookie'] = cookies

    split_url = url.split('/')
    bj_id = split_url[3] if len(split_url) < 6 else split_url[5]
    room_password = get_params(url, "pwd")
    if not room_password:
        room_password = ''
    data = {
        'bid': bj_id,
        'bno': '',
        'type': rtype,
        'pwd': room_password,
        'player_type': 'html5',
        'stream_type': 'common',
        'quality': 'master',
        'mode': 'landing',
        'from_api': '0',
        'is_revive': 'false',
    }

    url2 = f'https://live.sooplive.co.kr/afreeca/player_live_api.php?bjid={bj_id}'
    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = json.loads(json_str)

    if rtype == 'aid':
        token = json_data["CHANNEL"]["AID"]
        return token
    else:
        bj_name = json_data['CHANNEL']['BJNICK']
        bj_id = json_data['CHANNEL']['BJID']
        return f"{bj_name}-{bj_id}", json_data['CHANNEL']['BNO']


@trace_error_decorator
async def get_sooplive_stream_data(
        url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None,
        username: OptionalStr = None, password: OptionalStr = None
) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://m.sooplive.co.kr/',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    if cookies:
        headers['Cookie'] = cookies

    split_url = url.split('/')
    bj_id = split_url[3] if len(split_url) < 6 else split_url[5]

    data = {
        'bj_id': bj_id,
        'broad_no': '',
        'agent': 'web',
        'confirm_adult': 'true',
        'player_type': 'webm',
        'mode': 'live',
    }

    url2 = 'http://api.m.sooplive.co.kr/broad/a/watch'

    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = json.loads(json_str)

    if 'user_nick' in json_data['data']:
        anchor_name = json_data['data']['user_nick']
        if "bj_id" in json_data['data']:
            anchor_name = f"{anchor_name}-{json_data['data']['bj_id']}"
    else:
        anchor_name = ''

    result = {"anchor_name": anchor_name or '' ,"is_live": False}

    async def get_url_list(m3u8: str) -> List[str]:
        resp = await async_req(url=m3u8, proxy_addr=proxy_addr, headers=headers, abroad=True)
        play_url_list = []
        url_prefix = m3u8.rsplit('/', maxsplit=1)[0] + '/'
        for i in resp.split('\n'):
            if i.startswith('auth_playlist'):
                play_url_list.append(url_prefix + i.strip())
        bandwidth_pattern = re.compile(r'BANDWIDTH=(\d+)')
        bandwidth_list = bandwidth_pattern.findall(resp)
        url_to_bandwidth = {purl: int(bandwidth) for bandwidth, purl in zip(bandwidth_list, play_url_list)}
        play_url_list = sorted(play_url_list, key=lambda purl: url_to_bandwidth[purl], reverse=True)
        return play_url_list

    if not anchor_name:
        async def handle_login() -> OptionalStr:
            cookie = await login_sooplive(username, password, proxy_addr=proxy_addr)
            if 'AuthTicket=' in cookie:
                print("sooplive platform login successful! Starting to fetch live streaming data...")
                return cookie

        async def fetch_data(cookie, _result) -> dict:
            aid_token = await get_sooplive_tk(url, rtype='aid', proxy_addr=proxy_addr, cookies=cookie)
            _anchor_name, _broad_no = await get_sooplive_tk(url, rtype='info', proxy_addr=proxy_addr, cookies=cookie)
            _view_url_data = await get_sooplive_cdn_url(_broad_no, proxy_addr=proxy_addr)
            _view_url = _view_url_data['view_url']
            _m3u8_url = _view_url + '?aid=' + aid_token
            _result |= {
                "anchor_name": _anchor_name,
                "is_live": True,
                "m3u8_url": _m3u8_url,
                'play_url_list': await get_url_list(_m3u8_url),
                'new_cookies': cookie
            }
            return _result

        if json_data['data']['code'] == -3001:
            print("sooplive live stream failed to retrieve, the live stream just ended.")
            return result

        elif json_data['data']['code'] == -3002:
            print("sooplive live stream retrieval failed, the live needs 19+, you are not logged in.")
            print("Attempting to log in to the sooplive live streaming platform with your account and password, "
                  "please ensure it is configured.")
            new_cookie = await handle_login()
            if new_cookie and len(new_cookie) > 0:
                return await fetch_data(new_cookie, result)
            raise RuntimeError("sooplive login failed, please check if the account and password are correct")

        elif json_data['data']['code'] == -3004:
            if cookies and len(cookies) > 0:
                return await fetch_data(cookies, result)
            else:
                raise RuntimeError("sooplive login failed, please check if the account and password are correct")
        elif json_data['data']['code'] == -6001:
            print("error message：Please check if the input sooplive live room address "
                  "is correct.")
            return result
    if json_data['result'] == 1 and anchor_name:
        broad_no = json_data['data']['broad_no']
        hls_authentication_key = json_data['data']['hls_authentication_key']
        view_url_data = await get_sooplive_cdn_url(broad_no, proxy_addr=proxy_addr)
        view_url = view_url_data['view_url']
        m3u8_url = view_url + '?aid=' + hls_authentication_key
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'play_url_list': await get_url_list(m3u8_url)}
    result['new_cookies'] = None
    return result


@trace_error_decorator
async def get_netease_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://cc.163.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies
    url = url + '/' if url[-1] != '/' else url

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    json_str = re.search('<script id="__NEXT_DATA__" .* crossorigin="anonymous">(.*?)</script></body>',
                         html_str, re.DOTALL).group(1)
    json_data = json.loads(json_str)
    room_data = json_data['props']['pageProps']['roomInfoInitData']
    live_data = room_data['live']
    result = {"is_live": False}
    live_status = live_data.get('status') == 1
    result["anchor_name"] = live_data.get('nickname', room_data.get('nickname'))
    if live_status:
        result |= {
            'is_live': True,
            'title': live_data['title'],
            'stream_list': live_data.get('quickplay'),
            'm3u8_url': live_data.get('sharefile')
        }
    return result


@trace_error_decorator
async def get_qiandurebo_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://qiandurebo.com/web/index.php',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    data = re.search('var user = (.*?)\r\n\\s+user\\.play_url', html_str, re.DOTALL).group(1)
    anchor_name = re.findall('"zb_nickname": "(.*?)",\r\n', data)

    result = {"anchor_name": "", "is_live": False}
    if len(anchor_name) > 0:
        result['anchor_name'] = anchor_name[0]
        play_url = re.findall('"play_url": "(.*?)",\r\n', data)

        if len(play_url) > 0 and 'common-text-center" style="display:block' not in html_str:
            result |= {
                'anchor_name': anchor_name[0],
                'is_live': True,
                'flv_url': play_url[0],
                'record_url': play_url[0]
            }
    return result


@trace_error_decorator
async def get_pandatv_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.pandalive.co.kr',
        'referer': 'https://www.pandalive.co.kr/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    user_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    url2 = 'https://api.pandalive.co.kr/v1/live/play'
    data = {
        'userId': user_id,
        'info': 'media fanGrade',
    }
    room_password = get_params(url, "pwd")
    if not room_password:
        room_password = ''
    data2 = {
        'action': 'watch',
        'userId': user_id,
        'password': room_password,
        'shareLinkType': '',
    }

    result = {"anchor_name": "", "is_live": False}
    json_str = await async_req('https://api.pandalive.co.kr/v1/member/bj',
                       proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = json.loads(json_str)
    if "bjInfo" not in json_data:
        raise RuntimeError(json_data.get("message", 'Unknown error'))
    anchor_id = json_data['bjInfo']['id']
    anchor_name = f"{json_data['bjInfo']['nick']}-{anchor_id}"
    result['anchor_name'] = anchor_name
    live_status = 'media' in json_data

    if live_status:
        json_str = await async_req(url2, proxy_addr=proxy_addr, headers=headers, data=data2, abroad=True)
        json_data = json.loads(json_str)
        if 'errorData' in json_data:
            if json_data['errorData']['code'] == 'needAdult':
                raise RuntimeError(f"{url} The live room requires login and is only accessible to adults. Please "
                                   f"correctly fill in the login cookie in the configuration file.")
            else:
                raise RuntimeError(json_data['errorData']['code'], json_data['message'])
        play_url = json_data['PlayList']['hls'][0]['url']
        play_url_list = await get_play_url_list(m3u8=play_url, proxy=proxy_addr, header=headers, abroad=True)
        result |= {'is_live': True, 'm3u8_url': play_url, 'play_url_list': play_url_list}
    return result


@trace_error_decorator
async def get_maoerfm_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://fm.missevan.com/live/868895007',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    url2 = f'https://fm.missevan.com/api/v2/live/{room_id}'

    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    anchor_name = json_data['info']['creator']['username']
    live_status = False
    if 'room' in json_data['info']:
        live_status = json_data['info']['room']['status']['broadcasting']

    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        stream_list = json_data['info']['room']['channel']
        m3u8_url = stream_list['hls_pull_url']
        flv_url = stream_list['flv_pull_url']
        title = json_data['info']['room']['name']
        result |= {'is_live': True, 'title': title, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_winktv_bj_info(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> tuple:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://www.winktv.co.kr/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies
    user_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    data = {
        'userId': user_id,
        'info': 'media',
    }

    info_api = 'https://api.winktv.co.kr/v1/member/bj'
    json_str = await async_req(url=info_api, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = json.loads(json_str)
    live_status = 'media' in json_data
    anchor_id = json_data['bjInfo']['id']
    anchor_name = f"{json_data['bjInfo']['nick']}-{anchor_id}"
    return anchor_name, live_status


@trace_error_decorator
async def get_winktv_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://www.winktv.co.kr',
        'origin': 'https://www.winktv.co.kr',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',

    }
    if cookies:
        headers['Cookie'] = cookies
    user_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    room_password = get_params(url, "pwd")
    if not room_password:
        room_password = ''
    data = {
        'action': 'watch',
        'userId': user_id,
        'password': room_password,
        'shareLinkType': '',
    }

    anchor_name, live_status = await get_winktv_bj_info(url=url, proxy_addr=proxy_addr, cookies=cookies)
    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        play_api = 'https://api.winktv.co.kr/v1/live/play'
        json_str = await async_req(url=play_api, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
        if '403: Forbidden' in json_str:
            raise ConnectionError(f"Your network has been banned from accessing WinkTV ({json_str})")
        json_data = json.loads(json_str)
        if 'errorData' in json_data:
            if json_data['errorData']['code'] == 'needAdult':
                raise RuntimeError(f"{url} The live stream is only accessible to logged-in adults. Please ensure that "
                                   f"the cookie is correctly filled in the configuration file after logging in.")
            else:
                raise RuntimeError(json_data['errorData']['code'], json_data['message'])
        m3u8_url = json_data['PlayList']['hls'][0]['url']
        play_url_list = await get_play_url_list(m3u8=m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        result['m3u8_url'] = m3u8_url
        result['play_url_list'] = play_url_list
    return result


@trace_error_decorator
async def login_flextv(username: str, password: str, proxy_addr: OptionalStr = None) -> OptionalStr:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'content-type': 'application/json;charset=UTF-8',
        'referer': 'https://www.flextv.co.kr/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }

    data = {
        'loginId': username,
        'password': password,
        'loginKeep': True,
        'saveId': True,
        'device': 'PCWEB',
    }

    url = 'https://api.flextv.co.kr/v2/api/auth/signin'

    try:
        print("Logging into FlexTV platform...")
        cookie_dict = await async_req(url, proxy_addr=proxy_addr, headers=headers, json_data=data,
                                      return_cookies=True, timeout=20)

        if cookie_dict and 'flx_oauth_access' in cookie_dict:
            cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
            return cookie_str
        else:
            print("Please check if the FlexTV account and password in the configuration file are correct.")
            return None

    except Exception as e:
        print(f"FlexTV login request exception: {e}")
        raise Exception(
            "FlexTV login failed, please check if the account and password in the configuration file are correct."
        )


async def get_flextv_stream_url(
        url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None
) -> str:
    async def fetch_data(cookie) -> dict:
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'referer': 'https://www.flextv.co.kr/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        }
        user_id = url.split('/live')[0].rsplit('/', maxsplit=1)[-1]
        if cookie:
            headers['Cookie'] = cookie
        play_api = f'https://api.flextv.co.kr/api/channels/{user_id}/stream?option=all'
        json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers, abroad=True)
        if 'HTTP Error 400: Bad Request' in json_str:
            raise ConnectionError(
                "Failed to retrieve FlexTV live streaming data, please switch to a different proxy and try again."
            )
        return json.loads(json_str)

    json_data = await fetch_data(cookies)
    if 'sources' in json_data and len(json_data['sources']) > 0:
        play_url = json_data['sources'][0]['url']
        return play_url


@trace_error_decorator
async def get_flextv_stream_data(
        url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None,
        username: OptionalStr = None, password: OptionalStr = None
) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://www.flextv.co.kr/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies
    user_id = url.split('/live')[0].rsplit('/', maxsplit=1)[-1]
    result = {"anchor_name": '', "is_live": False}
    new_cookies = None
    try:
        url2 = f'https://www.flextv.co.kr/channels/{user_id}/live'
        html_str = await async_req(url2, proxy_addr=proxy_addr, headers=headers, abroad=True)
        json_str = re.search('<script id="__NEXT_DATA__" type=".*">(.*?)</script>', html_str).group(1)
        json_data = json.loads(json_str)
        channel_data = json_data['props']['pageProps']['channel']
        login_need = 'message' in channel_data and '로그인후 이용이 가능합니다.' in channel_data.get('message')
        if login_need:
            print("FlexTV live stream retrieval failed [not logged in]: 19+ live streams are only available for "
                  "logged-in adults.")
            print("Attempting to log in to the FlexTV live streaming platform, please ensure your account and "
                  "password are correctly filled in the configuration file.")
            if len(username) < 6 or len(password) < 8:
                raise RuntimeError("FlexTV登录失败！请在config.ini配置文件中填写正确的FlexTV平台的账号和密码")
            new_cookies = await login_flextv(username, password, proxy_addr=proxy_addr)
            if new_cookies:
                print("Logged into FlexTV platform successfully! Starting to fetch live streaming data...")
            else:
                raise RuntimeError("FlexTV login failed")
            cookies = new_cookies if new_cookies else cookies
            headers['Cookie'] = cookies
            html_str = await async_req(url2, proxy_addr=proxy_addr, headers=headers, abroad=True)
            json_str = re.search('<script id="__NEXT_DATA__" type=".*">(.*?)</script>', html_str).group(1)
            json_data = json.loads(json_str)
            channel_data = json_data['props']['pageProps']['channel']

        live_status = 'message' not in channel_data
        if live_status:
            anchor_id = channel_data['owner']['loginId']
            anchor_name = f"{channel_data['owner']['nickname']}-{anchor_id}"
            result["anchor_name"] = anchor_name
            play_url = await get_flextv_stream_url(url=url, proxy_addr=proxy_addr, cookies=cookies)
            if play_url:
                play_url_list = await get_play_url_list(m3u8=play_url, proxy=proxy_addr, header=headers, abroad=True)
                if play_url_list:
                    result['m3u8_url'] = play_url
                    result['play_url_list'] = play_url_list
                    result['is_live'] = True
        else:
            url2 = f'https://www.flextv.co.kr/channels/{user_id}'
            html_str = await async_req(url2, proxy_addr=proxy_addr, headers=headers, abroad=True)
            anchor_name = re.search('<meta name="twitter:title" content="(.*?)의', html_str).group(1)
            result["anchor_name"] = anchor_name
    except Exception as e:
        print("Failed to retrieve data from FlexTV live room", e)
    result['new_cookies'] = new_cookies
    return result


def get_looklive_secret_data(text) -> tuple:
    # 本算法参考项目：https://github.com/785415581/MusicBox/blob/b8f716d43d/doc/analysis/analyze_captured_data.md

    modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee' \
              '341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe487' \
              '5d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    nonce = b'0CoJUm6Qyw8W8jud'
    public_key = '010001'
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    import base64
    import binascii
    import secrets

    def create_secret_key(size: int) -> bytes:
        charset = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?'
        return ''.join(secrets.choice(charset) for _ in range(size)).encode('utf-8')

    def aes_encrypt(_text: str | bytes, _sec_key: str | bytes) -> bytes:
        if isinstance(_text, str):
            _text = _text.encode('utf-8')
        if isinstance(_sec_key, str):
            _sec_key = _sec_key.encode('utf-8')
        _sec_key = _sec_key[:16]  # 16 (AES-128), 24 (AES-192), or 32 (AES-256) bytes
        iv = bytes('0102030405060708', 'utf-8')
        encryptor = AES.new(_sec_key, AES.MODE_CBC, iv)
        padded_text = pad(_text, AES.block_size)
        ciphertext = encryptor.encrypt(padded_text)
        encoded_ciphertext = base64.b64encode(ciphertext)
        return encoded_ciphertext

    def rsa_encrypt(_text: str | bytes, pub_key: str, mod: str) -> str:
        if isinstance(_text, str):
            _text = _text.encode('utf-8')
        text_reversed = _text[::-1]
        text_int = int(binascii.hexlify(text_reversed), 16)
        encrypted_int = pow(text_int, int(pub_key, 16), int(mod, 16))
        return format(encrypted_int, 'x').zfill(256)

    sec_key = create_secret_key(16)
    enc_text = aes_encrypt(aes_encrypt(json.dumps(text), nonce), sec_key)
    enc_sec_key = rsa_encrypt(sec_key, public_key, modulus)
    return enc_text.decode(), enc_sec_key


async def get_looklive_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    """
    通过PC网页端的接口获取完整直播源，只有params和encSecKey这两个加密请求参数。
    params: 由两次AES加密完成
    ncSecKey: 由一次自写的加密函数完成，值可固定
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Accept': 'application/json, text/javascript',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://look.163.com/',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = re.search('live\\?id=(.*?)&', url).group(1)
    params, secretkey = get_looklive_secret_data({"liveRoomNo": room_id})
    request_data = {'params': params, 'encSecKey': secretkey}
    api = 'https://api.look.163.com/weapi/livestream/room/get/v3'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers, data=request_data)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['anchor']['nickName']
    live_status = json_data['data']['liveStatus']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        result["is_live"] = True
        if json_data['data']['roomInfo']['liveType'] == 1:
            print("Look live currently only supports audio live streaming, not video live streaming!")
        else:
            play_url_list = json_data['data']['roomInfo']['liveUrl']
            live_title = json_data['data']['roomInfo']['title']
            result |= {
                "title": live_title,
                "flv_url": play_url_list['httpPullUrl'],
                "m3u8_url": play_url_list['hlsPullUrl'],
                "record_url": play_url_list['hlsPullUrl'],
            }
    return result


@trace_error_decorator
async def login_popkontv(
        username: str, password: str, proxy_addr: OptionalStr = None, code: OptionalStr = 'P-00001'
) -> tuple:
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Authorization': 'Basic FpAhe6mh8Qtz116OENBmRddbYVirNKasktdXQiuHfm88zRaFydTsFy63tzkdZY0u',
        'Content-Type': 'application/json',
        'Origin': 'https://www.popkontv.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }

    data = {
        'partnerCode': code,
        'signId': username,
        'signPwd': password,
    }

    url = 'https://www.popkontv.com/api/proxy/member/v1/login'

    try:
        proxy_addr = utils.handle_proxy_addr(proxy_addr)
        async with httpx.AsyncClient(proxy=proxy_addr, timeout=20, verify=False) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()

            json_data = response.json()
            login_status_code = json_data.get("statusCd")

            if login_status_code == 'E4010':
                raise Exception("popkontv login failed, please reconfigure the correct login account or password!")
            elif login_status_code == 'S2000':
                token = json_data['data'].get("token")
                partner_code = json_data['data'].get("partnerCode")
                return token, partner_code
            else:
                raise Exception(f"popkontv login failed, {json_data.get('statusMsg', 'unknown error')}")
    except httpx.HTTPStatusError as e:
        print(f"HTTP status error occurred during login: {e.response.status_code}")
        raise
    except Exception as e:
        print(f"An exception occurred during popkontv login: {e}")
        raise


@trace_error_decorator
async def get_popkontv_stream_data(
        url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None,
        username: OptionalStr = None, code: OptionalStr = 'P-00001'
) -> tuple:
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Content-Type': 'application/json',
        'Origin': 'https://www.popkontv.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies
    if 'mcid' in url:
        anchor_id = re.search('mcid=(.*?)&', url).group(1)
    else:
        anchor_id = re.search('castId=(.*?)(?=&|$)', url).group(1)

    data = {
        'partnerCode': code,
        'searchKeyword': anchor_id,
        'signId': username,
    }

    api = 'https://www.popkontv.com/api/proxy/broadcast/v1/search/all'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers, json_data=data, abroad=True)
    json_data = json.loads(json_str)

    partner_code = ''
    anchor_name = 'Unknown'
    for item in json_data['data']['broadCastList']:
        if item['mcSignId'] == anchor_id:
            mc_name = item['nickName']
            anchor_name = f"{mc_name}-{anchor_id}"
            partner_code = item['mcPartnerCode']
            break

    if not partner_code:
        if 'mcPartnerCode' in url:
            regex_result = re.search('mcPartnerCode=(P-\\d+)', url)
        else:
            regex_result = re.search('partnerCode=(P-\\d+)', url)
        partner_code = regex_result.group(1) if regex_result else code
        notices_url = f'https://www.popkontv.com/channel/notices?mcid={anchor_id}&mcPartnerCode={partner_code}'
        notices_response = await async_req(notices_url, proxy_addr=proxy_addr, headers=headers, abroad=True)
        mc_name_match = re.search(r'"mcNickName":"([^"]+)"', notices_response)
        mc_name = mc_name_match.group(1) if mc_name_match else 'Unknown'
        anchor_name = f"{anchor_id}-{mc_name}"

    live_url = f"https://www.popkontv.com/live/view?castId={anchor_id}&partnerCode={partner_code}"
    html_str2 = await async_req(live_url, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_str2 = re.search('<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_str2).group(1)
    json_data2 = json.loads(json_str2)
    if 'mcData' in json_data2['props']['pageProps']:
        room_data = json_data2['props']['pageProps']['mcData']['data']
        is_private = room_data['mc_isPrivate']
        cast_start_date_code = room_data['mc_castStartDate']
        mc_sign_id = room_data['mc_signId']
        cast_type = room_data['castType']
        return anchor_name, [cast_start_date_code, partner_code, mc_sign_id, cast_type, is_private]
    else:
        return anchor_name, None


@trace_error_decorator
async def get_popkontv_stream_url(
        url: str,
        proxy_addr: OptionalStr = None,
        access_token: OptionalStr = None,
        username: OptionalStr = None,
        password: OptionalStr = None,
        partner_code: OptionalStr = 'P-00001'
) -> dict:
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'ClientKey': 'Client FpAhe6mh8Qtz116OENBmRddbYVirNKasktdXQiuHfm88zRaFydTsFy63tzkdZY0u',
        'Content-Type': 'application/json',
        'Origin': 'https://www.popkontv.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }

    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    anchor_name, room_info = await get_popkontv_stream_data(
        url, proxy_addr=proxy_addr, code=partner_code, username=username)
    result = {"anchor_name": anchor_name, "is_live": False}
    new_token = None
    if room_info:
        cast_start_date_code, cast_partner_code, mc_sign_id, cast_type, is_private = room_info
        result["is_live"] = True
        room_password = get_params(url, "pwd")
        if int(is_private) != 0 and not room_password:
            raise RuntimeError(f"Failed to retrieve live room data because {anchor_name}'s room is a private room. "
                               f"Please configure the room password and try again.")

        async def fetch_data(header: dict = None, code: str = None) -> str:
            data = {
                'androidStore': 0,
                'castCode': f'{mc_sign_id}-{cast_start_date_code}',
                'castPartnerCode': cast_partner_code,
                'castSignId': mc_sign_id,
                'castType': cast_type,
                'commandType': 0,
                'exePath': 5,
                'isSecret': is_private,
                'partnerCode': code,
                'password': room_password,
                'signId': username,
                'version': '4.6.2',
            }
            play_api = 'https://www.popkontv.com/api/proxy/broadcast/v1/castwatchonoffguest'
            return await async_req(play_api, proxy_addr=proxy_addr, json_data=data, headers=header, abroad=True)

        json_str = await fetch_data(headers, partner_code)

        if 'HTTP Error 400' in json_str or 'statusCd":"E5000' in json_str:
            print("Failed to retrieve popkontv live stream [token does not exist or has expired]: Please log in to "
                  "watch.")
            print("Attempting to log in to the popkontv live streaming platform, please ensure your account "
                  "and password are correctly filled in the configuration file.")
            if len(username) < 4 or len(password) < 10:
                raise RuntimeError("popkontv login failed! Please enter the correct account and password for the "
                                   "popkontv platform in the config.ini file.")
            print("Logging into popkontv platform...")
            new_access_token, new_partner_code = await login_popkontv(
                username=username, password=password, proxy_addr=proxy_addr, code=partner_code
            )
            if new_access_token and len(new_access_token) == 640:
                print("Logged into popkontv platform successfully! Starting to fetch live streaming data...")
                headers['Authorization'] = f'Bearer {new_access_token}'
                new_token = f'Bearer {new_access_token}'
                json_str = await fetch_data(headers, new_partner_code)
            else:
                raise RuntimeError("popkontv login failed, please check if the account and password are correct")
        json_data = json.loads(json_str)
        status_msg = json_data["statusMsg"]
        if json_data['statusCd'] == "L000A":
            print("Failed to retrieve live stream source,", status_msg)
            raise RuntimeError("You are an unverified member. After logging into the popkontv official website, "
                               "please verify your mobile phone at the bottom of the 'My Page' > 'Edit My "
                               "Information' to use the service.")
        elif json_data['statusCd'] == "L0001":
            cast_start_date_code = int(cast_start_date_code) - 1
            json_str = await fetch_data(headers, partner_code)
            json_data = json.loads(json_str)
            m3u8_url = json_data['data']['castHlsUrl']
            result |= {"m3u8_url": m3u8_url, "record_url": m3u8_url}
        elif json_data['statusCd'] == "L0000":
            m3u8_url = json_data['data']['castHlsUrl']
            result |= {"m3u8_url": m3u8_url, "record_url": m3u8_url}
        else:
            raise RuntimeError("Failed to retrieve live stream source,", status_msg)
    result['new_token'] = new_token
    return result


@trace_error_decorator
async def login_twitcasting(
        account_type: str, username: str, password: str, proxy_addr: OptionalStr = None,
        cookies: OptionalStr = None
) -> OptionalStr:
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://twitcasting.tv/indexcaslogin.php?redir=%2Findexloginwindow.php%3Fnext%3D%252F&keep=1',
        'Cookie': 'hl=zh; did=04fb08f1b15d248644f1dfa82816d323; _ga=GA1.1.1021187740.1709706998; keep=1; mfadid=yrQiEB26ruRg7mlMavABMBZWdOddzojW; _ga_X8R46Y30YM=GS1.1.1709706998.1.1.1709712274.0.0.0',
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    if account_type == "twitter":
        login_url = 'https://twitcasting.tv/indexpasswordlogin.php'
        login_api = 'https://twitcasting.tv/indexpasswordlogin.php?redir=/indexloginwindow.php?next=%2F&keep=1'
    else:
        login_url = 'https://twitcasting.tv/indexcaslogin.php?redir=%2F&keep=1'
        login_api = 'https://twitcasting.tv/indexcaslogin.php?redir=/indexloginwindow.php?next=%2F&keep=1'

    html_str = await async_req(login_url, proxy_addr=proxy_addr, headers=headers)
    cs_session_id = re.search('<input type="hidden" name="cs_session_id" value="(.*?)">', html_str).group(1)

    data = {
        'username': username,
        'password': password,
        'action': 'login',
        'cs_session_id': cs_session_id,
    }
    try:
        cookie_dict = await async_req(login_api, proxy_addr=proxy_addr, headers=headers,
                                      json_data=data, return_cookies=True, timeout=20)
        if 'tc_ss' in cookie_dict:
            cookie = utils.dict_to_cookie_str(cookie_dict)
            return cookie
    except Exception as e:
        print("TwitCasting login error,", e)


@trace_error_decorator
async def get_twitcasting_stream_url(
        url: str,
        proxy_addr: OptionalStr = None,
        cookies: OptionalStr = None,
        account_type: OptionalStr = None,
        username: OptionalStr = None,
        password: OptionalStr = None,
) -> dict:
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Referer': 'https://twitcasting.tv/?ch0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }

    anchor_id = url.split('/')[3]
    if cookies:
        headers['Cookie'] = cookies

    async def get_data(header) -> tuple:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=header)
        anchor = re.search("<title>(.*?) \\(@(.*?)\\)  的直播 - Twit", html_str)
        title = re.search('<meta name="twitter:title" content="(.*?)">\n\\s+<meta', html_str)
        status = re.search('data-is-onlive="(.*?)"\n\\s+data-view-mode', html_str)
        movie_id = re.search('data-movie-id="(.*?)" data-audience-id', html_str)
        return f'{anchor.group(1).strip()}-{anchor.group(2)}-{movie_id.group(1)}', status.group(1), title.group(1)

    result = {"anchor_name": '', "is_live": False}
    new_cookie = None
    try:
        to_login = get_params(url, "login")
        if to_login == 'true':
            print("Attempting to log in to TwitCasting...")
            new_cookie = await login_twitcasting(
                account_type=account_type, username=username, password=password, proxy_addr=proxy_addr, cookies=cookies)
            if not new_cookie:
                raise RuntimeError("TwitCasting login failed, please check if the account password in the "
                                   "configuration file is correct")
            print("TwitCasting login successful! Starting to fetch data...")
            headers['Cookie'] = new_cookie
        anchor_name, live_status, live_title = get_data(headers)
    except AttributeError:
        print("Failed to retrieve TwitCasting data, attempting to log in...")
        new_cookie = await login_twitcasting(
            account_type=account_type, username=username, password=password, proxy_addr=proxy_addr, cookies=cookies)
        if not new_cookie:
            raise RuntimeError("TwitCasting login failed, please check if the account and password in the "
                               "configuration file are correct")
        print("TwitCasting login successful! Starting to fetch data...")
        headers['Cookie'] = new_cookie
        anchor_name, live_status, live_title = await get_data(headers)

    result["anchor_name"] = anchor_name
    if live_status == 'true':
        play_url = f'https://twitcasting.tv/{anchor_id}/metastream.m3u8/?video=1&mode=source'
        result |= {'title': live_title, 'is_live': True, "m3u8_url": play_url, "record_url": play_url}
    result['new_cookies'] = new_cookie
    return result


@trace_error_decorator
async def get_baidu_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Referer': 'https://live.baidu.com/',
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }
    if cookies:
        headers['Cookie'] = cookies

    uid = random.choice([
        'h5-683e85bdf741bf2492586f7ca39bf465',
        'h5-c7c6dc14064a136be4215b452fab9eea',
        'h5-4581281f80bb8968bd9a9dfba6050d3a'
    ])
    room_id = re.search('room_id=(.*?)&', url).group(1)
    params = {
        'cmd': '371',
        'action': 'star',
        'service': 'bdbox',
        'osname': 'baiduboxapp',
        'data': '{"data":{"room_id":"' + room_id + '","device_id":"h5-683e85bdf741bf2492586f7ca39bf465",'
                                                   '"source_type":0,"osname":"baiduboxapp"},"replay_slice":0,'
                                                   '"nid":"","schemeParams":{"src_pre":"pc","src_suf":"other",'
                                                   '"bd_vid":"","share_uid":"","share_cuk":"","share_ecid":"",'
                                                   '"zb_tag":"","shareTaskInfo":"{\\"room_id\\":\\"9175031377\\"}",'
                                                   '"share_from":"","ext_params":"","nid":""}}',
        'ua': '360_740_ANDROID_0',
        'bd_vid': '',
        'uid': uid,
        '_': str(int(time.time() * 1000)),
    }
    app_api = f'https://mbd.baidu.com/searchbox?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=app_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    key = list(json_data['data'].keys())[0]
    data = json_data['data'][key]
    anchor_name = data['host']['name']
    result = {"anchor_name": anchor_name, "is_live": False}
    if data['status'] == "0":
        result["is_live"] = True
        live_title = data['video']['title']
        play_url_list = data['video']['url_clarity_list']
        url_list = []
        prefix = 'https://hls.liveshow.bdstatic.com/live/'
        if play_url_list:
            for i in play_url_list:
                url_list.append(
                    prefix + i['urls']['flv'].rsplit('.', maxsplit=1)[0].rsplit('/', maxsplit=1)[1] + '.m3u8')
        else:
            play_url_list = data['video']['url_list']
            for i in play_url_list:
                url_list.append(prefix + i['urls'][0]['hls'].rsplit('?', maxsplit=1)[0].rsplit('/', maxsplit=1)[1])

        if url_list:
            result |= {"is_live": True, "title": live_title, 'play_url_list': url_list}
    return result


@trace_error_decorator
async def get_weibo_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cookie': 'XSRF-TOKEN=qAP-pIY5V4tO6blNOhA4IIOD; SUB=_2AkMRNMCwf8NxqwFRmfwWymPrbI9-zgzEieKnaDFrJRMxHRl-yT9kqmkhtRB6OrTuX5z9N_7qk9C3xxEmNR-8WLcyo2PM; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WWemwcqkukCduUO11o9sBqA; WBPSESS=Wk6CxkYDejV3DDBcnx2LOXN9V1LjdSTNQPMbBDWe4lO2HbPmXG_coMffJ30T-Avn_ccQWtEYFcq9fab1p5RR6PEI6w661JcW7-56BszujMlaiAhLX-9vT4Zjboy1yf2l',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = ''
    if 'show/' in url:
        room_id = url.split('?')[0].split('show/')[1]
    else:
        uid = url.split('?')[0].rsplit('/u/', maxsplit=1)[1]
        web_api = f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page=1&feature=0'
        json_str = await async_req(web_api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        for i in json_data['data']['list']:
            if 'page_info' in i and i['page_info']['object_type'] == 'live':
                room_id = i['page_info']['object_id']
                break

    result = {"anchor_name": '', "is_live": False}
    if room_id:
        app_api = f'https://weibo.com/l/pc/anchor/live?live_id={room_id}'
        # app_api = f'https://weibo.com/l/!/2/wblive/room/show_pc_live.json?live_id={room_id}'
        json_str = await async_req(url=app_api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        anchor_name = json_data['data']['user_info']['name']
        result["anchor_name"] = anchor_name
        live_status = json_data['data']['item']['status']
        if live_status == 1:
            result["is_live"] = True
            live_title = json_data['data']['item']['desc']
            play_url_list = json_data['data']['item']['stream_info']['pull']
            m3u8_url = play_url_list['live_origin_hls_url']
            flv_url = play_url_list['live_origin_flv_url']
            result['title'] = live_title
            result['play_url_list'] = [
                {"m3u8_url": m3u8_url, "flv_url": flv_url},
                {"m3u8_url": m3u8_url.split('_')[0] + '.m3u8', "flv_url": flv_url.split('_')[0] + '.flv'}
            ]
    return result


@trace_error_decorator
async def get_kugou_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://fanxing2.kugou.com/',
    }
    if cookies:
        headers['Cookie'] = cookies

    if 'roomId' in url:
        room_id = re.search('roomId=(\\d+)', url).group(1)
    else:
        room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]

    app_api = f'https://service2.fanxing.kugou.com/roomcen/room/web/cdn/getEnterRoomInfo?roomId={room_id}'
    json_str = await async_req(url=app_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['normalRoomInfo']['nickName']
    result = {"anchor_name": anchor_name, "is_live": False}
    if not anchor_name:
        raise RuntimeError(
            "Music channel live rooms are not supported for recording, please switch to a different live room."
        )
    live_status = json_data['data']['liveType']
    if live_status != -1:
        params = {
            'std_rid': room_id,
            'std_plat': '7',
            'std_kid': '0',
            'streamType': '1-2-4-5-8',
            'ua': 'fx-flash',
            'targetLiveTypes': '1-5-6',
            'version': '1000',
            'supportEncryptMode': '1',
            'appid': '1010',
            '_': str(int(time.time() * 1000)),
        }
        api = f'https://fx1.service.kugou.com/video/pc/live/pull/mutiline/streamaddr?{urllib.parse.urlencode(params)}'
        json_str2 = await async_req(api, proxy_addr=proxy_addr, headers=headers)
        json_data2 = json.loads(json_str2)
        stream_data = json_data2['data']['lines']
        if stream_data:
            flv_url = stream_data[-1]['streamProfiles'][0]['httpsFlv'][0]
            result |= {"is_live": True, "flv_url": flv_url, "record_url": flv_url}
    return result


async def get_twitchtv_room_info(url: str, token: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> tuple:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept-Language': 'zh-CN',
        'Referer': 'https://www.twitch.tv/',
        'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'Client-Integrity': token,
        'Content-Type': 'text/plain;charset=UTF-8',
    }
    if cookies:
        headers['Cookie'] = cookies
    uid = url.split('?')[0].rsplit('/', maxsplit=1)[-1]

    data = [
        {
            "operationName": "ChannelShell",
            "variables": {
                "login": uid
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "580ab410bcd0c1ad194224957ae2241e5d252b2c5173d8e0cce9d32d5bb14efe"
                }
            }
        },
    ]

    json_str = await async_req('https://gql.twitch.tv/gql', proxy_addr=proxy_addr, headers=headers,
                               json_data=data, abroad=True)
    json_data = json.loads(json_str)
    user_data = json_data[0]['data']['userOrError']
    login_name = user_data["login"]
    nickname = f"{user_data['displayName']}-{login_name}"
    status = True if user_data['stream'] else False
    return nickname, status


@trace_error_decorator
async def get_twitchtv_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'en-US',
        'Referer': 'https://www.twitch.tv/',
        'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'device-id': generate_random_string(16).lower(),
    }

    if cookies:
        headers['Cookie'] = cookies
    uid = url.split('?')[0].rsplit('/', maxsplit=1)[-1]

    data = {
        "operationName": "PlaybackAccessToken_Template",
        "query": "query PlaybackAccessToken_Template($login: String!, $isLive: Boolean!, $vodID: ID!, "
                 "$isVod: Boolean!, $playerType: String!) {  streamPlaybackAccessToken(channelName: $login, "
                 "params: {platform: \"web\", playerBackend: \"mediaplayer\", playerType: $playerType}) @include(if: "
                 "$isLive) {    value    signature   authorization { isForbidden forbiddenReasonCode }   __typename  "
                 "}  videoPlaybackAccessToken(id: $vodID, params: {platform: \"web\", playerBackend: \"mediaplayer\", "
                 "playerType: $playerType}) @include(if: $isVod) {    value    signature   __typename  }}",
        "variables": {
            "isLive": True,
            "login": uid,
            "isVod": False,
            "vodID": "",
            "playerType": "site"
        }
    }

    json_str = await async_req('https://gql.twitch.tv/gql', proxy_addr=proxy_addr, headers=headers,
                               json_data=data, abroad=True)
    json_data = json.loads(json_str)
    token = json_data['data']['streamPlaybackAccessToken']['value']
    sign = json_data['data']['streamPlaybackAccessToken']['signature']

    anchor_name, live_status = await get_twitchtv_room_info(url=url, token=token, proxy_addr=proxy_addr, cookies=cookies)
    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        play_session_id = random.choice(["bdd22331a986c7f1073628f2fc5b19da", "064bc3ff1722b6f53b0b5b8c01e46ca5"])
        params = {
            "acmb": "e30=",
            "allow_source": "true",
            "browser_family": "firefox",
            "browser_version": "124.0",
            "cdm": "wv",
            "fast_bread": "true",
            "os_name": "Windows",
            "os_version": "NT%2010.0",
            "p": "3553732",
            "platform": "web",
            "play_session_id": play_session_id,
            "player_backend": "mediaplayer",
            "player_version": "1.28.0-rc.1",
            "playlist_include_framerate": "true",
            "reassignments_supported": "true",
            "sig": sign,
            "token": token,
            "transcode_mode": "cbr_v1"
        }
        access_key = urllib.parse.urlencode(params)
        m3u8_url = f'https://usher.ttvnw.net/api/channel/hls/{uid}.m3u8?{access_key}'
        play_url_list = await get_play_url_list(m3u8=m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        result |= {'m3u8_url': m3u8_url, 'play_url_list': play_url_list}
    return result


@trace_error_decorator
async def get_liveme_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.liveme.com',
        'referer': 'https://www.liveme.com',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split("/index.html")[0].rsplit('/', maxsplit=1)[-1]
    sign_data = execjs.compile(open(f'{JS_SCRIPT_PATH}/liveme.js').read()).call('sign', room_id,
                                                                                f'{JS_SCRIPT_PATH}/crypto-js.min.js')
    lm_s_sign = sign_data.pop("lm_s_sign")
    tongdun_black_box = sign_data.pop("tongdun_black_box")
    platform = sign_data.pop("os")
    headers['lm-s-sign'] = lm_s_sign

    params = {
        'alias': 'liveme',
        'tongdun_black_box': tongdun_black_box,
        'os': platform,
    }

    api = f'https://live.liveme.com/live/queryinfosimple?{urllib.parse.urlencode(params)}'
    json_str = await async_req(api, data=sign_data, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    stream_data = json_data['data']['video_info']
    anchor_name = stream_data['uname']
    live_status = stream_data['status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == "0":
        m3u8_url = stream_data['hlsvideosource']
        flv_url = stream_data['videosource']
        result |= {
            'is_live': True,
            'm3u8_url': m3u8_url,
            'flv_url': flv_url,
            'record_url': m3u8_url or flv_url
        }
    return result


async def get_huajiao_sn(url: str, cookies: OptionalStr = None, proxy_addr: OptionalStr = None) -> tuple | None:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://www.huajiao.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies

    live_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    api = f'https://www.huajiao.com/l/{live_id}'
    try:
        html_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
        json_str = re.search('var feed = (.*?});', html_str).group(1)
        json_data = json.loads(json_str)
        sn = json_data['feed']['sn']
        uid = json_data['author']['uid']
        nickname = json_data['author']['nickname']
        live_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
        return nickname, sn, uid, live_id
    except Exception:
        utils.replace_url(f'{script_path}/config/URL_config.ini', old=url, new='#' + url)
        raise RuntimeError("Failed to retrieve live room data, the Huajiao live room address is not fixed, please use "
                           "the anchor's homepage address for recording.")


async def get_huajiao_user_info(url: str, cookies: OptionalStr = None, proxy_addr: OptionalStr = None) -> OptionalDict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://www.huajiao.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies

    if 'user' in url:
        uid = url.split('?')[0].split('user/')[1]
        params = {
            'uid': uid,
            'fmt': 'json',
            '_': str(int(time.time() * 1000)),
        }

        api = f'https://webh.huajiao.com/User/getUserFeeds?{urllib.parse.urlencode(params)}'
        json_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)

        html_str = await async_req(url=f'https://www.huajiao.com/user/{uid}', proxy_addr=proxy_addr, headers=headers)
        anchor_name = re.search('<title>(.*?)的主页.*</title>', html_str).group(1)
        if json_data['data'] and 'sn' in json_data['data']['feeds'][0]['feed']:
            feed = json_data['data']['feeds'][0]['feed']
            return {
                "anchor_name": anchor_name,
                "title": feed['title'],
                "is_live": True,
                "sn": feed['sn'],
                "liveid": feed['relateid'],
                "uid": uid
            }
        else:
            return {"anchor_name": anchor_name, "is_live": False}


async def get_huajiao_stream_url_app(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> OptionalDict:
    headers = {
        'User-Agent': 'living/9.4.0 (com.huajiao.seeding; build:2410231746; iOS 17.0.0) Alamofire/9.4.0',
        'accept-language': 'zh-Hans-US;q=1.0',
        'sdk_version': '1',
    }
    if cookies:
        headers['Cookie'] = cookies
    room_id = url.rsplit('/', maxsplit=1)[1]
    api = f'https://live.huajiao.com/feed/getFeedInfo?relateid={room_id}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    if json_data['errmsg'] or not json_data['data'].get('creatime'):
        print("Failed to retrieve live room data, the Huajiao live room address is not fixed, please manually change "
              "the address for recording.")
        return
    data = json_data['data']
    return {
        "anchor_name": data['author']['nickname'],
        "title": data['feed']['title'],
        "is_live": True,
        "sn": data['feed']['sn'],
        "liveid": data['feed']['relateid'],
        "uid": data['author']['uid']
    }


@trace_error_decorator
async def get_huajiao_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://www.huajiao.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    result = {"anchor_name": "", "is_live": False}

    if 'user/' in url:
        if not cookies:
            return result
        room_data = await get_huajiao_user_info(url, cookies, proxy_addr)
    else:
        url = await async_req(url, proxy_addr=proxy_addr, headers=headers, redirect_url=True)
        if url.rstrip('/') == 'https://www.huajiao.com':
            print(
                "Failed to retrieve live room data, the Huajiao live room address is not fixed, please manually change "
                "the address for recording.")
            return result
        room_data = await get_huajiao_stream_url_app(url, proxy_addr)

    if room_data:
        result["anchor_name"] = room_data.pop("anchor_name")
        live_status = room_data.pop("is_live")

        if live_status:
            result["title"] = room_data.pop("title")
            params = {
                "time": int(time.time() * 1000),
                "version": "1.0.0",
                **room_data,
                "encode": "h265"
            }

            api = f'https://live.huajiao.com/live/substream?{urllib.parse.urlencode(params)}'
            json_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
            json_data = json.loads(json_str)
            result |= {
                'is_live': True,
                'flv_url': json_data['data']['h264_url'],
                'record_url': json_data['data']['h264_url'],
            }
    return result


@trace_error_decorator
async def get_liuxing_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Referer': 'https://wap.7u66.com/198189?promoters=0',
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',

    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    params = {
        "promoters": "0",
        "roomidx": room_id,
        "currentUrl": f"https://www.7u66.com/{room_id}?promoters=0"
    }
    api = f'https://wap.7u66.com/api/ui/room/v1.0.0/live.ashx?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    room_info = json_data['data']['roomInfo']
    anchor_name = room_info['nickname']
    live_status = room_info["live_stat"]
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        idx = room_info['idx']
        live_id = room_info['liveId1']
        flv_url = f'https://txpull1.5see.com/live/{idx}/{live_id}.flv'
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_showroom_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    if '/room/profile' in url:
        room_id = url.split('room_id=')[-1]
    else:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers, abroad=True)
        room_id = re.search('href="/room/profile\\?room_id=(.*?)"', html_str).group(1)
    info_api = f'https://www.showroom-live.com/api/live/live_info?room_id={room_id}'
    json_str = await async_req(info_api, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    anchor_name = json_data['room_name']
    result = {"anchor_name": anchor_name, "is_live": False}
    live_status = json_data['live_status']
    if live_status == 2:
        result["is_live"] = True
        web_api = f'https://www.showroom-live.com/api/live/streaming_url?room_id={room_id}&abr_available=1'
        json_str = await async_req(web_api, proxy_addr=proxy_addr, headers=headers, abroad=True)
        if json_str:
            json_data = json.loads(json_str)
            streaming_url_list = json_data['streaming_url_list']

            for i in streaming_url_list:
                if i['type'] == 'hls_all':
                    m3u8_url = i['url']
                    result['m3u8_url'] = m3u8_url
                    if m3u8_url:
                        m3u8_url_list = await get_play_url_list(m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
                        if m3u8_url_list:
                            result['play_url_list'] = [f"{m3u8_url.rsplit('/', maxsplit=1)[0]}/{i}" for i in
                                                       m3u8_url_list]
                        else:
                            result['play_url_list'] = [m3u8_url]
                        result['play_url_list'] = [i.replace('https://', 'http://') for i in result['play_url_list']]
                        break
    return result


@trace_error_decorator
async def get_acfun_sign_params(proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> tuple:
    did = f'web_{utils.generate_random_string(16)}'
    headers = {
        'referer': 'https://live.acfun.cn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'cookie': f'_did={did};',
    }
    if cookies:
        headers['Cookie'] = cookies
    data = {
        'sid': 'acfun.api.visitor',
    }
    api = 'https://id.app.acfun.cn/rest/app/visitor/login'
    json_str = await async_req(api, data=data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    user_id = json_data["userId"]
    visitor_st = json_data["acfun.api.visitor_st"]
    return user_id, did, visitor_st


@trace_error_decorator
async def get_acfun_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'referer': 'https://live.acfun.cn/live/17912421',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    author_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    user_info_api = f'https://live.acfun.cn/rest/pc-direct/user/userInfo?userId={author_id}'
    json_str = await async_req(user_info_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['profile']['name']
    status = 'liveId' in json_data['profile']
    result = {"anchor_name": anchor_name, "is_live": False}
    if status:
        result["is_live"] = True
        user_id, did, visitor_st = await get_acfun_sign_params(proxy_addr=proxy_addr, cookies=cookies)
        params = {
            'subBiz': 'mainApp',
            'kpn': 'ACFUN_APP',
            'kpf': 'PC_WEB',
            'userId': user_id,
            'did': did,
            'acfun.api.visitor_st': visitor_st,
        }

        data = {
            'authorId': author_id,
            'pullStreamType': 'FLV',
        }
        play_api = f'https://api.kuaishouzt.com/rest/zt/live/web/startPlay?{urllib.parse.urlencode(params)}'
        json_str = await async_req(play_api, data=data, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        live_title = json_data['data']['caption']
        videoPlayRes = json_data['data']['videoPlayRes']
        play_url_list = json.loads(videoPlayRes)['liveAdaptiveManifest'][0]['adaptationSet']['representation']
        play_url_list = sorted(play_url_list, key=itemgetter('bitrate'), reverse=True)
        result |= {'play_url_list': play_url_list, 'title': live_title}
    return result


@trace_error_decorator
async def get_changliao_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://wap.tlclw.com/phone/15777?promoters=0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    params = {
        'roomidx': room_id,
        'currentUrl': f'https://wap.tlclw.com/{room_id}',
    }
    play_api = f'https://wap.tlclw.com/api/ui/room/v1.0.0/live.ashx?{urllib.parse.urlencode(params)}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['roomInfo']['nickname']
    live_status = json_data['data']['roomInfo']['live_stat']

    async def get_live_domain(page_url):
        html_str = await async_req(page_url, proxy_addr=proxy_addr, headers=headers)
        config_json_str = re.findall("var config = (.*?)config.webskins",
                                     html_str, re.DOTALL)[0].rsplit(";", maxsplit=1)[0].strip()
        config_json_data = json.loads(config_json_str)
        stream_flv_domain = config_json_data['domainpullstream_flv']
        stream_hls_domain = config_json_data['domainpullstream_hls']
        return stream_flv_domain, stream_hls_domain

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        flv_domain, hls_domain = await get_live_domain(url)
        live_id = json_data['data']['roomInfo']['liveID']
        flv_url = f'{flv_domain}/{live_id}.flv'
        m3u8_url = f'{hls_domain}/{live_id}.m3u8'
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_yingke_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Referer': 'https://www.inke.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    uid = query_params['uid'][0]
    live_id = query_params['id'][0]
    params = {
        'uid': uid,
        'id': live_id,
        '_t': str(int(time.time())),
    }

    api = f'https://webapi.busi.inke.cn/web/live_share_pc?{urllib.parse.urlencode(params)}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['media_info']['nick']
    live_status = json_data['data']['status']

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        m3u8_url = json_data['data']['live_addr'][0]['hls_stream_addr']
        flv_url = json_data['data']['live_addr'][0]['stream_addr']
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': m3u8_url}
    return result


@trace_error_decorator
async def get_yinbo_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://live.ybw1666.com/800005143?promoters=0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    params = {
        'roomidx': room_id,
        'currentUrl': f'https://wap.ybw1666.com/{room_id}',
    }
    play_api = f'https://wap.ybw1666.com/api/ui/room/v1.0.0/live.ashx?{urllib.parse.urlencode(params)}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    room_data = json_data['data']['roomInfo']
    anchor_name = room_data['nickname']
    live_status = room_data['live_stat']

    async def get_live_domain(page_url):
        html_str = await async_req(page_url, proxy_addr=proxy_addr, headers=headers)
        config_json_str = re.findall("var config = (.*?)config.webskins",
                                     html_str, re.DOTALL)[0].rsplit(";", maxsplit=1)[0].strip()
        config_json_data = json.loads(config_json_str)
        stream_flv_domain = config_json_data['domainpullstream_flv']
        stream_hls_domain = config_json_data['domainpullstream_hls']
        return stream_flv_domain, stream_hls_domain

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        flv_domain, hls_domain = await get_live_domain(url)
        live_id = room_data['liveID']
        flv_url = f'{flv_domain}/{live_id}.flv'
        m3u8_url = f'{hls_domain}/{live_id}.m3u8'
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_zhihu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    if 'people/' in url:
        user_id = url.split('people/')[1]
        api = f'https://api.zhihu.com/people/{user_id}/profile?profile_new_version='
        json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        live_page_url = json_data['drama']['living_theater']['theater_url']
    else:
        live_page_url = url

    web_id = live_page_url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    html_str = await async_req(live_page_url, proxy_addr=proxy_addr, headers=headers)
    json_str2 = re.findall('<script id="js-initialData" type="text/json">(.*?)</script>', html_str)[0]
    json_data2 = json.loads(json_str2)
    live_data = json_data2['initialState']['theater']['theaters'][web_id]
    anchor_name = live_data['actor']['name']
    live_status = live_data['drama']['status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        live_title = live_data['theme']
        play_url = live_data['drama']['playInfo']
        result |= {
            'is_live': True,
            'title': live_title,
            'm3u8_url': play_url['hlsUrl'],
            'flv_url': play_url['playUrl'],
            'record_url': play_url['hlsUrl']
        }
    return result


@trace_error_decorator
async def get_chzzk_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'origin': 'https://chzzk.naver.com',
        'referer': 'https://chzzk.naver.com/live/458f6ec20b034f49e0fc6d03921646d2',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    play_api = f'https://api.chzzk.naver.com/service/v3/channels/{room_id}/live-detail'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    live_data = json_data['content']
    anchor_name = live_data['channel']['channelName']
    live_status = live_data['status']

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 'OPEN':
        play_data = json.loads(live_data['livePlaybackJson'])
        m3u8_url = play_data['media'][0]['path']
        m3u8_url_list = await get_play_url_list(m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        prefix = m3u8_url.split('?')[0].rsplit('/', maxsplit=1)[0]
        m3u8_url_list = [prefix + '/' + i for i in m3u8_url_list]
        result |= {"is_live": True, "m3u8_url": m3u8_url, "play_url_list": m3u8_url_list}
    return result


@trace_error_decorator
async def get_haixiu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.haixiutv.com',
        'referer': 'https://www.haixiutv.com/',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split("?")[0].rsplit('/', maxsplit=1)[-1]
    if 'haixiutv' in url:
        access_token = "pLXSC%252FXJ0asc1I21tVL5FYZhNJn2Zg6d7m94umCnpgL%252BuVm31GQvyw%253D%253D"
    else:
        access_token = "s7FUbTJ%252BjILrR7kicJUg8qr025ZVjd07DAnUQd8c7g%252Fo4OH9pdSX6w%253D%253D"

    params = {
        "accessToken": access_token,
        "tku": "3000006",
        "c": "10138100100000",
        "_st1": int(time.time() * 1000)
    }
    ajax_data = execjs.compile(open(f'{JS_SCRIPT_PATH}/haixiu.js').read()).call('sign', params,
                                                                                f'{JS_SCRIPT_PATH}/crypto-js.min.js')

    params["accessToken"] = urllib.parse.unquote(urllib.parse.unquote(access_token))
    params['_ajaxData1'] = ajax_data
    params['_'] = int(time.time() * 1000)

    if 'haixiutv' in url:
        api = f'https://service.haixiutv.com/v2/room/{room_id}/media/advanceInfoRoom?{urllib.parse.urlencode(params)}'
    else:
        headers['origin'] = 'https://www.lehaitv.com'
        headers['referer'] = 'https://www.lehaitv.com'
        api = f'https://service.lehaitv.com/v2/room/{room_id}/media/advanceInfoRoom?{urllib.parse.urlencode(params)}'

    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)

    stream_data = json_data['data']
    anchor_name = stream_data['nickname']
    live_status = stream_data['live_status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        flv_url = stream_data['media_url_web']
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_vvxqiu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Access-Control-Request-Method': 'GET',
        'Origin': 'https://h5webcdn-pro.vvxqiu.com',
        'Referer': 'https://h5webcdn-pro.vvxqiu.com/',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = get_params(url, "roomId")
    api_1 = f'https://h5p.vvxqiu.com/activity-center/fanclub/activity/captain/banner?roomId={room_id}&product=vvstar'
    json_str = await async_req(api_1, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['anchorName']
    if not anchor_name:
        params = {
            'sessionId': '',
            'userId': '',
            'product': 'vvstar',
            'tickToken': '',
            'roomId': room_id,
        }
        json_str = await async_req(
            f'https://h5p.vvxqiu.com/activity-center/halloween2023/banner?{urllib.parse.urlencode(params)}',
            proxy_addr=proxy_addr, headers=headers
        )
        json_data = json.loads(json_str)
        anchor_name = json_data['data']['memberVO']['memberName']

    result = {"anchor_name": anchor_name, "is_live": False}
    m3u8_url = f'https://liveplay-pro.wasaixiu.com/live/1400442770_{room_id}_{room_id[2:]}_single.m3u8'
    resp = await async_req(m3u8_url, proxy_addr=proxy_addr, headers=headers)
    if 'Not Found' not in resp:
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'record_url': m3u8_url}
    return result


@trace_error_decorator
async def get_17live_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://17.live',
        'referer': 'https://17.live/',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    api_1 = f'https://wap-api.17app.co/api/v1/user/room/{room_id}'
    json_str = await async_req(api_1, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data["displayName"]
    result = {"anchor_name": anchor_name, "is_live": False}
    json_data = {
        'liveStreamID': room_id,
    }
    api_1 = f'https://wap-api.17app.co/api/v1/lives/{room_id}/viewers/alive'
    json_str = await async_req(api_1, json_data=json_data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_status = json_data.get("status")
    if live_status and live_status == 2:
        flv_url = json_data['pullURLsInfo']['rtmpURLs'][0]['urlHighQuality']
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_langlive_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.lang.live',
        'referer': 'https://www.lang.live/',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    api_1 = f'https://api.lang.live/langweb/v1/room/liveinfo?room_id={room_id}'
    json_str = await async_req(api_1, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    live_info = json_data['data']['live_info']
    anchor_name = live_info['nickname']
    live_status = live_info['live_status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        flv_url = json_data['data']['live_info']['liveurl']
        m3u8_url = json_data['data']['live_info']['liveurl_hls']
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': m3u8_url}
    return result


@trace_error_decorator
async def get_pplive_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://m.pp.weimipopo.com',
        'Referer': 'https://m.pp.weimipopo.com/',
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = get_params(url, 'anchorUid')
    json_data = {
        'inviteUuid': '',
        'anchorUuid': room_id,
    }

    if 'catshow' in url:
        api = 'https://api.catshow168.com/live/preview'
        headers['Origin'] = 'https://h.catshow168.com'
        headers['Referer'] = 'https://h.catshow168.com'
    else:
        api = 'https://api.pp.weimipopo.com/live/preview'
    json_str = await async_req(api, json_data=json_data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_info = json_data['data']
    anchor_name = live_info['name']
    live_status = live_info['living']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status:
        m3u8_url = live_info['pullUrl']
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'record_url': m3u8_url}
    return result


@trace_error_decorator
async def get_6room_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://ios.6.cn/?ver=8.0.3&build=4',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    html_str = await async_req(f'https://v.6.cn/{room_id}', proxy_addr=proxy_addr, headers=headers)
    room_id = re.search('rid: \'(.*?)\',\n\\s+roomid', html_str).group(1)
    data = {
        'av': '3.1',
        'encpass': '',
        'logiuid': '',
        'project': 'v6iphone',
        'rate': '1',
        'rid': '',
        'ruid': room_id,
    }
    api = 'https://v.6.cn/coop/mobile/index.php?padapi=coop-mobile-inroom.php'
    json_str = await async_req(api, data=data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    flv_title = json_data['content']['liveinfo']['flvtitle']
    anchor_name = json_data['content']['roominfo']['alias']
    result = {"anchor_name": anchor_name, "is_live": False}
    if flv_title:
        flv_url = f'https://wlive.6rooms.com/httpflv/{flv_title}.flv'
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_shopee_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://live.shopee.sg/share?from=live&session=802458&share_user_id=',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    result = {"anchor_name": "", "is_live": False}
    is_living = False

    if 'live.shopee' not in url and 'uid' not in url:
        url = await async_req(url, proxy_addr=proxy_addr, headers=headers, redirect_url=True, abroad=True)

    if 'live.shopee' in url:
        host_suffix = url.split('/')[2].rsplit('.', maxsplit=1)[1]
        is_living = get_params(url, 'uid') is None
    else:
        host_suffix = url.split('/')[2].split('.', maxsplit=1)[0]

    uid = get_params(url, 'uid')
    api_host = f'https://live.shopee.{host_suffix}'
    session_id = get_params(url, 'session')
    if uid:
        json_str = await async_req(f'{api_host}/api/v1/shop_page/live/ongoing?uid={uid}',
                           proxy_addr=proxy_addr, headers=headers, abroad=True)
        json_data = json.loads(json_str)
        if json_data['data']['ongoing_live']:
            session_id = json_data['data']['ongoing_live']['session_id']
            is_living = True
        else:
            json_str = await async_req(f'{api_host}/api/v1/shop_page/live/replay_list?offset=0&limit=1&uid={uid}',
                               proxy_addr=proxy_addr, headers=headers, abroad=True)
            json_data = json.loads(json_str)
            if json_data['data']['replay']:
                result['anchor_name'] = json_data['data']['replay'][0]['nick_name']
                return result

    json_str = await async_req(f'{api_host}/api/v1/session/{session_id}', proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    if not json_data.get('data'):
        print("Fetch shopee live data failed, please update the address of the live broadcast room and try again.")
        return result
    uid = json_data['data']['session']['uid']
    anchor_name = json_data['data']['session']['nickname']
    live_status = json_data['data']['session']['status']
    result["anchor_name"] = anchor_name
    result['uid'] = f'uid={uid}&session={session_id}'
    if live_status == 1 and is_living:
        flv_url = json_data['data']['session']['play_url']
        title = json_data['data']['session']['title']
        result |= {'is_live': True, 'title': title, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_youtube_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_str = re.search('var ytInitialPlayerResponse = (.*?);var meta = document\\.createElement', html_str).group(1)
    json_data = json.loads(json_str)
    result = {"anchor_name": "", "is_live": False}
    if 'videoDetails' not in json_data:
        print("Error: Please log in to YouTube on your device's webpage and configure cookies in the config.ini")
        return result
    result['anchor_name'] = json_data['videoDetails']['author']
    live_status = json_data['videoDetails'].get('isLive')
    if live_status:
        live_title = json_data['videoDetails']['title']
        m3u8_url = json_data['streamingData']["hlsManifestUrl"]
        play_url_list = await get_play_url_list(m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        result |= {"is_live": True, "title": live_title, "m3u8_url": m3u8_url, "play_url_list": play_url_list}
    return result


@trace_error_decorator
async def get_taobao_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Referer': 'https://huodong.m.taobao.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Cookie': '',
    }

    if cookies:
        headers['Cookie'] = cookies

    if '_m_h5_tk' not in headers['Cookie']:
        print('Error: Cookies is empty! please input correct cookies')

    live_id = get_params(url, 'id')
    if not live_id:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
        redirect_url = re.findall("var url = '(.*?)';", html_str)[0]
        live_id = get_params(redirect_url, 'id')

    params = {
        'jsv': '2.7.0',
        'appKey': '12574478',
        't': '1733104933120',
        'sign': '',
        'AntiFlood': 'true',
        'AntiCreep': 'true',
        'api': 'mtop.mediaplatform.live.livedetail',
        'v': '4.0',
        'preventFallback': 'true',
        'type': 'jsonp',
        'dataType': 'jsonp',
        'callback': 'mtopjsonp1',
        'data': '{"liveId":"' + live_id + '","creatorId":null}',
    }

    for i in range(2):
        app_key = '12574478'
        _m_h5_tk = re.findall('_m_h5_tk=(.*?);', headers['Cookie'])[0]
        t13 = int(time.time() * 1000)
        pre_sign_str = f'{_m_h5_tk.split("_")[0]}&{t13}&{app_key}&' + params['data']
        sign = execjs.compile(open(f'{JS_SCRIPT_PATH}/taobao-sign.js').read()).call('sign', pre_sign_str)
        params |= {'sign': sign, 't': t13}
        api = f'https://h5api.m.taobao.com/h5/mtop.mediaplatform.live.livedetail/4.0/?{urllib.parse.urlencode(params)}'
        jsonp_str, new_cookie = await async_req(url=api, proxy_addr=proxy_addr, headers=headers, timeout=20,
                                                return_cookies=True, include_cookies=True)
        json_data = utils.jsonp_to_json(jsonp_str)

        ret_msg = json_data['ret']
        if ret_msg == ['SUCCESS::调用成功']:
            anchor_name = json_data['data']['broadCaster']['accountName']
            result = {"anchor_name": anchor_name, "is_live": False}
            live_status = json_data['data']['streamStatus']
            if live_status == '1':
                live_title = json_data['data']['title']
                play_url_list = json_data['data']['liveUrlList']

                def get_sort_key(item):
                    definition_priority = {
                        "lld": 0, "ld": 1, "md": 2, "hd": 3, "ud": 4
                    }
                    def_value = item.get('definition') or item.get('newDefinition')
                    priority = definition_priority.get(def_value, -1)
                    return priority

                play_url_list = sorted(play_url_list, key=get_sort_key, reverse=True)
                result |= {"is_live": True, "title": live_title, "play_url_list": play_url_list, 'live_id': live_id}

            return result
        else:
            print(f'Error: Taobao live data fetch failed, {ret_msg[0]}')

        if '_m_h5_tk' in new_cookie and '_m_h5_tk_enc' in new_cookie:
            headers['Cookie'] = re.sub('_m_h5_tk=(.*?);', new_cookie['_m_h5_tk'], headers['Cookie'])
            headers['Cookie'] = re.sub('_m_h5_tk_enc=(.*?);', new_cookie['_m_h5_tk_enc'], headers['Cookie'])
        else:
            print('Error: Try to update cookie failed, please update the cookies in the configuration file')


@trace_error_decorator
async def get_jd_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'origin': 'https://lives.jd.com',
        'referer': 'https://lives.jd.com/',
        'x-referer-page': 'https://lives.jd.com/',
    }

    if cookies:
        headers['Cookie'] = cookies

    redirect_url = await async_req(url, proxy_addr=proxy_addr, headers=headers, redirect_url=True)
    author_id = get_params(redirect_url, 'authorId')
    result = {"anchor_name": '', "is_live": False}
    if not author_id:
        live_id = re.search('#/(.*?)\\?origin', redirect_url)
        if not live_id:
            return result
        live_id = live_id.group(1)
        result['anchor_name'] = f'jd_{live_id}'
    else:
        data = {
            'functionId': 'talent_head_findTalentMsg',
            'appid': 'dr_detail',
            'body': '{"authorId":"' + author_id + '","monitorSource":"1","userId":""}',
        }
        info_api = 'https://api.m.jd.com/talent_head_findTalentMsg'
        json_str = await async_req(info_api, data=data, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        anchor_name = json_data['result']['talentName']
        result['anchor_name'] = anchor_name
        if 'livingRoomJump' not in json_data['result']:
            return result
        live_id = json_data['result']['livingRoomJump']['params']['id']
    params = {
        "body": '{"liveId": "' + live_id + '"}',
        "functionId": "getImmediatePlayToM",
        "appid": "h5-live"
    }

    api = f'https://api.m.jd.com/client.action?{urllib.parse.urlencode(params)}'
    # backup_api: https://api.m.jd.com/api
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_status = json_data['data']['status']
    if live_status == 1:
        if author_id:
            data = {
                'functionId': 'jdTalentContentList',
                'appid': 'dr_detail',
                'body': '{"authorId":"' + author_id + '","type":1,"userId":"","page":1,"offset":"-1",'
                                                      '"monitorSource":"1","pageSize":1}',
            }
            json_str2 = await async_req('https://api.m.jd.com/jdTalentContentList', data=data,
                                proxy_addr=proxy_addr, headers=headers)
            json_data2 = json.loads(json_str2)
            result['title'] = json_data2['result']['content'][0]['title']

        flv_url = json_data['data']['videoUrl']
        m3u8_url = json_data['data']['h5VideoUrl']
        result |= {"is_live": True, "m3u8_url": m3u8_url, "flv_url": flv_url, "record_url": m3u8_url}
    return result


@trace_error_decorator
async def get_faceit_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Referer': 'https://www.faceit.com/zh/players/qpjzz/stream',
        'faceit-referer': 'web-next',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies
    nickname = re.findall('/players/(.*?)/stream', url)[0]
    api = f'https://www.faceit.com/api/users/v1/nicknames/{nickname}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    user_id = json_data['payload']['id']
    api2 = f'https://www.faceit.com/api/stream/v1/streamings?userId={user_id}'
    json_str2 = await async_req(api2, proxy_addr=proxy_addr, headers=headers)
    json_data2 = json.loads(json_str2)
    platform_info = json_data2['payload'][0]
    anchor_name = platform_info.get('userNickname')
    anchor_id = platform_info.get('platformId')
    platform = platform_info.get('platform')
    if platform == 'twitch':
        result = await get_twitchtv_stream_data(f'https://www.twitch.tv/{anchor_id}')
        result['anchor_name'] = anchor_name
    else:
        result = {'anchor_name': anchor_name, 'is_live': False}
    return result


@trace_error_decorator
async def get_migu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
            'origin': 'https://www.miguvideo.com',
            'referer': 'https://www.miguvideo.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'appCode': 'miguvideo_default_www',
            'appId': 'miguvideo',
            'channel': 'H5',
        }

    if cookies:
        headers['Cookie'] = cookies

    web_id = url.split('?')[0].rsplit('/')[-1]
    api = f'https://vms-sc.miguvideo.com/vms-match/v6/staticcache/basic/basic-data/{web_id}/miguvideo'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    anchor_name = json_data['body']['title']
    live_title = json_data['body'].get('title') + '-' + json_data['body'].get('detailPageTitle', '')
    room_id = json_data['body'].get('pId')

    result = {"anchor_name": anchor_name, "is_live": False}
    if not room_id:
        return result

    params = {
        'contId': room_id,
        'rateType': '3',
        'clientId': str(uuid.uuid4()),
        'timestamp': int(time.time() * 1000),
        'flvEnable': 'true',
        'xh265': 'false',
        'chip': 'mgwww',
        'channelId': '',
    }

    api = f'https://webapi.miguvideo.com/gateway/playurl/v3/play/playurl?{urllib.parse.urlencode(params)}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_status = json_data['body']['content']['currentLive']
    if live_status != '1':
        return result
    else:
        result['title'] = live_title
        source_url = json_data['body']['urlInfo']['url']

        async def _get_dd_calcu(url):
            try:
                result = subprocess.run(
                    ["node", f"{JS_SCRIPT_PATH}/migu.js", url],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except execjs.ProgramError:
                raise execjs.ProgramError('Failed to execute JS code. Please check if the Node.js environment')

        ddCalcu = await _get_dd_calcu(source_url)
        real_source_url = f'{source_url}&ddCalcu={ddCalcu}&sv=10010'
        if '.m3u8' in real_source_url:
            m3u8_url = await async_req(
                real_source_url, proxy_addr=proxy_addr, headers=headers, redirect_url=True)
            result['m3u8_url'] = m3u8_url
            result['record_url'] = m3u8_url
        else:
            result['flv_url'] = real_source_url
            result['record_url'] = real_source_url
        result['is_live'] = True
    return result


@trace_error_decorator
async def get_lianjie_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        }

    if cookies:
        headers['cookie'] = cookies

    room_id = url.split('?')[0].rsplit('lailianjie.com/', maxsplit=1)[-1]
    play_api = f'https://api.lailianjie.com/ApiServices/service/live/getRoomInfo?&_$t=&_sign=&roomNumber={room_id}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    room_data = json_data['data']
    anchor_name = room_data['nickname']
    live_status = room_data['isonline']

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        title = room_data['defaultRoomTitle']
        webrtc_url = room_data['videoUrl']
        https_url = "https://" + webrtc_url.split('webrtc://')[1]
        flv_url = https_url.replace('?', '.flv?')
        m3u8_url = https_url.replace('?', '.m3u8?')
        result |= {'is_live': True, 'title': title, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_laixiu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    def generate_uuid(ua_type: str):
        if ua_type == "mobile":
            return str(uuid.uuid4())
        return str(uuid.uuid4()).replace('-', '')

    def calculate_sign(ua_type: str = 'pc'):
        a = int(time.time() * 1000)
        s = generate_uuid(ua_type)
        u = 'kk792f28d6ff1f34ec702c08626d454b39pro'

        input_str = f"web{s}{a}{u}"
        md5_hash = hashlib.md5(input_str.encode('utf-8')).hexdigest()

        return {
            'timestamp': a,
            'imei': s,
            'requestId': md5_hash,
            'inputString': input_str
        }

    sign_data = calculate_sign(ua_type='pc')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'mobileModel': 'web',
        'timestamp': str(sign_data['timestamp']),
        'loginType': '2',
        'versionCode': '10003',
        'imei': sign_data['imei'],
        'requestId': sign_data['requestId'],
        'channel': '9',
        'version': '1.0.0',
        'os': 'web',
        'platform': 'WEB',
        'Origin': 'https://www.imkktv.com',
        'Referer': 'https://www.imkktv.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    }

    if cookies:
        headers['cookie'] = cookies

    pattern = r"(?:roomId|anchorId)=(.*?)(?=&|$)"
    match = re.search(pattern, url)
    room_id = match.group(1) if match else ''
    play_api = f'https://api.imkktv.com/liveroom/getShareLiveVideo?roomId={room_id}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    room_data = json_data['data']
    anchor_name = room_data['nickname']
    live_status = room_data['playStatus'] == 0

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status:
        flv_url = room_data['playUrl']
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_picarto_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        }

    if cookies:
        headers['cookie'] = cookies

    anchor_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    api = f'https://ptvintern.picarto.tv/api/channel/detail/{anchor_id}'

    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    anchor_name = json_data['channel']['name']
    live_status = json_data['channel']['online']

    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        title = json_data['channel']['title']
        m3u8_url = f"https://1-edge1-us-newyork.picarto.tv/stream/hls/golive+{anchor_name}/index.m3u8"
        result |= {'is_live': True, 'title': title, 'm3u8_url': m3u8_url, 'record_url': m3u8_url}
    return result