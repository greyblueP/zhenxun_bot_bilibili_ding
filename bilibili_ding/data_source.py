import httpx
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.log import logger

from utils.browser import get_browser
from utils.message_builder import image

from pathlib import Path

null = ""
head = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.50"
}


async def GetInfo(mid: str):  # 返回格式为状态码(int),用户名(str)，直播间存在(int)
    param = {'mid': mid, 'jsonp': 'jsonp'}
    url = "https://api.bilibili.com/x/space/acc/info"
    async with httpx.AsyncClient() as client:
        try:
            re = await client.get(url=url, headers=head, params=param)
        except:
            logger.error('获取用户信息失败')
            return -1, '', 0
        data = re.json()
    status = data['code']
    if(status != 0):
        return status, '', 0
    Name = data['data']['name']
    LiveRoom = data['data']['live_room']
    try:
        RoomStatus = LiveRoom['roomStatus']  # 1为直播间存在
    except:
        RoomStatus = 0
    return status, Name, RoomStatus


async def LiveRoomInfo(mid: str):  # 返回格式为状态码(int),直播状态码(int)，推送内容
    url = f"https://api.bilibili.com/x/space/wbi/acc/info?mid={mid}&token=&platform=web&w_rid=213155d0da46f257c97bc4c2e44fd233&wts=1671116667"
    async with httpx.AsyncClient() as client:
        try:
            re = await client.get(url=url, headers=head)
        except:
            logger.error('更新直播间信息失败')
            return -1, 0, ''
        data = re.json()
    status = data['code']
    if(status != 0):
        return status, 0, ''
    LiveRoom = data['data']['live_room']
    Name = data['data']['name']
    try:
        LiveStatus = LiveRoom['liveStatus']  # 1为直播中
    except:
        LiveStatus = 0
    LiveURL = LiveRoom['url']
    LiveTitle = LiveRoom['title']
    LiveCover = LiveRoom['cover']

    text = str(LiveStatus).replace('1', '开播').replace('0', '下播')
    text = text.replace('99', '开播')  # 加密直播间
    return status, LiveStatus, '您关注的 {} {}了！\n'.format(Name, text)+'\n'+LiveTitle+'\n'+MessageSegment.image(LiveCover)+'\n'+LiveURL


async def LatestDynamicInfo(mid: str, times: int):  # 状态码，动态时间，动态内容
    url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?offset=&host_mid={mid}&timezone_offset=-480'
    async with httpx.AsyncClient() as client:
        try:
            re = await client.get(url=url, headers=head)
        except:
            logger.error('更新动态信息失败')
            return -1, '', ''
        data = re.json()
    status = data['code']  # 0为成功，其它均为失败
    if(status != 0):
        return status, '', ''
    # 确认上一条推送之后的新动态
    if times != 0:
        newone = 0
        for i in range(1, 10):
            pub_ts = data['data']['items'][i]['modules']['module_author']['pub_ts']
            if pub_ts <= times:
                newone = i-1
                break
        # 确定这个动态是真的新动态
        pub_ts = data['data']['items'][newone]['modules']['module_author']['pub_ts']
        if pub_ts <= times:
            return status, '', ''
    else:  # 没有历史记录
        for i in range(5):
            pub_ts = data['data']['items'][i]['modules']['module_author']['pub_ts']
            if pub_ts > times:
                times = pub_ts
            else:
                newone = i-1
                pub_ts = data['data']['items'][newone]['modules']['module_author']['pub_ts']
                break
    # 获取内容
    LatestDynamic = data['data']['items'][newone]
    # 动态类型1
    Type = LatestDynamic['type']
    # 动态类型2
    DynamicType = LatestDynamic['basic']['comment_type']
    # 动态id
    LatestDynamicID = LatestDynamic['id_str']
    # 动态链接
    LatestDynamicURLMobile = 'https://m.bilibili.com/dynamic/'+LatestDynamicID
    # up名字
    Name = LatestDynamic['modules']['module_author']['name']
    # 判断动态内容
    # 视频动态
    if DynamicType == 1:
        Details = LatestDynamic['modules']['module_dynamic']['major']['archive']
        BV = Details['bvid']
        VideoTitle = Details['title'].replace('\/', '/')
        VideoCover = MessageSegment.image(Details['cover'].replace('\/', '/'))
        VideoURL = 'https://b23.tv/'+BV
        return status, pub_ts, '您关注的 {} 投稿了新视频：'.format(Name)+'\n'+VideoTitle+'\n'+VideoCover+'\n'+VideoURL
    # 跳过直播动态
    elif DynamicType == 17 and Type == 'DYNAMIC_TYPE_LIVE_RCMD':
        return status, pub_ts, ''
    else:
        # 动态截图
        browser = await get_browser()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(
            f"https://t.bilibili.com/{LatestDynamicID}",
            wait_until="networkidle",
            timeout=5*60*1000,
        )
        await page.set_viewport_size(
            {"width": 2560, "height": 1080, "timeout": 5*60*1000}
        )
        # 展开
        await page.wait_for_selector(".bili-dyn-item__main")
        card = page.locator(".bili-dyn-item__main")
        await card.wait_for()
        # 截图并保存
        file = Path.cwd()/'my_plugins'/'bilibili_ding'/'dynamic'/f'{mid}.jpg'
        await card.screenshot(path=file)
        await context.close()
        await page.close()
        return status, pub_ts, '您关注的 {} 发布了新动态：\n'.format(Name)+image(file)+'\n'+LatestDynamicURLMobile
